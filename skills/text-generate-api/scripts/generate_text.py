#!/usr/bin/env python3
"""
Generate text using WebAI2API with OpenAI-compatible API.

Usage:
    python3 generate_text.py --prompt "What is the capital of France?"
    python3 generate_text.py --prompt "Summarize this article" --model "gpt-5"
    python3 generate_text.py --prompt "Hello" --system "You are a helpful assistant"
    python3 generate_text.py -j '{"messages": [{"role": "system", "content": "You are helpful"}, {"role": "user", "content": "Hi"}]}'

Note: WebAI2API converts multi-turn conversations into single-turn prompts internally.
      Not ideal for complex multi-turn conversations or detailed system instructions.

Environment Variables:
    WEBAI2API_HOST: API host URL (default: http://127.0.0.1:3000/)
    WEBAI2API_API_KEY: API key for authentication (required)

Dependencies:
    pip install requests
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path


def get_api_key(provided_key: str | None) -> str | None:
    """Get API key from argument first, then environment."""
    if provided_key:
        return provided_key
    return os.environ.get("WEBAI2API_API_KEY")


def get_api_host() -> str:
    """Get API host from environment or use default."""
    host = os.environ.get("WEBAI2API_HOST", "http://127.0.0.1:3000/")
    if not host.endswith("/"):
        host += "/"
    return host


def restart_service(api_host: str, api_key: str) -> None:
    """Restart the WebAI2API service."""
    import requests

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        endpoint = f"{api_host}admin/restart"
        response = requests.post(endpoint, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            print(f"Service restart initiated: {result.get('message', 'OK')}")
            print("Waiting 60 seconds for service to restart...", end="", flush=True)
            import time
            for i in range(60):
                time.sleep(1)
                if (i + 1) % 10 == 0:
                    print(f" {i + 1}s", end="", flush=True)
            print(" Done.")
        else:
            print(f"Restart failed: {result}", file=sys.stderr)
            sys.exit(1)

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error restarting service: {e}", file=sys.stderr)
        sys.exit(1)


def is_text_generation_model(model_id: str) -> bool:
    """Check if model is a text generation model by name patterns."""
    model_lower = model_id.lower()
    # Exclude image/video generation models
    exclude_patterns = [
        "image",
        "flux",
        "seedream",
        "hunyuan-image",
        "veo",
        "imagine",
        "t2i",
    ]
    if any(p in model_lower for p in exclude_patterns):
        return False

    # Known text generation model patterns
    text_gen_patterns = [
        "claude",
        "gpt-5",
        "gemini-3",
        "gemini-2.5",
        "grok-4",
        "deepseek",
        "kimi",
        "glm",
        "qwen",
        "seed",
        "ernie",
    ]
    return any(p in model_lower for p in text_gen_patterns)


def normalize_text_adapter(adapter: str) -> str:
    """Normalize adapter name to text adapter format.

    For text generation, adapter names should end with '_text'.
    User can input 'lmarena' or 'lmarena_text', both will work.
    """
    if not adapter:
        return adapter

    # Already has _text suffix
    if adapter.endswith('_text'):
        return adapter

    # Map short names to full text adapter names
    text_adapter_map = {
        'lmarena': 'lmarena_text',
        'gemini': 'gemini_text',
        'gemini_biz': 'gemini_biz_text',
        'chatgpt': 'chatgpt_text',
        'zai_is': 'zai_is_text',
        'zai': 'zai_is_text',
        'doubao': 'doubao_text',
        'deepseek': 'deepseek_text',
        'zenmux': 'zenmux_ai_text',
        'zenmux_ai': 'zenmux_ai_text',
    }

    return text_adapter_map.get(adapter, adapter)


def list_models(api_host: str, api_key: str) -> None:
    """List available text generation models from the API."""
    import requests

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    try:
        endpoint = f"{api_host}v1/models"
        response = requests.get(endpoint, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()

        if "data" not in result:
            print("No models data in response.", file=sys.stderr)
            sys.exit(1)

        # Collect full model IDs (adapter/model) with metadata
        # full_id -> { image_policy: str, type: str }
        model_list = []
        for m in result["data"]:
            full_id = m.get("id", "")
            if "/" not in full_id:
                continue  # Skip non-prefixed models

            adapter, base_model = full_id.split("/", 1)
            if not adapter.endswith("_text"):
                continue  # Skip non-text adapters

            if not is_text_generation_model(base_model):
                continue

            model_list.append({
                "full_id": full_id,
                "image_policy": m.get("image_policy", ""),
            })

        if not model_list:
            print("No text generation models found.", file=sys.stderr)
            sys.exit(1)

        print(f"Available text generation models ({len(model_list)}):\n")
        for info in sorted(model_list, key=lambda x: x["full_id"]):
            full_id = info["full_id"]
            image_policy = info["image_policy"]
            vision_hint = " [vision]" if image_policy == "optional" else ""
            print(f"  - {full_id}{vision_hint}")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching models: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate text using WebAI2API with OpenAI-compatible API"
    )
    parser.add_argument(
        "--list-models", "-l",
        action="store_true",
        help="List available models and exit"
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Restart the WebAI2API service and exit"
    )
    parser.add_argument(
        "--prompt", "-p",
        help="User prompt/question (required unless using --json with messages)"
    )
    parser.add_argument(
        "--input-image", "-i",
        action="append",
        dest="input_images",
        metavar="IMAGE",
        help="Input image path(s) for vision. Can be specified multiple times (up to 10 images)."
    )
    parser.add_argument(
        "--system", "-s",
        help="System instruction"
    )
    parser.add_argument(
        "--model", "-m",
        default="gemini-3-pro",
        help="Model to use for text generation (default: gemini-3-pro)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Save output to file (optional)"
    )
    parser.add_argument(
        "--api-key", "-k",
        help="API key (overrides WEBAI2API_API_KEY env var)"
    )
    parser.add_argument(
        "--host",
        help="API host URL (overrides WEBAI2API_HOST env var)"
    )
    parser.add_argument(
        "--adapter", "-a",
        help="Adapter/provider prefix (e.g., lmarena or lmarena_text). Model will be called as adapter/model"
    )
    parser.add_argument(
        "--raw-response",
        action="store_true",
        help="Output raw API response message object (JSON format)"
    )
    parser.add_argument(
        "--input-messages", "-j",
        dest="input_messages",
        help='Input messages in OpenAI format. Example: {"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]}'
    )
    parser.add_argument(
        "--input-messages-file", "-J",
        dest="input_messages_file",
        help="Read input messages from JSON file"
    )
    parser.add_argument(
        "--show-thinking",
        action="store_true",
        help="Include thinking/reasoning content in output (for thinking models like glm-4.7, claude-*-thinking)"
    )

    args = parser.parse_args()

    # Get API key
    api_key = get_api_key(args.api_key)
    if not api_key:
        print("Error: No API key provided.", file=sys.stderr)
        print("Please either:", file=sys.stderr)
        print("  1. Provide --api-key argument", file=sys.stderr)
        print("  2. Set WEBAI2API_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    # Get API host
    api_host = args.host if args.host else get_api_host()
    if not api_host.endswith("/"):
        api_host += "/"

    # Handle list-models command
    if args.list_models:
        list_models(api_host, api_key)
        return

    # Handle restart command
    if args.restart:
        restart_service(api_host, api_key)
        return

    # Parse JSON input if provided
    json_input = None
    if args.input_messages_file:
        try:
            with open(args.input_messages_file, 'r', encoding='utf-8') as f:
                json_input = json.load(f)
        except Exception as e:
            print(f"Error reading JSON file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.input_messages:
        try:
            json_input = json.loads(args.input_messages)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}", file=sys.stderr)
            sys.exit(1)

    # Build messages array
    messages = []
    model = args.model

    # Load input images if provided
    input_images_b64 = []
    if args.input_images:
        if len(args.input_images) > 10:
            print(f"Error: Too many input images ({len(args.input_images)}). Maximum is 10.", file=sys.stderr)
            sys.exit(1)
        for img_path in args.input_images:
            try:
                with open(img_path, 'rb') as f:
                    img_data = f.read()
                # Detect mime type
                if img_path.lower().endswith('.png'):
                    mime = 'image/png'
                elif img_path.lower().endswith(('.jpg', '.jpeg')):
                    mime = 'image/jpeg'
                elif img_path.lower().endswith('.gif'):
                    mime = 'image/gif'
                elif img_path.lower().endswith('.webp'):
                    mime = 'image/webp'
                else:
                    mime = 'image/png'  # default
                b64 = base64.b64encode(img_data).decode('utf-8')
                input_images_b64.append(f"data:{mime};base64,{b64}")
                print(f"Loaded input image: {img_path}", file=sys.stderr)
            except Exception as e:
                print(f"Error loading input image '{img_path}': {e}", file=sys.stderr)
                sys.exit(1)

    if json_input:
        # JSON input: use messages directly if provided
        if "messages" in json_input:
            messages = json_input["messages"]
        else:
            # Legacy format support: build messages from system/prompt
            if json_input.get("system"):
                messages.append({"role": "system", "content": json_input["system"]})
            if json_input.get("prompt"):
                messages.append({"role": "user", "content": json_input["prompt"]})
        model = json_input.get("model") or args.model
    else:
        # CLI args: build messages from --system and --prompt
        if args.system:
            messages.append({"role": "system", "content": args.system})
        if args.prompt:
            # Build user message content
            if input_images_b64:
                # Vision format: content is array of image_url and text
                content_parts = []
                for img_url in input_images_b64:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": img_url}
                    })
                content_parts.append({"type": "text", "text": args.prompt})
                messages.append({"role": "user", "content": content_parts})
            else:
                messages.append({"role": "user", "content": args.prompt})

    # Validate messages
    if not messages:
        print("Error: --prompt is required for text generation.", file=sys.stderr)
        sys.exit(1)

    import requests

    # Normalize adapter name for text generation
    adapter = normalize_text_adapter(args.adapter) if args.adapter else None

    # Build actual model name with adapter prefix
    actual_model = f"{adapter}/{model}" if adapter else model

    print(f"Generating with model {actual_model}...", file=sys.stderr)
    print(f"API Host: {api_host}", file=sys.stderr)

    # Build request payload
    payload = {
        "model": actual_model,
        "messages": messages
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        endpoint = f"{api_host}v1/chat/completions"
        response = requests.post(endpoint, json=payload, headers=headers, timeout=300)
        response.raise_for_status()
        result = response.json()

        if "choices" not in result or len(result["choices"]) == 0:
            print("Error: No choices in response.", file=sys.stderr)
            sys.exit(1)

        message = result["choices"][0].get("message", {})
        content = message.get("content", "")
        reasoning_content = message.get("reasoning_content", "")

        # Determine output content
        if args.raw_response:
            output_text = json.dumps(message, ensure_ascii=False, indent=2)
        elif args.show_thinking and reasoning_content:
            # Include reasoning with <thinking> tags
            output_text = f"<thinking>\n{reasoning_content}\n</thinking>\n\n{content}"
        else:
            output_text = content

        # Output to stdout (pipe-friendly)
        print(output_text)

        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"\nOutput saved to: {output_path.resolve()}", file=sys.stderr)

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error generating text: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
