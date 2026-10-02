#!/usr/bin/env python3
"""
Report what is configured for kSuite (Infomaniak), and optionally test it.

Usage:
    python3 check_status.py            # presence of settings only (no network)
    python3 check_status.py --test     # also tries IMAP, SMTP and CalDAV logins

Never prints secrets. Never sends any message.
"""

import argparse
import imaplib
import importlib.util
import shutil
import smtplib
import subprocess

import ksuite_env as K

BLOCKS = {
    "mail_imap_smtp": ["KSUITE_MAIL_USER", "KSUITE_MAIL_PASSWORD"],
    "calendar_tasks_contacts_dav": ["KSUITE_DAV_USER", "KSUITE_DAV_PASSWORD"],
    "kdrive_local_folder": ["KDRIVE_LOCAL_PATH"],
    "kchat_webhook": ["KCHAT_WEBHOOK_URL"],
    "api_token_for_mcp": ["INFOMANIAK_TOKEN"],
    "kdrive_mcp": ["KDRIVE_ID"],
    "kchat_mcp": ["KCHAT_TEAM_NAME"],
    "odoo_crm": ["ODOO_URL", "ODOO_API_KEY"],
}


def registered_mcp():
    claude = shutil.which("claude")
    if not claude:
        return None
    try:
        out = subprocess.run([claude, "mcp", "list"], capture_output=True, text=True,
                             timeout=60, cwd=K.PROJECT_ROOT).stdout
    except Exception:
        return None
    return sorted({line.split(":")[0].strip() for line in out.splitlines()
                   if line.strip().startswith(("ksuite-", "searxng", "r-session", "qgis"))})


def test_carddav():
    import contacts
    dav = contacts.DAV(K.get("KSUITE_CARDDAV_URL") or K.get("KSUITE_CALDAV_URL"),
                       K.get("KSUITE_DAV_USER"), K.get("KSUITE_DAV_PASSWORD"), fatal=False)
    return [b["name"] for b in dav.address_books()]


def test_imap():
    imap = imaplib.IMAP4_SSL(K.get("KSUITE_IMAP_HOST"), int(K.get("KSUITE_IMAP_PORT")))
    imap.login(K.get("KSUITE_MAIL_USER"), K.get("KSUITE_MAIL_PASSWORD"))
    imap.logout()


def test_smtp():
    port = int(K.get("KSUITE_SMTP_PORT"))
    host = K.get("KSUITE_SMTP_HOST")
    server = smtplib.SMTP_SSL(host, port, timeout=20) if port == 465 else smtplib.SMTP(host, port, timeout=20)
    if port != 465:
        server.starttls()
    server.login(K.get("KSUITE_MAIL_USER"), K.get("KSUITE_MAIL_PASSWORD"))
    server.quit()


def test_caldav():
    import caldav
    client = caldav.DAVClient(url=K.get("KSUITE_CALDAV_URL"),
                              username=K.get("KSUITE_DAV_USER"),
                              password=K.get("KSUITE_DAV_PASSWORD"))
    cals = client.principal().calendars()
    return [(c.get_display_name() if hasattr(c, 'get_display_name') else c.name) for c in cals]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()
    K.load_env()

    configured = {name: all(K.get(k) for k in keys) for name, keys in BLOCKS.items()}
    tools = {
        "python_caldav": importlib.util.find_spec("caldav") is not None,
        "npx": shutil.which("npx") is not None,
        "claude_cli": shutil.which("claude") is not None,
        "quarto": shutil.which("quarto") is not None,
        "uvx_for_qgis": shutil.which("uvx") is not None,
        "rscript": bool(K.get("AIGORA_RSCRIPT") or shutil.which("Rscript")),
    }
    kdrive_path = K.get("KDRIVE_LOCAL_PATH")
    if kdrive_path:
        from pathlib import Path
        configured["kdrive_local_folder"] = Path(kdrive_path).is_dir()
    configured["community_mcp_opt_in"] = K.get("KSUITE_EXTRA_MCP") == "1"
    configured["r_session_mcp_opt_in"] = K.get("AIGORA_R_MCP") == "1"
    configured["qgis_mcp_opt_in"] = K.get("AIGORA_QGIS_MCP") == "1"
    result = {"configured": configured, "tools": tools, "mcp_registered": registered_mcp()}

    if args.test:
        tests = {}
        for name, block, fn in (("imap", "mail_imap_smtp", test_imap),
                                ("smtp", "mail_imap_smtp", test_smtp),
                                ("caldav", "calendar_tasks_contacts_dav", test_caldav),
                                ("carddav", "calendar_tasks_contacts_dav", test_carddav)):
            if not configured[block]:
                tests[name] = "not configured"
                continue
            if name == "caldav" and not tools["python_caldav"]:
                tests[name] = "pip install caldav"
                continue
            try:
                out = fn()
                tests[name] = {"ok": True, "found": out} if out else {"ok": True}
            except Exception as e:
                tests[name] = {"ok": False, "error": str(e)[:300]}
        result["tests"] = tests
        if any(isinstance(t, dict) and not t.get("ok") for t in tests.values()):
            K.fail("At least one kSuite connection test failed", **result)

    K.ok(**result)


if __name__ == "__main__":
    main()
