#!/usr/bin/env python3
"""Convert a Claude Code session JSONL to a Cursor/Codex-compatible markdown file."""

import json
import os
import sys


def content_to_text(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        btype = block.get("type", "")
        if btype == "text":
            t = block.get("text", "").strip()
            if t:
                parts.append(t)
        elif btype == "tool_use":
            name = block.get("name", "Tool")
            inp = block.get("input", {}) or {}
            path = inp.get("file_path", inp.get("path", ""))
            basename = os.path.basename(path) if path else ""
            if name in ("Read", "Edit", "Write") and basename:
                parts.append(f"`[{name}: {basename}]`")
            elif name == "Bash":
                cmd = (inp.get("command", "") or "")[:80].replace("\n", " ")
                parts.append(f"`[Bash: {cmd}]`")
            elif name == "Agent":
                desc = inp.get("description", "")
                parts.append(f"`[Agent: {desc}]`")
            else:
                parts.append(f"`[{name}]`")
    return "\n\n".join(parts)


def is_meta_user(record):
    if record.get("isMeta"):
        return True
    content = record.get("message", {}).get("content", "")
    text = content if isinstance(content, str) else " ".join(
        b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
    )
    return any(m in text for m in [
        "command-name", "local-command", "local-stdin",
        "local-command-stdout", "<local-command",
    ])


def export(session_file, output_file=None):
    session_id = os.path.basename(session_file).replace(".jsonl", "")
    title = "(untitled)"
    cwd = ""
    date = ""
    messages = []

    with open(session_file, "r", errors="replace") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue

            rtype = rec.get("type", "")

            if rtype == "ai-title":
                title = rec.get("aiTitle", "(untitled)")

            elif rtype == "user":
                if is_meta_user(rec):
                    continue
                if not cwd:
                    cwd = rec.get("cwd", "")
                if not date:
                    ts = rec.get("timestamp", "")
                    date = ts[:10] if ts else ""
                text = content_to_text(rec.get("message", {}).get("content", ""))
                if text.strip():
                    messages.append(("user", text.strip()))

            elif rtype == "assistant":
                text = content_to_text(rec.get("message", {}).get("content", []))
                if text.strip():
                    messages.append(("assistant", text.strip()))

    lines = [
        "# Claude Session Handoff",
        "",
        f"**Title:** {title}",
        f"**Date:** {date}",
        f"**Project:** {cwd}",
        f"**Session ID:** `{session_id}`",
        "",
        "<!--",
        f"  Cursor : @CLAUDE_HANDOFF.md in chat",
        f"  Codex  : codex --context CLAUDE_HANDOFF.md",
        f"  Resume : claude --resume {session_id}",
        "-->",
        "",
        "---",
        "",
        "## Conversation",
        "",
    ]

    for role, text in messages:
        lines.append("### User" if role == "user" else "### Assistant")
        lines.append("")
        lines.append(text)
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append(f"*Auto-exported from Claude Code · {date}*")

    output = "\n".join(lines)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Exported → {output_file}")
    else:
        print(output)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: export-session.py <session.jsonl> [output.md]", file=sys.stderr)
        sys.exit(1)
    export(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
