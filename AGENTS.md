# Repository Guidelines


## Project Structure & Module Organization
- `src/` contains the application code. Use `src/main.py` as the interactive entrypoint.
- `src/classes/` holds provider-specific components (for example `youtube.py`, `twitter.py`) and shared account flow (`account_menu.py`).
- Shared utilities and configuration live in modules like `src/config.py`, `src/cache.py`, `src/constants.py`, `src/lm_provider.py`, and `src/status.py`.
- `Scripts/` contains local validation workflows (currently `Scripts/preflight_checks.py`).
- `Assets/` contains static resources such as `Assets/banner.txt` and `Assets/workflow_api.json`; generated artifacts are written to `output/`.

## Build, Test, and Development Commands
- `python -m venv .venv && .\.venv\Scripts\Activate.ps1 && pip install -r requirements.txt`: create/activate a local virtual environment and install dependencies.
- `python Scripts\preflight_checks.py`: validate local provider/config readiness before running tasks.
- `python src\main.py`: start the CLI app.
- `python Tests\comfy_generate.py --prompt "a cinematic ruined castle at sunset"`: run the standalone ComfyUI workflow tester.

## Coding Style & Naming Conventions
- Target Python 3.12 (project requirement in `README.md`).
- Use 4-space indentation and follow existing Python conventions:
  - `snake_case` for functions/variables
  - `PascalCase` for classes
  - `UPPER_SNAKE_CASE` for constants
- Keep new business logic in focused modules under `src/`; keep provider/integration code in `src/classes/`.
- Prefer small, explicit functions and preserve existing CLI-first behavior.

## Testing Guidelines
- There is currently no enforced automated test suite or coverage threshold.
- Minimum validation for changes:
  - Run `python Scripts\preflight_checks.py`
  - Smoke-test impacted flows via `python src\main.py`
  - For image-workflow changes, run `python Tests\comfy_generate.py --prompt "..." --no-show`
- Existing ad-hoc test utilities live in top-level `Tests/` (for example `Tests/comfy_generate.py`).

## Commit & Pull Request Guidelines
- Follow the existing commit style: imperative summaries like `Fix ...`, `Update ...`, optionally with issue refs (for example `(#128)`).
- Open PRs against `main`.
- Link each PR to an issue, keep scope to one feature/fix, and use a clear title + description.
- Mark not-ready PRs with `WIP` and remove it when ready for review.

## Security & Configuration Tips
- Treat `config.json` as environment-specific; do not commit real API keys or private profile paths.
- Start from `config.example.json` and prefer environment variables where supported (for example `LLM_API_KEY` for OpenRouter-compatible checks).
