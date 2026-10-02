---
name: email-assistant
description: Help manage email — triage messages, draft responses, summarize threads. Use when user says "help with this email", "draft a reply to X", "triage my inbox", or pastes an email for analysis.
user-invocable: true
---

# Email Assistant

Triage emails, draft responses, and summarize threads.

## Default Mode (No API Keys Required)

User pastes email text directly. Claude analyzes and responds.

## Capabilities

### 1. Triage (Categorize)

When user pastes one or more emails:

Categorize each as:
- **Urgent** — Needs response within hours (client escalation, deadline, time-sensitive)
- **Respond** — Needs a thoughtful reply within 1-2 days
- **Delegate** — Someone else should handle this
- **Archive** — No response needed (newsletters, FYI, automated)

Output format:
```
| # | From | Subject | Category | Suggested Action |
|---|------|---------|----------|-----------------|
| 1 | [name] | [subject] | Urgent | [what to do] |
| 2 | [name] | [subject] | Respond | [what to do] |
```

### 2. Draft Response

When user says "reply to this" or "draft a response":

1. Read `context/my-voice.md` for tone
2. Analyze the incoming email (intent, tone, urgency)
3. Draft a response that:
   - Addresses all points raised
   - Matches the user's communication style
   - Is appropriately formal/casual for the relationship
   - Includes clear next steps if applicable

### 3. Summarize Thread

When user pastes a long email thread:

- Extract the key decisions and action items
- Identify who needs to do what
- Note any unresolved questions
- Present as a bullet-point summary

## Upgrade Path (kSuite)

For automated inbox processing (no manual pasting):
- Connect the kSuite mailbox with the `ksuite-setup` skill (IMAP application password,
  or the official Infomaniak Mail MCP server)
- Then read mail with `mcp__ksuite-mail__*` tools or `ksuite-setup/scripts/mail_fetch.py`
- Save replies as drafts in kSuite Mail with `ksuite-setup/scripts/mail_draft.py`
- Use the `email-digest` skill for daily briefings, optionally posted to kChat

## Rules

- Always read `context/my-voice.md` before drafting responses
- Never send emails automatically — always show drafts for approval
- Flag emails that mention money, contracts, or legal matters
- If an email is ambiguous, present two interpretation options to the user
