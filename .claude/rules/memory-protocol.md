# Memory Protocol (Local Edition)

How the AIGORA remembers things across sessions, all on the local filesystem. No cloud and no API keys by default.

## Two layers (default)

```
LAYER 1: Native auto-memory (Claude Code, project-scoped)
  Location: ~/.claude/projects/<project>/memory/
  Loaded automatically every session by Claude Code.
  Owner: Claude. Write here freely when you learn something worth keeping
  across sessions (user identity, conventions, decisions, preferences).

LAYER 2: Daily logs + curated index (this repo)
  Location: memory/logs/YYYY-MM-DD.md  and  memory/MEMORY.md
  memory/MEMORY.md is the curated, always-relevant index of facts, goals,
  and preferences. The daily logs are the chronological narrative.
  Owner: Claude during the session + the Stop hook (keeps today's log present).
```

## How each layer is used

**Layer 1 (native auto-memory):** stable project-level facts. User identity, system conventions, technical decisions. Claude reads this automatically at session start and writes to it when something is worth remembering long term.

**Layer 2 (daily logs + MEMORY.md):** day-by-day narrative plus a curated index. Append notable events, decisions, completions, and bugs to today's log as you work. Keep `memory/MEMORY.md` tight (curated facts, not a dump).

## At session start

1. Claude Code natively loads Layer 1.
2. Read `memory/MEMORY.md` for curated facts and preferences.
3. Read today's log `memory/logs/YYYY-MM-DD.md` (create it if missing) and yesterday's log for continuity.

## During the session

- Append notable events to today's daily log.
- When you learn a durable fact (a preference, a decision, a convention), write it to Layer 1 and, if it should always be in view, add a short line to `memory/MEMORY.md`.
- Do not store secrets (API keys, tokens) in any memory file. Secrets live only in `.env`.

## What goes where

| Content | Where |
|---------|-------|
| Stable user / system facts, conventions, decisions | Layer 1 native memory |
| Today's chronological narrative | `memory/logs/YYYY-MM-DD.md` |
| Curated always-relevant facts and goals | `memory/MEMORY.md` |
| API keys, secrets | `.env` only. Never in memory. |
| Code structure, file paths | Read from the codebase directly |

## Optional Layer 3 (power users only)

A semantic memory layer (mem0, local Ollama + Qdrant) is available through the `memory`
skill for users who want vector search and automatic fact extraction across
years of history. It is **off by default** and requires a one-time local install
(Ollama, Qdrant client), no API key. It is not needed for normal use. See
`docs/MEMORY-UPGRADE.md` and the `memory` skill for setup and the manual
commands (`smart_search.py`, `mem0_add.py`, `mem0_list.py`).

When Layer 3 is not configured (the default), simply rely on Layers 1 and 2.
