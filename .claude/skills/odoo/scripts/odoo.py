#!/usr/bin/env python3
"""
Odoo CRM connector for AIGORA (Odoo Community or Online, any recent version).

Protocols:
  - JSON-2  (Odoo 19+): POST {ODOO_URL}/json/2/<model>/<method>, header
    "Authorization: bearer <API key>", named arguments in the JSON body.
  - XML-RPC (Odoo <= 21, deprecated since 19, removal planned in 22):
    {ODOO_URL}/xmlrpc/2/common + /xmlrpc/2/object, login + API key.
  ODOO_API=auto (default) tries JSON-2 then falls back to XML-RPC.

Usage:
    python3 odoo.py status
    python3 odoo.py stages
    python3 odoo.py pipeline [--stage "Qualifié"] [--limit 50]
    python3 odoo.py find [--email x@y.ch] [--name "Jeanne Martin"] [--company "Géo-Conseil"]
    python3 odoo.py create-lead --from-json .tmp/leads/<slug>/combined.json [--stage "Nouveau"] [--tags "AIGORA,Prospection"] --confirm
    python3 odoo.py create-lead --name "Géo-Conseil - Jeanne Martin" --contact "Jeanne Martin" \
        --company "Géo-Conseil SA" --email j@geo.ch [--phone ..] [--function ..] [--website ..] \
        [--description "..."] [--revenue 5000] [--type opportunity|lead] --confirm
    python3 odoo.py move --id 42 --stage "Proposition" --confirm
    python3 odoo.py note --id 42 --text "Relancé par mail" --confirm

Writes (create-lead, move, note) are refused without --confirm. create-lead also refuses
a probable duplicate (same email, or same contact + company) unless --allow-duplicate.

.env: ODOO_URL, ODOO_API_KEY, and for XML-RPC or multi-database servers ODOO_DB,
ODOO_LOGIN (user login, usually the email). Standard library only.
"""

import argparse
import html
import json
import os
import sys
import urllib.error
import urllib.request
import xmlrpc.client
from pathlib import Path

LEAD_FIELDS = ["name", "type", "partner_name", "contact_name", "email_from", "phone",
               "function", "stage_id", "expected_revenue", "probability", "user_id",
               "create_date", "active"]


def project_root() -> Path:
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "CLAUDE.md").exists():
            return p
        p = p.parent
    raise RuntimeError("AIGORA project root not found")


ROOT = project_root()


def load_env():
    f = ROOT / ".env"
    if not f.exists():
        return
    for raw in f.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if " #" in v:
            v = v.split(" #", 1)[0]
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k.startswith("ODOO_") and k not in os.environ:
            os.environ[k] = v


def out(payload, code=0):
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    sys.exit(code)


def fail(msg, **kw):
    out({"success": False, "error": msg, **kw}, 1)


class OdooError(Exception):
    pass


