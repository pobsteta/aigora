#!/usr/bin/env python3
"""
Fetch recent emails from an Infomaniak (kSuite) mailbox over IMAP.

Usage:
    python3 mail_fetch.py --hours 24
    python3 mail_fetch.py --hours 48 --unread-only --folder INBOX --limit 50
    python3 mail_fetch.py --hours 24 --output .tmp/email-digest/emails.json

Read-only: messages are opened with BODY.PEEK, so nothing is marked as read.
Needs in .env: KSUITE_MAIL_USER, KSUITE_MAIL_PASSWORD (an application password).
Standard library only.
"""

import argparse
import email
import imaplib
import json
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

import ksuite_env as K


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def _decode(value) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)


def _body_text(msg, max_chars: int) -> str:
    plain, html = None, None
    for part in msg.walk() if msg.is_multipart() else [msg]:
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition", "").lower().startswith("attachment"):
            continue
        ctype = part.get_content_type()
        try:
            payload = part.get_payload(decode=True) or b""
            text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            continue
        if ctype == "text/plain" and plain is None:
            plain = text
        elif ctype == "text/html" and html is None:
            html = text
    if plain is None and html is not None:
        parser = _TextExtractor()
        parser.feed(html)
        plain = " ".join(" ".join(parser.parts).split())
    return (plain or "").strip()[:max_chars]


def _attachments(msg):
    names = []
    for part in msg.walk():
        if part.get("Content-Disposition", "").lower().startswith("attachment"):
            names.append(_decode(part.get_filename()))
    return names


def main():
    ap = argparse.ArgumentParser(description="Fetch recent kSuite emails (IMAP, read-only)")
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--folder", default="INBOX")
    ap.add_argument("--unread-only", action="store_true")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--max-body", type=int, default=4000, help="Max characters of body per email")
    ap.add_argument("--output", help="Write the JSON to this file instead of stdout")
    args = ap.parse_args()

    K.load_env()
    user = K.get("KSUITE_MAIL_USER", required=True)
    password = K.get("KSUITE_MAIL_PASSWORD", required=True)
    host, port = K.get("KSUITE_IMAP_HOST"), int(K.get("KSUITE_IMAP_PORT"))

    since = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    criteria = ["SINCE", since.strftime("%d-%b-%Y")]
    if args.unread_only:
        criteria.append("UNSEEN")

    try:
        imap = imaplib.IMAP4_SSL(host, port)
        imap.login(user, password)
    except Exception as e:
        K.fail(f"IMAP login failed on {host}:{port}: {e}. Check the application password.")

    try:
        status, _ = imap.select(f'"{args.folder}"', readonly=True)
        if status != "OK":
            K.fail(f"Folder not found: {args.folder}")
        status, data = imap.search(None, *criteria)
        ids = data[0].split() if status == "OK" and data and data[0] else []
        ids = ids[-args.limit:]

        emails = []
        for msg_id in reversed(ids):
            status, parts = imap.fetch(msg_id, "(BODY.PEEK[] FLAGS UID)")
            if status != "OK" or not parts or not isinstance(parts[0], tuple):
                continue
            meta = parts[0][0].decode(errors="replace")
            msg = email.message_from_bytes(parts[0][1])
            try:
                sent = parsedate_to_datetime(msg.get("Date"))
                if sent.tzinfo is None:
                    sent = sent.replace(tzinfo=timezone.utc)
            except Exception:
                sent = None
            if sent and sent < since:  # IMAP SINCE is day-granular, refine here
                continue
            uid = meta.split("UID ", 1)[1].split()[0].rstrip(")") if "UID " in meta else msg_id.decode()
            emails.append({
                "uid": uid,
                "message_id": msg.get("Message-ID", ""),
                "in_reply_to": msg.get("In-Reply-To", ""),
                "from": _decode(msg.get("From")),
                "to": _decode(msg.get("To")),
                "cc": _decode(msg.get("Cc")),
                "subject": _decode(msg.get("Subject")),
                "date": sent.isoformat() if sent else msg.get("Date"),
                "unread": "\\Seen" not in meta,
                "attachments": _attachments(msg),
                "body": _body_text(msg, args.max_body),
            })
    finally:
        try:
            imap.logout()
        except Exception:
            pass

    result = {"folder": args.folder, "hours": args.hours, "count": len(emails), "emails": emails}
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        K.ok(folder=args.folder, count=len(emails), output=str(out))
    K.ok(**result)


if __name__ == "__main__":
    main()
