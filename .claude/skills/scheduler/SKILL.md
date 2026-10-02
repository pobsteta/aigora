---
name: scheduler
description: Set reminders and recurring tasks locally. Use when the user says "remind me", "schedule", "set a reminder", "run this every day/week", or wants something to happen later. On the Local Edition there is no server cron; scheduling uses Claude Code's native scheduling and the task-manager skill.
---

# Skill: Scheduler (Local Edition)

> Reminders and recurring actions on your own machine. No server, no cron daemon.

AIGORA runs on the user's machine (RStudio + Claude Code). There is no server cron. Use the tools that run locally. To notify the user or a team, post to kChat (`ksuite-setup/scripts/kchat_post.py`) or create a kSuite Calendar event with a reminder.

## How to schedule things locally

### 1. Recurring or timed Claude actions -> Claude Code native scheduling
Claude Code can run a prompt or slash command on a schedule or interval, directly on the user's machine, while Claude Code is available.

- **Recurring agent (cron-style):** use the `/schedule` capability to create a routine that runs on a cron schedule (e.g. "every weekday at 9am, give me a stand-up").
- **Repeat on an interval / poll:** use the `/loop` capability (e.g. "every 30 minutes, check X").

When the user asks to "schedule" or "automate at" a time, propose one of these and set it up with them. Confirm the exact time, timezone (`config/preferences.yaml`), and what should happen.

### 2. Plain reminders and due dates -> task-manager
For "remind me to do X on Friday", the simplest durable option is a task with a due date in the `task-manager` skill. It persists in SQLite and shows up when the user asks "what's on my plate".

```bash
python3 .claude/skills/task-manager/scripts/task_db.py add --title "Follow up with Acme" --due 2026-06-06
```

## Choosing between them

| User intent | Use |
|-------------|-----|
| "Run a stand-up every morning" | `/schedule` (recurring routine) |
| "Check the deploy every 5 minutes" | `/loop` |
| "Remind me to call the bank Friday" | `task-manager` task with a due date |
| "One-off: ping me at 3pm today" | `/schedule` one-time run, or a dated task |

## Notes
- Native scheduling runs while the user's Claude Code is available. It is not a 24/7 server. For always-on automation, the user would deploy separately (out of scope for the Local Edition).
