#!/usr/bin/env python3
"""
Safe wrapper around the official QFieldCloud CLI (qfieldcloud-sdk, MIT, OPENGIS.ch).

Usage (any qfieldcloud-cli command, JSON output is forced):
    python3 qfc.py status
    python3 qfc.py list-projects
    python3 qfc.py list-files <PROJECT_ID>
    python3 qfc.py download-files <PROJECT_ID> data/qfield/<name> [--filter "*.gpkg"]
    python3 qfc.py upload-files <PROJECT_ID> <LOCAL_PROJECT_DIR>
    python3 qfc.py job-trigger <PROJECT_ID> package
    python3 qfc.py job-status <JOB_ID>
    python3 qfc.py package-latest <PROJECT_ID>
    python3 qfc.py delete-file <PROJECT_ID> <FILE> --confirm     # destructive: needs --confirm

Reads QFIELDCLOUD_URL and QFIELDCLOUD_TOKEN from the project .env.
`login` is refused here on purpose: the password must never go through the chat.
The user logs in from the R console with aigora_qfieldcloud_login().
Needs: pip install qfieldcloud-sdk
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Commands that delete, revoke access or change rights / settings in the cloud
DESTRUCTIVE = {
    "delete-project", "delete-file", "delete-files", "patch-project",
    "collaborators-add", "collaborators-patch", "collaborators-remove",
    "members-add", "members-patch", "members-remove",
    "teams-create", "teams-delete", "teams-patch",
    "team-members-add", "team-members-remove", "logout", "create-user", "delta-push",
}
REFUSED = {"login"}


def project_root() -> Path:
    path = Path(__file__).resolve().parent
    while path != path.parent:
        if (path / "CLAUDE.md").exists():
            return path
        path = path.parent
    raise RuntimeError("AIGORA project root not found")


ROOT = project_root()


def load_env():
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if " #" in value:
            value = value.split(" #", 1)[0]
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key.startswith(("QFIELDCLOUD_", "QFC_SDK_")) and key not in os.environ:
            os.environ[key] = value


def out(payload, code=0):
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    sys.exit(code)


def main():
    args = sys.argv[1:]
    confirm = "--confirm" in args
    args = [a for a in args if a != "--confirm"]
    if not args or args[0] in ("-h", "--help"):
        out({"success": True, "usage": __doc__.strip()})

    command = args[0]
    if command in REFUSED:
        out({"success": False, "error": "Login is not done through AIGORA. In the R console run "
             "aigora_qfieldcloud_login(): it asks for the password locally and stores only the token."}, 1)
    if command in DESTRUCTIVE and not confirm:
        out({"success": False, "needs_confirmation": True, "command": " ".join(args),
             "error": "This command changes or deletes data or access rights in QFieldCloud. "
                      "Explain the effect to the user, get an explicit yes, then rerun with --confirm."}, 1)

    load_env()
    if command != "status" and not os.environ.get("QFIELDCLOUD_TOKEN"):
        out({"success": False, "error": "QFIELDCLOUD_TOKEN missing. Ask the user to run "
             "aigora_qfieldcloud_login() in the R console (see docs/QFIELDCLOUD.md)."}, 1)

    # Relative local paths are resolved from the project root
    if command in ("download-files", "package-download") and len(args) >= 3 and not Path(args[2]).is_absolute():
        args[2] = str(ROOT / args[2])
        Path(args[2]).mkdir(parents=True, exist_ok=True)
    if command == "upload-files" and len(args) >= 3 and not Path(args[2]).is_absolute():
        args[2] = str(ROOT / args[2])

    try:
        import qfieldcloud_sdk  # noqa: F401
    except ImportError:
        out({"success": False, "error": "qfieldcloud-sdk missing: pip install qfieldcloud-sdk "
             "(or aigora_qfieldcloud_installer() in R)."}, 1)

    res = subprocess.run([sys.executable, "-m", "qfieldcloud_sdk", "--json", *args],
                         capture_output=True, text=True, cwd=ROOT)
    text = res.stdout.strip()
    try:
        result = json.loads(text) if text else None
    except json.JSONDecodeError:
        result = []
        for line in text.splitlines():
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                result.append(line)
    # The CLI can exit with code 0 while printing an HTTP error ("Requested ... and got 4xx/5xx")
    http_error = next((l for l in (text + "\n" + res.stderr).splitlines()
                       if re.match(r'^Requested ".*" and got "\d{3}', l.strip())), None)
    if res.returncode != 0 or http_error:
        lines = [l for l in (res.stderr.strip() or text).splitlines() if l.strip()]
        out({"success": False, "command": command,
             "error": http_error or (lines[-1] if lines else "unknown error"),
             "details": "\n".join(lines[-12:])}, 1)
    out({"success": True, "command": command, "result": result})


if __name__ == "__main__":
    main()
