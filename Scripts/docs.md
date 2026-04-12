# Scripts Folder Guide

This folder contains utility scripts that support the main CLI app and speed up local development tasks.

## `preflight_checks.py`

### What it does
- Runs environment and configuration validation checks before automation runs.
- Verifies `config.json` structure and key fields (LLM, image, STT, Firefox profile, ImageMagick path).
- Checks provider connectivity (for example Ollama/OpenRouter/LM Studio and ComfyUI endpoints).
- Returns a non-zero exit code if required checks fail.

### Why it is here
- It is a guardrail script for setup correctness.
- The same readiness logic is also used by the main app flow, so this script lets you validate issues early.

### Usage examples
```powershell
python Scripts\preflight_checks.py
```

```powershell
# Example with env var fallback for OpenRouter-compatible checks
$env:LLM_API_KEY = "your_api_key_here"
python Scripts\preflight_checks.py
```

## `comfy_generate.py`

### What it does
- Generates a single image through ComfyUI using your configured image provider settings.
- Loads a workflow JSON (default: `Assets/workflow_api.json`) and injects:
  - prompt text
  - configured model
  - computed image size from `image_aspect_ratio`
  - randomized seed
- Saves the generated image to `output/` (or your custom output path) and can optionally display it.

### Why it is here
- It is a focused integration test for ComfyUI access and config correctness.
- It provides a fast way to validate image pipeline behavior outside the full app workflow.

### Usage examples
```powershell
python Scripts\comfy_generate.py --prompt "a cinematic ruined castle at sunset"
```

```powershell
# Headless run (no image preview window)
python Scripts\comfy_generate.py --prompt "neon cyberpunk alley in rain" --no-show
```

```powershell
# Custom workflow/output and size target
python Scripts\comfy_generate.py --prompt "ultra detailed mountain vista" --workflow "Assets\workflow_api.json" --output "output\mountain.png" --base-pixels 1280
```

## `scaffold_provider.py`

### What it does
- Creates a new provider scaffold under `src/classes/providers/<provider_slug>/`.
- Generates three starter files:
  - `__init__.py`
  - `controller.py`
  - `service.py`
- Adds boilerplate controller/service classes so new providers can be integrated faster.

### Why it is here
- It standardizes provider structure and reduces copy/paste setup work.
- It makes expanding the project with new providers safer and more consistent.

### Usage examples
```powershell
# Minimal usage (auto-derives class prefix from slug)
python Scripts\scaffold_provider.py tiktok
```

```powershell
# Explicit naming options
python Scripts\scaffold_provider.py instagram --class-prefix Instagram --display-name "Instagram" --service-name "Instagram Automator"
```

```powershell
# Overwrite existing scaffold files
python Scripts\scaffold_provider.py instagram --force
```

## Notes
- Run all commands from the repository root (`AutoSocials/`).
- These scripts are developer utilities and are intended for setup validation, isolated integration testing, and scaffolding support.

