# AIGORA (Local Edition) — Architecture & Design

> Give this document plus the project folder to any AI or human. They will understand the full system, why it is built this way, and how to extend it.

---

## What This Is

The AIGORA is a Claude Code workspace structured like an operating system. It turns a folder on your machine into a persistent, intelligent business assistant that:

- Knows your business (context files filled by a setup wizard)
- Writes in your voice (voice guide captured during setup)
- Runs structured workflows (skills, from research to slide generation)
- Remembers across sessions (file-based memory)
- Enforces safety rules (hooks that block dangerous actions)
- Delegates to specialists (3 custom agents with restricted permissions)
- Grows with you (create new skills for any repeatable workflow)

The Local Edition runs entirely on your computer through Claude Code. There is no server, no webapp, no VPS, no always-on bot. It requires only a Claude Code subscription. The core skills need no other API keys.

---

## The Core Idea: Separation of Concerns

AI reasoning handles the WHAT (decisions, analysis, creative judgment). Deterministic scripts handle the HOW (API calls, data processing, file operations).

```
All-advisory approach (AI does every step):
  90% × 90% × 90% × 90% × 90% = 59% reliable over 5 steps

Separation of concerns (AIGORA approach):
  AI decides WHAT (90%) -> Scripts execute HOW (99.9%) = consistent results
```

That is why a multi-step pipeline produces consistent results instead of probabilistic guessing.

---

## The OS Analogy

