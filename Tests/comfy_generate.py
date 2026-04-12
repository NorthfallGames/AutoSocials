#!/usr/bin/env python3
import os
import sys
import re
import json
import uuid
import time
import argparse
import io
from pathlib import Path
from urllib.parse import urlencode, urlparse
from datetime import datetime

import requests
import websocket
from PIL import Image

ROOT_DIR = os.path.dirname(sys.path[0])
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
CLIENT_ID = str(uuid.uuid4())

# =========================================================
# LOGGING
# =========================================================
def log(msg: str) -> None:
    print(f"[INFO] {msg}", flush=True)

def dbg(msg: str) -> None:
    print(f"[DEBUG] {msg}", flush=True)

def warn(msg: str) -> None:
    print(f"[WARN] {msg}", flush=True)

def fail(msg: str) -> None:
    print(f"[FAIL] {msg}", flush=True)


# =========================================================
# CONFIG HELPERS
# =========================================================
def load_config() -> dict:
    log(f"Loading config from: {CONFIG_PATH}")

    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    if not isinstance(cfg, dict):
        raise ValueError("config.json must contain a JSON object at the top level.")

    image_cfg = cfg.get("llm_image_details")
    if not isinstance(image_cfg, dict):
        raise ValueError("llm_image_details block is missing or invalid in config.json")

    provider = str(image_cfg.get("llm_image_provider", "")).strip().lower()
    if provider != "comfyui":
        raise ValueError(f"Unsupported llm_image_provider: {provider!r}. Expected 'comfyui'.")

    image_api_base_url = str(image_cfg.get("image_api_base_url", "")).strip()
    if not image_api_base_url:
        raise ValueError("image_api_base_url is missing in llm_image_details")

    parsed = urlparse(image_api_base_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid image_api_base_url: {image_api_base_url}")

    image_api_key = str(image_cfg.get("image_api_key", "")).strip()
    image_model = str(image_cfg.get("image_model", "")).strip()
    image_aspect_ratio = str(image_cfg.get("image_aspect_ratio", "1:1")).strip()

    if not image_model:
        raise ValueError("image_model is missing in llm_image_details")

    http_base = image_api_base_url.rstrip("/")
    ws_scheme = "wss" if parsed.scheme == "https" else "ws"
    ws_base = f"{ws_scheme}://{parsed.netloc}/ws"

    out = {
        "provider": provider,
        "http_base": http_base,
        "ws_base": ws_base,
        "api_key": image_api_key,
        "model": image_model,
        "aspect_ratio": image_aspect_ratio,
    }

    dbg(f"Resolved HTTP base: {out['http_base']}")
    dbg(f"Resolved WS base: {out['ws_base']}")
    dbg(f"Configured model: {out['model']}")
    dbg(f"Configured aspect ratio: {out['aspect_ratio']}")

    return out


# =========================================================
# PATH HELPERS
# =========================================================
def resolve_project_path(path: str) -> str:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    resolved = (project_root / path).resolve()

    dbg(f"Resolving path: {path} -> {resolved}")
    return str(resolved)


# =========================================================
# STRING HELPERS
# =========================================================
def slugify(text: str, max_length: int = 60) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text[:max_length] or "image"


# =========================================================
# ASPECT RATIO HELPERS
# =========================================================
def parse_aspect_ratio(ratio: str) -> tuple[int, int]:
    """
    Parses strings like:
      1:1
      16:9
      9:16
      4:3
    """
    match = re.fullmatch(r"\s*(\d+)\s*:\s*(\d+)\s*", ratio)
    if not match:
        raise ValueError(f"Invalid image_aspect_ratio: {ratio!r}. Expected format like '1:1' or '16:9'.")

    w_ratio = int(match.group(1))
    h_ratio = int(match.group(2))

    if w_ratio <= 0 or h_ratio <= 0:
        raise ValueError(f"Invalid image_aspect_ratio values: {ratio!r}")

    return w_ratio, h_ratio


def nearest_multiple(value: int, multiple: int = 64) -> int:
    return max(multiple, round(value / multiple) * multiple)


def compute_dimensions_from_ratio(ratio: str, base_pixels: int = 1024) -> tuple[int, int]:
    """
    Compute a sensible width/height pair from an aspect ratio.
    Keeps the long side near base_pixels and rounds both to a multiple of 64.
    """
    w_ratio, h_ratio = parse_aspect_ratio(ratio)

    if w_ratio == h_ratio:
        width = base_pixels
        height = base_pixels
    elif w_ratio > h_ratio:
        width = base_pixels
        height = int(base_pixels * h_ratio / w_ratio)
    else:
        height = base_pixels
        width = int(base_pixels * w_ratio / h_ratio)

    width = nearest_multiple(width, 64)
    height = nearest_multiple(height, 64)

    return width, height


# =========================================================
# WORKFLOW HELPERS
# =========================================================
def load_workflow(path: str) -> dict:
    log(f"Loading workflow JSON from: {path}")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Workflow file does not exist: {path}")

    with open(path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    if not isinstance(workflow, dict):
        raise ValueError("workflow_api.json must contain a JSON object at the top level.")

    dbg(f"Workflow loaded with {len(workflow)} nodes.")
    return workflow


def replace_model(workflow: dict, model_name: str) -> bool:
    """
    Replace CheckpointLoaderSimple.ckpt_name from config.image_model
    """
    log("Looking for CheckpointLoaderSimple node to replace model...")

    for node_id, node in workflow.items():
        class_type = node.get("class_type", "")
        inputs = node.get("inputs", {})

        dbg(f"Inspecting node {node_id}: class_type={class_type}")

        if class_type == "CheckpointLoaderSimple" and "ckpt_name" in inputs:
            old_model = inputs.get("ckpt_name", "")
            inputs["ckpt_name"] = model_name

            log(f"Model replaced in node {node_id}.")
            dbg(f"Old model: {old_model}")
            dbg(f"New model: {model_name}")
            return True

    warn("No CheckpointLoaderSimple node with ckpt_name was found.")
    return False


def inject_prompt(workflow: dict, prompt_text: str, aspect_ratio: str = "") -> bool:
    """
    Replace the first positive CLIPTextEncode text prompt.
    Appends aspect ratio hint to the prompt.
    """
    final_prompt = prompt_text.strip()
    if aspect_ratio:
        final_prompt = f"{final_prompt}, aspect ratio {aspect_ratio}"

    log("Looking for positive CLIPTextEncode node to inject the custom prompt...")

    for node_id, node in workflow.items():
        class_type = node.get("class_type", "")
        meta_title = str(node.get("_meta", {}).get("title", "")).lower()
        inputs = node.get("inputs", {})

        dbg(f"Inspecting node {node_id}: class_type={class_type}, title={meta_title}")

        if class_type == "CLIPTextEncode" and "text" in inputs:
            current_text = str(inputs.get("text", ""))
            is_negative = (
                "negative" in meta_title
                or current_text.strip().lower() in {"text, watermark", "watermark", "bad quality"}
            )

            if is_negative:
                dbg(f"Skipping likely negative prompt node {node_id}.")
                continue

            old_prompt = inputs.get("text", "")
            inputs["text"] = final_prompt

            log(f"Prompt replaced in node {node_id}.")
            dbg(f"Old prompt: {old_prompt}")
            dbg(f"New prompt: {final_prompt}")
            return True

    warn("No positive CLIPTextEncode node with a text input was found.")
    return False


def replace_image_size(workflow: dict, aspect_ratio: str, base_pixels: int = 1024) -> bool:
    """
    Replace EmptyLatentImage.width and EmptyLatentImage.height based on config.image_aspect_ratio
    """
    width, height = compute_dimensions_from_ratio(aspect_ratio, base_pixels=base_pixels)
    log(f"Computed image size from aspect ratio {aspect_ratio}: {width}x{height}")

    for node_id, node in workflow.items():
        class_type = node.get("class_type", "")
        inputs = node.get("inputs", {})

        dbg(f"Inspecting node {node_id}: class_type={class_type}")

        if class_type == "EmptyLatentImage" and "width" in inputs and "height" in inputs:
            old_width = inputs.get("width")
            old_height = inputs.get("height")

            inputs["width"] = width
            inputs["height"] = height

            log(f"Image size replaced in node {node_id}.")
            dbg(f"Old size: {old_width}x{old_height}")
            dbg(f"New size: {width}x{height}")
            return True

    warn("No EmptyLatentImage node with width/height was found.")
    return False


def randomise_seed(workflow: dict) -> bool:
    seed_value = int(time.time() * 1000) % 2**31
    log(f"Trying to update seed to: {seed_value}")

    for node_id, node in workflow.items():
        class_type = node.get("class_type", "")
        inputs = node.get("inputs", {})

        if "KSampler" in class_type and "seed" in inputs:
            old_seed = inputs.get("seed")
            inputs["seed"] = seed_value

            log(f"Seed updated in node {node_id}.")
            dbg(f"Old seed: {old_seed}")
            dbg(f"New seed: {seed_value}")
            return True

    warn("No sampler node with a seed input was found.")
    return False


# =========================================================
# API CALLS
# =========================================================
def build_headers(api_key: str) -> dict:
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        dbg("Using Authorization header from image_api_key.")
    else:
        dbg("No image_api_key configured; sending requests without auth.")
    return headers


def queue_prompt(http_base: str, api_key: str, workflow: dict) -> str:
    url = f"{http_base}/prompt"
    payload = {
        "prompt": workflow,
        "client_id": CLIENT_ID,
    }

    headers = build_headers(api_key)

    log(f"Queueing prompt to: {url}")
    dbg(f"Payload keys: {list(payload.keys())}")

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    dbg(f"/prompt response status: {response.status_code}")
    response.raise_for_status()

    data = response.json()
    dbg(f"/prompt response JSON: {json.dumps(data, indent=2)}")

    prompt_id = data.get("prompt_id")
    if not prompt_id:
        raise RuntimeError("ComfyUI did not return a prompt_id.")

    log(f"Prompt queued successfully. prompt_id={prompt_id}")
    return prompt_id


def wait_for_completion(ws_base: str, prompt_id: str) -> None:
    ws_url = f"{ws_base}?clientId={CLIENT_ID}"
    log(f"Opening WebSocket connection: {ws_url}")

    ws = websocket.create_connection(ws_url, timeout=60)
    log("WebSocket connected. Waiting for generation events...")

    try:
        while True:
            message = ws.recv()

            if isinstance(message, bytes):
                dbg(f"Received binary WebSocket frame ({len(message)} bytes). Ignoring preview frame.")
                continue

            dbg(f"Received WebSocket text frame: {message}")

            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                warn("Received non-JSON WebSocket message. Ignoring.")
                continue

            msg_type = data.get("type")
            msg_data = data.get("data", {})

            if msg_type == "status":
                dbg(f"Status update: {json.dumps(msg_data, indent=2)}")

            elif msg_type == "progress":
                value = msg_data.get("value")
                maximum = msg_data.get("max")
                log(f"Progress: {value}/{maximum}")

            elif msg_type == "executing":
                node = msg_data.get("node")
                current_prompt_id = msg_data.get("prompt_id")
                dbg(f"Executing event: node={node}, prompt_id={current_prompt_id}")

                if current_prompt_id == prompt_id and node is None:
                    log("Generation finished.")
                    break

            elif msg_type == "execution_error":
                raise RuntimeError(f"ComfyUI reported an execution error: {json.dumps(msg_data, indent=2)}")

            else:
                dbg(f"Unhandled WebSocket event type: {msg_type}")

    finally:
        log("Closing WebSocket connection.")
        ws.close()


def get_history(http_base: str, api_key: str, prompt_id: str) -> dict:
    url = f"{http_base}/history/{prompt_id}"
    headers = build_headers(api_key)

    log(f"Fetching history from: {url}")

    response = requests.get(url, headers=headers, timeout=30)
    dbg(f"/history response status: {response.status_code}")
    response.raise_for_status()

    data = response.json()
    dbg(f"/history response JSON keys: {list(data.keys())}")
    return data


def find_first_image_meta(history: dict, prompt_id: str) -> dict:
    log("Searching history output for generated images...")

    prompt_entry = history.get(prompt_id)
    if not prompt_entry:
        raise RuntimeError(f"No history entry found for prompt_id={prompt_id}")

    outputs = prompt_entry.get("outputs", {})
    dbg(f"History contains outputs for {len(outputs)} nodes.")

    for node_id, node_output in outputs.items():
        dbg(f"Inspecting output node {node_id}: keys={list(node_output.keys())}")

        images = node_output.get("images")
        if images:
            image_meta = images[0]
            log(f"Found generated image in node {node_id}.")
            dbg(f"Image metadata: {json.dumps(image_meta, indent=2)}")
            return image_meta

    raise RuntimeError("No generated images were found in the workflow history.")


def download_image(http_base: str, api_key: str, image_meta: dict) -> bytes:
    params = {
        "filename": image_meta["filename"],
        "subfolder": image_meta.get("subfolder", ""),
        "type": image_meta["type"],
    }
    url = f"{http_base}/view?{urlencode(params)}"
    headers = build_headers(api_key)

    log(f"Downloading image from: {url}")
    dbg(f"Image query params: {params}")

    response = requests.get(url, headers=headers, timeout=60)
    dbg(f"/view response status: {response.status_code}")
    response.raise_for_status()

    log(f"Downloaded image bytes: {len(response.content)}")
    return response.content


def save_and_show_image(image_bytes: bytes, output_path: str, prompt: str, show: bool = True) -> Path:
    log("Opening image with Pillow...")
    image = Image.open(io.BytesIO(image_bytes))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt_slug = slugify(prompt)

    out_file = Path(output_path)
    final_name = f"{prompt_slug}_{timestamp}{out_file.suffix}"
    final_path = out_file.with_name(final_name)

    final_path.parent.mkdir(parents=True, exist_ok=True)

    log(f"Saving image to: {final_path}")
    image.save(final_path)

    if show:
        log("Displaying image...")
        image.show()
    else:
        dbg("Image display disabled.")

    return final_path


# =========================================================
# MAIN
# =========================================================
def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and show an image via ComfyUI API.")
    parser.add_argument(
        "--workflow",
        default="Assets/workflow_api.json",
        help="Path to a ComfyUI workflow exported using Save (API format), relative to project root."
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Custom prompt text to inject into the workflow."
    )
    parser.add_argument(
        "--output",
        default="output/generated.png",
        help="Base output file path, relative to project root."
    )
    parser.add_argument(
        "--base-pixels",
        type=int,
        default=1024,
        help="Target long side used when deriving size from aspect ratio."
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open the image after saving."
    )
    args = parser.parse_args()

    log("Starting ComfyUI image generation script.")
    dbg(f"CLIENT_ID={CLIENT_ID}")
    dbg(f"Args={args}")

    try:
        cfg = load_config()

        workflow_path = resolve_project_path(args.workflow)
        output_path = resolve_project_path(args.output)

        log(f"Image provider: {cfg['provider']}")
        log(f"Image API base URL: {cfg['http_base']}")
        log(f"Configured model: {cfg['model']}")
        log(f"Configured aspect ratio: {cfg['aspect_ratio']}")

        workflow = load_workflow(workflow_path)

        if not replace_model(workflow, cfg["model"]):
            warn("Model was not replaced automatically.")

        if not inject_prompt(workflow, args.prompt, cfg["aspect_ratio"]):
            warn("Prompt was not replaced automatically.")

        if not replace_image_size(workflow, cfg["aspect_ratio"], base_pixels=args.base_pixels):
            warn("Image size was not replaced automatically.")

        randomise_seed(workflow)

        prompt_id = queue_prompt(cfg["http_base"], cfg["api_key"], workflow)
        wait_for_completion(cfg["ws_base"], prompt_id)

        history = get_history(cfg["http_base"], cfg["api_key"], prompt_id)
        image_meta = find_first_image_meta(history, prompt_id)
        image_bytes = download_image(cfg["http_base"], cfg["api_key"], image_meta)

        saved_path = save_and_show_image(
            image_bytes=image_bytes,
            output_path=output_path,
            prompt=args.prompt,
            show=not args.no_show
        )

        log(f"Done. Saved file: {saved_path}")
        return 0

    except Exception as exc:
        fail(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())