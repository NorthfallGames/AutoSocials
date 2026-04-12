import json
import os

import openai
import ollama
from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam

from config import *

_selected_model: str | None = None


def _normalise_provider(provider: str) -> str:
    value = str(provider or "").strip().lower().replace(" ", "").replace("_", "")
    if value == "lmstudio":
        return "lmstudio"
    if value == "openrouter":
        return "openrouter"
    return "ollama"


def _normalise_openai_base_url(provider: str, base_url: str) -> str:
    base = str(base_url or "").strip().rstrip("/")

    if provider == "openrouter":
        if not base:
            return "https://openrouter.ai/api/v1"
        if base == "https://openrouter.ai":
            return "https://openrouter.ai/api/v1"
        if base.endswith("/api/v1"):
            return base
        if base.endswith("/v1"):
            return f"{base[:-3]}/api/v1"
        return f"{base}/api/v1"

    if provider == "lmstudio":
        if not base:
            return "http://127.0.0.1:1234/v1"
        if base.endswith("/v1"):
            return base
        return f"{base}/v1"

    return base


def _get_llm_settings() -> dict[str, str]:
    cfg = {}
    try:
        with open(os.path.join(ROOT_DIR, "config.json"), "r", encoding="utf-8") as file:
            cfg = json.load(file)
    except Exception:
        cfg = {}

    llm_cfg = cfg.get("llm_details", {}) if isinstance(cfg, dict) else {}

    provider = _normalise_provider(llm_cfg.get("llm_provider") or get_llm_provider())
    base_url = str(llm_cfg.get("llm_base_url", "")).strip()
    endpoint = str(llm_cfg.get("llm_endpoint", "")).strip()
    default_model = str(llm_cfg.get("default_model", "")).strip() or get_default_model()

    api_key = str(llm_cfg.get("llm_api_key", "")).strip()
    if not api_key:
        api_key = os.environ.get("LLM_API_KEY", "").strip()
    if not api_key:
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()

    if not base_url:
        if provider == "openrouter":
            base_url = "https://openrouter.ai"
        elif provider == "lmstudio":
            base_url = "http://127.0.0.1:1234"
        else:
            base_url = get_ollama_base_url()

    return {
        "provider": provider,
        "base_url": base_url,
        "api_key": api_key,
        "default_model": default_model,
        "endpoint": endpoint,
    }


def _openai_client(settings: dict[str, str]) -> openai.Client:
    provider = settings["provider"]
    api_key = settings["api_key"]
    base_url = _normalise_openai_base_url(provider, settings["base_url"])

    if provider == "openrouter" and not api_key:
        raise RuntimeError(
            "OpenRouter API key not set. Add 'llm_api_key' under 'llm_details' in "
            "config.json or set LLM_API_KEY / OPENROUTER_API_KEY."
        )

    return OpenAI(
        base_url=base_url,
        api_key=api_key or "lm-studio",
    )


def _ollama_client(base_url: str) -> ollama.Client:
    return ollama.Client(host=base_url)


def list_models() -> list[str]:
    """
    Lists all models available on the local Ollama server.

    Returns:
        models (list[str]): Sorted list of model names.
    """
    settings = _get_llm_settings()
    provider = settings["provider"]
    if provider != "ollama":
        return [settings["default_model"]] if settings["default_model"] else []

    response = _ollama_client(settings["base_url"]).list()
    return sorted(str(m.model) for m in response.models if getattr(m, "model", None))


def select_model(model: str) -> None:
    """
    Sets the model to use for all subsequent generate_text calls.

    Args:
        model (str): An Ollama model name (must be already pulled).
    """
    global _selected_model
    _selected_model = model


def get_active_model() -> str | None:
    """
    Returns the currently selected model, or None if none has been selected.
    """
    return _selected_model


def generate_text(prompt: str, model_name: str = None) -> str:
    """
    Generates text using the configured provider.

    Args:
        prompt (str): User prompt
        model_name (str): Optional model name override

    Returns:
        response (str): Generated text
    """
    settings = _get_llm_settings()
    provider = settings["provider"]
    model = model_name or _selected_model or settings["default_model"] or settings["endpoint"]
    if not model:
        raise RuntimeError(
            "No model configured. Set llm_details.default_model, call select_model(), "
            "or pass model_name."
        )

    messages: list[ChatCompletionUserMessageParam] = [{"role": "user", "content": prompt}]

    if provider == "ollama":
        response = _ollama_client(settings["base_url"]).chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"].strip()

    if provider in {"lmstudio", "openrouter"}:
        completion = _openai_client(settings).chat.completions.create(
            model=model,
            messages=messages,
        )
        message = completion.choices[0].message.content or ""
        return message.strip()

    raise RuntimeError(
        f"Unsupported llm provider '{provider}'. Supported providers are ollama, lmstudio, and openrouter."
    )

