#!/usr/bin/env python3
"""MarkItDown-backed Source -> Markdown helper for Beautiful Article.

This script intentionally depends on MarkItDown and fails clearly when it is not
available. Use source-to-markdown.py as the lightweight fallback.

Usage:
    python3 source-to-markdown-markitdown.py <file-or-url> -o source/source.md

Optional dependency:
    python3.10 -m pip install "markitdown[pdf,docx]"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse


INSTALL_HINT = 'python3.10 -m pip install "markitdown[pdf,docx]"'


def load_markitdown():
    if sys.version_info < (3, 10):
        print(
            "✗ MarkItDown requires Python 3.10+; current Python is "
            f"{sys.version_info.major}.{sys.version_info.minor}.",
            file=sys.stderr,
        )
        print(f"  Install with: {INSTALL_HINT}", file=sys.stderr)
        raise SystemExit(2)

    try:
        from markitdown import MarkItDown  # type: ignore
    except Exception as exc:
        print("✗ MarkItDown is not installed in this Python environment.", file=sys.stderr)
        print(f"  Install with: {INSTALL_HINT}", file=sys.stderr)
        print("  Or use scripts/source-to-markdown.py as the fallback.", file=sys.stderr)
        print(f"  Import error: {exc}", file=sys.stderr)
        raise SystemExit(2)

    return MarkItDown


def result_text(result) -> str:
    for attr in ("text_content", "markdown"):
        value = getattr(result, attr, None)
        if isinstance(value, str) and value.strip():
            return value
    if isinstance(result, str):
        return result
    raise RuntimeError("MarkItDown returned no text_content/markdown output.")


def is_url(src: str) -> bool:
    return urlparse(src).scheme in ("http", "https")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a source file or URL to Markdown via MarkItDown")
    parser.add_argument("input", help="PDF / DOCX / PPTX / HTML / TXT / MD file or URL")
    parser.add_argument("-o", "--output", help="write Markdown here (default: stdout)")
    parser.add_argument(
        "--use-plugins",
        action="store_true",
        help="enable installed MarkItDown plugins; disabled by default",
    )
    args = parser.parse_args()

    src = args.input
    if not is_url(src) and not Path(src).exists():
        print(f"✗ 文件不存在：{src}", file=sys.stderr)
        raise SystemExit(1)

    MarkItDown = load_markitdown()
    converter = MarkItDown(enable_plugins=args.use_plugins)

    try:
        markdown = result_text(converter.convert(src)).strip() + "\n"
    except Exception as exc:
        print(f"✗ MarkItDown 转换失败：{exc}", file=sys.stderr)
        print("  可改用 scripts/source-to-markdown.py 做轻量 fallback。", file=sys.stderr)
        raise SystemExit(2)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown, "utf-8")
        print(
            f"✓ MarkItDown 写入 {out}（{len(markdown)} 字符）。"
            "请继续清理噪音并补 extraction-notes.md。",
            file=sys.stderr,
        )
    else:
        sys.stdout.write(markdown)


if __name__ == "__main__":
    main()
