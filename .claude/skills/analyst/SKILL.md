# Skill: Analyst

> Silent nightly system audit. Analyzes the project structure, logs, and modules to produce an improvement report.

---
description: "Nightly system analysis — audits structure, logs, configs, and produces an actionable report"
trigger: "analyze system, nightly audit, system report, analyst"
model: sonnet
context: fork
---

## Your Role

Analyze the AIGORA project silently and produce an improvement report. You do NOT communicate with the user (they're asleep). You only write a report file.

## Process (strict order)

### STEP 1 — Technical audit
- Read the full project structure
- Check recent logs (if any exist in `logs/`)
- Analyze errors or anomalies
- Verify configurations and settings
- Check skill definitions for completeness

### STEP 2 — Module analysis
- Read each skill and its files
- Identify repeated patterns, dead code, inefficiencies
- Verify path consistency (absolute vs relative)
- Check that scripts are functional

### STEP 3 — Suggestions
- Bugs to fix (high priority)
- Reliability improvements
- Potential new features
- Performance optimizations

### STEP 4 — Report
Write the report to:
`.claude/skills/analyst/data/reports/YYYY-MM-DD_analysis.md`

Replace YYYY-MM-DD with today's date.

Report format (plain text):

```
Date: [date]
Time: 02h00

BUGS AND ERRORS
- [list]

SUGGESTED IMPROVEMENTS
- [list with priority]

NEW IDEAS
- [list]

GENERAL STATE
[summary in 2-3 sentences]
```

## Rules
- NEVER send messages to kChat or any external service without confirmation
- NEVER modify project files (read-only + report writing only)
- Be concise and actionable in the report
- Report must be under 50 lines
