# AutoSocials

AutoSocials is a local-first automation scaffold for social-content workflows. The current codebase focuses on three practical pieces:

- a menu-driven launcher in `src/main.py`
- provider/account helpers for YouTube and Twitter in `src/classes/`
- a standalone ComfyUI workflow tester in `Tests/comfy_generate.py`

The repository targets **Python 3.12**.

## What this repo currently does

- validates local readiness with `Scripts/preflight_checks.py`
- opens a simple CLI in `src/main.py`
- lets you create, list, select, and delete cached provider accounts for YouTube and Twitter
- stores and reads configuration from `config.json`
- generates images through a ComfyUI API workflow using `Tests/comfy_generate.py`

## Installation

Create a virtual environment, activate it, and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install --upgrade pip wheel
pip install -r requirements.txt
```

Then copy the example configuration and edit it for your machine:

```powershell
Copy-Item config.example.json config.json
```

The current `requirements.txt` includes:

- `wheel`
- `termcolor`
- `schedule`
- `requests`
- `openai`
- `ollama`
- `faster-whisper`
- `prettytable`
- `websocket-client`
- `pillow`

## Configuration

Start from `config.example.json` and keep `config.json` valid JSON.

The current layout is nested:

```json
{
  "verbose": true,
  "firefox_profile": "",
  "llm_details": {
    "llm_provider": "lmstudio",
    "llm_endpoint": "qwen/qwen3.5-9b",
    "llm_base_url": "http://127.0.0.1:11434",
    "openrouter_api_key": "",
    "default_model": "qwen/qwen3.5-9b"
  },
  "llm_image_details": {
    "llm_image_provider": "comfyui",
    "image_api_base_url": "http://127.0.0.1:8188",
    "image_api_key": "",
    "image_model": "SD 1.5 Hyper\\realisticVisionV60B1_v51HyperVAE.safetensors",
    "image_aspect_ratio": "9:16"
  },
  "stt_details": {
    "stt_provider": "local_whisper",
    "whisper_model": "base",
    "whisper_device": "auto"
  }
}
```

### Top-level settings

- `verbose`: enables extra logging in the launcher and helpers
- `firefox_profile`: local Firefox profile path used by browser automation flows

### `llm_details`

Used for text-model provider selection and model defaults.

- `llm_provider`: `lmstudio`, `ollama`, or `openrouter`
- `llm_endpoint`: model name or endpoint identifier used by the app
- `llm_base_url`: local or remote base URL for the selected provider
- `openrouter_api_key`: required if you use OpenRouter
- `default_model`: fallback model name used by the app

### `llm_image_details`

Used by the ComfyUI image-generation tester.

- `llm_image_provider`: must be `comfyui`
- `image_api_base_url`: ComfyUI HTTP API base URL, for example `http://127.0.0.1:8188`
- `image_api_key`: optional bearer token for protected endpoints
- `image_model`: checkpoint name to inject into the workflow
- `image_aspect_ratio`: ratio hint such as `1:1`, `16:9`, or `9:16`

### `stt_details`

Used for speech-to-text configuration.

- `stt_provider`: currently expected to be `local_whisper`
- `whisper_model`: Whisper model size such as `base`, `small`, or `medium`
- `whisper_device`: runtime target such as `auto`, `cpu`, or `cuda`

### Important note about config migration

Some legacy helpers in `src/config.py` still read a few top-level config keys directly, while the newer template uses nested blocks. If you are actively using both older and newer helpers, keep an eye on that drift until the config readers are fully unified.

## Preflight checks

Run the repository preflight script before launching the app:

```powershell
python Scripts\preflight_checks.py
```

It currently checks:

- `config.json` exists
- the selected LLM provider is reachable or has the expected credentials
- Ollama is reachable when the fallback path is used
- `faster-whisper` is installed when `stt_provider=local_whisper`
- optional local paths such as `firefox_profile` and `imagemagick_path`

## Main launcher

`src/main.py` now runs a real menu flow rather than a stub. When launched, it:

