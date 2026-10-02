#!/usr/bin/env python3
"""
Shared helpers for the kSuite (Infomaniak) scripts.

- Finds the AIGORA project root (folder containing CLAUDE.md).
- Loads `.env` without any third-party dependency.
- Prints JSON results in the format the PostToolUse hook validates.

Standard library only.
"""

import json
import os
import re
import sys
from pathlib import Path

# Default Infomaniak endpoints (overridable from .env)
DEFAULTS = {
    "KSUITE_IMAP_HOST": "mail.infomaniak.com",
    "KSUITE_IMAP_PORT": "993",
    "KSUITE_SMTP_HOST": "mail.infomaniak.com",
    "KSUITE_SMTP_PORT": "587",
    "KSUITE_CALDAV_URL": "https://sync.infomaniak.com",
}


def find_project_root() -> Path:
    path = Path(__file__).resolve().parent
    while path != path.parent:
        if (path / "CLAUDE.md").exists():
            return path
        path = path.parent
    raise RuntimeError("AIGORA project root not found (no CLAUDE.md above this script)")


PROJECT_ROOT = find_project_root()


def load_env() -> dict:
    """Load PROJECT_ROOT/.env into os.environ (existing variables win)."""
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            # strip inline comments only when preceded by whitespace
            if " #" in value:
                value = value.split(" #", 1)[0]
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    for key, value in DEFAULTS.items():
        os.environ.setdefault(key, value)
    return dict(os.environ)


def update_env_lines(lines: list, key: str, value) -> list:
    """Set KEY=value in .env lines, in place (same rules as .aigora_set_env in R/aigora.R).

    - an existing active line KEY=... is updated where it is;
    - otherwise the template line "# KEY=..." from .env.example is uncommented and filled
      (its trailing comment is kept on the line above);
    - an active line appended at the end by an older version moves back to the template line;
    - duplicates are removed; a new line is appended only for an unknown key.
    value=None comments the active line out ("# KEY=...").
    """
    active_re = re.compile(rf"^\s*{re.escape(key)}\s*=")
    model_re = re.compile(rf"^\s*#\s*{re.escape(key)}\s*=")
    actives = [i for i, l in enumerate(lines) if active_re.match(l)]
    models = [i for i, l in enumerate(lines) if model_re.match(l)]
    lines = list(lines)
    if value is None:
        if actives:
            lines[actives[0]] = "# " + lines[actives[0]].lstrip()
            for i in reversed(actives[1:]):
                del lines[i]
        return lines
    new = f"{key}={value}"
    if models and (not actives or actives[0] > models[0]):
        at = models[0]
        rest = re.sub(model_re.pattern + r"[^#]*", "", lines[at], count=1)
        replacement = ["# " + re.sub(r"^#\s*", "", rest), new] if rest.startswith("#") else [new]
        remove = actives
    elif actives:
        at, replacement, remove = actives[0], [new], actives[1:]
    else:
        if lines and lines[-1].strip():
            lines.append("")
        return lines + [new]
    shift = len(replacement) - 1
    lines[at:at + 1] = replacement
    for i in sorted(remove, reverse=True):
        del lines[i + shift if i > at else i]
    return lines


def set_env(key: str, value) -> None:
    """Write KEY=value into PROJECT_ROOT/.env at its place (creates .env from .env.example)."""
    env = PROJECT_ROOT / ".env"
    example = PROJECT_ROOT / ".env.example"
    if not env.exists() and example.exists():
        env.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    env.write_text("\n".join(update_env_lines(lines, key, value)) + "\n", encoding="utf-8")


def get(key: str, required: bool = False) -> str:
    value = os.environ.get(key, "").strip()
    if required and not value:
        fail(
            f"Missing {key} in .env. See docs/KSUITE.md (or ask: 'connecte kSuite').",
            missing=key,
        )
    return value


def ok(**payload):
    payload = {"success": True, **payload}
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    sys.exit(0)


def fail(error: str, **payload):
    payload = {"success": False, "error": error, **payload}
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    sys.exit(1)
