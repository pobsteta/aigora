# Connections Protocol (AIGORA, RStudio Local Edition)

How AIGORA connects external services when running locally in Claude Code inside RStudio.

## Preference order for services (user's choice, always respect it)

1. **kSuite (Infomaniak)** for mail, calendar, contacts, files (kDrive) and team chat (kChat).
2. **Open-source software** (self-hosted or hosted in Europe) for everything else:
   see `docs/CONNECTEURS-OPEN-SOURCE.md` for the mapping (Odoo CRM, SearXNG,
   Vikunja, Ollama, Qdrant, Quarto, Nextcloud, Mattermost, etc.).
3. Proprietary US services (Google Workspace, Slack, Notion, Airtable, Todoist,
   OpenAI, Pinecone, Perplexity, Gamma...) **only if the user explicitly asks** for them.
   Never propose them by default.

When a user says *"I want to connect X"*, *"can you access my X"*, or asks you to act on
a service you can't currently reach, follow the tiers below. **Never skip ahead.**
Never ask for a main account password.

Order: **Tier 0 -> Tier 1 -> Tier 2 -> Tier 3.**

---

## Tier 0: Is it already configured? (check FIRST)

- For kSuite: run `python3 .claude/skills/ksuite-setup/scripts/check_status.py`.
- Look for a setup skill under `.claude/skills/<service>-setup/`.
- Check `.env` for the service's keys (names only, never print values).
- Check your tool list for MCP tools of the service (`mcp__ksuite-mail__*`,
  `mcp__ksuite-calendar__*`, `mcp__ksuite-kdrive__*`, `mcp__ksuite-kchat__*`, `mcp__searxng__*`...).

If Tier 0 applies (even if broken: expired token, wrong password), use the skill's own
recovery flow.

---

## Tier 1: Official MCP server of the vendor

Infomaniak publishes official, MIT-licensed MCP servers for Mail, Calendar, kDrive, kChat
and Contacts (`@infomaniak/mcp-server-*`). For kMeet, Chk, kPaste and CalDAV tasks there is
only a community server (`@henrikogard/infomaniak-mcp`, opt-in `KSUITE_EXTRA_MCP=1`, filtered
to those tools, strict confirmation of external sends). They are registered from `.env` with
`ksuite-setup/scripts/register_mcp.py` (scope `local`: stored in the user's Claude Code
config for this project only, never in a committed file). Many open-source apps also
ship an official MCP server (Qdrant...) or a documented API (Odoo JSON-2).

If the MCP tools are present, use them. If they were just registered, the user must
restart Claude Code in the RStudio Terminal (`/exit`, then `claude`).

---

## Tier 2: Preinstalled setup skill

`ksuite-setup` covers Infomaniak (Mail via IMAP/SMTP, Calendar via CalDAV, kChat webhook,
MCP registration). Hand off to it and follow its `SKILL.md` step by step. Test at the end.

---

## Tier 3: Improvised guidance (last resort)

1. State the situation honestly and ask to proceed.
2. Identify the connection method, preferring open standards:
   IMAP/SMTP, CalDAV/CardDAV, WebDAV, a REST API with a token, or an MCP server.
   - REST API with a token -> the user puts the token in `.env`; you write a thin script
     inside the relevant skill's `scripts/` (standard library first).
   - Third-party MCP server -> check licence, maintenance and permissions first, then
     `claude mcp add-json --scope local <name> '{"type":"stdio","command":"npx","args":["-y","<package>"],"env":{"KEY":"value"}}'`
     (on Windows: `"command":"cmd","args":["/c","npx","-y","<package>"]`). Avoid `claude mcp add --env ...`:
     the variadic `--env` option can swallow the server name.
3. Walk **one step per message**. Confirm before continuing. Give direct links.
4. At the end, offer to formalize it as a `<service>-setup` skill via `skill-creator`.

### Anti-patterns (never do these)
- Asking for a main account **password** (only application passwords and API tokens).
- Hardcoding credentials anywhere outside `.env` or Claude Code's local MCP config.
- Writing tokens into `.mcp.json` (it is meant to be shared/committed).
- Claiming a service "has no API" without checking.
- Suggesting browser automation before exhausting API / open-protocol options.
- Steering the user towards a proprietary service when a kSuite or open-source option exists.

---

## Style for the walkthrough (tiers 2 and 3)

- One step per message, numbered ("Étape 3/7 ..."), in the user's language.
- Direct clickable links over long explanations.
- Confirm ("ok" / "c'est fait") before moving on.
- Test the connection for real before declaring success.
