#!/usr/bin/env python3
"""
Give AIGORA access to the LOCAL kDrive folder synced by the kDrive desktop app.

This is the simplest kDrive connector and it works on every kSuite plan
(including the free ones, where WebDAV is not available): the kDrive app keeps a
folder on the computer in sync, and Claude Code reads / writes it like any folder.
Files written there (.docx, .xlsx, .pptx, .pdf...) appear in kDrive and open in
kSuite Docs / Grids / Points.

Usage:
    python3 link_kdrive.py                    # auto-detect ~/kDrive (or KDRIVE_LOCAL_PATH)
    python3 link_kdrive.py --path "D:/kDrive"
    python3 link_kdrive.py --unlink

What it does: adds the folder to `permissions.additionalDirectories` in
.claude/settings.local.json (personal, never committed) and stores
KDRIVE_LOCAL_PATH in .env. Restart Claude Code afterwards.
"""

import argparse
import json
from pathlib import Path

import ksuite_env as K

SETTINGS = K.PROJECT_ROOT / ".claude" / "settings.local.json"


def candidates():
    home = Path.home()
    names = ["kDrive", "kdrive", "KDrive"]
    found = [home / n for n in names]
    found += [p for p in home.glob("kDrive*") if p.is_dir()]
    unique = {}
    for p in found:
        if p.is_dir():
            unique.setdefault(str(p.resolve()).lower(), p)
    return list(unique.values())


def set_env(key, value):
    K.set_env(key, value)


def load_settings():
    if SETTINGS.exists():
        try:
            return json.loads(SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            K.fail(f"{SETTINGS} is not valid JSON: fix it first.")
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path")
    ap.add_argument("--unlink", action="store_true")
    args = ap.parse_args()
    K.load_env()

    settings = load_settings()
    perms = settings.setdefault("permissions", {})
    dirs = perms.setdefault("additionalDirectories", [])

    if args.unlink:
        old = K.get("KDRIVE_LOCAL_PATH")
        perms["additionalDirectories"] = [d for d in dirs if d != old]
        SETTINGS.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        set_env("KDRIVE_LOCAL_PATH", None)
        K.ok(unlinked=old)

    raw = args.path or K.get("KDRIVE_LOCAL_PATH")
    if raw:
        path = Path(raw).expanduser()
    else:
        found = candidates()
        if not found:
            K.fail("kDrive folder not found. Install the kDrive desktop app "
                   "(https://www.infomaniak.com/en/apps/download-kdrive), or give --path.")
        if len(found) > 1:
            K.fail("Several kDrive folders found: choose one with --path.", found=[str(p) for p in found])
        path = found[0]
    if not path.is_dir():
        K.fail(f"Not a folder: {path}")

    resolved = path.resolve().as_posix()
    if resolved not in dirs:
        dirs.append(resolved)
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    set_env("KDRIVE_LOCAL_PATH", resolved)
    sample = sorted(p.name for p in path.iterdir())[:15]
    K.ok(kdrive_local_path=resolved, settings=str(SETTINGS), top_level=sample,
         next_step="Restart Claude Code (/exit, then `claude`).")


if __name__ == "__main__":
    main()
