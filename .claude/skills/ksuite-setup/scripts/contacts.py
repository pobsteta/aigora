#!/usr/bin/env python3
"""
kSuite Contacts (Infomaniak) over CardDAV. Read-only.

Usage:
    python3 contacts.py books                       # list address books
    python3 contacts.py search "dupont"             # name, email, phone, company
    python3 contacts.py list [--limit 500]
    python3 contacts.py export --output data/contacts.csv   # CSV ";" UTF-8 BOM, for R / LibreOffice

Same credentials as the calendar: KSUITE_DAV_USER (short username) and
KSUITE_DAV_PASSWORD (application password if 2FA). Base URL: KSUITE_CARDDAV_URL,
default https://sync.infomaniak.com (discovery through current-user-principal).
These contacts also sync to phones with kSync (Android) or the iOS CardDAV account.
Standard library only.
"""

import argparse
import base64
import csv
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import ksuite_env as K

NS = {"d": "DAV:", "card": "urn:ietf:params:xml:ns:carddav"}


class DAV:
    def __init__(self, base, user, password, fatal=True):
        self.fatal = fatal  # False when used as a library (check_status): raise instead of exit
        self.base = base.rstrip("/") + "/"
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}", "Content-Type": "application/xml; charset=utf-8"}
        self.ctx = ssl.create_default_context()

    def request(self, method, url, body, depth="0"):
        url = urllib.parse.urljoin(self.base, url)
        req = urllib.request.Request(url, data=body.encode("utf-8"), method=method,
                                     headers={**self.headers, "Depth": depth})
        try:
            with urllib.request.urlopen(req, timeout=60, context=self.ctx) as resp:
                return url, ET.fromstring(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self._error("CardDAV refused the login (401). Use the short username (e.g. AB12345) "
                            "and an application password.")
            self._error(f"CardDAV error {e.code} on {url}")
        except urllib.error.URLError as e:
            self._error(f"CardDAV server unreachable: {e.reason}")

    def _error(self, msg):
        if self.fatal:
            K.fail(msg)
        raise RuntimeError(msg)

    def prop_href(self, url, prop_xml, path):
        _, root = self.request("PROPFIND", url, f'<?xml version="1.0"?><d:propfind xmlns:d="DAV:" '
                                                f'xmlns:card="urn:ietf:params:xml:ns:carddav"><d:prop>{prop_xml}</d:prop></d:propfind>')
        el = root.find(path, NS)
        return el.text.strip() if el is not None and el.text else None

    def address_books(self):
        principal = self.prop_href("", "<d:current-user-principal/>",
                                   ".//d:current-user-principal/d:href") or ""
        home = self.prop_href(principal, "<card:addressbook-home-set/>",
                              ".//card:addressbook-home-set/d:href") or principal
        home_url, root = self.request(
            "PROPFIND", home,
            '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:resourcetype/><d:displayname/></d:prop></d:propfind>',
            depth="1")
        books = []
        for resp in root.findall("d:response", NS):
            if resp.find(".//d:resourcetype/card:addressbook", NS) is None:
                continue
            href = resp.find("d:href", NS).text
            name = resp.find(".//d:displayname", NS)
            books.append({"name": (name.text if name is not None and name.text else href.rstrip("/").split("/")[-1]),
                          "href": href})
        return books

    def cards(self, book_href):
        body = ('<?xml version="1.0"?><card:addressbook-query xmlns:d="DAV:" '
                'xmlns:card="urn:ietf:params:xml:ns:carddav"><d:prop><card:address-data/></d:prop>'
                '</card:addressbook-query>')
        _, root = self.request("REPORT", book_href, body, depth="1")
        for el in root.iter("{urn:ietf:params:xml:ns:carddav}address-data"):
            if el.text:
                yield el.text


def unfold(text):
    return re.sub(r"\r?\n[ \t]", "", text)


def parse_vcard(raw, book):
    c = {"book": book, "name": "", "emails": [], "phones": [], "org": "", "title": "", "note": "", "uid": ""}
    for line in unfold(raw).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        prop = key.split(";")[0].upper().split(".")[-1]  # strip item1. groups
        value = value.replace("\\,", ",").replace("\\;", ";").replace("\\n", "\n").strip()
        if prop == "FN":
            c["name"] = value
        elif prop == "N" and not c["name"]:
            parts = value.split(";")
            c["name"] = " ".join(p for p in (parts[1:2] + parts[:1]) if p).strip()
        elif prop == "EMAIL":
            c["emails"].append(value)
        elif prop == "TEL":
            c["phones"].append(value)
        elif prop == "ORG":
            c["org"] = value.replace(";", " ").strip()
        elif prop == "TITLE":
            c["title"] = value
        elif prop == "NOTE":
            c["note"] = value[:500]
        elif prop == "UID":
            c["uid"] = value
    return c


def all_contacts(dav):
    out = []
    for b in dav.address_books():
        out += [parse_vcard(v, b["name"]) for v in dav.cards(b["href"])]
    return out


def main():
    ap = argparse.ArgumentParser(description="kSuite Contacts (CardDAV, read-only)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("books")
    s = sub.add_parser("search"); s.add_argument("query")
    lst = sub.add_parser("list"); lst.add_argument("--limit", type=int, default=500)
    e = sub.add_parser("export"); e.add_argument("--output", default="data/contacts.csv")
    args = ap.parse_args()

    K.load_env()
    dav = DAV(K.get("KSUITE_CARDDAV_URL") or K.get("KSUITE_CALDAV_URL"),
              K.get("KSUITE_DAV_USER", required=True), K.get("KSUITE_DAV_PASSWORD", required=True))

    if args.cmd == "books":
        K.ok(address_books=dav.address_books())
    contacts = all_contacts(dav)
    if args.cmd == "search":
        q = args.query.lower()
        digits = re.sub(r"\D", "", q).lstrip("0")  # 079 123 matches +41 79 123
        hits = [c for c in contacts if q in " ".join([c["name"], c["org"], c["title"], *c["emails"]]).lower()
                or (len(digits) >= 4 and any(digits in re.sub(r"\D", "", p) for p in c["phones"]))]
        K.ok(query=args.query, count=len(hits), contacts=hits[:50])
    if args.cmd == "list":
        K.ok(count=len(contacts), contacts=contacts[: args.limit])
    out = Path(args.output)
    if not out.is_absolute():
        out = K.PROJECT_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["nom", "organisation", "fonction", "emails", "telephones", "carnet"])
        for c in contacts:
            w.writerow([c["name"], c["org"], c["title"], ", ".join(c["emails"]), ", ".join(c["phones"]), c["book"]])
    K.ok(count=len(contacts), output=str(out))


if __name__ == "__main__":
    main()
