# claude-chats

A [Claude Code](https://claude.ai/code) plugin that lets you browse, inspect, and export previous chat sessions — with built-in Cursor and Codex handoff support.

## Features

- **`/chats`** — lists all sessions for the current project with short hashes, dates, and titles
- **`/chats <hash>`** — shows session details (title, date, message count, first message preview) and the exact `claude --resume` command
- **`/chats export <hash>`** — exports a session to `CLAUDE_HANDOFF.md` so Cursor or Codex can continue it
- **`/chats export`** — exports the most recent session
- **SessionStart hook** — notifies you of previous sessions with their short hashes every time you open Claude Code
- **Stop hook** — auto-exports the current session to `CLAUDE_HANDOFF.md` after each response (skips ephemeral sessions)

## Prerequisites

- [jq](https://jqlang.org) — `brew install jq` (macOS) or `apt-get install jq` (Linux)
- `python3` — pre-installed on macOS

## Installation

### Via Claude Code plugin marketplace

```
/plugin marketplace add https://github.com/muhshahabipour/claude-chats-plugin
/plugin install claude-chats@muhshahabipour
```

### Manual (local)

```bash
claude --plugin-dir /path/to/claude-chats-plugin
```

Or install globally:

```bash
# Install the skill
mkdir -p ~/.claude/skills/chats
cp skills/chats/SKILL.md ~/.claude/skills/chats/SKILL.md

# Register hooks in ~/.claude/settings.json
# (add the SessionStart and Stop entries shown below)
```

`~/.claude/settings.json` hooks section:

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [{ "type": "command", "command": "bash \"/path/to/claude-chats-plugin/hooks/session-start.sh\"" }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "bash \"/path/to/claude-chats-plugin/hooks/session-end.sh\"" }] }
    ]
  }
}
```

## Usage

```
/chats
```
```
HASH        DATE          TITLE
----------  ------------  ----------------------------------------
[5d78b77e]  2026-05-12    Build authentication flow
[9936b28e]  2026-05-10    Refactor database layer
```

```
/chats 5d78b77e
```
```
Session:  5d78b77e-93d6-4596-a355-573f5658856c
Title:    Build authentication flow
Date:     2026-05-12
Messages: 41
Preview:  implement JWT auth with refresh tokens

Resume:  claude --resume 5d78b77e-93d6-4596-a355-573f5658856c
Export:  /chats export 5d78b77e
```

```
/chats export 5d78b77e
```
Creates `CLAUDE_HANDOFF.md` in the project root. Then in Cursor or Codex:
- **Cursor**: type `@CLAUDE_HANDOFF.md` in the chat panel
- **Codex**: run `codex --context CLAUDE_HANDOFF.md`

## How it works

Claude Code stores each conversation as a `.jsonl` file in `~/.claude/projects/{encoded-path}/{sessionId}.jsonl`. This plugin reads those files directly — no external services, no data leaves your machine.

The export converts the raw JSONL into clean markdown with user/assistant turns, tool call summaries, and instructions for Cursor and Codex at the top.

## Notes

- `CLAUDE_HANDOFF.md` is auto-generated — add it to your `.gitignore`
- The Stop hook only exports sessions with 5+ user messages and an auto-generated title, so quick command sessions don't overwrite your handoff file

## License

MIT