class Odoo:
    def __init__(self):
        self.url = os.environ.get("ODOO_URL", "").rstrip("/")
        self.key = os.environ.get("ODOO_API_KEY", "")
        self.db = os.environ.get("ODOO_DB", "")
        self.login = os.environ.get("ODOO_LOGIN", "")
        self.mode = os.environ.get("ODOO_API", "auto").lower()
        if not self.url:
            fail("ODOO_URL missing in .env", missing="ODOO_URL")
        if not self.key:
            fail("ODOO_API_KEY missing in .env", missing="ODOO_API_KEY")
        self.uid = None
        self.protocol = None

    # ---- JSON-2 -------------------------------------------------------------
    def _json2(self, model, method, ids=None, **kwargs):
        body = dict(kwargs)
        if ids:
            body["ids"] = list(ids)
        headers = {"Authorization": f"bearer {self.key}", "Content-Type": "application/json; charset=utf-8"}
        if self.db:
            headers["X-Odoo-Database"] = self.db
        req = urllib.request.Request(f"{self.url}/json/2/{model}/{method}",
                                     data=json.dumps(body).encode(), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")[:600]
            try:
                msg = json.loads(text).get("message") or text
            except Exception:
                msg = text
            if e.code == 404 and "/json/2" in e.url and ("Did you mean" not in msg and "does not exist" not in msg):
                raise OdooError("JSON2_NOT_AVAILABLE")
            if e.code in (401, 403):
                raise OdooError(f"Access refused ({e.code}): check ODOO_API_KEY (and ODOO_DB). {msg}")
            raise OdooError(f"Odoo error {e.code}: {msg}")
        except urllib.error.URLError as e:
            raise OdooError(f"Odoo unreachable at {self.url}: {e.reason}")
        except (OSError, ValueError) as e:  # dropped connection, invalid answer...
            raise OdooError(f"Odoo connection problem at {self.url}: {e}")

    # ---- XML-RPC ------------------------------------------------------------
    def _xmlrpc(self, model, method, ids=None, **kwargs):
        if not (self.db and self.login):
            raise OdooError("XML-RPC needs ODOO_DB and ODOO_LOGIN in .env (Odoo < 19).")
        if self.uid is None:
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common", allow_none=True)
            try:
                self.uid = common.authenticate(self.db, self.login, self.key, {})
            except (OSError, xmlrpc.client.ProtocolError, xmlrpc.client.Fault) as e:
                raise OdooError(f"Odoo unreachable or refused at {self.url}: {e}")
            if not self.uid:
                raise OdooError("XML-RPC authentication failed: check ODOO_DB, ODOO_LOGIN, ODOO_API_KEY.")
        models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object", allow_none=True)
        args = [list(ids)] if ids else []
        try:
            return models.execute_kw(self.db, self.uid, self.key, model, method, args, kwargs)
        except xmlrpc.client.Fault as f:
            raise OdooError(f"Odoo error: {f.faultString.strip().splitlines()[-1][:400]}")
        except (OSError, xmlrpc.client.ProtocolError) as e:
            raise OdooError(f"Odoo connection problem at {self.url}: {e}")

    def call(self, model, method, ids=None, **kwargs):
        if self.protocol == "xmlrpc" or self.mode == "xmlrpc":
            self.protocol = "xmlrpc"
            return self._xmlrpc(model, method, ids, **kwargs)
        try:
            res = self._json2(model, method, ids, **kwargs)
            self.protocol = "json2"
            return res
        except OdooError as e:
            if str(e) == "JSON2_NOT_AVAILABLE" and self.mode == "auto":
                self.protocol = "xmlrpc"
                return self._xmlrpc(model, method, ids, **kwargs)
            raise

    # ---- helpers ------------------------------------------------------------
    def stage_id(self, name):
        rows = self.call("crm.stage", "search_read", domain=[["name", "ilike", name]],
                         fields=["id", "name"], limit=5)
        if not rows:
            all_stages = [s["name"] for s in self.call("crm.stage", "search_read", domain=[], fields=["name"])]
            raise OdooError(f"Stage not found: {name}. Available: {', '.join(all_stages)}")
        exact = [r for r in rows if r["name"].lower() == name.lower()]
        return (exact or rows)[0]["id"]

    def tag_ids(self, names):
        ids = []
        for n in [t.strip() for t in names.split(",") if t.strip()]:
            found = self.call("crm.tag", "search_read", domain=[["name", "=", n]], fields=["id"], limit=1)
            ids.append(found[0]["id"] if found else self.call("crm.tag", "create", vals_list=[{"name": n}])[0])
        return ids

    def duplicates(self, email=None, contact=None, company=None):
        domains = []
        if email:
            domains.append([["email_from", "=ilike", email.strip()]])
        if contact and company:
            domains.append([["contact_name", "ilike", contact], ["partner_name", "ilike", company]])
        found = {}
        for d in domains:
            for r in self.call("crm.lead", "search_read", domain=d, fields=LEAD_FIELDS, limit=20,
                               context={"active_test": False}):
                found[r["id"]] = r
        return list(found.values())


def lead_from_combined(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    prof = d.get("profile_data") or {}
    exp = (prof.get("experiences") or [{}])[0] or {}
    dms = (d.get("dm_sequence") or {}).get("data", {}) or {}
    review = (d.get("dm_quality_review") or {}).get("data", {}) or {}
    lp = (d.get("lead_profile") or {}).get("data", {}) or {}
    contact = prof.get("full_name", "")
    company = prof.get("company") or exp.get("company", "")
    parts = []
    if d.get("linkedin_url"):
        parts.append(f"<p><b>LinkedIn :</b> {html.escape(d['linkedin_url'])}</p>")
    for label, key in (("Profil", "person_profile"), ("Entreprise", "company_profile")):
        if lp.get(key):
            parts.append(f"<p><b>{label} :</b> {html.escape(str(lp[key]))}</p>")
    hook = dms.get("hook_selected") or {}
    if isinstance(hook, dict) and hook.get("fact"):
        parts.append(f"<p><b>Accroche :</b> {html.escape(hook['fact'])}</p>")
    dm1 = (dms.get("dm1") or {}).get("message")
    if dm1:
        parts.append(f"<p><b>Message 1 proposé :</b> {html.escape(dm1)}</p>")
    if review.get("overall_quality_score") is not None:
        parts.append(f"<p><b>Score qualité :</b> {review.get('overall_quality_score')} "
                     f"({html.escape(str(review.get('approval_recommendation', '')))})</p>")
    parts.append("<p><i>Créé par AIGORA (research-lead).</i></p>")
    return {
        "name": f"{company} - {contact}".strip(" -") or "Lead AIGORA",
        "contact_name": contact or False,
        "partner_name": company or False,
        "function": exp.get("title") or prof.get("headline") or False,
        "email_from": prof.get("email") or False,
        "website": False,
        "description": "".join(parts),
    }


def main():
    ap = argparse.ArgumentParser(description="Odoo CRM connector (JSON-2 / XML-RPC)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("stages")
    p = sub.add_parser("pipeline"); p.add_argument("--stage"); p.add_argument("--limit", type=int, default=50)
    p.add_argument("--all-types", action="store_true", help="include leads, not only opportunities")
    f = sub.add_parser("find"); f.add_argument("--email"); f.add_argument("--name"); f.add_argument("--company")
    c = sub.add_parser("create-lead")
    for a in ("from-json", "name", "contact", "company", "email", "phone", "function", "website",
              "description", "stage", "tags"):
        c.add_argument(f"--{a}")
    c.add_argument("--revenue", type=float)
    c.add_argument("--type", choices=["opportunity", "lead"], default="opportunity")
    c.add_argument("--confirm", action="store_true"); c.add_argument("--allow-duplicate", action="store_true")
    m = sub.add_parser("move"); m.add_argument("--id", type=int, required=True); m.add_argument("--stage", required=True)
    m.add_argument("--confirm", action="store_true")
    n = sub.add_parser("note"); n.add_argument("--id", type=int, required=True); n.add_argument("--text", required=True)
    n.add_argument("--confirm", action="store_true")
    args = ap.parse_args()

    load_env()
    odoo = Odoo()
    try:
        if args.cmd == "status":
            stages = odoo.call("crm.stage", "search_read", domain=[], fields=["name"], limit=20)
            out({"success": True, "url": odoo.url, "protocol": odoo.protocol,
                 "crm_stages": [s["name"] for s in stages]})
        if args.cmd == "stages":
            out({"success": True, "stages": odoo.call("crm.stage", "search_read", domain=[],
                                                      fields=["id", "name", "sequence"], order="sequence")})
        if args.cmd == "pipeline":
            domain = [] if args.all_types else [["type", "=", "opportunity"]]
            if args.stage:
                domain.append(["stage_id", "=", odoo.stage_id(args.stage)])
            rows = odoo.call("crm.lead", "search_read", domain=domain, fields=LEAD_FIELDS,
                             limit=args.limit, order="create_date desc")
            out({"success": True, "protocol": odoo.protocol, "count": len(rows), "leads": rows})
        if args.cmd == "find":
            if not (args.email or args.name or args.company):
                fail("Give --email, --name and/or --company")
            rows = odoo.duplicates(args.email, args.name, args.company) if (args.email or (args.name and args.company)) else []
            if not rows:
                domain = ["|", ["contact_name", "ilike", args.name or args.company],
                          ["partner_name", "ilike", args.company or args.name]]
                rows = odoo.call("crm.lead", "search_read", domain=domain, fields=LEAD_FIELDS, limit=20,
                                 context={"active_test": False})
            out({"success": True, "count": len(rows), "leads": rows})
        if args.cmd == "create-lead":
            vals = lead_from_combined(Path(args.from_json)) if args.from_json else {}
            for field, value in (("name", args.name), ("contact_name", args.contact), ("partner_name", args.company),
                                 ("email_from", args.email), ("phone", args.phone), ("function", args.function),
                                 ("website", args.website), ("expected_revenue", args.revenue)):
                if value not in (None, ""):
                    vals[field] = value
            if args.description:
                vals["description"] = "".join(f"<p>{html.escape(l)}</p>" for l in args.description.splitlines())
            if not vals.get("name"):
                vals["name"] = f"{vals.get('partner_name') or ''} - {vals.get('contact_name') or ''}".strip(" -")
            if not vals.get("name"):
                fail("A lead needs at least --name, --contact/--company or --from-json")
            vals["type"] = args.type
            vals = {k: v for k, v in vals.items() if v not in (False, None, "")}
            dups = odoo.duplicates(vals.get("email_from"), vals.get("contact_name"), vals.get("partner_name"))
            if dups and not args.allow_duplicate:
                fail("Probable duplicate already in Odoo: no lead created.", duplicates=dups,
                     hint="Show them to the user; rerun with --allow-duplicate only if they confirm it is a different lead.")
            if args.stage:
                vals["stage_id"] = odoo.stage_id(args.stage)
            if args.tags:
                if not args.confirm:
                    vals["tag_ids"] = f"[tags to create/link: {args.tags}]"
                else:
                    vals["tag_ids"] = [[6, 0, odoo.tag_ids(args.tags)]]
            if not args.confirm:
                out({"success": False, "needs_confirmation": True, "would_create": vals,
                     "error": "Nothing created. Show this to the user, then rerun with --confirm."}, 1)
            new_id = odoo.call("crm.lead", "create", vals_list=[vals])[0]
            link = f"{odoo.url}/web#id={new_id}&model=crm.lead&view_type=form"
            out({"success": True, "created_id": new_id, "protocol": odoo.protocol, "url": link})
        if args.cmd == "move":
            sid = odoo.stage_id(args.stage)
            if not args.confirm:
                out({"success": False, "needs_confirmation": True,
                     "error": f"Would move lead {args.id} to stage id {sid}. Rerun with --confirm."}, 1)
            odoo.call("crm.lead", "write", ids=[args.id], vals={"stage_id": sid})
            out({"success": True, "moved": args.id, "stage_id": sid})
        if args.cmd == "note":
            if not args.confirm:
                out({"success": False, "needs_confirmation": True,
                     "error": "Would add an internal note. Rerun with --confirm."}, 1)
            body = "".join(f"<p>{html.escape(l)}</p>" for l in args.text.splitlines())
            odoo.call("crm.lead", "message_post", ids=[args.id], body=body,
                      message_type="comment", subtype_xmlid="mail.mt_note")
            out({"success": True, "noted": args.id})
    except OdooError as e:
        fail(str(e), protocol=odoo.protocol)
    except Exception as e:  # never show a raw traceback to the user
        fail(f"Unexpected error: {type(e).__name__}: {e}", protocol=odoo.protocol)


if __name__ == "__main__":
    main()
