# Project Backlog

## High Priority

- [ ] Finish provider support for the remaining platforms
  - [ ] `Youtube`
  - [ ] `Twitter`
  - [ ] `Instagram`
  - [ ] `LinkedIn`
  - [ ] `Facebook`
  - [ ] `TikTok`
  - [ ] `Reddit`
- [ ] Replace the remaining YouTube stubs with real session, generation, and upload flow
- [ ] Wire each provider into the main menu / launcher flow so every option works end-to-end
- [ ] Chatterbox TTS to have custom voices instead of AI sounding robotic voice
- [ ] Fix the Config.py file as it uses the old loading method and doesn't work with the new config structure

## Configuration & Runtime

- [ ] Align `src/config.py` with the current `config.json` / `config.example.json` structure
- [ ] Verify `src/lm_provider.py` matches the active config schema and provider requirements
- [ ] Make resource and asset paths fully portable across Windows and other environments
- [ ] Confirm account caching and session handling works consistently after provider changes
- [ ] Ensure we have CUDA and not CPU for Chatterbox TTS

## Product & Workflow

- [ ] Document the full end-to-end automation flow from setup to posting
- [ ] Add provider-specific account/session actions so each menu choice performs meaningful work
- [ ] Review and tighten onboarding docs so setup steps match the actual runtime behavior

## Verification

- [ ] Run the preflight check against a clean environment after provider/config changes
- [ ] Smoke-test the CLI launcher after each provider is added
- [ ] Validate the image generation workflow with the standalone ComfyUI helper

## Done

- [x] ~~Update preflight to check if the Firefox profile is valid~~
- [x] ~~Decide whether `Tests/comfy_generate.py` stays a standalone utility or becomes part of the main app~~.... Moved them all into the 'Scripts' folder and created 'Scripts/docs.md' to clarify their purpose as show usages.
