#!/usr/bin/env bash
# Fires at SessionStart. Shows how many previous sessions exist for this project,
# with short hashes so the user can jump straight to /chats <hash>.

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  echo '{"priority": "INFO", "message": "claude-chats: install jq to enable session history hints (brew install jq)."}'
  exit 0
fi

# Read current session_id from hook stdin (graceful fallback for older versions)
if [ -t 0 ]; then
  INPUT="{}"
else
  INPUT=$(cat)
fi
CURRENT_SESSION=$(printf '%s' "$INPUT" | jq -r '.session_id // ""' 2>/dev/null || true)

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$PROJECT_DIR" ]; then
  exit 0
fi

ENCODED=$(printf '%s' "$PROJECT_DIR" | sed 's|/|-|g')
SESSIONS_DIR="${HOME}/.claude/projects/${ENCODED}"

if [ ! -d "$SESSIONS_DIR" ]; then
  exit 0
fi

# Collect previous sessions (exclude current), newest first
PREV_FILES=()
while IFS= read -r f; do
  SID=$(basename "$f" .jsonl)
  [ "$SID" = "$CURRENT_SESSION" ] && continue
  PREV_FILES+=("$f")
done < <(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null || true)

PREV=${#PREV_FILES[@]}
if [ "$PREV" -le 0 ]; then
  exit 0
fi

SESSION_WORD="session"
[ "$PREV" -gt 1 ] && SESSION_WORD="sessions"

# Build hint line: up to 3 short hashes
HINTS=""
SHOWN=0
for f in "${PREV_FILES[@]}"; do
  [ "$SHOWN" -ge 3 ] && break
  SID=$(basename "$f" .jsonl)
  SHORT="${SID:0:8}"
  HINTS="${HINTS}[${SHORT}] "
  SHOWN=$((SHOWN + 1))
done

MSG="You have ${PREV} previous ${SESSION_WORD} in this project. Use /chats to browse them.
Recent hashes: ${HINTS}
Type /chats <hash> for details and the resume command."

jq -cn --arg msg "$MSG" '{priority: "INFO", message: $msg}'
