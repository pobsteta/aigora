---
name: qfieldcloud
description: Work with QFieldCloud (field data collection with QField) - list projects and files, download the latest field data for QGIS or R, upload a QGIS project, trigger packaging, follow jobs, read collaborators. Use when the user mentions QField, QFieldCloud, field survey / relevés terrain, "données terrain", or syncing a project to tablets.
user-invocable: true
---

# QFieldCloud

QFieldCloud (MIT, by OPENGIS.ch) synchronizes QGIS projects with the QField mobile app.
AIGORA reaches it through the official CLI (`qfieldcloud-sdk`), wrapped by
`.claude/skills/qfieldcloud/scripts/qfc.py`. No MCP server exists for QFieldCloud; the
wrapper is the connector. It works with the hosted service (app.qfield.cloud) and with a
self-hosted server (`QFIELDCLOUD_URL` in `.env`).

## Setup (if `QFIELDCLOUD_TOKEN` is missing)

The user does it in the R console (never ask for their password in the chat):

```r
aigora_qfieldcloud_installer()   # pip install qfieldcloud-sdk
aigora_qfieldcloud_login()       # asks username + password locally, stores only the token in .env
# self-hosted: aigora_qfieldcloud_login("https://qfield.mon-domaine.ch/api/v1/")
```

Then test: `python3 .claude/skills/qfieldcloud/scripts/qfc.py list-projects`.

## Commands

```bash
Q=".claude/skills/qfieldcloud/scripts/qfc.py"
python3 $Q status
python3 $Q list-projects
python3 $Q get-project <PROJECT_ID>
python3 $Q list-files <PROJECT_ID>
python3 $Q download-files <PROJECT_ID> data/qfield/<project-name> [--filter "*.gpkg"] [--force-download]
python3 $Q upload-files <PROJECT_ID> <local_project_dir> [--filter "*.gpkg"]
python3 $Q job-trigger <PROJECT_ID> package      # prepare the project for QField devices
python3 $Q job-status <JOB_ID>
python3 $Q list-jobs <PROJECT_ID>
python3 $Q collaborators-get <PROJECT_ID>
```

Every output is JSON with `success`. Destructive or rights-changing commands (delete-*,
patch-*, collaborators-add/patch/remove, members-*, teams-*, logout, delta-push) are refused
unless `--confirm` is added: explain the effect, get an explicit yes, then rerun with `--confirm`.

## Typical workflows

**Bring field data back** ("récupère les relevés de la semaine"):
1. `list-projects` -> find the project; `list-files` -> see what changed (dates).
2. `download-files <id> data/qfield/<name> --filter "*.gpkg"`.
3. Offer: open it in QGIS (`qgis` skill: add the layer), or analyse in R
   (`sf::st_read("data/qfield/<name>/<file>.gpkg")`), or save a copy to the kDrive folder.

**Send a project to the field**:
1. Prepare the QGIS project (ideally with the QFieldSync plugin in QGIS, which handles
   offline layers and attachments). For a plain folder upload: `upload-files <id> <dir>`.
2. `job-trigger <id> package`, then poll `job-status` until `finished`.
3. Tell the user the devices can now synchronize in QField.

**Team overview**: `collaborators-get <id>` (read-only). Changing roles needs `--confirm`.

## Rules

- Field data can be personal or sensitive (owners, addresses, protected species): keep it in
  `data/` (git-ignored) or kDrive, never in memory files, logs or kChat messages.
- Never overwrite local edits: download into a new or dedicated folder; use `--force-download`
  only after saying what will be replaced.
- Uploading replaces the cloud version of those files for every field user: confirm first.
- The token is a credential: never print it.
