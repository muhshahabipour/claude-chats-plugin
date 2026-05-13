# claude-chats

A [Claude Code](https://claude.ai/code) plugin that lets you browse and resume previous chat sessions with `/chats`.

## Features

- **`/chats`** — lists all sessions for the current project with short hashes, dates, and titles
- **`/chats <hash>`** — shows session details (title, date, message count, first message preview) and the exact `claude --resume` command
- **SessionStart hook** — notifies you of previous sessions with their short hashes every time you open Claude Code in a project

## Prerequisites

- [jq](https://jqlang.org) — `brew install jq` (macOS) or `apt-get install jq` (Linux)

## Installation

### Via Claude Code plugin marketplace

```
/plugin marketplace add https://github.com/YOUR_USERNAME/claude-chats-plugin
/plugin install claude-chats@YOUR_USERNAME
```

### Manual (local)

```bash
claude --plugin-dir /path/to/claude-chats-plugin
```

Or copy the skill globally:

```bash
mkdir -p ~/.claude/skills/chats
cp skills/chats/SKILL.md ~/.claude/skills/chats/SKILL.md
```

And add the hook to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"/path/to/claude-chats-plugin/hooks/session-start.sh\""
          }
        ]
      }
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
CWD:      /Users/you/Projects/myapp
Messages: 41
Preview:  implement JWT auth with refresh tokens

Resume command:
  claude --resume 5d78b77e-93d6-4596-a355-573f5658856c
```

## How it works

Claude Code stores each conversation as a `.jsonl` file in `~/.claude/projects/{encoded-path}/{sessionId}.jsonl`. This plugin reads those files directly — no external services, no data leaves your machine.

## License

MIT
