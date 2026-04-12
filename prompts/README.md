# Prompt Templates

This folder stores editable LM prompt templates so prompt changes do not require Python code edits.

## Layout

- `prompts/common/` for shared templates.
- `prompts/providers/<provider>/` for provider-specific templates.

## Template Variables

Templates use Python `str.format(...)` placeholders.

Example:

```text
Create a short video idea for {provider_name} in the {niche} niche.
```

When rendering, provide values for every placeholder used in the template.

## Current Prompt Files

- `prompts/providers/youtube/generate_video.txt`
- `prompts/providers/twitter/generate_video.txt`
- `prompts/providers/linkedin/generate_video.txt`

