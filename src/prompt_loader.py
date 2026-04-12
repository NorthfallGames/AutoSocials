from pathlib import Path
from string import Formatter
from typing import Any

from config import ROOT_DIR

PROMPTS_DIR = Path(ROOT_DIR) / "prompts"
COMMON_PROMPTS_DIR = PROMPTS_DIR / "common"
PROVIDER_PROMPTS_DIR = PROMPTS_DIR / "providers"


def _normalise_prompt_name(prompt_name: str) -> str:
    name = str(prompt_name or "").strip().replace("\\", "/")
    if not name:
        raise ValueError("prompt_name cannot be empty")

    if not name.endswith(".txt"):
        name = f"{name}.txt"

    parts = Path(name).parts
    if any(part == ".." for part in parts) or Path(name).is_absolute():
        raise ValueError("prompt_name must be a relative prompt path")

    return name


def load_prompt(prompt_name: str, provider: str | None = None) -> str:
    name = _normalise_prompt_name(prompt_name)
    attempted_paths: list[Path] = []

    if provider:
        provider_path = PROVIDER_PROMPTS_DIR / provider.strip().lower() / name
        attempted_paths.append(provider_path)
        if provider_path.exists():
            return provider_path.read_text(encoding="utf-8")

    common_path = COMMON_PROMPTS_DIR / name
    attempted_paths.append(common_path)
    if common_path.exists():
        return common_path.read_text(encoding="utf-8")

    attempted = "\n - ".join(str(path) for path in attempted_paths)
    raise FileNotFoundError(f"Prompt template not found. Tried:\n - {attempted}")


def render_prompt(template: str, context: dict[str, Any]) -> str:
    required_fields: set[str] = set()
    for _, field_name, _, _ in Formatter().parse(template):
        if isinstance(field_name, str) and field_name:
            required_fields.add(field_name)

    missing_fields: list[str] = sorted(
        field for field in required_fields if field not in context
    )

    if missing_fields:
        joined = ", ".join(missing_fields)
        raise KeyError(f"Missing prompt context values: {joined}")

    return template.format(**context)


def load_and_render_prompt(prompt_name: str, provider: str | None = None, **context: Any) -> str:
    template = load_prompt(prompt_name=prompt_name, provider=provider)
    return render_prompt(template, context=context)

