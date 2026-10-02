---
name: ksuite-setup
description: Connect and use Infomaniak kSuite (Mail, Calendar, tasks, Contacts, kDrive, kChat, kMeet, Chk, kPaste). Use when the user says "connecte kSuite", "connect my mail / calendar / kDrive / kChat", "Infomaniak", asks to read mail, check the agenda, create a draft, post to kChat, or when another skill needs mail, calendar, files or team chat.
user-invocable: true
---

# kSuite (Infomaniak) connector

kSuite is the default suite of AIGORA (replaces Google Workspace and Slack).
Two complementary layers, both optional and independent:

| Layer | What | Needs | Best for |
|-------|------|-------|----------|
| A. Official Infomaniak MCP servers | `mcp__ksuite-mail__*`, `mcp__ksuite-calendar__*`, `mcp__ksuite-kdrive__*`, `mcp__ksuite-kchat__*`, `mcp__ksuite-contact__*` | Node.js + one API token | Interactive work: search mail, list events, browse kDrive, read kChat, find a contact |
| A'. Community MCP server (opt-in) | `mcp__ksuite-extra__*`: tasks, kMeet rooms, Chk short links, kPaste | `KSUITE_EXTRA_MCP=1`, token + DAV login | What Infomaniak has no official MCP for |
| B. Local Python scripts (this skill) | IMAP/SMTP, CalDAV (events + tasks), CardDAV (contacts), kChat webhook | Mail app password, DAV login, webhook URL | Deterministic pipelines (email-digest, scrum-master), no Node.js |
| C. kDrive desktop folder | Plain files in the folder synced by the kDrive app (`KDRIVE_LOCAL_PATH`) | kDrive desktop app, `link_kdrive.py` | Reading client files, saving deliverables; works on every plan |

Full inventory of Infomaniak tools and status: `docs/KSUITE.md`.

Prefer layer A when its tools are present in your tool list. Fall back to layer B
scripts otherwise. Never ask for the main Infomaniak account password: only
application passwords and API tokens.

## Step 0: Check status (always first)

```bash
python3 .claude/skills/ksuite-setup/scripts/check_status.py
```

If the user wants a real test: add `--test` (tries IMAP, SMTP and CalDAV logins,
sends nothing).

## Fastest setup: let the user run it in R

Recommend first: `aigora_ksuite_configurer()` in the RStudio console. It asks for the CalDAV
short username, the mail address, application passwords (masked, never shown to you) and the
kChat webhook, writes `.env`, installs `caldav` if needed and runs the connection tests.
Use the step-by-step walkthrough below only if the user prefers to edit `.env` by hand.

## Setup walkthrough (one step per message, in French if preferences say so)

Follow `.claude/rules/connections-protocol.md`: one step per message, wait for
"ok", number the steps, never ask for the account password. The user-facing guide
with screenshots-level detail is `docs/KSUITE.md`; quote from it.

1. **.env exists?** If not: copy `.env.example` to `.env` (offer to do it).
2. **Mail (IMAP/SMTP)**: IMAP/SMTP needs a **device password of the mail address**, NOT the
   account application password (that one only works for CalDAV/CardDAV). Path:
   manager.infomaniak.com > Service Mail > domain > address > "Appareils" tab >
   "Ajouter un appareil" (or the assistant at config.infomaniak.com). Login = full address.
   Symptom of the wrong password type: CalDAV/CardDAV OK but IMAP "Invalid login or password".
   They fill `KSUITE_MAIL_USER` (full address) and `KSUITE_MAIL_PASSWORD` in
   `.env` themselves. Do not ask them to paste the password in the chat; if they
   do, write it to `.env` and tell them it is now stored only there.
3. **Calendar (CalDAV)**: username from https://config.infomaniak.com > My Calendar >
   Manual synchronization (short form like `AB12345`). Fill `KSUITE_DAV_USER`,
   `KSUITE_DAV_PASSWORD`. Then `pip install caldav`.
4. **kChat webhook** (optional): kChat > New > Integrations > Incoming Webhooks >
   Add, pick the channel, copy the URL into `KCHAT_WEBHOOK_URL`.