| OS concept | AIGORA equivalent | What it does |
|------------|-----------------|-------------|
| **Kernel** | CLAUDE.md + .claude/rules/ | System instructions. How the AI thinks and operates. |
| **Programs** | .claude/skills/ | Self-contained workflows. Auto-discovered by description matching. |
| **Security** | .claude/hooks/ | Lifecycle hooks. Block dangerous commands, keep the daily log, validate output. |
| **Workers** | .claude/agents/ | Specialized subprocesses with restricted tools and cheaper models. |
| **Filesystem** | context/ | Domain knowledge: business details, voice guide, ICP. |
| **Config** | config/*.yaml | Runtime behavior settings. Change behavior without editing skills. |
| **Memory** | memory/ | Persistence across sessions: native memory + daily logs. |
| **Databases** | data/*.db | SQLite for structured data (tasks, tracking). |
| **Drivers** | MCP servers | Optional external service access (kSuite Mail/Calendar/kDrive/kChat, open-source apps). |
| **Package Mgr** | plugin.json | Bundle and distribute skills + hooks + agents. |

---

## File Structure

```
aigora/
├── AIGORA.Rproj             # RStudio project (open this)
├── .Rprofile              # Loads R/aigora.R helpers on project open
├── R/aigora.R               # R helpers: aigora_verifier(), aigora_demarrer(), aigora_ksuite()...
├── CLAUDE.md              # KERNEL — system instructions
├── README.md             # Public quickstart
├── LICENSE               # MIT
├── plugin.json           # Plugin manifest for distribution
├── .env.example          # Optional API key template (core needs none)
├── .gitignore
│
├── .claude/
│   ├── settings.json                 # Permissions + 3 hooks
│   ├── settings.local.json.example   # Local override template
│   │
│   ├── rules/                        # MODULAR RULES (part of the kernel)
│   │   ├── guardrails.md             # Safety rules
│   │   ├── output-style.md           # Em-dash ban + formatting
│   │   ├── bash-wait-patterns.md     # How to wait on background jobs
│   │   ├── connections-protocol.md   # How to connect external services
│   │   └── memory-protocol.md        # Memory management rules
│   │
│   ├── skills/                       # PROGRAMS — self-contained workflows
│   │   ├── business-setup/           # Setup wizard
│   │   ├── research/                 # Deep research (WebSearch, no keys)
│   │   ├── content-writer/           # Write in the user's voice
│   │   ├── meeting-prep/             # Research + talking points
│   │   ├── email-assistant/          # Paste-based email triage + drafts
│   │   ├── weekly-review/            # Structured weekly review
│   │   ├── task-manager/             # SQLite task tracking
│   │   ├── scrum-master/             # Stand-ups, planning
│   │   ├── analyst/                  # System audit + reporting
│   │   ├── skill-creator/            # Meta-skill: create new skills
│   │   ├── plugin-builder/           # Package skills into plugins
│   │   ├── build-website/            # PRISM framework -> static sites
│   │   ├── build-app/                # ATLAS framework -> full-stack apps
│   │   │
│   │   │  # Power skills (optional API keys)
│   │   ├── research-lead/            # LinkedIn -> research + outreach
│   │   ├── content-pipeline/         # YouTube -> LinkedIn posts + carousels
│   │   ├── email-digest/             # kSuite Mail -> analysis -> kChat briefing + drafts
│   │   ├── ksuite-setup/             # Infomaniak kSuite connector (IMAP, CalDAV, kChat, MCP)
│   │   ├── quarto-slides/            # Quarto -> reveal.js / pptx / pdf decks
│   │   ├── memory/                   # Optional mem0 semantic memory (local Ollama + Qdrant)
│   │   └── scheduler/                # Local reminder helpers
│   │
│   ├── hooks/                        # LIFECYCLE HOOKS (plain Python, no keys)
│   │   ├── guardrail_check.py        # PreToolUse: block dangerous commands
│   │   ├── memory_capture.py         # Stop: keep the daily log present
│   │   └── validate_output.py        # PostToolUse: validate JSON output
│   │
│   └── agents/                       # WORKERS — 3 subagents
│       ├── researcher.md             # Sonnet, read-only
│       ├── content-writer.md         # Sonnet, Read + Write + Glob
│       └── code-reviewer.md          # Opus, read-only
│
├── context/                         # FILESYSTEM — domain knowledge
│   ├── my-business.md               # Filled by the setup wizard
│   └── my-voice.md                  # Filled by the setup wizard
│
├── config/
│   └── preferences.yaml             # Timezone, language, model routing, defaults
│
├── memory/
│   ├── MEMORY.md                    # Curated facts, always loaded
│   └── logs/                        # Daily session logs
│
├── data/                            # SQLite + JSON runtime storage
└── docs/                            # ARCHITECTURE, SETUP, SKILLS-GUIDE, MCP-SERVERS, MEMORY-UPGRADE
```

---

## Key Design Decisions

### 1. Skills are self-contained packages

```
.claude/skills/email-digest/
├── SKILL.md          # What to do
├── scripts/          # How to do it (deterministic)
├── references/       # Supporting docs
└── assets/           # Templates, fonts
```

Each skill is portable and discoverable (Claude matches its description automatically) and can specify its own model, isolation, and tool restrictions via frontmatter.

### 2. CLAUDE.md is the lean kernel

The kernel is instructions, not philosophy. Detailed rules live in `.claude/rules/*.md` (loaded automatically). Detailed skill instructions live in each `SKILL.md` (loaded on demand, not every session).

### 3. Zero API keys for the core

The starter skills work with only a Claude Code subscription:
- `research` uses WebSearch (built into Claude Code)
- `email-assistant` works by paste (the user pastes the email text)
- `task-manager` uses SQLite (Python standard library)
- `content-writer` uses Claude's reasoning (no external calls)
- memory uses MEMORY.md + daily logs (plain files)

Power skills unlock with optional keys. Onboarding friction stays at zero.

### 4. Memory is file-based by default

```
Native memory  -> Claude Code's own project memory, loaded each session.
Daily logs      -> memory/logs/*.md, append-only, read at session start.
Vectors         -> OPTIONAL mem0 + local Qdrant via the memory skill (no key).
```

The default needs no keys and no cloud. The optional vector layer is documented in `docs/MEMORY-UPGRADE.md`.

### 5. Hooks for safety, deterministically

- **PreToolUse / guardrail_check** — blocks `rm -rf`, force-push, `DROP TABLE`, self-deadlocking `pgrep` loops. Exit code 2 = blocked.
- **Stop / memory_capture** — async, keeps today's daily log present.
- **PostToolUse / validate_output** — validates JSON output from scripts.

Claude can be talked into ignoring a CLAUDE.md rule. It cannot bypass a hook that returns exit code 2.

### 6. Agents are restricted specialists

| Agent | Model | Tools | Why |
|-------|-------|-------|-----|
| researcher | Sonnet | Read, Glob, Grep, WebSearch | Faster model for research, cannot modify files |
| content-writer | Sonnet | Read, Write, Glob | Writes content, cannot execute code |
| code-reviewer | Opus | Read, Grep, Glob | Best reasoning for review, cannot modify anything |

### 7. Model routing for speed and quota

```yaml
model: haiku    # Simple tasks: formatting, classification
model: sonnet   # Most pipelines: research, content, email
model: opus     # Complex reasoning: architecture, creative work
```

Cost is flat (your subscription). Routing is about speed and staying under usage caps, not API spend.

### 8. Python scripts over MCP for frequent operations

MCP servers add token overhead to context. For operations that always follow the same pattern (a pipeline step), a Python script calling the API directly is leaner. Use MCP when Claude needs to reason about WHAT to query; use scripts when the query is always the same.

---

## How It Works (End to End)

### First run

1. Open AIGORA.Rproj in RStudio, run aigora_demarrer() (or `claude` in the Terminal tab).
2. CLAUDE.md loads as the system prompt.
3. If `context/my-business.md` is still a placeholder, Claude offers the `business-setup` wizard.
4. The wizard asks a short questionnaire and writes `context/my-business.md` and `context/my-voice.md`, and updates `config/preferences.yaml`.

### Normal session

1. Claude loads CLAUDE.md + .claude/rules/ + MEMORY.md, then today's and yesterday's logs.
2. The user asks for something: "Write a LinkedIn post about AI automation".
3. Claude matches it to the `content-writer` skill, reads the voice guide, and writes in the user's voice.
4. The Stop hook keeps the daily log current.

---

## How to Extend

- **Add a skill:** *"Create a skill for [workflow]"* (uses `skill-creator`), or `python3 .claude/skills/skill-creator/scripts/init_skill.py my-skill`.
- **Add context files:** drop markdown in `context/` (e.g. `my-icp.md`, `competitors.md`). Skills reference them when relevant.
- **Add MCP servers:** see `docs/MCP-SERVERS.md`.
- **Upgrade memory:** see `docs/MEMORY-UPGRADE.md`.
- **Add hooks:** edit `.claude/settings.json`. Always use `"$CLAUDE_PROJECT_DIR"` in hook commands so they survive a working-directory change:
  ```json
  "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/your_hook.py"
  ```

---

## Cost Summary

| Component | Cost |
|-----------|------|
| Claude Code subscription | $20-200/month |
| Core skills | $0 additional |
| Power skills (API keys) | Varies by usage |
| Optional mem0 memory (local Ollama + Qdrant) | $0 |
| **Minimum viable AIGORA** | **$20/month** (Claude Pro) |
