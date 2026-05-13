---
name: chats
description: Browse and resume previous Claude Code chat sessions for the current project. Lists sessions with short hashes, dates, and titles. Use /chats <hash> for session details and the exact resume command.
argument-hint: [<hash>]
allowed-tools: [Bash]
---

# /chats — Browse Previous Sessions

The user invoked this with: $ARGUMENTS

Determine the mode from `$ARGUMENTS`:
- **Empty** → list all sessions for the current project
- **8-char hash** (e.g. `5d78b77e`) → show detail for that session

---

## Mode 1: List All Sessions (no argument)

Run this exact Bash block:

```bash
set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required. Install it with: brew install jq"
  exit 1
fi

ENCODED=$(printf '%s' "$PWD" | sed 's|/|-|g')
SESSIONS_DIR="$HOME/.claude/projects/$ENCODED"

if [ ! -d "$SESSIONS_DIR" ]; then
  echo "No sessions found for this project."
  exit 0
fi

FILES=($(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null || true))
if [ ${#FILES[@]} -eq 0 ]; then
  echo "No sessions found for this project."
  exit 0
fi

printf '%-10s  %-12s  %s\n' "HASH" "DATE" "TITLE"
printf '%-10s  %-12s  %s\n' "----------" "------------" "----------------------------------------"

for f in "${FILES[@]}"; do
  SID=$(basename "$f" .jsonl)
  SHORT="${SID:0:8}"

  TITLE=$(grep -m 1 '"type":"ai-title"' "$f" 2>/dev/null \
    | jq -r '.aiTitle // "(untitled)"' 2>/dev/null \
    || echo "(untitled)")

  DATE=$(grep -m 1 '"timestamp"' "$f" 2>/dev/null \
    | jq -r '.timestamp // ""' 2>/dev/null \
    | cut -c1-10)
  [ -z "$DATE" ] && DATE="(no date)"

  printf '%-10s  %-12s  %s\n' "[$SHORT]" "$DATE" "$TITLE"
done

echo ""
echo "Use /chats <hash> for details and the resume command."
```

Present the output as a clean table. If the list is empty say so and stop.

---

## Mode 2: Detail View (hash argument provided)

Run this exact Bash block, substituting the user's argument for `HASH`:

```bash
set -euo pipefail
HASH="$ARGUMENTS"

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required. Install it with: brew install jq"
  exit 1
fi

ENCODED=$(printf '%s' "$PWD" | sed 's|/|-|g')
SESSIONS_DIR="$HOME/.claude/projects/$ENCODED"

MATCHED=""
while IFS= read -r f; do
  SID=$(basename "$f" .jsonl)
  if [[ "$SID" == "${HASH}"* ]]; then
    MATCHED="$f"
    break
  fi
done < <(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null || true)

if [ -z "$MATCHED" ]; then
  echo "No session found matching: $HASH"
  echo "Run /chats to see all sessions."
  exit 0
fi

SESSION_ID=$(basename "$MATCHED" .jsonl)

TITLE=$(grep -m 1 '"type":"ai-title"' "$MATCHED" 2>/dev/null \
  | jq -r '.aiTitle // "(untitled)"' 2>/dev/null || echo "(untitled)")

DATE=$(grep -m 1 '"timestamp"' "$MATCHED" 2>/dev/null \
  | jq -r '.timestamp // ""' 2>/dev/null | cut -c1-10)
[ -z "$DATE" ] && DATE="(no date)"

CWD=$(grep -m 1 '"cwd"' "$MATCHED" 2>/dev/null \
  | jq -r '.cwd // ""' 2>/dev/null)

MSG_COUNT=$(grep -c '"type":"user"' "$MATCHED" 2>/dev/null || echo 0)

FIRST_MSG=$(grep '"type":"user"' "$MATCHED" 2>/dev/null \
  | grep -v '"isMeta":true' \
  | grep -v 'command-name\|local-command\|local-stdin' \
  | head -1 \
  | jq -r '
      .message.content
      | if type == "array"
        then (map(select(.type == "text")) | .[0].text // "")
        else (. // "")
        end
      | .[0:200]
    ' 2>/dev/null || echo "")

echo "Session:  $SESSION_ID"
echo "Title:    $TITLE"
echo "Date:     $DATE"
echo "CWD:      $CWD"
echo "Messages: $MSG_COUNT"
[ -n "$FIRST_MSG" ] && echo "Preview:  $FIRST_MSG"
echo ""
echo "Resume command:"
echo "  claude --resume $SESSION_ID"
```

After the output, display the resume command prominently in a code block:

```
claude --resume <full-session-id>
```

**Do not attempt to resume the session from here.** The user must run the command in a terminal themselves — there is no in-session mechanism to switch conversations.

---

## Notes

- `jq` is required. If missing, report it and suggest `brew install jq` (macOS) or `apt-get install jq` (Linux).
- Short hash = first 8 characters of the session UUID. Collisions are practically impossible.
- The `--resume` flag requires the full UUID, not the short hash.
- Sessions without an `ai-title` record (very short or interrupted sessions) show `(untitled)` — this is normal.
