# AutoSocials

AutoSocials is a local-first automation scaffold for social-content workflows. The current codebase centers on three practical entrypoints:

- a menu-driven CLI launcher in `src/main.py`
- provider/account helpers for YouTube, Twitter, and LinkedIn in `src/classes/`
- standalone utilities in `Scripts/` for preflight checks, ComfyUI image generation, and provider scaffolding

The repository targets **Python 3.12**.

## What this repository currently does

- validates local readiness with `Scripts/preflight_checks.py`
- opens a simple CLI in `src/main.py`
- lets you create, list, select, and delete cached provider accounts for YouTube, Twitter, and LinkedIn
- stores and reads configuration from `config.json`
- generates images through a ComfyUI API workflow using `Scripts/comfy_generate.py`

## Installation

Create a virtual environment, activate it, and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip wheel
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

The current runtime expects a nested layout:

```json
{
  "verbose": true,
  "firefox_profile": "",
  "imagemagick_path": "Path to magick.exe or on linux/macOS just /usr/bin/convert",
  "llm_details": {
    "llm_provider": "lmstudio",
    "llm_endpoint": "qwen/qwen3.5-9b",
    "llm_base_url": "http://127.0.0.1:11434",
    "llm_api_key": "",
    "default_model": "qwen/qwen3.5-9b"
  },
  "llm_image_details": {
    "llm_image_provider": "comfyui",
    "image_api_base_url": "http://127.0.0.1:8188",
    "image_api_key": "",
    "image_model": "Illustrious\\illustriousRealism_ilXL10V30.safetensors",
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
- `imagemagick_path`: optional path to `magick.exe` or `convert` for subtitle/image tooling

### `llm_details`

Used for text-model provider selection and model defaults.

- `llm_provider`: `ollama`, `lmstudio`, or `openrouter`
- `llm_endpoint`: model name or endpoint identifier used by the app
- `llm_base_url`: local or remote base URL for the selected provider
- `llm_api_key`: API key used for OpenAI-compatible providers; required for OpenRouter (or set `LLM_API_KEY` in your environment)
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

### Legacy config drift

Some older helpers in `src/config.py` still read top-level keys directly, while the newer scripts and preflight checks use the nested config blocks above. In particular, `src/config.py` still expects values like `firefox_profile`, `llm_provider`, `default_model`, `llm_endpoint`, `ollama_base_url`, and `openrouter_api_key` in their legacy locations.

If you are actively using both the launcher and the newer scripts, keep that drift in mind until the legacy readers are fully unified.

## Preflight checks

Run the repository preflight script before launching the app:

```powershell
python Scripts\preflight_checks.py
```

It currently checks:

- `config.json` exists and is valid JSON
- `firefox_profile` points to an existing directory
- the selected LLM provider is reachable or has the expected credentials
- Ollama is reachable when the fallback path is used
- `faster-whisper` is importable when `stt_provider=local_whisper`
- optional local paths such as `imagemagick_path`
- ComfyUI reachability and model availability when `llm_image_provider=comfyui`

## Main launcher

`src/main.py` runs the primary CLI flow. When launched, it:

1. prints the ASCII banner
2. runs `Scripts/preflight_checks.py`
3. ensures the local `.as` folder exists
4. cleans temporary files from `.as`
5. opens the provider menu

Run it with:

```powershell
python src\main.py
```

From the main menu you can start one of the provider flows or quit the app.

### Provider flows

The current provider menu includes:

- YouTube
- Twitter
- LinkedIn
- Quit

Each provider uses the shared account manager in `src/classes/account_menu.py` to:

- list cached accounts
- create a new account
- delete an existing account
- select an account and hand it to the provider-specific controller

When you create a new account, the shared flow generates a UUID, stores the Firefox profile path from `config.json`, and asks for the common account fields:

- nickname
- niche

After selection, each provider opens a small provider-specific menu with:

- test service
- generate video
- upload video
- show account details
- back

At the moment the provider services are lightweight scaffolds: `test_connection()` confirms the service wiring, while `generate_video()` and `upload_video()` are still placeholders.

## ComfyUI workflow testing

The repository includes a standalone ComfyUI test harness in `Scripts/comfy_generate.py`:

```powershell
python Scripts\comfy_generate.py --prompt "a cinematic ruined castle at sunset"
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
python Scripts\comfy_generate.py --prompt "a grim post-apocalyptic tower block at sunset"
python Scripts\comfy_generate.py --prompt "a cinematic forest shrine at dawn" --no-show
python Scripts\comfy_generate.py --prompt "an abandoned shopping centre in the rain" --base-pixels 1536
python Scripts\comfy_generate.py --workflow Assets\workflow_api.json --prompt "a futuristic skyline at blue hour"
```

### What the script edits in the workflow

`Scripts/comfy_generate.py` currently auto-updates these common ComfyUI node types:

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

The saved file name looks like this:

```text
output/a_grim_post_apocalyptic_tower_block_at_sunset_20260412_143522.png
```

### Workflow expectations

The bundled workflow at `Assets/workflow_api.json` is a ComfyUI API export that matches the script’s assumptions. It currently expects the following key node types:

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

## Provider scaffolding helper

`Scripts/scaffold_provider.py` can generate a starter provider package under `src/classes/providers/<provider_slug>`.

Example:

```powershell
python Scripts\scaffold_provider.py tiktok
python Scripts\scaffold_provider.py bluesky --class-prefix BlueSky --display-name Bluesky --service-name "Bluesky Automator"
```

It creates:

- `__init__.py`
- `controller.py`
- `service.py`

The generated service class is intentionally a stub so you can wire in provider-specific browser, content, and upload logic.

## Repository layout

- `src/` - application code and entrypoints
- `src/classes/` - provider-specific controllers and the shared account flow
- `src/classes/providers/` - provider implementations for YouTube, Twitter, and LinkedIn
- `Scripts/` - local validation utilities such as `preflight_checks.py`, `comfy_generate.py`, and `scaffold_provider.py`
- `Assets/` - static resources, including the default banner and ComfyUI workflow
- `output/` - generated files and other runtime artifacts

## Current limitations

- the launcher is menu-driven, but the overall automation flows are still scaffold-level
- provider services currently only verify wiring and print placeholder output for generation/upload actions
- the config layer still has some legacy drift between nested and top-level key lookups
- `Scripts/comfy_generate.py` assumes a compatible ComfyUI workflow structure with the node types listed above
- there is no documented end-to-end social automation workflow yet

## License

See `LICENSE` for project licensing details.
