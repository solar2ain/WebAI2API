#!/usr/bin/env python3
"""
Generate images using WebAI2API with OpenAI-compatible API.

Usage:
    python3 generate_image.py --prompt "your image description"
    python3 generate_image.py --prompt "your image description" --output "./my_image.png"
    python3 generate_image.py --prompt "your image description" --output "./output_dir/" -n 3

Filename convention (when output is a directory):
    {model_short}_{YYYYMMDD}_{prompt_summary}_{seq}.png
    Example: gemini3_20240226_sunset_mountain_01.png

Environment Variables:
    WEBAI2API_HOST: API host URL (default: http://127.0.0.1:3000/)
    WEBAI2API_API_KEY: API key for authentication (required)

Dependencies:
    pip install requests pillow
"""

import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime
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


def get_model_short_name(model: str) -> str:
    """Get short name for model."""
    model_lower = model.lower()

    # GPT/ChatGPT image models
    if "chatgpt-image" in model_lower:
        return "chatgpt"
    if "gpt-image-1.5" in model_lower:
        return "gpt1.5"
    if "gpt-image-1" in model_lower:
        return "gpt1"

    # Gemini models
    if "gemini-3.1" in model_lower:
        return "gemini3.1"
    if "gemini-3" in model_lower:
        return "gemini3"
    if "gemini-2.5" in model_lower:
        return "gemini2.5"

    # Flux models
    if "flux-2" in model_lower:
        return "flux2"
    if "flux-1" in model_lower:
        return "flux1"

    # Seedream models
    if "seedream-5" in model_lower:
        return "seedream5"
    if "seedream-4" in model_lower:
        return "seedream4"

    # Imagen
    if "imagen-4" in model_lower:
        return "imagen4"

    # Hunyuan
    if "hunyuan" in model_lower:
        return "hunyuan"

    # Qwen
    if "qwen-image" in model_lower:
        return "qwen"

    # Wan
    if "wan" in model_lower:
        return "wan"

    # Recraft
    if "recraft" in model_lower:
        return "recraft"

    # Mai
    if "mai-image" in model_lower:
        return "mai"

    # Veo
    if "veo" in model_lower:
        return "veo"

    # Grok
    if "grok-imagine" in model_lower:
        return "grok"

    # Fallback: use first part of model name
    return model.split("-")[0][:8]


def get_next_sequence(output_dir: Path, base_name: str) -> int:
    """Get next sequence number for filename."""
    pattern = re.compile(rf"^{re.escape(base_name)}_(\d+)\.png$")
    max_seq = 0

    if output_dir.exists():
        for f in output_dir.iterdir():
            match = pattern.match(f.name)
            if match:
                seq = int(match.group(1))
                max_seq = max(max_seq, seq)

    return max_seq + 1


def get_prompt_summary(prompt: str, max_words: int = 4) -> str:
    """Extract first few words from prompt for filename, sanitized for filesystem."""
    # Remove special characters, keep only alphanumeric and spaces
    clean = re.sub(r'[^\w\s]', '', prompt)
    # Split into words and take first N
    words = clean.split()[:max_words]
    # Join with underscore and lowercase
    summary = '_'.join(words).lower()
    # Limit length
    return summary[:30] if summary else "image"


def is_image_generation_model(model_id: str) -> bool:
    """Check if model is an image generation model by name patterns."""
    model_lower = model_id.lower()
    # Known image generation model patterns
    image_gen_patterns = [
        "gpt-image",
        "chatgpt-image",
        "gemini-3-pro-image",
        "gemini-3.1-flash-image",
        "gemini-2.5-flash-image",
        "imagen-",
        "flux-",
        "seedream-",
        "hunyuan-image",
        "qwen-image",
        "wan2.5-t2i",
        "recraft-",
        "mai-image",
        "veo-",
        "grok-imagine",
    ]
    return any(p in model_lower for p in image_gen_patterns)


def normalize_image_adapter(adapter: str) -> str:
    """Normalize adapter name to image adapter format.

    For image generation, adapter names should NOT have '_text' suffix.
    """
    if not adapter:
        return adapter

    # Remove _text suffix if present (user might input lmarena_text by mistake)
    if adapter.endswith('_text'):
        return adapter[:-5]

    # Map some common variations
    adapter_map = {
        'zai': 'zai_is',
        'zenmux': 'nanobananafree_ai',
        'nanobananafree': 'nanobananafree_ai',
    }

    return adapter_map.get(adapter, adapter)


