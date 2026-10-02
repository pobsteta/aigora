#!/usr/bin/env python3
"""
Register AIGORA's MCP servers in Claude Code, reading settings from .env:
official Infomaniak servers, the optional community kSuite server, open-source
servers, and the local apps RStudio (live R session, via btw) and QGIS.

The servers are added with `--scope local`: they are stored in your own
Claude Code user config for THIS project only. Tokens never land in a
file that could be committed (.mcp.json is not used).

Usage:
    python3 register_mcp.py --dry-run            # show what would be done
    python3 register_mcp.py                      # register every configured server
    python3 register_mcp.py --only mail calendar
    python3 register_mcp.py --remove             # unregister them

Needs: Node.js (npx) and the `claude` CLI on PATH.
Restart Claude Code afterwards (type /exit then `claude`) so the tools load.
"""

import argparse
import json
import os
import shutil
import subprocess

import ksuite_env as K

# name -> (npm package, {server env var: list of .env keys to try in order})
# A candidate starting with "=" is a literal value.
SERVERS = {
    "mail": ("@infomaniak/mcp-server-mail",
             {"MAIL_TOKEN": ["KSUITE_MAIL_TOKEN", "INFOMANIAK_TOKEN"]}),
    "calendar": ("@infomaniak/mcp-server-calendar",
                 {"CALENDAR_TOKEN": ["KSUITE_CALENDAR_TOKEN", "INFOMANIAK_TOKEN"]}),
    "kdrive": ("@infomaniak/mcp-server-kdrive",
               {"KDRIVE_TOKEN": ["KDRIVE_TOKEN", "INFOMANIAK_TOKEN"],
                "KDRIVE_ID": ["KDRIVE_ID"]}),
    "kchat": ("@infomaniak/mcp-server-kchat",
              {"KCHAT_TOKEN": ["KCHAT_TOKEN", "INFOMANIAK_TOKEN"],
               "KCHAT_TEAM_NAME": ["KCHAT_TEAM_NAME"]}),
    "contact": ("@infomaniak/mcp-server-contact",  # official, read-only (list/search)
                {"CONTACT_TOKEN": ["KSUITE_CONTACT_TOKEN", "INFOMANIAK_TOKEN"]}),
    # Community server (MIT, young project): only the services Infomaniak has no
    # official MCP for: CalDAV tasks, kMeet rooms, Chk short links, kPaste.
    # Opt-in with KSUITE_EXTRA_MCP=1 in .env (or --only extra).
    "extra": ("@henrikogard/infomaniak-mcp",
              {"INFOMANIAK_TOKEN": ["INFOMANIAK_TOKEN"],
               "DAV_USER": ["KSUITE_DAV_USER"],
               "DAV_PASSWORD": ["KSUITE_DAV_PASSWORD"],
               "INFOMANIAK_TOOLS": ["=tasks_*,kmeet_*,chk_*,kpaste_*,infomaniak_help"],
               "STRICT_CONFIRM_EXTERNAL_SEND": ["=1"]}),
    # Optional open-source servers (see docs/CONNECTEURS-OPEN-SOURCE.md)
    "searxng": ("mcp-searxng", {"SEARXNG_URL": ["SEARXNG_URL"]}),
    # Local applications (see docs/RSTUDIO-QGIS.md). Not npm: custom commands below.
    # R session: Posit's btw package (CRAN), sees the live RStudio session that
    # called btw::btw_mcp_session() (done by .Rprofile when AIGORA_R_MCP=1).
    "r": ("btw (R package)", {}),
    # QGIS: qgis-mcp by Nicolas Karasiak (server MIT, plugin GPL-2), pinned release.
    "qgis": ("git+https://github.com/nkarasiak/qgis-mcp@v0.15.0",
             {"QGIS_MCP_TOOL_MODE": ["AIGORA_QGIS_TOOL_MODE", "=compound"],
              "QGIS_MCP_PORT": ["AIGORA_QGIS_PORT", "=9876"]}),
}
PREFIX = "ksuite-"
OPEN_SOURCE = {"searxng"}
LOCAL_APPS = {"r": "r-session", "qgis": "qgis"}
OPT_IN = {"extra": "KSUITE_EXTRA_MCP", "r": "AIGORA_R_MCP", "qgis": "AIGORA_QGIS_MCP"}
PUBLIC_ENV = {"INFOMANIAK_TOOLS", "STRICT_CONFIRM_EXTERNAL_SEND", "SEARXNG_URL",
              "QGIS_MCP_TOOL_MODE", "QGIS_MCP_PORT"}
R_TOOL_GROUPS = "docs,pkg,env,sessioninfo,cran"


