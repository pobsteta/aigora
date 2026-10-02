---
name: quarto-slides
description: Generate presentation slide decks from content with Quarto (open source, bundled with RStudio). Outputs reveal.js HTML, PowerPoint (.pptx) or PDF (Beamer/Typst). Use when user says "create slides", "make a presentation", "build a deck", "fais-moi une présentation", or asks to turn content into slides. Run with /quarto-slides.
model: sonnet
allowed-tools: Bash(quarto:*)
user-invocable: true
---

# Quarto Slides

Replaces the Gamma skill of the original template. Everything stays local and open source:
Quarto (MIT/GPL) ships with RStudio, so no account and no API key are needed.

## Formats

| Format | Command | When |
|--------|---------|------|
| reveal.js (HTML) | `quarto render deck.qmd --to revealjs` | Default. Opens in any browser, self-contained with `embed-resources: true` |
| PowerPoint | `quarto render deck.qmd --to pptx` | The user must edit it in PowerPoint / LibreOffice Impress / kSuite (OnlyOffice in kDrive) |
| PDF | `quarto render deck.qmd --to beamer` (needs TinyTeX) or `--to typst` | Print or send as attachment |

Check Quarto first: `quarto --version`. If missing, RStudio's bundled Quarto may
not be on the terminal PATH: tell the user to install it from https://quarto.org/docs/get-started/.

## Steps

1. **Structure the content**: one idea per slide, 8 to 15 slides, a hook, a clear close.
   Read `context/my-voice.md` and `context/my-business.md` for tone and offers.
2. **Write the deck** to `.tmp/slides/<slug>-<date>/deck.qmd`, starting from
   `.claude/skills/quarto-slides/assets/template.qmd`. Slides are `##` headings.
   R code chunks are allowed (charts from the user's data render directly).
3. **Render**: `quarto render deck.qmd --to revealjs` (and/or `pptx`).
4. **Deliver**: give the output path; offer to upload it to kDrive
   (`mcp__ksuite-kdrive__kdrive_upload_file`) if kSuite is connected.

## Tips

- Speaker notes: `::: {.notes}` blocks.
- Two columns: `:::: {.columns}` / `::: {.column width="50%"}`.
- Incremental bullets: `::: {.incremental}`.
- Brand colors: set them in the YAML (`theme`, or a small `custom.scss`).
- Do not use the em-dash character in slides (see `.claude/rules/output-style.md`).