5. **API token for MCP servers** (optional, layer A): https://manager.infomaniak.com/v3/ng/accounts/token/list,
   create a token with scopes `workspace:mail`, `workspace:calendar`, `user_info`,
   `drive`, `kchat` (only the ones wanted). Put it in `INFOMANIAK_TOKEN`. Add
   `KDRIVE_ID` (number in the kDrive URL `.../app/drive/123456/...`) and
   `KCHAT_TEAM_NAME` (`<team>` in `https://<team>.kchat.infomaniak.com`).
   Then:
   ```bash
   python3 .claude/skills/ksuite-setup/scripts/register_mcp.py --dry-run
   python3 .claude/skills/ksuite-setup/scripts/register_mcp.py
   ```
   Tell the user to restart Claude Code in the RStudio Terminal (`/exit`, then `claude`).
6. **kDrive folder** (recommended, every plan): the user installs the kDrive desktop app, then
   `python3 .claude/skills/ksuite-setup/scripts/link_kdrive.py` (auto-detects `~/kDrive`, or `--path`).
   In R: `aigora_kdrive()`. Restart Claude Code.
7. **Community server** (optional): only if the user wants kMeet / Chk / kPaste / tasks via MCP.
   Explain it is a young community project (MIT), filtered to those tools with strict send
   confirmation. Then `KSUITE_EXTRA_MCP=1` in `.env` and `register_mcp.py --only extra`.
8. **Test**: `check_status.py --test` (IMAP, SMTP, CalDAV, CardDAV), and with MCP: call `calendar_list_calendars`.
9. Update `config/preferences.yaml`: `email: ksuite`, `calendar: ksuite`, `chat: kchat`, `files: kdrive`, and `task_manager: ksuite` if the user wants tasks on the phone.

## Everyday commands (layer B)

```bash
# Mail: read (read-only, does not mark as read)
python3 .claude/skills/ksuite-setup/scripts/mail_fetch.py --hours 24 [--unread-only] [--output .tmp/x.json]

# Mail: create drafts (NEVER sends; the user sends from kSuite Mail)
python3 .claude/skills/ksuite-setup/scripts/mail_draft.py --to a@b.ch --subject "..." --body-file .tmp/draft.txt [--in-reply-to "<message-id>"]
python3 .claude/skills/ksuite-setup/scripts/mail_draft.py --from-json .tmp/drafts.json

# Calendar
python3 .claude/skills/ksuite-setup/scripts/calendar_events.py calendars
python3 .claude/skills/ksuite-setup/scripts/calendar_events.py list --days 7
python3 .claude/skills/ksuite-setup/scripts/calendar_events.py create --summary "..." --start "2026-10-06 14:00" --end "2026-10-06 15:00" [--calendar "..."]

# Tasks (CalDAV VTODO, synced to the phone by kSync / iOS Reminders)
python3 .claude/skills/ksuite-setup/scripts/calendar_events.py tasks [--all]
python3 .claude/skills/ksuite-setup/scripts/calendar_events.py task-add --summary "..." [--due 2026-10-09] [--priority high]
python3 .claude/skills/ksuite-setup/scripts/calendar_events.py task-done --uid <uid>

# Contacts (CardDAV, read-only)
python3 .claude/skills/ksuite-setup/scripts/contacts.py search "dupont"
python3 .claude/skills/ksuite-setup/scripts/contacts.py export --output data/contacts.csv

# kDrive local folder
python3 .claude/skills/ksuite-setup/scripts/link_kdrive.py [--path "..."] [--unlink]

# kChat (posts to other people: confirm with the user first)
python3 .claude/skills/ksuite-setup/scripts/kchat_post.py --file .tmp/briefing.md
```

All scripts print JSON with a `success` key.

## Rules

- Drafts, never direct sending. The scripts have no send command on purpose.
- Confirm before: posting to kChat, creating or deleting calendar events, moving or
  deleting mail or kDrive files through MCP tools (`confirm_before_sending: true`).
- kDrive WebDAV is not available on kSuite Free/Standard plans and is unsupported by Infomaniak:
  use the synced folder (layer C) or the kDrive MCP server.
- Mail sending through MCP is denied in `.claude/settings.json` (`mail_send_email`). Keep it that way
  unless the user explicitly removes the rule.
- SwissTransfer cannot be automated reliably (anti-bot captcha): prepare the file in kDrive and let the
  user send it from swisstransfer.com or the app.
- Secrets live only in `.env` and in Claude Code's local MCP config. Never echo them.
