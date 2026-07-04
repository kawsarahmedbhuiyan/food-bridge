#!/usr/bin/env python3
"""Backfill logs/cursor-agent-interactions.log from Cursor agent transcript JSONL files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / ".cursor" / "hooks"))

from log_interaction import LOG_FILE, _extract_text_from_content, append_entry  # noqa: E402

TRANSCRIPT_GLOB = Path.home() / ".cursor" / "projects" / "Users-macbook-Documents-food-bridge" / "agent-transcripts"


def _collect_text_blocks(content: list) -> str:
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text = _extract_text_from_content(block.get("text", ""))
            if text and text != "[REDACTED]":
                parts.append(text)
    return "\n".join(parts).strip()


def backfill_transcript(path: Path) -> int:
    entries = 0
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if record.get("type") == "turn_ended":
                continue

            role = record.get("role")
            message = record.get("message", {})
            content = message.get("content", [])

            if role == "user":
                text = _collect_text_blocks(content) if isinstance(content, list) else str(content)
                if text:
                    append_entry("human", text, source=f"transcript:{path.name}")
                    entries += 1
            elif role == "assistant":
                text = _collect_text_blocks(content) if isinstance(content, list) else str(content)
                if text:
                    append_entry("assistant", text, source=f"transcript:{path.name}")
                    entries += 1

    return entries


def main() -> int:
    if not TRANSCRIPT_GLOB.exists():
        print(f"No transcript directory: {TRANSCRIPT_GLOB}")
        return 1

    jsonl_files = list(TRANSCRIPT_GLOB.glob("**/*.jsonl"))
    if not jsonl_files:
        print("No transcript JSONL files found.")
        return 1

    total = 0
    for path in sorted(jsonl_files):
        count = backfill_transcript(path)
        total += count
        print(f"Backfilled {count} entries from {path}")

    print(f"Wrote {total} entries to {LOG_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
