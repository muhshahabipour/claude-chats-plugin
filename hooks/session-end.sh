#!/usr/bin/env bash
# Fires on Stop event. Auto-exports the current session to CLAUDE_HANDOFF.md
# only when it looks like a real conversation (has title + enough messages).

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-}"
[ -z "$PROJECT_DIR" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0

ENCODED=$(printf '%s' "$PROJECT_DIR" | sed 's|/|-|g')
SESSIONS_DIR="$HOME/.claude/projects/$ENCODED"
[ ! -d "$SESSIONS_DIR" ] && exit 0

SESSION_FILE=$(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null | head -1 || true)
[ -z "$SESSION_FILE" ] && exit 0

# Skip ephemeral sessions: require an ai-title AND at least 5 user messages
HAS_TITLE=$(grep -c '"type":"ai-title"' "$SESSION_FILE" 2>/dev/null || echo 0)
USER_MSG_COUNT=$(grep -c '"type":"user"' "$SESSION_FILE" 2>/dev/null || echo 0)

if [ "$HAS_TITLE" -lt 1 ] || [ "$USER_MSG_COUNT" -lt 5 ]; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/../scripts/export-session.py" \
  "$SESSION_FILE" \
  "$PROJECT_DIR/CLAUDE_HANDOFF.md" 2>/dev/null || true
