---
name: chats
description: Browse and resume previous Claude Code chat sessions for the current project. Lists sessions with short hashes, dates, and titles. Use /chats <hash> for session details and the exact resume command. Use /chats export <hash> to export a session to markdown for Cursor or Codex.
argument-hint: [<hash> | export <hash> | search <keyword>]
allowed-tools: [Bash]
---

# /chats — Browse & Export Previous Sessions

The user invoked this with: $ARGUMENTS

Determine the mode from `$ARGUMENTS`:
- **Empty** → list all sessions
- **8-char hash** (e.g. `5d78b77e`) → show detail for that session
- **`export <hash>`** → export that session to `CLAUDE_HANDOFF.md`
- **`export`** (no hash) → export the most recent session
- **`search <keyword>`** → search across all sessions for a keyword

---

## Mode 1: List All Sessions (no argument)

Run this Bash block:

```bash
set -euo pipefail
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required. Install: brew install jq"; exit 1
fi
ENCODED=$(printf '%s' "$PWD" | sed 's|/|-|g')
SESSIONS_DIR="$HOME/.claude/projects/$ENCODED"
if [ ! -d "$SESSIONS_DIR" ]; then echo "No sessions found for this project."; exit 0; fi
FILES=($(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null || true))
if [ ${#FILES[@]} -eq 0 ]; then echo "No sessions found for this project."; exit 0; fi
printf '%-10s  %-12s  %s\n' "HASH" "DATE" "TITLE"
printf '%-10s  %-12s  %s\n' "----------" "------------" "----------------------------------------"
for f in "${FILES[@]}"; do
  SID=$(basename "$f" .jsonl); SHORT="${SID:0:8}"
  TITLE=$(grep -m 1 '"type":"ai-title"' "$f" 2>/dev/null | jq -r '.aiTitle // "(untitled)"' 2>/dev/null || echo "(untitled)")
  DATE=$(grep -m 1 '"timestamp"' "$f" 2>/dev/null | jq -r '.timestamp // ""' 2>/dev/null | cut -c1-10)
  [ -z "$DATE" ] && DATE="(no date)"
  printf '%-10s  %-12s  %s\n' "[$SHORT]" "$DATE" "$TITLE"
done
echo ""; echo "Use /chats <hash> for details · /chats export <hash> to export for Cursor/Codex"
```

---

## Mode 2: Detail View (hash argument)

