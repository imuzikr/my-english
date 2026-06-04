#!/usr/bin/env python3
"""Generate images with OpenAI gpt-image-2.

Usage:
  python scripts/generate_image2.py "A warm watercolor illustration" --out output/imagegen/hero.png

Requires:
  OPENAI_API_KEY environment variable.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


API_URL = "https://api.openai.com/v1/images/generations"
MODEL = "gpt-image-2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate PNG/JPEG/WebP images with OpenAI gpt-image-2."
    )
    parser.add_argument("prompt", nargs="?", help="Image prompt text.")
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Read the image prompt from a UTF-8 text file instead of an argument.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("output/imagegen/image.png"),
        help="Output image path. For --n > 1, numbered suffixes are added.",
    )
    parser.add_argument(
        "--size",
        default="1536x1024",
        help="Image size, for example 1024x1024, 1536x1024, 1024x1536, or auto.",
    )
    parser.add_argument(
        "--quality",
        default="medium",
        choices=("low", "medium", "high", "auto"),
        help="Generation quality.",
    )
    parser.add_argument(
        "--format",
        default="png",
        choices=("png", "jpeg", "webp"),
        help="Output image format.",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="Number of images to generate.",
    )
    return parser.parse_args()


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return args.prompt_file.read_text(encoding="utf-8").strip()
    if args.prompt:
        return args.prompt.strip()
    raise SystemExit("Prompt is required. Pass it as an argument or use --prompt-file.")


def request_images(api_key: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"OpenAI API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach OpenAI API: {exc}") from exc


def output_path(base: Path, index: int, total: int, output_format: str) -> Path:
    suffix = f".{output_format}"
    path = base.with_suffix(suffix)
    if total == 1:
        return path
    return path.with_name(f"{path.stem}-{index + 1:02d}{path.suffix}")


def save_image(item: dict, path: Path) -> None:
    if "b64_json" in item:
        data = base64.b64decode(item["b64_json"])
    elif "url" in item:
        with urllib.request.urlopen(item["url"], timeout=300) as response:
            data = response.read()
    else:
        raise SystemExit(f"Unexpected image response item: {item.keys()}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main() -> int:
    args = parse_args()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(
            "OPENAI_API_KEY is not set. Create an API key at "
            "https://platform.openai.com/api-keys and set it as an environment variable.",
            file=sys.stderr,
        )
        return 2

    prompt = load_prompt(args)
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": args.size,
        "quality": args.quality,
        "output_format": args.format,
        "n": args.n,
    }

    started = time.time()
    result = request_images(api_key, payload)
    images = result.get("data", [])
    if not images:
        raise SystemExit(f"No images returned: {json.dumps(result, ensure_ascii=False)}")

    saved = []
    for index, item in enumerate(images):
        path = output_path(args.out, index, len(images), args.format)
        save_image(item, path)
        saved.append(path)

    elapsed = time.time() - started
    for path in saved:
        print(path)
    print(f"Generated {len(saved)} image(s) with {MODEL} in {elapsed:.1f}s", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
