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
python3 {baseDir}/scripts/generate_image.py --list-models
```

Generate image (uses default model gemini-3.1-flash-image-preview)

```bash
python3 {baseDir}/scripts/generate_image.py --prompt "A majestic mountain landscape at sunset with golden clouds"
```

Generate multiple images

```bash
python3 {baseDir}/scripts/generate_image.py --prompt "A cute cat playing with yarn" -n 3
```

Generate with specific model and filename

```bash
python3 {baseDir}/scripts/generate_image.py --prompt "A cute cat playing with yarn" --model "gpt-image-1" --filename "cat_yarn.png"
```

Generate with specific adapter (provider)

```bash
python3 {baseDir}/scripts/generate_image.py --prompt "A mountain landscape" --model "gemini-3.1-flash-image-preview" --adapter lmarena
```

Generate with size hint (added to prompt)

```bash
python3 {baseDir}/scripts/generate_image.py --prompt "A wide panoramic view of a city skyline" --size "1792x1024"
```

Specify output directory

```bash
python3 {baseDir}/scripts/generate_image.py --prompt "Abstract digital art" --output-dir "/path/to/output"
```

Image editing with input image

```bash
python3 {baseDir}/scripts/generate_image.py --prompt "Add a rainbow to this photo" -i photo.jpg
```

Image composition with multiple inputs (up to 5)

```bash
python3 {baseDir}/scripts/generate_image.py --prompt "Combine these images into a collage" -i img1.png -i img2.png -i img3.png
```

Filename Convention

When `--filename` is not specified, filenames are auto-generated as:

```
{model_short}_{YYYYMMDD}_{prompt_summary}_{seq}.png
```

- `model_short`: Short name for the model (e.g., `gemini3.1`, `gpt1.5`, `flux2`)
- `YYYYMMDD`: Current date
- `prompt_summary`: First 4 words of the prompt (lowercase, underscored)
- `seq`: Sequence number (01, 02, ...)

Example: `gemini3.1_20260228_a_beautiful_sunset_over_01.png`

When `--filename` is specified:
- For single image (`-n 1`): uses the exact filename provided
- For multiple images (`-n > 1`): adds sequence number before extension (e.g., `cat_01.png`, `cat_02.png`)

Metadata

Each generation creates/updates a metadata JSON file (filename without sequence number):

```json
{
  "model": "gemini-3.1-flash-image-preview",
  "prompt": "A majestic mountain landscape at sunset...",
  "timestamp": "2026-02-28T14:30:52",
  "filenames": ["gemini3.1_20260228_a_majestic_mountain_landscape_01.png"]
}
```

Environment Variables

- `WEBAI2API_HOST`: API host URL (default: `http://127.0.0.1:3000/`)
- `WEBAI2API_API_KEY`: API key for authentication (required)
- Or set `skills."image-generate-api".apiKey` / `skills."image-generate-api".env.WEBAI2API_API_KEY` in `~/.openclaw/openclaw.json`

Available Image Generation Models

> Note: Model availability may change dynamically. Use `--list-models` to get the latest list. Models marked with `[no input image]` do not support image editing (input images).

| Model | Provider | Short Name | Adapters |
|-------|----------|------------|----------|
| `gemini-3.1-flash-image-preview` (default) | Google | gemini3.1 | lmarena |
| `gemini-3-pro-image-preview` | Google | gemini3 | gemini, lmarena |
| `gemini-3-pro-image-preview-2k` | Google | gemini3 | lmarena |
| `gemini-3-pro-image-preview-4k` | Google | gemini3 | - |
| `gemini-2.5-flash-image-preview` | Google | gemini2.5 | lmarena |
| `gpt-image-1` | OpenAI | gpt1 | lmarena |
| `gpt-image-1.5` | OpenAI | gpt1.5 | chatgpt |
| `gpt-image-1.5-high-fidelity` | OpenAI | gpt1.5 | lmarena |
| `gpt-image-1-mini` | OpenAI | gpt1 | lmarena |
| `chatgpt-image-latest-high-fidelity` | OpenAI | chatgpt | lmarena |
| `imagen-4.0-generate-001` | Google | imagen4 | lmarena |
| `veo-3.1-generate-preview` | Google | veo | gemini |
| `flux-2-max` | Black Forest Labs | flux2 | lmarena |
| `flux-2-pro` | Black Forest Labs | flux2 | lmarena |
| `flux-2-dev` | Black Forest Labs | flux2 | lmarena |
| `flux-2-flex` | Black Forest Labs | flux2 | lmarena |
| `seedream-4.0` | ByteDance | seedream4 | doubao, lmarena |
| `seedream-4.5` | ByteDance | seedream4 | doubao, lmarena |
| `seedream-4-high-res-fal` | ByteDance | seedream4 | lmarena |
| `seedream-5.0-lite` | ByteDance | seedream5 | lmarena |
| `hunyuan-image-3.0` | Tencent | hunyuan | lmarena |
| `qwen-image-2512` | Alibaba | qwen | lmarena |
| `wan2.5-t2i-preview` | Alibaba | wan | lmarena |
| `recraft-v4` | Recraft | recraft | lmarena |
| `mai-image-1` | - | mai | lmarena |
| `grok-imagine-image` | xAI | grok | lmarena |
| `grok-imagine-image-pro` | xAI | grok | lmarena |

Notes

- Default model: `gemini-3.1-flash-image-preview`
- Size hint options: `1024x1024`, `1792x1024`, `1024x1792` (will be added to prompt)
- Default output directory: `{baseDir}/images/`
- Use `-n` to generate multiple images in one command
- The script prints `MEDIA:` lines for OpenClaw to auto-attach on supported chat providers
- Do not read the image back; report the saved path only
