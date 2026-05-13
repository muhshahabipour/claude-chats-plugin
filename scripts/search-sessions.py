#!/usr/bin/env python3
"""Search across Claude Code session files for a keyword."""

import json
import os
import re
import sys


def extract_texts(content):
    """Yield plain text strings from a message content field."""
    if isinstance(content, str):
        if content.strip():
            yield content
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text", "").strip()
                if t:
                    yield t


def snippet(text, keyword, radius=120):
    """Return a short excerpt around the first match of keyword in text."""
    idx = text.lower().find(keyword.lower())
    if idx == -1:
        return None
    start = max(0, idx - radius // 2)
    end = min(len(text), idx + len(keyword) + radius // 2)
    excerpt = text[start:end].replace("\n", " ").strip()
    if start > 0:
        excerpt = "…" + excerpt
    if end < len(text):
        excerpt = excerpt + "…"
    return excerpt


def is_meta(rec):
    if rec.get("isMeta"):
        return True
    c = rec.get("message", {}).get("content", "")
    t = c if isinstance(c, str) else " ".join(
        b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"
    )
    return any(m in t for m in ["command-name", "local-command", "local-stdin", "<local-command"])


def search_file(path, keyword):
    """Return dict with match info if keyword found in session, else None."""
    sid = os.path.basename(path).replace(".jsonl", "")
    title = "(untitled)"
    date = ""
    matches = []

    with open(path, "r", errors="replace") as f:
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
                continue

            if rtype == "user":
                if is_meta(rec):
                    continue
                if not date:
                    date = (rec.get("timestamp", "") or "")[:10]
                content = rec.get("message", {}).get("content", "")
                for text in extract_texts(content):
                    s = snippet(text, keyword)
                    if s:
                        matches.append(("user", s))

            elif rtype == "assistant":
                content = rec.get("message", {}).get("content", [])
                for text in extract_texts(content):
                    s = snippet(text, keyword)
                    if s:
                        matches.append(("assistant", s))

    if not matches:
        return None

    return {
        "sid": sid,
        "short": sid[:8],
        "title": title,
        "date": date or "(no date)",
        "matches": matches[:3],  # up to 3 snippets per session
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: search-sessions.py <sessions-dir> <keyword>", file=sys.stderr)
        sys.exit(1)

    sessions_dir = sys.argv[1]
    keyword = " ".join(sys.argv[2:])

    if not os.path.isdir(sessions_dir):
        print(f"No sessions found.")
        sys.exit(0)

    files = sorted(
        [os.path.join(sessions_dir, f) for f in os.listdir(sessions_dir) if f.endswith(".jsonl")],
        key=os.path.getmtime,
        reverse=True,
    )

    if not files:
        print("No sessions found.")
        sys.exit(0)

    results = []
    for path in files:
        r = search_file(path, keyword)
        if r:
            results.append(r)

    if not results:
        print(f'No sessions found matching: "{keyword}"')
        sys.exit(0)

    print(f'Found {len(results)} session(s) matching "{keyword}"\n')
    for r in results:
        print(f"[{r['short']}]  {r['date']}  {r['title']}")
        for role, s in r["matches"]:
            prefix = "  user: " if role == "user" else "  asst: "
            print(f"{prefix}{s}")
        print()


if __name__ == "__main__":
    main()
