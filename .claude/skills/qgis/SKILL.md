---
name: qgis
description: Drive QGIS through the qgis MCP server - inspect the open project and layers, query and edit features, run Processing algorithms, style layers, render maps and build print layouts. Use when the user mentions QGIS, a layer, a shapefile / GeoPackage / raster, a map, a CRS, a buffer / intersection / spatial join, or asks for a map.
user-invocable: true
---

# QGIS

The `qgis` MCP server (qgis-mcp by Nicolas Karasiak, server MIT, plugin GPL-2, release
pinned to v0.15.0) talks over a local socket (default port 9876) to the **QGIS MCP** plugin
running inside the user's QGIS. Tools are prefixed `mcp__qgis__`.

Default mode is `compound`: 27 grouped tools (`system`, `project`, `layer`, `features`,
`selection`, `editing`, `style`, `canvas`, `render`, `processing`, `analysis`, `field`,
`query`, `transform`, `layer_tree`, `map_themes`, `bookmarks`, `code`, `batch`, ...).
`AIGORA_QGIS_TOOL_MODE=granular` exposes 125 fine-grained tools (more context used).

## Setup (if the tools are missing or calls fail)

1. Install **uv** (https://docs.astral.sh/uv/getting-started/installation/), restart RStudio.
2. In QGIS (3.28 or later): Plugins > Manage and Install Plugins > search "QGIS MCP" > Install.
   Click its toolbar button to start the socket server (it listens on localhost only).
   Optional shared secret: if `AIGORA_QGIS_TOKEN` is set in `.env`, the same value must be set as
   environment variable `QGIS_MCP_TOKEN` for QGIS (Settings > Options > System > Environment,
   then restart QGIS).
3. In the R console: `aigora_qgis_mcp(TRUE)`, then restart Claude Code (`/exit`, `claude`).
4. Test: call the `system` tool (ping / diagnose). "Connection refused" = QGIS closed or the
   plugin server not started.

## How to work

1. Start with the project and layer list; check each layer's CRS before any analysis.
2. Use Processing algorithms (native, GDAL, GRASS) rather than hand-written geometry code.
3. Write results to new layers or files (GeoPackage preferred), never overwrite source data.
4. For maps: set extent and style, render to `.tmp/qgis/` or the kDrive folder, show the path.
5. For R users: offer the equivalent `sf` / `terra` R code when the analysis must be
   reproducible, or export results to GeoPackage for R.
6. Field data from QField: use the `qfieldcloud` skill to download it, then add the
   GeoPackage as a layer here.

## Safety

- Edits, deletions, layer removal, project save and the `code` tool (arbitrary PyQGIS) are
  powerful: say exactly what will change and wait for confirmation. Claude Code also asks
  permission for each tool unless the user pre-allowed it; never pre-allow `code` or editing.
- Suggest a checkpoint (`project` tool, create checkpoint) before a batch of edits.
- The QGIS project may contain confidential data (cadastre, personal data): do not copy
  attributes into memory, logs or kChat.
- On a shared computer, set the shared secret (`AIGORA_QGIS_TOKEN` / `QGIS_MCP_TOKEN`). The plugin
  refuses non-localhost connections without a token.