def list_models(api_host: str, api_key: str) -> None:
    """List available image generation models from the API."""
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
        model_list = []
        for m in result["data"]:
            full_id = m.get("id", "")
            if "/" not in full_id:
                continue  # Skip non-prefixed models

            adapter, base_model = full_id.split("/", 1)
            if adapter.endswith("_text"):
                continue  # Skip text adapters

            if not is_image_generation_model(base_model):
                continue

            model_list.append({
                "full_id": full_id,
                "short_name": get_model_short_name(base_model),
                "image_policy": m.get("image_policy", ""),
            })

        if not model_list:
            print("No image generation models found.", file=sys.stderr)
            sys.exit(1)

        print(f"Available image generation models ({len(model_list)}):\n")
        for info in sorted(model_list, key=lambda x: x["full_id"]):
            full_id = info["full_id"]
            short_name = info["short_name"]
            image_policy = info["image_policy"]
            policy_hint = " [no input image]" if image_policy == "forbidden" else ""
            print(f"  - {full_id} ({short_name}){policy_hint}")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching models: {e}", file=sys.stderr)
        sys.exit(1)


def generate_single_image(api_host: str, api_key: str, model: str, prompt: str,
                          output_dir: Path, filename: str, requests_module, PILImage, BytesIO,
                          input_images_b64: list | None = None) -> Path | None:
    """Generate a single image and save it. Returns the output path or None on failure."""
    # Build user message content
    if input_images_b64:
        # Vision format: content is array of image_url and text
        content_parts = []
        for img_url in input_images_b64:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": img_url}
            })
        content_parts.append({"type": "text", "text": prompt})
        user_content = content_parts
    else:
        user_content = prompt

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": user_content}
        ]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        endpoint = f"{api_host}v1/chat/completions"
        response = requests_module.post(endpoint, json=payload, headers=headers, timeout=300)
        response.raise_for_status()
        result = response.json()

        if "choices" not in result or len(result["choices"]) == 0:
            print("Error: No choices in response.", file=sys.stderr)
            return None

        message = result["choices"][0].get("message", {})
        content = message.get("content", "")

        # Extract base64 image data from content
        b64_data = None
        if "data:image" in content and ";base64," in content:
            b64_start = content.find(";base64,") + len(";base64,")
            b64_end = content.find(")", b64_start)
            if b64_end == -1:
                b64_end = len(content)
            b64_data = content[b64_start:b64_end]
        else:
            print("Error: No base64 image data found in response.", file=sys.stderr)
            print(f"Response content preview: {content[:200]}...", file=sys.stderr)
            return None

        # Decode base64 and save image
        image_bytes = base64.b64decode(b64_data)
        image = PILImage.open(BytesIO(image_bytes))

        output_path = output_dir / filename

        # Ensure RGB mode for PNG
        if image.mode == 'RGBA':
            rgb_image = PILImage.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])
            rgb_image.save(str(output_path), 'PNG')
        elif image.mode == 'RGB':
            image.save(str(output_path), 'PNG')
        else:
            image.convert('RGB').save(str(output_path), 'PNG')

        return output_path

    except requests_module.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        return None


