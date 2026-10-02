#!/usr/bin/env python3
"""
kSuite Calendar (Infomaniak) over CalDAV.

Usage:
    python3 calendar_events.py calendars
    python3 calendar_events.py list --days 7                 # from today
    python3 calendar_events.py list --start 2026-10-05 --end 2026-10-10 --calendar "Travail"
    python3 calendar_events.py create --summary "Point client" \
        --start "2026-10-06 14:00" --end "2026-10-06 15:00" --calendar "Travail" \
        [--location "Visio kMeet"] [--description "..."]

Tasks (CalDAV VTODO, the "tasks" of Infomaniak Calendar; they sync to phones
with kSync + jtx Board on Android, or the iOS Reminders CalDAV account):
    python3 calendar_events.py tasks [--all] [--calendar "Travail"]
    python3 calendar_events.py task-add --summary "Rappeler Acme" [--due 2026-10-09] \
        [--priority high|medium|low] [--description "..."] [--calendar "Travail"]
    python3 calendar_events.py task-done --uid <uid>

Needs in .env: KSUITE_DAV_USER (the short CalDAV username, e.g. AB12345,
see config.infomaniak.com > My Calendar > Manual synchronization) and
KSUITE_DAV_PASSWORD (an application password if 2FA is on).
Needs: pip install caldav
Times without timezone are interpreted in TIMEZONE from .env / preferences.
"""

import argparse
from datetime import date, datetime, timedelta

import ksuite_env as K

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None


def tz():
    name = K.get("TIMEZONE") or "Europe/Paris"
    return ZoneInfo(name) if ZoneInfo else None


