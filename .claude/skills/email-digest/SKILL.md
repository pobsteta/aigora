---
name: email-digest
description: Process the kSuite (Infomaniak) inbox to identify high-risk emails, analyze sentiment and urgency, recommend actions, prepare draft replies in kSuite Mail, and optionally post an executive briefing to kChat. Run with /email-digest or ask to process emails.
model: sonnet
context: fork
allowed-tools: Bash(python3 .claude/skills/ksuite-setup/scripts/*)
user-invocable: true
---

# Email Digest (kSuite)

Inbox processing: fetch (script) -> analyze (you) -> brief (kChat or chat) -> drafts (kSuite Mail).

The analysis is done by you, inside the Claude Code session: no OpenAI key, no
email content leaves the machine except to Infomaniak (where it already lives).

## Prerequisites

- `KSUITE_MAIL_USER` and `KSUITE_MAIL_PASSWORD` in `.env` (see `ksuite-setup`).
- Optional: `KCHAT_WEBHOOK_URL` for the kChat briefing.
- If `mcp__ksuite-mail__*` tools are available you may use them instead of step 1.

If nothing is configured, say so in one line and offer either `ksuite-setup` or the
manual `email-assistant` skill (the user pastes emails).

## Step 1: Fetch

```bash
python3 .claude/skills/ksuite-setup/scripts/mail_fetch.py --hours 24 --output .tmp/email-digest/emails.json
```

Options: `--hours N`, `--unread-only`, `--folder INBOX`, `--limit 100`. Read-only.

## Step 2: Analyze (you)

Read `.tmp/email-digest/emails.json`, `context/my-voice.md` and `context/my-business.md`.
For each email produce:

- **category**: urgent / respond / delegate / archive / irate
- **sentiment**: positive / neutral / negative / irate
- **urgency**: high / medium / low
- **summary**: one sentence
- **recommendation**: what to do and why
- **draft**: reply text, only for urgent / respond / irate

Irate client: highest priority, de-escalation draft, recommend a same-day personal
follow-up, note it in today's log. Flag anything about money, contracts or legal
matters. Summarize long threads once instead of message by message.

Write the result to `.tmp/email-digest/analysis.json`.

## Step 3: Briefing

Write `.tmp/email-digest/briefing.md` (Markdown, language from `config/preferences.yaml`):

```
### Synthèse mails, [date]
**🔴 Urgent (2)**
- [Expéditeur], [Objet]: [recommandation]
**🟡 À répondre (5)**
- [Expéditeur], [Objet]: [résumé]
**🟢 Faible priorité (12)**
- [n] archivables, [n] newsletters
```

Show it in the chat. Post it to kChat only if the user confirms (or asked for it
explicitly in a scheduled run):

```bash
python3 .claude/skills/ksuite-setup/scripts/kchat_post.py --file .tmp/email-digest/briefing.md
```

## Step 4: Drafts (optional, after confirmation)

Write `.tmp/email-digest/drafts.json` as a list of
`{"to", "subject", "body", "in_reply_to"}` (use the original `message_id` for
`in_reply_to`, prefix subjects with "Re: "), then:

```bash
python3 .claude/skills/ksuite-setup/scripts/mail_draft.py --from-json .tmp/email-digest/drafts.json
```

Drafts appear in kSuite Mail > Drafts. Nothing is ever sent by AIGORA.

## Automation

Use the `scheduler` skill (Claude Code `/schedule`), for example every weekday
at 7:00: "run /email-digest and post the briefing to kChat".

## Edge cases

- No urgent email: still produce the briefing with counts.
- IMAP login fails: the mailbox needs an application password, not the account password.
- Very large inbox: lower `--hours` or use `--unread-only`.
