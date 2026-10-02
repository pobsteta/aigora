---
name: r-session
description: Work with the user's live R session in RStudio through the r-session MCP server (Posit's btw package) - inspect data frames and objects in memory, read help pages of installed packages, check session info and CRAN. Use when the user mentions "mes données", "ma session R", "l'objet X", a data frame by name, an R package, or asks for analysis on data already loaded in RStudio.
user-invocable: true
---

# Live R session (RStudio)

The `r-session` MCP server runs `btw::btw_mcp_server()` (Posit, CRAN). It connects to the
interactive RStudio session that called `btw::btw_mcp_session()` (done automatically by the
project `.Rprofile` when `AIGORA_R_MCP=1`). Its tools are prefixed `mcp__r-session__`.

## When to use it

- The user refers to an object that lives in their R session ("le data frame `ventes`",
  "mon modèle", "ce que j'ai chargé") -> describe it with the env tools before writing code.
- Questions about a package or function -> read the installed help page (docs tools),
  so the answer matches the version the user has, not memory.
- Writing code for the user -> check `sessioninfo` (R version, loaded packages) first.

## Setup (if the tools are missing)

1. `aigora_verifier()` in the R console: the "Paquet R btw" line must be "ok".
   Otherwise: `aigora_installer_r_mcp()` (installs btw + mcptools from CRAN).
2. `aigora_r_mcp(TRUE)`: writes `AIGORA_R_MCP=1` to `.env`, makes the session visible,
   registers the server in Claude Code (scope local).
3. Restart Claude Code in the Terminal (`/exit`, then `claude`).
4. If several R sessions are open, use the session-selection tools the server offers and
   confirm with the user which one to use.

## Tool groups

Default: `docs, pkg, env, sessioninfo, cran` (read-only, no code execution in the session).
`AIGORA_R_MCP_TOOLS` in `.env` changes the list. Adding `run` lets you execute R code **inside
the user's live session** (it can modify or delete their objects): propose it only if the user
asks, explain the risk, and re-register with `aigora_mcp(simulation = FALSE)`.

## Rules

- Never print large objects: summarize (dimensions, column types, a few rows).
- Data can be personal or confidential: do not copy it into memory files, logs or kChat.
- Prefer writing a script in `R/` or a `.qmd` the user runs themselves; with `run`, show the
  code and get a yes before executing anything that changes the session.
- Without the MCP server you can still run `Rscript` in the terminal, but that is a separate,
  empty session: say so if the user expects their in-memory objects.