def parse_dt(value: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(tzinfo=tz())
        except ValueError:
            continue
    K.fail(f"Unrecognised date: {value} (use YYYY-MM-DD or 'YYYY-MM-DD HH:MM')")


def connect():
    try:
        import caldav
    except ImportError:
        K.fail("Python package 'caldav' missing. Run: pip install caldav")
    K.load_env()
    client = caldav.DAVClient(
        url=K.get("KSUITE_CALDAV_URL"),
        username=K.get("KSUITE_DAV_USER", required=True),
        password=K.get("KSUITE_DAV_PASSWORD", required=True),
    )
    try:
        return client.principal()
    except Exception as e:
        K.fail(f"CalDAV connection failed: {e}. Check KSUITE_DAV_USER (short username, not the email).")


def pick_calendar(principal, name):
    cals = principal.calendars()
    if not cals:
        K.fail("No calendar found on this account.")
    if not name:
        return cals
    for c in cals:
        if (cal_name(c) or "").lower() == name.lower():
            return [c]
    K.fail(f"Calendar not found: {name}", available=[cal_name(c) for c in cals])


def cal_name(c):
    getter = getattr(c, "get_display_name", None)
    try:
        return getter() if getter else c.name
    except Exception:
        return c.name


def as_iso(v):
    v = getattr(v, "dt", v)
    return v.isoformat() if isinstance(v, (datetime, date)) else str(v)


def cmd_calendars(_args):
    principal = connect()
    K.ok(calendars=[{"name": cal_name(c), "url": str(c.url)} for c in principal.calendars()])


def cmd_list(args):
    principal = connect()
    start = parse_dt(args.start) if args.start else datetime.now(tz()).replace(hour=0, minute=0, second=0, microsecond=0)
    end = parse_dt(args.end) if args.end else start + timedelta(days=args.days)
    events = []
    for cal in pick_calendar(principal, args.calendar or None):
        try:
            found = cal.search(start=start, end=end, event=True, expand=True)
        except Exception:
            found = cal.date_search(start=start, end=end, expand=True)
        for ev in found:
            comp = ev.icalendar_component
            events.append({
                "calendar": cal_name(cal),
                "summary": str(comp.get("summary", "")),
                "start": as_iso(comp.get("dtstart")),
                "end": as_iso(comp.get("dtend")) if comp.get("dtend") else None,
                "location": str(comp.get("location", "")),
                "description": str(comp.get("description", ""))[:1000],
                "uid": str(comp.get("uid", "")),
            })
    events.sort(key=lambda e: e["start"])
    K.ok(start=start.isoformat(), end=end.isoformat(), count=len(events), events=events)


def cmd_create(args):
    principal = connect()
    cal = pick_calendar(principal, args.calendar)[0] if args.calendar else principal.calendars()[0]
    start, end = parse_dt(args.start), parse_dt(args.end)
    if end <= start:
        K.fail("--end must be after --start")
    kwargs = {"dtstart": start, "dtend": end, "summary": args.summary}
    if args.location:
        kwargs["location"] = args.location
    if args.description:
        kwargs["description"] = args.description
    cal.save_event(**kwargs)
    K.ok(created={"calendar": cal_name(cal), **{k: as_iso(v) for k, v in kwargs.items()}})


PRIORITY = {"high": 1, "medium": 5, "low": 9}


def supports_todo(cal):
    try:
        return "VTODO" in cal.get_supported_components()
    except Exception:
        return True  # unknown: assume yes


def task_calendars(principal, name):
    if name:
        return pick_calendar(principal, name)
    cals = [c for c in principal.calendars() if supports_todo(c)]
    if not cals:
        K.fail("No calendar accepting tasks (VTODO) on this account.")
    return cals


def todo_dict(cal, todo):
    comp = todo.icalendar_component
    prio = comp.get("priority")
    prio = int(prio) if prio not in (None, "") else None
    label = None if not prio else ("high" if prio <= 4 else "medium" if prio == 5 else "low")
    return {
        "calendar": cal_name(cal),
        "uid": str(comp.get("uid", "")),
        "summary": str(comp.get("summary", "")),
        "due": as_iso(comp.get("due")) if comp.get("due") else None,
        "priority": label,
        "status": str(comp.get("status", "NEEDS-ACTION")),
        "description": str(comp.get("description", ""))[:500],
    }


def cmd_tasks(args):
    principal = connect()
    tasks = []
    for cal in task_calendars(principal, args.calendar):
        try:
            todos = cal.todos(include_completed=args.all)
        except Exception:
            continue
        tasks += [todo_dict(cal, t) for t in todos]
    tasks.sort(key=lambda t: (t["due"] is None, t["due"] or "", t["summary"]))
    K.ok(count=len(tasks), tasks=tasks)


def cmd_task_add(args):
    principal = connect()
    cal = task_calendars(principal, args.calendar)[0]
    kwargs = {"summary": args.summary}
    if args.due:
        due = parse_dt(args.due)
        kwargs["due"] = due.date() if len(args.due) == 10 else due
    if args.priority:
        kwargs["priority"] = PRIORITY[args.priority]
    if args.description:
        kwargs["description"] = args.description
    todo = cal.save_todo(**kwargs)
    K.ok(created=todo_dict(cal, todo))


def cmd_task_done(args):
    principal = connect()
    for cal in task_calendars(principal, None):
        try:
            todos = cal.todos(include_completed=True)
        except Exception:
            continue
        for t in todos:
            if str(t.icalendar_component.get("uid", "")) == args.uid:
                t.complete()
                K.ok(completed=todo_dict(cal, t))
    K.fail(f"Task not found: {args.uid}")


def main():
    ap = argparse.ArgumentParser(description="kSuite Calendar and tasks via CalDAV")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("calendars")
    p = sub.add_parser("list")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--calendar")
    c = sub.add_parser("create")
    c.add_argument("--summary", required=True)
    c.add_argument("--start", required=True)
    c.add_argument("--end", required=True)
    c.add_argument("--calendar")
    c.add_argument("--location")
    c.add_argument("--description")
    t = sub.add_parser("tasks")
    t.add_argument("--all", action="store_true", help="include completed tasks")
    t.add_argument("--calendar")
    ta = sub.add_parser("task-add")
    ta.add_argument("--summary", required=True)
    ta.add_argument("--due")
    ta.add_argument("--priority", choices=sorted(PRIORITY))
    ta.add_argument("--description")
    ta.add_argument("--calendar")
    td = sub.add_parser("task-done")
    td.add_argument("--uid", required=True)
    args = ap.parse_args()
    {"calendars": cmd_calendars, "list": cmd_list, "create": cmd_create, "tasks": cmd_tasks,
     "task-add": cmd_task_add, "task-done": cmd_task_done}[args.cmd](args)


if __name__ == "__main__":
    main()
