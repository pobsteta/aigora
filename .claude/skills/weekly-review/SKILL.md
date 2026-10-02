---
name: weekly-review
description: Structured weekly business review and planning session. Use when user says "weekly review", "let's do a review", "what happened this week", or at the start of a new week.
user-invocable: true
---

# Weekly Review

Structured review of the past week and planning for the next.

## Process

### Step 1: Gather Data

Read the past 7 days of daily logs from `memory/logs/`:
- Today's log and the 6 preceding days
- If logs don't exist for some days, note which days are missing

Read current goals and priorities from Claude Code's native auto-memory: open the `goals.md` topic file in Claude Code's native project memory folder (or whatever topic file holds them, check `MEMORY.md` index) with the Read tool. If goals haven't been captured yet, ask the user for them and write them to `goals.md`.

Optionally run `scripts/weekly_metrics.py` to parse log files for patterns.

### Step 2: Review Format

Present the review in this structure:

```markdown
## Weekly Review: [Week of Mon DD - Sun DD]

### What Happened This Week
- [Key events, meetings, decisions from logs]
- [Notable accomplishments]
- [Unexpected issues or changes]

### What Got Done
- [Completed tasks and deliverables]
- [Progress on goals from `goals.md` topic file]

### What Didn't Get Done
- [Tasks that slipped]
- [Why they slipped (if apparent from logs)]

### Patterns & Insights
- [Recurring themes across the week]
- [Time spent on different categories]
- [Energy observations — what drained, what energized]

### Next Week's Plan
- **Priority 1:** [Most important thing]
- **Priority 2:** [Second most important]
- **Priority 3:** [Third most important]
- **Carry-over:** [Tasks from this week that roll forward]

### Goals Check
- [Progress against 90-day goals from `goals.md` topic file]
- [Any goal adjustments needed?]
```

### Step 3: Update Memory

After the review:
1. Update the `goals.md` topic file in Claude Code's native project memory folder with new priorities if they've changed (Write tool). If the topic file doesn't exist yet, create it and add a pointer line to `MEMORY.md`.
2. Create next Monday's daily log template with the priorities
3. Ask user if any goals need adjustment

## Script

`scripts/weekly_metrics.py` — Parses daily logs and extracts:
- Number of events per day
- Common themes/keywords
- Tasks mentioned as completed

## Rules

- Be honest about what didn't get done — don't spin it
- If logs are sparse, note this and suggest better logging habits
- Keep the review concise — scannable in 5 minutes
- The planning section is the most important output — make it actionable
