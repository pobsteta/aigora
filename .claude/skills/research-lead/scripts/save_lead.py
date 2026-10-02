#!/usr/bin/env python3
"""
Append (or update) a researched lead in data/leads.csv.

Usage:
    python3 save_lead.py --data .tmp/leads/jane-doe/combined.json
    python3 save_lead.py --list

The CSV uses ";" as separator and UTF-8 with BOM so it opens cleanly in
LibreOffice / Excel with French settings, and in R with
read.csv2("data/leads.csv", fileEncoding = "UTF-8-BOM").
Standard library only.
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CSV_PATH = PROJECT_ROOT / "data" / "leads.csv"
FIELDS = ["date", "full_name", "company", "role", "linkedin_url", "archetype",
          "hook", "dm1", "quality_score", "approval", "status", "report_json"]


def out(payload, code=0):
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(code)


def data_of(block):
    if isinstance(block, dict):
        return block.get("data", block) or {}
    return {}


def row_from(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    profile = d.get("profile_data", {}) or {}
    exp = (profile.get("experiences") or [{}])[0] or {}
    dms = data_of(d.get("dm_sequence"))
    review = data_of(d.get("dm_quality_review"))
    hook = dms.get("hook_selected") or {}
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "full_name": profile.get("full_name", ""),
        "company": profile.get("company", "") or exp.get("company", ""),
        "role": exp.get("title", "") or profile.get("headline", ""),
        "linkedin_url": d.get("linkedin_url", ""),
        "archetype": dms.get("archetype", ""),
        "hook": hook.get("fact", "") if isinstance(hook, dict) else str(hook),
        "dm1": (dms.get("dm1") or {}).get("message", ""),
        "quality_score": review.get("overall_quality_score", ""),
        "approval": review.get("approval_recommendation", ""),
        "status": "to_review",
        "report_json": str(path),
    }


def read_rows():
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def write_rows(rows):
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    rows = read_rows()
    if args.list:
        out({"success": True, "count": len(rows), "leads": rows})
    if not args.data:
        out({"success": False, "error": "Give --data <combined.json> or --list"}, 1)

    try:
        new = row_from(Path(args.data))
    except Exception as e:
        out({"success": False, "error": f"Cannot read {args.data}: {e}"}, 1)

    key = (new["linkedin_url"] or new["full_name"] + "|" + new["company"]).lower()
    action = "added"
    for i, r in enumerate(rows):
        if (r.get("linkedin_url") or r.get("full_name", "") + "|" + r.get("company", "")).lower() == key:
            new["status"] = r.get("status") or new["status"]
            rows[i] = new
            action = "updated"
            break
    else:
        rows.append(new)
    write_rows(rows)
    out({"success": True, "action": action, "csv": str(CSV_PATH), "lead": new["full_name"]})


if __name__ == "__main__":
    main()