Run this Bash block (replace HASH with the user's argument):

```bash
set -euo pipefail
HASH="$ARGUMENTS"
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required. Install: brew install jq"; exit 1
fi
ENCODED=$(printf '%s' "$PWD" | sed 's|/|-|g')
SESSIONS_DIR="$HOME/.claude/projects/$ENCODED"
MATCHED=""
while IFS= read -r f; do
  SID=$(basename "$f" .jsonl)
  if [[ "$SID" == "${HASH}"* ]]; then MATCHED="$f"; break; fi
done < <(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null || true)
if [ -z "$MATCHED" ]; then
  echo "No session found matching: $HASH"; echo "Run /chats to see all sessions."; exit 0
fi
SESSION_ID=$(basename "$MATCHED" .jsonl)
TITLE=$(grep -m 1 '"type":"ai-title"' "$MATCHED" 2>/dev/null | jq -r '.aiTitle // "(untitled)"' 2>/dev/null || echo "(untitled)")
DATE=$(grep -m 1 '"timestamp"' "$MATCHED" 2>/dev/null | jq -r '.timestamp // ""' 2>/dev/null | cut -c1-10)
[ -z "$DATE" ] && DATE="(no date)"
CWD=$(grep -m 1 '"cwd"' "$MATCHED" 2>/dev/null | jq -r '.cwd // ""' 2>/dev/null)
MSG_COUNT=$(grep -c '"type":"user"' "$MATCHED" 2>/dev/null || echo 0)
FIRST_MSG=$(grep '"type":"user"' "$MATCHED" 2>/dev/null \
  | grep -v '"isMeta":true' | grep -v 'command-name\|local-command\|local-stdin' \
  | head -1 \
  | jq -r '.message.content | if type=="array" then (map(select(.type=="text")) | .[0].text // "") else (. // "") end | .[0:200]' 2>/dev/null || echo "")
echo "Session:  $SESSION_ID"
echo "Title:    $TITLE"; echo "Date:     $DATE"; echo "CWD:      $CWD"
echo "Messages: $MSG_COUNT"
[ -n "$FIRST_MSG" ] && echo "Preview:  $FIRST_MSG"
echo ""; echo "Resume:  claude --resume $SESSION_ID"
echo "Export:  /chats export $SESSION_ID"
```

Show the resume command in a code block. Do not attempt to resume in-session.

---

## Mode 3: Export to Markdown (export argument)

Parse `$ARGUMENTS`:
- If `$ARGUMENTS` starts with `export `, extract the hash after it
- If `$ARGUMENTS` is exactly `export`, use the most recent session

Run this Bash block:

```bash
set -euo pipefail
ARGS="$ARGUMENTS"
ENCODED=$(printf '%s' "$PWD" | sed 's|/|-|g')
SESSIONS_DIR="$HOME/.claude/projects/$ENCODED"

# Resolve session file
if [[ "$ARGS" == "export "* ]]; then
  HASH="${ARGS#export }"
  SESSION_FILE=""
  while IFS= read -r f; do
    SID=$(basename "$f" .jsonl)
    if [[ "$SID" == "${HASH}"* ]]; then SESSION_FILE="$f"; break; fi
  done < <(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null || true)
  if [ -z "$SESSION_FILE" ]; then
    echo "No session found matching: $HASH"; exit 0
  fi
else
  SESSION_FILE=$(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null | head -1 || true)
  if [ -z "$SESSION_FILE" ]; then
    echo "No sessions found for this project."; exit 0
  fi
fi

OUTPUT="$PWD/CLAUDE_HANDOFF.md"

# Inline export using python3
python3 - "$SESSION_FILE" "$OUTPUT" << 'PYEOF'
import json, os, sys

def content_to_text(content):
    if isinstance(content, str): return content
    if not isinstance(content, list): return ""
    parts = []
    for b in content:
        btype = b.get("type","")
        if btype == "text":
            t = b.get("text","").strip()
            if t: parts.append(t)
        elif btype == "tool_use":
            name = b.get("name","Tool")
            inp = b.get("input",{}) or {}
            path = inp.get("file_path", inp.get("path",""))
            base = os.path.basename(path) if path else ""
            if name in ("Read","Edit","Write") and base: parts.append(f"`[{name}: {base}]`")
            elif name == "Bash":
                cmd = (inp.get("command","") or "")[:80].replace("\n"," ")
                parts.append(f"`[Bash: {cmd}]`")
            elif name == "Agent": parts.append(f"`[Agent: {inp.get('description','')}]`")
            else: parts.append(f"`[{name}]`")
    return "\n\n".join(parts)

def is_meta(rec):
    if rec.get("isMeta"): return True
    c = rec.get("message",{}).get("content","")
    t = c if isinstance(c,str) else " ".join(b.get("text","") for b in c if isinstance(b,dict) and b.get("type")=="text")
    return any(m in t for m in ["command-name","local-command","local-stdin","<local-command"])

session_file, output_file = sys.argv[1], sys.argv[2]
sid = os.path.basename(session_file).replace(".jsonl","")
title,cwd,date,msgs = "(untitled)","","",[]

with open(session_file,"r",errors="replace") as f:
    for raw in f:
        raw = raw.strip()
        if not raw: continue
        try: rec = json.loads(raw)
        except: continue
        rt = rec.get("type","")
        if rt == "ai-title": title = rec.get("aiTitle","(untitled)")
        elif rt == "user":
            if is_meta(rec): continue
            if not cwd: cwd = rec.get("cwd","")
            if not date: date = (rec.get("timestamp","") or "")[:10]
            t = content_to_text(rec.get("message",{}).get("content",""))
            if t.strip(): msgs.append(("user",t.strip()))
        elif rt == "assistant":
            t = content_to_text(rec.get("message",{}).get("content",[]))
            if t.strip(): msgs.append(("assistant",t.strip()))

out = ["# Claude Session Handoff","",
    f"**Title:** {title}", f"**Date:** {date}",
    f"**Project:** {cwd}", f"**Session ID:** `{sid}`","",
    "<!--",
    f"  Cursor : @CLAUDE_HANDOFF.md in chat",
    f"  Codex  : codex --context CLAUDE_HANDOFF.md",
    f"  Resume : claude --resume {sid}","-->","","---","","## Conversation",""]

for role,text in msgs:
    out += ["### User" if role=="user" else "### Assistant","",text,"","---",""]

out.append(f"*Auto-exported from Claude Code · {date}*")
with open(output_file,"w",encoding="utf-8") as f: f.write("\n".join(out))
print(f"Exported → {output_file}")
PYEOF
```

After running, tell the user:
- The file was written to `CLAUDE_HANDOFF.md` in the project root
- **Cursor**: type `@CLAUDE_HANDOFF.md` in the chat
- **Codex**: run `codex --context CLAUDE_HANDOFF.md`

---

---

## Mode 4: Search Sessions (search keyword)

`$ARGUMENTS` starts with `search `. Extract everything after `search ` as the keyword.

Run this Bash block:

```bash
set -euo pipefail
KEYWORD="${ARGUMENTS#search }"
if [ -z "$KEYWORD" ]; then
  echo "Usage: /chats search <keyword>"; exit 0
fi
ENCODED=$(printf '%s' "$PWD" | sed 's|/|-|g')
SESSIONS_DIR="$HOME/.claude/projects/$ENCODED"
SEARCH_SCRIPT="$HOME/.claude/skills/chats/search-sessions.py"

# Fallback to plugin dir if running via plugin install
if [ ! -f "$SEARCH_SCRIPT" ]; then
  SEARCH_SCRIPT="${CLAUDE_PLUGIN_ROOT}/scripts/search-sessions.py"
fi

python3 "$SEARCH_SCRIPT" "$SESSIONS_DIR" "$KEYWORD"
```

Present the results clearly. Each matching session shows its hash, date, title, and up to 3 snippets with the role (`user`/`asst`) prefixed. If no matches, say so.

---

## Notes

- `jq` required for Modes 1 & 2. `python3` required for Modes 3 & 4.
- `CLAUDE_HANDOFF.md` is safe to add to `.gitignore` if you don't want it committed.
- The auto-export hook writes this file after every Claude response automatically.
