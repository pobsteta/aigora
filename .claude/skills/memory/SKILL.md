---
name: memory
description: Query and manage the AIGORA long-term memory (mem0 + local Qdrant + Ollama, optional) and the daily logs. Layer 1 is owned by Claude Code natively.
---

# Memory Skill

Operates on layers 2 and 3 of the AIGORA memory stack. Layer 1 (native auto-memory) is managed by Claude Code itself; see `.claude/rules/memory-protocol.md` for the full architecture.

## When to use this skill

- The user references something from a past session that is not in the native auto-memory topic files → search layer 3.
- The user asks "what have you got on me?" or wants an export → list layer 3.
- You want to manually add a fact you judge important enough → add to layer 3.
- You want to append a chronological event to today's log → write to layer 2.
- A skill (weekly-review, meeting-prep, business-setup) needs to persist project facts → use the Write tool against layer 1 topic files directly. Do NOT use this skill for layer 1 writes.

## Layer 3 operations (mem0 + Qdrant, optional)

### Search (recommended: smart_search)
```bash
python3 .claude/skills/memory/scripts/smart_search.py --query "topic" --limit 5
```
Hybrid retrieval: BM25 keyword (30%) + vector similarity (70%) + temporal decay + MMR diversity. First run on a fresh install requires `--rebuild-index` to populate the FTS5 keyword index.

### Search (basic vector only)
```bash
python3 .claude/skills/memory/scripts/mem0_search.py --query "topic" --limit 10
```

### Rebuild keyword index
```bash
python3 .claude/skills/memory/scripts/smart_search.py --rebuild-index
```
Repopulates FTS5 from the history DB. Run after installation or to fix drift.

### Add a fact manually
```bash
python3 .claude/skills/memory/scripts/mem0_add.py --content "User prefers kSuite over Google Workspace"
```

### Add from conversation messages
```bash
python3 .claude/skills/memory/scripts/mem0_add.py --messages '[{"role":"user","content":"I switched to ClickUp"}]'
```

### List all memories
```bash
python3 .claude/skills/memory/scripts/mem0_list.py --limit 50
```

### Delete a memory
```bash
python3 .claude/skills/memory/scripts/mem0_delete.py --memory-id "abc123"
python3 .claude/skills/memory/scripts/mem0_delete.py --all --confirm
```

## Layer 2 operation (daily logs)

### Append to today's session log
```bash
python3 .claude/skills/memory/scripts/daily_log.py --content "Completed memory system overhaul" --type event
```

## Auto-capture (background, no action needed)

Stop hook `auto_capture.py` runs after every response cycle. It reads new transcript messages, feeds them to mem0 for fact extraction and dedup against the vector store, and appends a session summary to today's daily log. Logs at `data/auto_capture.log`.

## Config

- mem0 config: `.claude/skills/memory/references/mem0_config.yaml`
- Default (100% local, open source): LLM `qwen3:4b` and embeddings `nomic-embed-text` served by
  **Ollama** on this computer; vectors in **Qdrant embedded mode** (`data/qdrant/`, no server).
- Alternative LLM: Infomaniak AI Tools (OpenAI-compatible, open-source models hosted in Switzerland),
  see the commented block at the bottom of the config.
- History DB: `data/mem0_history.db` (SQLite, auto-managed)
- Capture markers: `data/capture_markers/` (tracks transcript position per session)

## Security

- `sanitize_text()` in `mem0_client.py` strips secrets (API keys, tokens, JWTs, connection strings) before any processing.
- With the default local stack, **nothing leaves the computer**: extraction, embeddings and storage are local.
- If you switch the LLM to Infomaniak AI Tools, conversation snippets are sent to Infomaniak (Switzerland).
- Local files (SQLite history DB, Qdrant folder, daily logs) are plaintext on disk; `.gitignore` excludes them.

## Known issues

1. Small local models can occasionally return invalid JSON on heavy markdown. `prepare_messages()` strips most of it;
   failed batches are skipped, the transcript is preserved. A larger model (`qwen3:8b`) is more reliable if the machine allows.
2. First run on a long conversation is slow on CPU. Incremental runs (2-4 messages) are fast.
3. Layer 3 is off by default. Layers 1 and 2 (native memory + daily logs) always work with no install.