1. prints the ASCII banner
2. runs the preflight checker
3. ensures the local `.as` folder exists
4. opens the provider menu

From the menu you can:

- start the YouTube account flow
- start the Twitter account flow
- exit the app

Each provider menu uses the shared account manager in `src/classes/account_menu.py` to:

- list cached accounts
- create a new account
- delete an existing account
- select an account and hand it to the provider-specific controller

Run it with:

```powershell
python src\main.py
```

## ComfyUI workflow testing

The repository also includes a standalone ComfyUI test harness:

```powershell
python Tests\comfy_generate.py --prompt "a cinematic ruined castle at sunset"
```

This script is intended for local ComfyUI testing outside the main app. It loads `config.json`, reads the `llm_image_details` block, edits an API-format workflow, submits it to ComfyUI, waits for completion, downloads the result, and saves the generated image locally.

### Default files and paths

By default the script uses:

- workflow file: `Assets/workflow_api.json`
- output base path: `output/generated.png`

All paths are resolved relative to the project root, so you can run the script from different working directories.

### CLI options

- `--workflow`: alternate API workflow JSON file
- `--prompt`: required prompt text to inject into the workflow
- `--output`: base output file path used when saving the rendered image
- `--base-pixels`: target long side used to derive width and height from the aspect ratio
- `--no-show`: skip opening the image after saving

Examples:

```powershell
python Tests\comfy_generate.py --prompt "a grim post-apocalyptic tower block at sunset"
python Tests\comfy_generate.py --prompt "a cinematic forest shrine at dawn" --no-show
python Tests\comfy_generate.py --prompt "an abandoned shopping centre in the rain" --base-pixels 1536
python Tests\comfy_generate.py --workflow Assets\workflow_api.json --prompt "a futuristic skyline at blue hour"
```

### What the script edits in the workflow

`Tests/comfy_generate.py` currently auto-updates these common ComfyUI node types:

- `CheckpointLoaderSimple`: replaces the checkpoint name with `image_model`
- `CLIPTextEncode`: replaces the first positive prompt node with your prompt
- `EmptyLatentImage`: recalculates width and height from `image_aspect_ratio`
- `KSampler`: randomises the seed

It then:

1. sends the workflow to ComfyUI with `POST /prompt`
2. waits for completion over WebSocket
3. fetches run history from `GET /history/{prompt_id}`
4. downloads the first generated image via `GET /view`
5. saves the output with a prompt-based timestamped filename

The filename looks like this:

```text
output/a_grim_post_apocalyptic_tower_block_at_sunset_20260412_143522.png
```

### Workflow expectations

The bundled workflow at `Assets/workflow_api.json` is a ComfyUI API export that matches the script’s assumptions. It currently contains the following key node types:

- `CheckpointLoaderSimple`
- `EmptyLatentImage`
- positive and negative `CLIPTextEncode` nodes
- `KSampler`
- `VAEDecode`
- `SaveImage`

If your workflow has a different shape, the script may still work, but only if those key nodes and input fields are present.

### ComfyUI requirements

To use the test script, you need:

- a running ComfyUI instance
- API access enabled on that instance
- a valid API-format workflow JSON
- the checkpoint referenced by `image_model` available in ComfyUI

The default local endpoint is expected to be:

```text
http://127.0.0.1:8188
```

## Repository layout

- `src/` - application code and entrypoints
- `src/classes/` - provider-specific controllers and shared menu flow
- `Scripts/` - local validation utilities such as `preflight_checks.py`
- `Assets/` - static resources, including the default ComfyUI workflow
- `Tests/` - standalone testing utilities such as `comfy_generate.py`
- `output/` - generated files and other runtime artifacts

## Current limitations

- the launcher is menu-driven, but the overall automation flows are still lightweight scaffolding
- the config layer still has some legacy drift between nested and top-level key lookups
- `Tests/comfy_generate.py` is a standalone utility, not yet wired into the main runtime
- the ComfyUI workflow tester assumes a compatible workflow structure with the node types listed above
- there is no documented end-to-end social automation workflow yet

## License

See `LICENSE` for project licensing details.
