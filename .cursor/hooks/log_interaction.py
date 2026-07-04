#!/usr/bin/env python3
"""
Append human ↔ Cursor agent interactions to logs/cursor-agent-interactions.log.

Used by Cursor hooks (beforeSubmitPrompt, afterAgentResponse) and by
scripts/backfill_cursor_log.py for historical transcripts.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "cursor-agent-interactions.log"

TAG_RE = re.compile(r"<[^>]+>")
USER_QUERY_RE = re.compile(r"<user_query>\s*(.*?)\s*</user_query>", re.DOTALL)


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _strip_markup(text: str) -> str:
    match = USER_QUERY_RE.search(text)
    if match:
        text = match.group(1).strip()
    text = TAG_RE.sub("", text)
    return text.strip()


def _extract_text_from_content(content) -> str:
    if isinstance(content, str):
        return _strip_markup(content)
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(_strip_markup(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(_strip_markup(block))
        return "\n".join(p for p in parts if p).strip()
    return _strip_markup(str(content))


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def append_entry(role: str, message: str, source: str = "cursor-hook") -> None:
    message = message.strip()
    if not message:
        return
    _ensure_log_dir()
    divider = "=" * 80
    block = (
        f"{divider}\n"
        f"[{_now_iso()}] {role.upper()}  (source: {source})\n"
        f"{divider}\n"
        f"{message}\n\n"
    )
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(block)


def _find_message(payload: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        val = payload.get(key)
        if val:
            return _extract_text_from_content(val)
    return ""


def handle_hook_payload(payload: dict, event: str) -> None:
    if event == "beforeSubmitPrompt":
        text = _find_message(payload, ("prompt", "message", "text", "content"))
        if not text:
            text = _extract_text_from_content(payload)
        append_entry("human", text, source="beforeSubmitPrompt")
        return

    if event in ("afterAgentResponse", "stop"):
        text = _find_message(payload, ("response", "text", "message", "content", "output"))
        if not text:
            text = _extract_text_from_content(payload)
        append_entry("assistant", text, source=event)


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        append_entry("system", raw, source="raw-stdin")
        return 0

    event = (
        payload.get("hook_event_name")
        or payload.get("event")
        or (sys.argv[1] if len(sys.argv) > 1 else "")
    )
    handle_hook_payload(payload, event)
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
