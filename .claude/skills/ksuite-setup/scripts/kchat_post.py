#!/usr/bin/env python3
"""
Post a Markdown message to a kChat channel through an incoming webhook.

Create the webhook in kChat: New (next to the organisation name) >
Integrations > Incoming Webhooks > Add. Put the URL in .env as KCHAT_WEBHOOK_URL.

Usage:
    python3 kchat_post.py --text "Bonjour **équipe**"
    python3 kchat_post.py --file .tmp/email-digest/briefing.md
    python3 kchat_post.py --file briefing.md --username "AIGORA" --channel "town-square"

This sends a message to other people: only run it after the user confirmed
(see .claude/rules/guardrails.md).
Standard library only.
"""

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

import ksuite_env as K

MAX_LEN = 16000  # keep well below kChat's message limit


def main():
    ap = argparse.ArgumentParser(description="Post to kChat (incoming webhook)")
    ap.add_argument("--text")
    ap.add_argument("--file")
    ap.add_argument("--username", default=None)
    ap.add_argument("--channel", default=None)
    args = ap.parse_args()

    K.load_env()
    url = K.get("KCHAT_WEBHOOK_URL", required=True)
    text = Path(args.file).read_text(encoding="utf-8") if args.file else args.text
    if not text:
        K.fail("Nothing to post: give --text or --file")
    if len(text) > MAX_LEN:
        text = text[: MAX_LEN - 40] + "\n\n_(message tronqué)_"

    payload = {"text": text}
    if args.username or K.get("KCHAT_USERNAME"):
        payload["username"] = args.username or K.get("KCHAT_USERNAME")
    if args.channel:
        payload["channel"] = args.channel

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            K.ok(status=resp.status, characters=len(text))
    except urllib.error.HTTPError as e:
        K.fail(f"kChat refused the message: HTTP {e.code} {e.read()[:300]!r}")
    except Exception as e:
        K.fail(f"kChat webhook unreachable: {e}")


if __name__ == "__main__":
    main()
