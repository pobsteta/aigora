---
name: research-lead
description: Turn a lead (LinkedIn URL, name + company, or pasted profile) into a research package with relevant personalization and an outreach sequence, reviewed by a human before anything is sent. Run with /research-lead or ask to research a lead.
model: sonnet
context: fork
allowed-tools: Bash(python3 .claude/skills/research-lead/scripts/*), Bash(python3 .claude/skills/ksuite-setup/scripts/*)
user-invocable: true
---

# Lead Research & Personalization (AIGORA)

## What changed from the original template

The original pipeline chained five paid services (Relevance AI scraping through a
workflow owned by the template author, Perplexity, OpenAI, Airtable, Google Sheets,
Slack). In AIGORA the reasoning is done by you inside Claude Code, research uses
WebSearch/WebFetch (or a self-hosted SearXNG MCP), storage is a local CSV, and the
review card goes to kChat. Zero extra API key. The expert prompts were kept in
`assets/prompts/` and are your instructions for each analysis.

## Objective

Produce a research package with **relevant personalization only**.
Relevant = relates to a problem they're likely facing that we can solve.
Theater = personal but irrelevant (marathons, shared schools, hobbies).
Test for every fact: "Does this relate to a problem they're facing that we can solve?" If no, discard it.

## Inputs

- A LinkedIn URL, or name + company, or profile text pasted by the user.
- `context/my-business.md` (replace `{COMPANY_NAME}` and the offer in the prompts with it).

LinkedIn pages usually block automated reading. Do not scrape LinkedIn. Use public
sources (company site, press, public posts found by WebSearch) and ask the user to
paste the profile text (About, Experience, recent posts) when needed.

## Steps

1. **Profile**: build `profile_data` = `{full_name, first_name, company, headline,
   experiences: [{title, company, start, end}], recent_posts: [...], source_notes}`.
2. **Company research**: follow `assets/prompts/perplexity_research.txt` with WebSearch /
   WebFetch (or `mcp__searxng__*` if configured). Cite URLs. Output `perplexity_data`.
3. **Analyses (you, in order)**, each following its prompt file and the schemas in
   `references/output-structures.md`:
   - `lead_profile` (`assets/prompts/lead_profile.txt`)
   - `pain_gain_operational` (`assets/prompts/pain_gain_operational.txt`)
   - `dm_sequence` (`assets/prompts/dm_sequence.txt`), max 300 characters per DM
   - `dm_quality_review`: score 1-10 against the hard constraints of the DM prompt,
     `approval_recommendation` APPROVE / REVISE / REJECT. Revise once if below 7.
4. **Assemble** `.tmp/leads/<slug>/combined.json`:
   ```json
   {
     "linkedin_url": "...",
     "profile_data": {...},
     "perplexity_data": {...},
     "lead_profile": {"data": {...}},
     "pain_gain_operational": {"data": {...}},
     "dm_sequence": {"data": {...}},
     "dm_quality_review": {"data": {"overall_quality_score": 8, "approval_recommendation": "APPROVE"}},
     "quality_flags": []
   }
   ```
5. **Review report** (HTML, for the human):
   ```bash
   python3 .claude/skills/research-lead/scripts/generate_review_report.py --data .tmp/leads/<slug>/combined.json
   ```
6. **Store** (local CSV `data/leads.csv`, opens in R, LibreOffice or kSuite):
   ```bash
   python3 .claude/skills/research-lead/scripts/save_lead.py --data .tmp/leads/<slug>/combined.json
   ```
   Then, if Odoo is configured (`ODOO_URL` in `.env`) and the user approved the lead, offer to
   create the opportunity (preview first, then `--confirm`):
   `python3 .claude/skills/odoo/scripts/odoo.py create-lead --from-json .tmp/leads/<slug>/combined.json [--stage ...]`
   See the `odoo` skill.
7. **kChat review card** (only if the user confirms): write a short Markdown summary
   (who, why now, chosen hook, DM1, score) and post it with
   `python3 .claude/skills/ksuite-setup/scripts/kchat_post.py --file ...`.

Never send a DM or an email yourself. The human copies the approved message.

## Batch

For a list of leads (CSV with `linkedin_url` or `name,company`), process them one by
one, skip those already in `data/leads.csv`, and give a summary table at the end.

## Edge cases

- Private or unreachable profile: work from what the user pastes; note the limits.
- Company not found: say so; use headline and posts only; lower confidence.
- No allowed hook: do not invent one; recommend not contacting yet.
