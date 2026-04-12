import os.path

from status import error, info, success, warning
import sys
import re
import json
import uuid
import time
import requests
import websocket
from urllib.parse import urlencode, urlparse
from pathlib import Path
from datetime import datetime

from config import *

class ComfyUI:
    def __init__(self):
        self.client_id = str(uuid.uuid4())

        image_api_base_url = get_image_gen_base()
        http_base = image_api_base_url.rstrip("/")

        parsed = urlparse(image_api_base_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid image_api_base_url: {image_api_base_url}")

        self.ws_scheme = "wss" if parsed.scheme == "https" else "ws"
        self.ws_base = f"{self.ws_scheme}://{parsed.netloc}/ws"

    # =========================================================
    # STRING HELPERS
    # =========================================================
    def slugify(self, text: str, max_length: int = 60) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9]+", "_", text)
        text = text.strip("_")
        return text[:max_length] or "image"

    # =========================================================
    # ASPECT RATIO HELPERS
    # =========================================================
    def parse_aspect_ratio(self, ratio: str) -> tuple[int, int]:
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

    def nearest_multiple(self, value: int, multiple: int = 64) -> int:
        return max(multiple, round(value / multiple) * multiple)

    def compute_dimensions_from_ratio(self, ratio: str, base_pixels: int = 1024) -> tuple[int, int]:
        """
        Compute a sensible width/height pair from an aspect ratio.
        Keeps the long side near base_pixels and rounds both to a multiple of 64.
        """
        w_ratio, h_ratio = self.parse_aspect_ratio(ratio)

        if w_ratio == h_ratio:
            width = base_pixels
            height = base_pixels
        elif w_ratio > h_ratio:
            width = base_pixels
            height = int(base_pixels * h_ratio / w_ratio)
        else:
            height = base_pixels
            width = int(base_pixels * w_ratio / h_ratio)

        width = self.nearest_multiple(width, 64)
        height = self.nearest_multiple(height, 64)

        return width, height

    # =========================================================
    # WORKFLOW HELPERS
    # =========================================================
    def load_workflow(self, path: str) -> dict:
        info(f"Loading workflow JSON from: {path}", False)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Workflow file does not exist: {path}")

        with open(path, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        if not isinstance(workflow, dict):
            raise ValueError("workflow_api.json must contain a JSON object at the top level.")

        info(f"Workflow loaded with {len(workflow)} nodes.", False)
        return workflow

    def replace_model(self, workflow: dict, model_name: str) -> bool:
        """
        Replace CheckpointLoaderSimple.ckpt_name from config.image_model
        """

        if get_verbose():
            info("Looking for CheckpointLoaderSimple node to replace model...", False)

        for node_id, node in workflow.items():
            class_type = node.get("class_type", "")
            inputs = node.get("inputs", {})

            if get_verbose():
                info(f"Inspecting node {node_id}: class_type={class_type}", False)

            if class_type == "CheckpointLoaderSimple" and "ckpt_name" in inputs:
                old_model = inputs.get("ckpt_name", "")
                inputs["ckpt_name"] = model_name

                if get_verbose():
                    info(f"Model replaced in node {node_id}.", False)
                    info(f"Old model: {old_model}", False)
                    info(f"New model: {model_name}", False)
                return True

        warning("No CheckpointLoaderSimple node with ckpt_name was found.")
        return False

    def inject_prompt(self, workflow: dict, prompt_text: str, aspect_ratio: str = "") -> bool:
        """
        Replace the first positive CLIPTextEncode text prompt.
        Appends aspect ratio hint to the prompt.
        """
        final_prompt = prompt_text.strip()
        if aspect_ratio:
            final_prompt = f"{final_prompt}, aspect ratio {aspect_ratio}"

        if get_verbose():
            info("Looking for positive CLIPTextEncode node to inject the custom prompt...", False)

        for node_id, node in workflow.items():
            class_type = node.get("class_type", "")
            meta_title = str(node.get("_meta", {}).get("title", "")).lower()
            inputs = node.get("inputs", {})

            if get_verbose():
                info(f"Inspecting node {node_id}: class_type={class_type}, title={meta_title}", False)

            if class_type == "CLIPTextEncode" and "text" in inputs:
                current_text = str(inputs.get("text", ""))
                is_negative = (
                        "negative" in meta_title
                        or current_text.strip().lower() in {"text, watermark", "watermark", "bad quality"}
                )

                if is_negative:
                    if get_verbose():
                        info(f"Skipping likely negative prompt node {node_id}.", False)
                    continue

                old_prompt = inputs.get("text", "")
                inputs["text"] = final_prompt
                if get_verbose():
                    info(f"Prompt replaced in node {node_id}.", False)
                    info(f"Old prompt: {old_prompt}", False)
                    info(f"New prompt: {final_prompt}", False)
                return True

        warning("No positive CLIPTextEncode node with a text input was found.")
        return False

    def replace_image_size(self, workflow: dict, aspect_ratio: str, base_pixels: int = 1024) -> bool:
        """
        Replace EmptyLatentImage.width and EmptyLatentImage.height based on config.image_aspect_ratio
        """
        width, height = self.compute_dimensions_from_ratio(aspect_ratio, base_pixels=base_pixels)
        if get_verbose():
            info(f"Computed image size from aspect ratio {aspect_ratio}: {width}x{height}")

        for node_id, node in workflow.items():
            class_type = node.get("class_type", "")
            inputs = node.get("inputs", {})

            if get_verbose():
                info(f"Inspecting node {node_id}: class_type={class_type}")

            if class_type == "EmptyLatentImage" and "width" in inputs and "height" in inputs:
                old_width = inputs.get("width")
                old_height = inputs.get("height")

                inputs["width"] = width
                inputs["height"] = height

                if get_verbose():
                    info(f"Image size replaced in node {node_id}.")
                    info(f"Old size: {old_width}x{old_height}")
                    info(f"New size: {width}x{height}")
                return True

        warning("No EmptyLatentImage node with width/height was found.")
        return False

    def randomise_seed(self, workflow: dict) -> bool:
        seed_value = int(time.time() * 1000) % 2 ** 31
        if get_verbose():
            info(f"Trying to update seed to: {seed_value}", False)

        for node_id, node in workflow.items():
            class_type = node.get("class_type", "")
            inputs = node.get("inputs", {})

            if "KSampler" in class_type and "seed" in inputs:
                old_seed = inputs.get("seed")
                inputs["seed"] = seed_value

                if get_verbose():
                    info(f"Seed updated in node {node_id}.", False)
                    info(f"Old seed: {old_seed}", False)
                    info(f"New seed: {seed_value}", False)
                return True

        warning("No sampler node with a seed input was found.")
        return False

    # =========================================================
    # API CALLS
    # =========================================================
    def build_headers(self, api_key: str) -> dict:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            if get_verbose():
                info("Using Authorization header from image_api_key.")
        else:
            if get_verbose():
                info("No image_api_key configured; sending requests without auth.")
        return headers

    def queue_prompt(self, http_base: str, api_key: str, workflow: dict) -> str:
        url = f"{http_base}/prompt"
        payload = {
            "prompt": workflow,
            "client_id": self.client_id,
        }

        headers = self.build_headers(api_key)

        if get_verbose():
            info(f"Queueing prompt to: {url}", False)
            info(f"Payload keys: {list(payload.keys())}", False)

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if get_verbose():
            info(f"/prompt response status: {response.status_code}", False)
        response.raise_for_status()

        data = response.json()
        if get_verbose():
            info(f"/prompt response JSON: {json.dumps(data, indent=2)}", False)

        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise RuntimeError("ComfyUI did not return a prompt_id.")

        if get_verbose():
            info(f"Prompt queued successfully. prompt_id={prompt_id}", False)
        return prompt_id

    def wait_for_completion(self, ws_base: str, prompt_id: str) -> None:
        ws_url = f"{ws_base}?clientId={self.client_id}"
        if get_verbose():
            info(f"Opening WebSocket connection: {ws_url}", False)

        ws = websocket.create_connection(ws_url, timeout=60)

        if get_verbose():
            info("WebSocket connected. Waiting for generation events...", False)

        try:
            while True:
                message = ws.recv()

                if isinstance(message, bytes):
                    if get_verbose():
                        info(f"Received binary WebSocket frame ({len(message)} bytes). Ignoring preview frame.", False)
                    continue

                if get_verbose():
                    info(f"Received WebSocket text frame: {message}", False)

                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    warning("Received non-JSON WebSocket message. Ignoring.")
                    continue

                msg_type = data.get("type")
                msg_data = data.get("data", {})

                if msg_type == "status":
                    info(f"Status update: {json.dumps(msg_data, indent=2)}")

                elif msg_type == "progress":
                    value = msg_data.get("value")
                    maximum = msg_data.get("max")
                    info(f"Progress: {value}/{maximum}")

                elif msg_type == "executing":
                    node = msg_data.get("node")
                    current_prompt_id = msg_data.get("prompt_id")
                    info(f"Executing event: node={node}, prompt_id={current_prompt_id}")

                    if current_prompt_id == prompt_id and node is None:
                        info("Generation finished.")
                        break

                elif msg_type == "execution_error":
                    raise RuntimeError(f"ComfyUI reported an execution error: {json.dumps(msg_data, indent=2)}")

                else:
                    info(f"Unhandled WebSocket event type: {msg_type}")

        finally:
            info("Closing WebSocket connection.")
            ws.close()

    def get_history(self, http_base: str, api_key: str, prompt_id: str) -> dict:
        url = f"{http_base}/history/{prompt_id}"
        headers = self.build_headers(api_key)

        info(f"Fetching history from: {url}")

        response = requests.get(url, headers=headers, timeout=30)
        info(f"/history response status: {response.status_code}")
        response.raise_for_status()

        data = response.json()
        info(f"/history response JSON keys: {list(data.keys())}")
        return data

    def find_first_image_meta(self, history: dict, prompt_id: str) -> dict:
        info("Searching history output for generated images...")

        prompt_entry = history.get(prompt_id)
        if not prompt_entry:
            raise RuntimeError(f"No history entry found for prompt_id={prompt_id}")

        outputs = prompt_entry.get("outputs", {})
        info(f"History contains outputs for {len(outputs)} nodes.")

        for node_id, node_output in outputs.items():
            info(f"Inspecting output node {node_id}: keys={list(node_output.keys())}")

            images = node_output.get("images")
            if images:
                image_meta = images[0]
                info(f"Found generated image in node {node_id}.")
                info(f"Image metadata: {json.dumps(image_meta, indent=2)}")
                return image_meta

        raise RuntimeError("No generated images were found in the workflow history.")

    def download_image(self, http_base: str, api_key: str, image_meta: dict) -> bytes:
        params = {
            "filename": image_meta["filename"],
            "subfolder": image_meta.get("subfolder", ""),
            "type": image_meta["type"],
        }
        url = f"{http_base}/view?{urlencode(params)}"
        headers = self.build_headers(api_key)

        info(f"Downloading image from: {url}")
        info(f"Image query params: {params}")

        response = requests.get(url, headers=headers, timeout=60)
        info(f"/view response status: {response.status_code}")
        response.raise_for_status()

        info(f"Downloaded image bytes: {len(response.content)}")
        return response.content

    def save_image(self, image_bytes: bytes, output_path: str, prompt: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_slug = self.slugify(prompt)

        out_file = Path(output_path)
        final_name = f"{prompt_slug}_{timestamp}{out_file.suffix}"
        final_path = out_file.with_name(final_name)

        final_path.parent.mkdir(parents=True, exist_ok=True)

        info(f"Saving image to: {final_path}")

        with open(final_path, "wb") as f:
            f.write(image_bytes)

        return str(final_path)

    # =========================================================
    # IMAGE GENERATION FLOW
    # =========================================================
    def generate_image(self, prompt: str) -> str:
        try:
            info("Starting ComfyUI image generation script.")
            workflow_path = get_image_workflow()
            workflow = self.load_workflow(workflow_path)

            if not self.replace_model(workflow, get_image_model()):
                warning("Model was not replaced automatically.")

            if not self.inject_prompt(workflow, prompt):
                warning("Prompt was not replaced automatically.")

            if not self.replace_image_size(workflow, get_aspect_ratio(), base_pixels=get_image_pixels()):
                warning("Image size was not replaced automatically.")

            self.randomise_seed(workflow)

            prompt_id = self.queue_prompt(get_image_gen_base(), get_image_gen_api_key(), workflow)
            self.wait_for_completion(self.ws_base, prompt_id)

            history = self.get_history(get_image_gen_base(), get_image_gen_api_key(), prompt_id)
            image_meta = self.find_first_image_meta(history, prompt_id)
            image_bytes = self.download_image(get_image_gen_base(), get_image_gen_api_key(), image_meta)

            saved_path = self.save_image(
                image_bytes=image_bytes,
                output_path=os.path.join(ROOT_DIR, "output", "images", "image.png"),
                prompt=prompt,
            )

            info(f"Done. Saved file: {saved_path}")
            return saved_path

        except Exception as exc:
            error(str(exc))
            return "FAILED"



