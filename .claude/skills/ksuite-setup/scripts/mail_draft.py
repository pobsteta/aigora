#!/usr/bin/env python3
"""
Create a DRAFT (never sends) in the kSuite mailbox, via IMAP APPEND
into the Drafts folder. The user reviews and sends it from kSuite Mail.

Usage:
    python3 mail_draft.py --to "client@example.com" --subject "Re: Devis" --body-file .tmp/draft.txt
    python3 mail_draft.py --to a@b.ch --subject "Bonjour" --body "Texte" --in-reply-to "<id@host>"
    python3 mail_draft.py --from-json .tmp/email-digest/drafts.json   # list of drafts

JSON format for --from-json: [{"to": "...", "subject": "...", "body": "...",
                              "cc": "...", "in_reply_to": "<message-id>"}]

Needs in .env: KSUITE_MAIL_USER, KSUITE_MAIL_PASSWORD.
Standard library only.
"""

import argparse
import imaplib
import json
import re
import time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

import ksuite_env as K

DRAFT_NAMES = ("Drafts", "Brouillons", "INBOX.Drafts", "Draft")


def find_drafts_folder(imap) -> str:
    override = K.get("KSUITE_DRAFTS_FOLDER")
    if override:
        return override
    status, folders = imap.list()
    names = []
    for raw in folders or []:
        line = raw.decode(errors="replace")
        match = re.search(r'"([^"]+)"\s*$|(\S+)\s*$', line)
        name = (match.group(1) or match.group(2)) if match else ""
        if "\\Drafts" in line:
            return name
        names.append(name)
    for candidate in DRAFT_NAMES:
        if candidate in names:
            return candidate
    K.fail("Drafts folder not found. Set KSUITE_DRAFTS_FOLDER in .env.", folders=names)


def build(user, d) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = K.get("KSUITE_MAIL_FROM") or user
    msg["To"] = d["to"]
    if d.get("cc"):
        msg["Cc"] = d["cc"]
    msg["Subject"] = d["subject"]
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=user.split("@")[-1])
    if d.get("in_reply_to"):
        msg["In-Reply-To"] = d["in_reply_to"]
        msg["References"] = d["in_reply_to"]
    msg.set_content(d["body"])
    return msg


def main():
    ap = argparse.ArgumentParser(description="Create kSuite mail drafts (never sends)")
    ap.add_argument("--to")
    ap.add_argument("--cc")
    ap.add_argument("--subject")
    ap.add_argument("--body")
    ap.add_argument("--body-file")
    ap.add_argument("--in-reply-to")
    ap.add_argument("--from-json", help="JSON file with a list of drafts")
    args = ap.parse_args()

    if args.from_json:
        drafts = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
        if isinstance(drafts, dict):
            drafts = drafts.get("drafts", [drafts])
    else:
        body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else args.body
        if not (args.to and args.subject and body):
            K.fail("Provide --to, --subject and --body/--body-file (or --from-json).")
        drafts = [{"to": args.to, "cc": args.cc, "subject": args.subject,
                   "body": body, "in_reply_to": args.in_reply_to}]

    K.load_env()
    user = K.get("KSUITE_MAIL_USER", required=True)
    password = K.get("KSUITE_MAIL_PASSWORD", required=True)
    try:
        imap = imaplib.IMAP4_SSL(K.get("KSUITE_IMAP_HOST"), int(K.get("KSUITE_IMAP_PORT")))
        imap.login(user, password)
    except Exception as e:
        K.fail(f"IMAP login failed: {e}")

    created = []
    try:
        folder = find_drafts_folder(imap)
        for d in drafts:
            msg = build(user, d)
            status, resp = imap.append(f'"{folder}"', "(\\Draft)",
                                       imaplib.Time2Internaldate(time.time()), msg.as_bytes())
            if status != "OK":
                K.fail(f"APPEND refused: {resp}", created=created)
            created.append({"to": d["to"], "subject": d["subject"]})
    finally:
        try:
            imap.logout()
        except Exception:
            pass

    K.ok(drafts_folder=folder, created=created,
         note="Drafts only. Nothing was sent. Review them in kSuite Mail.")


if __name__ == "__main__":
    main()
