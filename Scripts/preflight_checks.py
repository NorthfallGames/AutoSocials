#!/usr/bin/env python3
import json
import os
import sys
import re
from typing import Tuple, Any
from urllib.parse import urlparse

import requests
from termcolor import colored

ROOT_DIR = os.path.dirname(sys.path[0])
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")


def ok(msg: str) -> None:
    print(colored(f"[OK] {msg}", "green"))


def warn(msg: str) -> None:
    print(colored(f"[WARN] {msg}", "yellow"))


def fail(msg: str) -> None:
    print(colored(f"[FAIL] {msg}", "red"))


def check_url(url: str, timeout: int = 3, headers: dict | None = None) -> Tuple[bool, str]:
    try:
        response = requests.get(url, timeout=timeout, headers=headers or {})
        return True, f"HTTP {response.status_code}"
    except Exception as exc:
        return False, str(exc)


def safe_get_json(url: str, timeout: int = 5, headers: dict | None = None) -> Tuple[bool, Any]:
    try:
        response = requests.get(url, timeout=timeout, headers=headers or {})
        response.raise_for_status()
        return True, response.json()
    except Exception as exc:
        return False, exc


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


def parse_aspect_ratio(ratio: str) -> Tuple[int, int]:
    match = re.fullmatch(r"\s*(\d+)\s*:\s*(\d+)\s*", ratio)
    if not match:
        raise ValueError("Expected format like '1:1', '16:9', or '9:16'.")

    w_ratio = int(match.group(1))
    h_ratio = int(match.group(2))

    if w_ratio <= 0 or h_ratio <= 0:
        raise ValueError("Aspect ratio values must be greater than zero.")

    return w_ratio, h_ratio


def build_auth_headers(api_key: str = "") -> dict:
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def normalise_openai_base_url(provider: str, base_url: str) -> str:
    base = str(base_url or "").strip().rstrip("/")

    if not base:
        return ""

    if provider == "lmstudio":
        if not base.endswith("/v1"):
            base = f"{base}/v1"
    elif provider == "openrouter":
        if base == "https://openrouter.ai":
            base = "https://openrouter.ai/api/v1"
        elif not base.endswith("/api/v1"):
            if base.endswith("/v1"):
                base = f"{base[:-3]}/api/v1"
            else:
                base = f"{base}/api/v1"

    return base


def check_openai_compatible_models(base_url: str, api_key: str = "", timeout: int = 5) -> list[str]:
    headers = build_auth_headers(api_key)
    url = f"{base_url.rstrip('/')}/models"

    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    data = response.json()
    return [m.get("id") for m in data.get("data", []) if m.get("id")]


def find_comfy_model(object_info: dict, model_name: str) -> bool:
    """
    Tries to find the configured checkpoint model in ComfyUI's object_info response.
    We specifically inspect CheckpointLoaderSimple input metadata.
    """
    try:
        node_info = object_info.get("CheckpointLoaderSimple", {})
        input_info = node_info.get("input", {})
        required = input_info.get("required", {})
        ckpt_entry = required.get("ckpt_name")

        if not ckpt_entry or not isinstance(ckpt_entry, list) or not ckpt_entry:
            return False

        available_models = ckpt_entry[0]
        if not isinstance(available_models, list):
            return False

        return model_name in available_models
    except Exception:
        return False


