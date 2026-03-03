---
name: text-generate-api
description: Generate text via WebAI2API with OpenAI-compatible API, supporting multiple LLM models for one-shot QA, summary, and generation.
homepage: https://github.com/foxhui/WebAI2API
metadata:
  {
    "openclaw":
      {
        "emoji": "💬",
        "requires": { "bins": ["python3"], "env": ["WEBAI2API_API_KEY"] },
        "primaryEnv": "WEBAI2API_API_KEY",
      },
  }
---

# Text Generate API (WebAI2API)

Use the bundled script to generate text via WebAI2API with OpenAI-compatible API.

> **Note**: WebAI2API internally converts multi-turn conversations into a single prompt. This API is best suited for one-shot QA, summary, and generation tasks.

List available models

```bash
python3 {skillDir}/scripts/generate_text.py --list-models
```

Simple question (uses default model gemini-3-pro)

```bash
python3 {skillDir}/scripts/generate_text.py --prompt "What is the capital of France?"
```

Generate with specific model (full name format: adapter/model)

```bash
python3 {skillDir}/scripts/generate_text.py --prompt "Explain quantum computing in simple terms" --model "lmarena_text/claude-opus-4-6"
```

Generate with adapter and model name separately

```bash
python3 {skillDir}/scripts/generate_text.py --prompt "Hello" --model "gemini-3-pro" --adapter lmarena
```

> Note: For text generation, you can use short adapter names like `lmarena`, `gemini`, `chatgpt` - they will be automatically converted to `lmarena_text`, `gemini_text`, `chatgpt_text` etc.

With system instruction

```bash
python3 {skillDir}/scripts/generate_text.py --prompt "Hello" --system "You are a helpful coding assistant"
```

With input image (vision)

```bash
python3 {skillDir}/scripts/generate_text.py --prompt "Describe this image" -i photo.jpg
```

With multiple input images (up to 10)

```bash
python3 {skillDir}/scripts/generate_text.py --prompt "Compare these two images" -i img1.png -i img2.png
```

Save output to file

```bash
python3 {skillDir}/scripts/generate_text.py --prompt "Write a poem about sunset" --output "poem.txt"
```

Output raw API response (JSON format)

```bash
python3 {skillDir}/scripts/generate_text.py --prompt "Hello" --raw-response
```

With thinking output (for thinking models)

```bash
python3 {skillDir}/scripts/generate_text.py --prompt "What is 15 factorial?" --model "lmarena_text/glm-4.7" --show-thinking
```

> Note: The `--show-thinking` flag includes the model's thinking process wrapped in `<thinking>` tags. Only works with thinking models (e.g., glm-4.7, deepseek-v3.2-thinking, claude-*-thinking).

Input messages (OpenAI messages format)

For multi-turn conversations, use `-j` / `--input-messages` with OpenAI messages format:

```bash
python3 {skillDir}/scripts/generate_text.py -j '{"messages": [{"role": "system", "content": "You are helpful"}, {"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}, {"role": "user", "content": "How are you?"}]}'
```

Or from a file with `-J` / `--input-messages-file`:

```bash
python3 {skillDir}/scripts/generate_text.py -J conversation.json
```

JSON format (recommended):

```json
{
  "model": "gemini-3-pro",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "What is 2+2?"}
  ]
}
```

Environment Variables

- `WEBAI2API_HOST`: API host URL (default: `http://127.0.0.1:3000/`)
- `WEBAI2API_API_KEY`: API key for authentication (required)
- Or set `skills."text-generate-api".apiKey` / `skills."text-generate-api".env.WEBAI2API_API_KEY` in `~/.openclaw/openclaw.json`

Available Text Generation Models

> Note: Model availability may change dynamically. Use `--list-models` to get the latest list. Models are listed as `adapter/model` (full name). Models marked with `[vision]` support image input.

Recommended models:

| Full Name | Description | Vision |
|-----------|-------------|--------|
| `gemini_text/gemini-3-pro` | Google Gemini 3 Pro | ✅ |
| `lmarena_text/gemini-3-pro` | Google Gemini 3 Pro via LMArena | ✅ |
| `lmarena_text/claude-opus-4-6-thinking` | Anthropic Claude Opus 4.6 (thinking) | ❌ |
| `lmarena_text/claude-opus-4-6` | Anthropic Claude Opus 4.6 | ❌ |
| `lmarena_text/gpt-5.2-chat-latest` | OpenAI GPT-5.2 | ✅ |
| `lmarena_text/glm-5` | 智谱 GLM-5 | ❌ |
| `lmarena_text/deepseek-v3.2-thinking` | DeepSeek V3.2 (thinking) | ❌ |
| `lmarena_text/ernie-5.0-0110` | 百度文心 ERNIE 5.0 | ❌ |

Other supported models can be viewed via `--list-models`.

Limitations

- **No temperature/max_tokens support**: The underlying API doesn't support these parameters
- **Single-turn internally**: WebAI2API converts multi-turn messages into a single prompt
- Best for: One-shot QA, summarization, simple text generation
