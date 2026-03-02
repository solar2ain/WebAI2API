---
name: image-generate-api
description: Generate images via WebAI2API with OpenAI-compatible API, supporting multiple image generation models.
homepage: https://github.com/foxhui/WebAI2API
metadata:
  {
    "openclaw":
      {
        "emoji": "🖼️",
        "requires": { "bins": ["python3"], "env": ["WEBAI2API_API_KEY"] },
        "primaryEnv": "WEBAI2API_API_KEY",
      },
  }
---

# Image Generate API (WebAI2API)

Use the bundled script to generate images via WebAI2API with OpenAI-compatible API.

List available models

```bash
python3 {skillDir}/scripts/generate_image.py --list-models
```

Generate image (uses default model gemini/gemini-3-pro-image-preview)

```bash
python3 {skillDir}/scripts/generate_image.py --prompt "A majestic mountain landscape at sunset with golden clouds"
```

Generate multiple images

```bash
python3 {skillDir}/scripts/generate_image.py --prompt "A cute cat playing with yarn" -n 3
```

Output to specific file

```bash
python3 {skillDir}/scripts/generate_image.py --prompt "A cute cat playing with yarn" --output "./cat_yarn.png"
```

Output to specific directory (auto-generate filename)

```bash
python3 {skillDir}/scripts/generate_image.py --prompt "Abstract digital art" --output "/path/to/output/"
```

Generate with specific model

```bash
python3 {skillDir}/scripts/generate_image.py --prompt "A mountain landscape" --model "lmarena/gemini-3.1-flash-image-preview"
```

Generate with size hint (added to prompt)

```bash
python3 {skillDir}/scripts/generate_image.py --prompt "A wide panoramic view of a city skyline" --size "1792x1024"
```

Image editing with input image

```bash
python3 {skillDir}/scripts/generate_image.py --prompt "Add a rainbow to this photo" -i photo.jpg
```

Image composition with multiple inputs (up to 10)

```bash
python3 {skillDir}/scripts/generate_image.py --prompt "Combine these images into a collage" -i img1.png -i img2.png -i img3.png
```

Output Parameter

The `--output` (`-o`) parameter accepts either:
- **File path**: Direct path to save the image (e.g., `./my_image.png`)
- **Directory path**: Directory where auto-generated filename will be used (e.g., `./output/`)

Default output directory: `{skillDir}/images/`

Filename Convention

When output is a directory (or not specified), filenames are auto-generated as:

```
{model_short}_{YYYYMMDD}_{prompt_summary}_{seq}.png
```

- `model_short`: Short name for the model (e.g., `gemini3`, `gpt1.5`, `flux2`)
- `YYYYMMDD`: Current date
- `prompt_summary`: First 4 words of the prompt (lowercase, underscored)
- `seq`: Sequence number (01, 02, ...)

Example: `gemini3_20260228_a_beautiful_sunset_over_01.png`

Metadata

Each generation creates/updates a metadata JSON file with the same base name as the image:

```json
{
  "model": "gemini/gemini-3-pro-image-preview",
  "prompt": "A majestic mountain landscape at sunset...",
  "timestamp": "2026-02-28T14:30:52",
  "filenames": ["gemini3_20260228_a_majestic_mountain_landscape_01.png"]
}
```

Environment Variables

- `WEBAI2API_HOST`: API host URL (default: `http://127.0.0.1:3000/`)
- `WEBAI2API_API_KEY`: API key for authentication (required)
- Or set `skills."image-generate-api".apiKey` / `skills."image-generate-api".env.WEBAI2API_API_KEY` in `~/.openclaw/openclaw.json`

Available Image Generation Models

> Note: Model availability may change dynamically. Use `--list-models` to get the latest list. Models are listed as `adapter/model` (full name). Models marked with `[no input image]` do not support image editing (input images).

Example models (use `--list-models` for current list):

| Full Name | Short Name | Description |
|-----------|------------|-------------|
| `gemini/gemini-3-pro-image-preview` (default) | gemini3 | Google Gemini 3 Pro via Gemini |
| `lmarena/gemini-3.1-flash-image-preview` | gemini3.1 | Google Gemini 3.1 Flash via LMArena |
| `lmarena/chatgpt-image-latest-high-fidelity` | chatgpt | OpenAI ChatGPT Image via LMArena |
| `chatgpt/gpt-image-1.5` | gpt1.5 | OpenAI GPT Image 1.5 via ChatGPT |
| `lmarena/flux-2-max` | flux2 | Black Forest Labs Flux 2 Max via LMArena |
| `doubao/seedream-4.0` | seedream4 | ByteDance Seedream 4.0 via Doubao |

Notes

- Default model: `gemini/gemini-3-pro-image-preview`
- Size hint options: `1024x1024`, `1792x1024`, `1024x1792` (will be added to prompt)
- Default output directory: `{s'k'i'l'l'Di'r}/images/`
- Use `-n` to generate multiple images in one command
- The script prints `MEDIA:` lines for OpenClaw to auto-attach on supported chat providers
- Do not read the image back; report the saved path only
