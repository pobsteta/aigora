---
name: odoo
description: Odoo CRM for leads and opportunities - show the pipeline, find a prospect, create an opportunity from a validated research-lead file, move it to another stage, add an internal note. Use when the user mentions Odoo, CRM, pipeline, opportunité, prospect à suivre, relance, or after a research-lead the user approved.
user-invocable: true
---

# Odoo CRM

Odoo Community (LGPL-3, open source) or Odoo Online, reached through the official external API
by `.claude/skills/odoo/scripts/odoo.py`:
- **JSON-2** (Odoo 19+): `POST /json/2/<model>/<method>`, bearer API key.
- **XML-RPC** fallback for Odoo 18 and older (deprecated since 19, removal planned in Odoo 22):
  needs `ODOO_DB` and `ODOO_LOGIN` too.
`ODOO_API=auto` (default) picks the right one. All output is JSON with `success`.

## Setup (if `ODOO_URL` / `ODOO_API_KEY` are missing)

The user runs `aigora_odoo_configurer()` in the R console (asks URL, database, login and API
key, key masked, then tests). Never ask for the Odoo password; only an API key. Guide:
`docs/ODOO.md`. On Odoo Online, external API access may require a specific plan: if the
API answers 401/403 with a valid key, say so.

## Commands

```bash
O=".claude/skills/odoo/scripts/odoo.py"
python3 $O status                                   # protocol + CRM stages
python3 $O stages
python3 $O pipeline [--stage "Qualifié"] [--limit 50] [--all-types]
python3 $O find --email x@y.ch | --name "Jeanne Martin" --company "Géo-Conseil"
python3 $O create-lead --from-json .tmp/leads/<slug>/combined.json [--stage "Nouveau"] [--tags "AIGORA"]   # preview
python3 $O create-lead ... --confirm                # really creates
python3 $O move --id 42 --stage "Proposition" --confirm
python3 $O note --id 42 --text "Relancé par mail" --confirm
```

## Rules

- Every write (create-lead, move, note) runs first WITHOUT `--confirm`: show the preview,
  get an explicit yes, then rerun with `--confirm`.
- create-lead refuses probable duplicates (same email, or same contact + company). Show the
  existing records; use `--allow-duplicate` only if the user says it is a different deal.
- Opportunities are created with `type=opportunity` (they appear in the pipeline even when the
  "Leads" step is disabled in Odoo). Use `--type lead` only if the user works with leads.
- Never delete records and never change partners, quotes or invoices from AIGORA.
- Personal data stays in Odoo: do not copy prospect details into memory files, logs or kChat.
- After a research-lead the user approved: offer `create-lead --from-json`, which fills contact,
  company, job title, LinkedIn URL, summary, chosen hook, proposed first message and score.