def server_name(key):
    if key in LOCAL_APPS:
        return LOCAL_APPS[key]
    return key if key in OPEN_SOURCE else PREFIX + key


def local_app_command(key, package):
    """Return (command list, extra env, error) for local applications."""
    if key == "r":
        rscript = K.get("AIGORA_RSCRIPT") or shutil.which("Rscript") or ""
        if not rscript:
            return None, {}, "Rscript not found: set AIGORA_RSCRIPT (aigora_mcp() in R does it)"
        groups = [g.strip() for g in (K.get("AIGORA_R_MCP_TOOLS") or R_TOOL_GROUPS).split(",") if g.strip()]
        r_list = "list(" + ", ".join(f"'{g}'" for g in groups) + ")"
        return [rscript, "-e", f"btw::btw_mcp_server({r_list})"], {}, None
    if key == "qgis":
        uvx = shutil.which("uvx")
        if not uvx:
            return None, {}, "uvx not found: install uv (https://docs.astral.sh/uv/)"
        token = K.get("AIGORA_QGIS_TOKEN")
        return [uvx, "--from", package, "qgis-mcp-server"], ({"QGIS_MCP_TOKEN": token} if token else {}), None
    return None, {}, f"unknown local app {key}"


def resolve(env_map):
    values, missing = {}, []
    for target, candidates in env_map.items():
        value = next((c[1:] if c.startswith("=") else K.get(c)
                      for c in candidates if c.startswith("=") or K.get(c)), "")
        if value:
            values[target] = value
        else:
            missing.append(" or ".join(candidates))
    return values, missing


def npx_command(package):
    # On native Windows, npx must be wrapped in `cmd /c`
    if os.name == "nt":
        return ["cmd", "/c", "npx", "-y", package]
    return ["npx", "-y", package]


def main():
    ap = argparse.ArgumentParser(description="Register kSuite MCP servers in Claude Code")
    ap.add_argument("--only", nargs="*", choices=sorted(SERVERS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--remove", action="store_true")
    args = ap.parse_args()

    K.load_env()
    claude = shutil.which("claude")
    if not claude and not args.dry_run:
        K.fail("The `claude` CLI is not on PATH. Install Claude Code first.")
    wanted = args.only or list(SERVERS)
    needs_npx = any(k not in LOCAL_APPS for k in wanted)
    if needs_npx and not shutil.which("npx") and not args.remove and not args.dry_run:
        K.fail("npx not found: install Node.js LTS from nodejs.org, then reopen RStudio.")

    done, skipped = [], []
    for key in args.only or SERVERS:
        package, env_map = SERVERS[key]
        name = server_name(key)
        if not args.remove and key in OPT_IN and not args.only and K.get(OPT_IN[key]) != "1":
            skipped.append({"server": name, "missing": [f"{OPT_IN[key]}=1 (opt-in)"]})
            continue
        if args.remove:
            cmd = [claude or "claude", "mcp", "remove", "--scope", "local", name]
            shown = cmd
        else:
            values, missing = resolve(env_map)
            if missing:
                skipped.append({"server": name, "missing": missing})
                continue
            if key in LOCAL_APPS:
                command, extra_env, err = local_app_command(key, package)
                if err:
                    skipped.append({"server": name, "missing": [err]})
                    continue
                values.update(extra_env)
            else:
                command = npx_command(package)
            config = {"type": "stdio", "command": command[0], "args": command[1:], "env": values}
            cmd = [claude or "claude", "mcp", "add-json", "--scope", "local", name, json.dumps(config)]
            shown_config = dict(config, env={k: (v if k in PUBLIC_ENV else "***") for k, v in values.items()})
            shown = [claude or "claude", "mcp", "add-json", "--scope", "local", name, json.dumps(shown_config)]

        if args.dry_run:
            done.append({"server": name, "command": " ".join(shown)})
            continue
        if not args.remove:  # re-register cleanly if it already exists
            subprocess.run([claude, "mcp", "remove", "--scope", "local", name],
                           capture_output=True, text=True, cwd=K.PROJECT_ROOT)
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=K.PROJECT_ROOT)
        entry = {"server": name, "ok": res.returncode == 0}
        if res.returncode != 0:
            entry["error"] = (res.stderr or res.stdout).strip()[:400]
        done.append(entry)

    failed = [d for d in done if d.get("ok") is False]
    payload = {"dry_run": args.dry_run, "servers": done, "skipped": skipped,
               "next_step": "Restart Claude Code (/exit, then `claude`) to load the new tools."}
    if failed:
        K.fail("Some servers could not be registered", **payload)
    K.ok(**payload)


if __name__ == "__main__":
    main()