def main():
    # Get script directory for default output
    script_dir = Path(__file__).parent.parent
    default_output_dir = script_dir / "images"

    parser = argparse.ArgumentParser(
        description="Generate images using WebAI2API with OpenAI-compatible API"
    )
    parser.add_argument(
        "--list-models", "-l",
        action="store_true",
        help="List available models and exit"
    )
    parser.add_argument(
        "--prompt", "-p",
        help="Image description/prompt (required for generation)"
    )
    parser.add_argument(
        "--input-image", "-i",
        action="append",
        dest="input_images",
        metavar="IMAGE",
        help="Input image path(s) for editing/composition. Can be specified multiple times (up to 10 images)."
    )
    parser.add_argument(
        "--output", "-o",
        help=f"Output path: directory (auto-generate filename) or file path (default: {default_output_dir})"
    )
    parser.add_argument(
        "--model", "-m",
        default="gemini/gemini-3-pro-image-preview",
        help="Model to use for image generation (default: gemini/gemini-3-pro-image-preview)"
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=1,
        help="Number of images to generate (default: 1)"
    )
    parser.add_argument(
        "--size", "-s",
        choices=["1024x1024", "1792x1024", "1024x1792"],
        help="Image size hint (will be added to prompt). Options: 1024x1024, 1792x1024, 1024x1792"
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
        help="Adapter/provider prefix (e.g., lmarena, gemini). Model will be called as adapter/model"
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

    # Validate prompt is provided for generation
    if not args.prompt:
        print("Error: --prompt is required for image generation.", file=sys.stderr)
        sys.exit(1)

    # Validate count
    if args.count < 1:
        print("Error: -n must be at least 1.", file=sys.stderr)
        sys.exit(1)

    # Import here after checking API key to avoid slow import on error
    import requests
    from PIL import Image as PILImage
    from io import BytesIO

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
                print(f"Loaded input image: {img_path}")
            except Exception as e:
                print(f"Error loading input image '{img_path}': {e}", file=sys.stderr)
                sys.exit(1)

    # Determine output directory and filename
    output_path = Path(args.output) if args.output else None
    user_provided_filename = False

    if output_path:
        # Check if output is a file path or directory
        # If it has a file extension or doesn't end with /, treat as file
        if output_path.suffix or (output_path.exists() and output_path.is_file()):
            # File path provided
            output_dir = output_path.parent or Path(".")
            user_provided_filename = True
            name_stem = output_path.stem
            name_ext = output_path.suffix or ".png"
        else:
            # Directory provided
            output_dir = output_path
            user_provided_filename = False
    else:
        output_dir = default_output_dir
        user_provided_filename = False

    output_dir.mkdir(parents=True, exist_ok=True)

    # Build the actual prompt (add size hint if specified)
    actual_prompt = args.prompt
    if args.size:
        actual_prompt = f"{args.prompt} [Image size: {args.size}]"

    # Prepare filename base
    # Extract base model name for short name (remove adapter prefix if present)
    base_model_for_short = args.model.split("/")[-1] if "/" in args.model else args.model
    model_short = get_model_short_name(base_model_for_short)
    date_str = datetime.now().strftime("%Y%m%d")
    prompt_summary = get_prompt_summary(args.prompt)

    if not user_provided_filename:
        # Auto-generate: {model_short}_{YYYYMMDD}_{prompt_summary}
        name_stem = f"{model_short}_{date_str}_{prompt_summary}"
        name_ext = ".png"

    # Normalize adapter name for image generation
    adapter = normalize_image_adapter(args.adapter) if args.adapter else None

    # Build actual model name with adapter prefix
    actual_model = f"{adapter}/{args.model}" if adapter else args.model

    print(f"Generating {args.count} image(s) with model {actual_model}...")
    if args.size:
        print(f"Size hint: {args.size}")
    print(f"API Host: {api_host}")
    print()

    # Generate images
    generated_files = []
    for i in range(args.count):
        if args.count == 1 and user_provided_filename:
            # Single image with user-provided filename (no sequence)
            output_filename = f"{name_stem}{name_ext}"
        else:
            # Multiple images or auto-generated: add sequence number
            seq = get_next_sequence(output_dir, name_stem) if not user_provided_filename else i + 1
            output_filename = f"{name_stem}_{seq:02d}{name_ext}"

        print(f"[{i+1}/{args.count}] Generating {output_filename}...", end=" ", flush=True)

        output_file_path = generate_single_image(
            api_host, api_key, actual_model, actual_prompt,
            output_dir, output_filename, requests, PILImage, BytesIO,
            input_images_b64
        )

        if output_file_path:
            print(f"OK")
            generated_files.append(output_file_path)
        else:
            print(f"FAILED")

    if not generated_files:
        print("\nNo images were generated.", file=sys.stderr)
        sys.exit(1)

    # Generate metadata file (same name as image, but .json extension)
    timestamp = datetime.now().isoformat()
    # Use the first generated file's stem for metadata filename
    first_file_stem = generated_files[0].stem
    # Remove sequence suffix if present (e.g., _01, _02)
    meta_stem = re.sub(r'_\d+$', '', first_file_stem)
    meta_filename = f"{meta_stem}.json"
    meta_path = output_dir / meta_filename

    # Load existing metadata or create new
    if meta_path.exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        for fp in generated_files:
            if fp.name not in metadata.get("filenames", []):
                metadata["filenames"].append(fp.name)
        metadata["timestamp"] = timestamp
    else:
        metadata = {
            "model": args.model,
            "prompt": args.prompt,
            "timestamp": timestamp,
            "filenames": [fp.name for fp in generated_files]
        }
        if args.size:
            metadata["size_hint"] = args.size

    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{len(generated_files)} image(s) saved to: {output_dir.resolve()}")
    print(f"Metadata saved: {meta_path.resolve()}")

    # OpenClaw parses MEDIA tokens
    for fp in generated_files:
        print(f"MEDIA: {fp.resolve()}")


if __name__ == "__main__":
    main()