def main() -> int:
    if not os.path.exists(CONFIG_PATH):
        fail(f"Missing config file: {CONFIG_PATH}")
        return 1

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as exc:
        fail(f"Could not read config.json: {exc}")
        return 1

    llm_cfg = cfg.get("llm_details", {})
    image_cfg = cfg.get("llm_image_details", {})
    stt_cfg = cfg.get("stt_details", {})

    failures = 0

    # STT testing
    stt_provider = str(stt_cfg.get("stt_provider", "local_whisper")).strip().lower()
    ok(f"stt_provider={stt_provider}")

    # ImageMagick
    imagemagick_path = cfg.get("imagemagick_path", "")
    if imagemagick_path:
        if os.path.exists(imagemagick_path):
            ok(f"imagemagick_path exists: {imagemagick_path}")
        else:
            warn(
                "imagemagick_path is set but does not exist. "
                "MoviePy subtitle rendering may fail."
            )
    else:
        warn(
            "imagemagick_path is not set. "
            "MoviePy subtitle rendering may fail."
        )

    # Firefox profile
    firefox_profile = cfg.get("firefox_profile", "")
    if firefox_profile:
        if os.path.isdir(firefox_profile):
            ok(f"firefox_profile exists: {firefox_profile}")
        else:
            fail(f"firefox_profile does not exist: {firefox_profile}")
    else:
        fail("firefox_profile is empty. Twitter/YouTube automation requires this.")

    # LLM provider
    llm_provider = str(llm_cfg.get("llm_provider", "ollama")).strip().lower()
    llm_base_raw = str(llm_cfg.get("llm_base_url", "")).strip()
    llm_api_key = str(llm_cfg.get("llm_api_key", "")).strip() or os.environ.get("LLM_API_KEY", "")
    default_model = str(llm_cfg.get("default_model", "")).strip()

    if llm_provider in {"lmstudio", "openrouter"}:
        if not llm_base_raw:
            if llm_provider == "openrouter":
                llm_base_raw = "https://openrouter.ai"
            else:
                fail(f"llm_provider={llm_provider} but llm_base_url is empty")
                failures += 1
                llm_base_raw = ""

        llm_base = normalise_openai_base_url(llm_provider, llm_base_raw)

        if llm_base:
            if not is_valid_url(llm_base):
                fail(f"Invalid llm_base_url for {llm_provider}: {llm_base}")
                failures += 1
            else:
                if llm_provider == "openrouter":
                    if "openrouter.ai" in urlparse(llm_base).netloc.lower():
                        ok(f"OpenRouter base URL configured: {llm_base}")
                    else:
                        warn(f"OpenRouter base URL looks unusual: {llm_base}")

                    if llm_api_key:
                        ok("llm_api_key is set for OpenRouter")
                    else:
                        fail("llm_provider=openrouter but llm_api_key is empty (and LLM_API_KEY is not set)")
                        failures += 1

                elif llm_provider == "lmstudio":
                    if llm_api_key:
                        ok("llm_api_key is set for LM Studio and will be used")
                    else:
                        ok("LM Studio running without llm_api_key")

                try:
                    models = check_openai_compatible_models(llm_base, api_key=llm_api_key)
                    ok(f"{llm_provider} is reachable at {llm_base}")

                    if models:
                        ok(f"{llm_provider} models available: {', '.join(models[:10])}")
                    else:
                        warn(f"No models found in {llm_provider}. Load or enable a model first.")
                except Exception as exc:
                    fail(f"Selected LLM Provider ({llm_provider}) is not reachable at {llm_base}: |__ {exc}")
                    failures += 1

                if default_model:
                    ok(f"default_model={default_model}")
                else:
                    warn("default_model is not set.")
    else:
        reachable, detail = check_url("http://127.0.0.1:11434/api/tags")
        if not reachable:
            fail(f"Ollama is not reachable at http://127.0.0.1:11434/: |__ {detail}")
            failures += 1
        else:
            ok("Ollama reachable at http://127.0.0.1:11434")
            try:
                response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
                response.raise_for_status()
                tags = response.json()
                models = [m.get("name") for m in tags.get("models", []) if m.get("name")]
                if models:
                    ok(f"Ollama models available: {', '.join(models[:10])}")
                else:
                    warn("No models found on Ollama. Pull a model first.")
            except Exception as exc:
                warn(f"Could not validate Ollama model list: {exc}")

    # ComfyUI image generation checks
    image_provider = str(image_cfg.get("llm_image_provider", "")).strip().lower()
    image_base = str(image_cfg.get("image_api_base_url", "")).strip().rstrip("/")
    image_api_key = str(image_cfg.get("image_api_key", "")).strip()
    image_model = str(image_cfg.get("image_model", "")).strip()
    image_aspect_ratio = str(image_cfg.get("image_aspect_ratio", "1:1")).strip()

    if image_provider == "comfyui":
        ok("llm_image_provider=comfyui")

        if not image_base:
            fail("image_api_base_url is empty in llm_image_details")
            failures += 1
        elif not is_valid_url(image_base):
            fail(f"image_api_base_url is invalid: {image_base}")
            failures += 1
        else:
            ok(f"ComfyUI base URL configured: {image_base}")

            headers = build_auth_headers(image_api_key)
            if image_api_key:
                ok("image_api_key is set")
            else:
                warn("image_api_key is empty. This is fine for unsecured local ComfyUI instances.")

            reachable, detail = check_url(f"{image_base}/system_stats", timeout=8, headers=headers)
            if not reachable:
                fail(f"ComfyUI is not reachable at {image_base}: |__ {detail}")
                failures += 1
            else:
                ok(f"ComfyUI reachable at {image_base}")

                success, stats_or_exc = safe_get_json(f"{image_base}/system_stats", timeout=8, headers=headers)
                if success:
                    ok("ComfyUI /system_stats responded with valid JSON")
                else:
                    warn(f"Could not parse ComfyUI /system_stats JSON: {stats_or_exc}")

                success, object_info_or_exc = safe_get_json(f"{image_base}/object_info", timeout=12, headers=headers)
                if success:
                    ok("ComfyUI /object_info responded with valid JSON")

                    if image_model:
                        if find_comfy_model(object_info_or_exc, image_model):
                            ok(f"Configured image_model found in ComfyUI: {image_model}")
                        else:
                            warn(
                                f"Configured image_model was not found in ComfyUI object info: {image_model}"
                            )
                    else:
                        fail("image_model is empty in llm_image_details")
                        failures += 1
                else:
                    warn(f"Could not validate ComfyUI /object_info: {object_info_or_exc}")
                    if not image_model:
                        fail("image_model is empty in llm_image_details")
                        failures += 1

        try:
            w_ratio, h_ratio = parse_aspect_ratio(image_aspect_ratio)
            ok(f"image_aspect_ratio valid: {w_ratio}:{h_ratio}")
        except Exception as exc:
            fail(f"Invalid image_aspect_ratio '{image_aspect_ratio}': {exc}")
            failures += 1

    elif image_provider:
        fail(f"Unsupported llm_image_provider: {image_provider}")
        failures += 1
    else:
        warn("llm_image_provider is not set.")

    # STT import validation
    if stt_provider == "local_whisper":
        try:
            import faster_whisper  # noqa: F401
            ok("faster-whisper is installed")
        except Exception as exc:
            fail(f"faster-whisper is not importable: {exc}")
            failures += 1

    return failures


if __name__ == "__main__":
    sys.exit(main())