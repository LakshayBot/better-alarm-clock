#!/usr/bin/env python3
"""A small CLI alarm clock.

Built for the Better (BTR Group) take-home exercise: Python CLI only,
no web UI, no database, no third-party dependencies.

Usage:
    python3 alarm.py set 07:30 --label "Standup"
    python3 alarm.py set 7:30am --daily
    python3 alarm.py list
    python3 alarm.py snooze 1 --minutes 5
    python3 alarm.py dismiss 1
    python3 alarm.py run
"""

import argparse
import json
import os
import time
from datetime import datetime, timedelta

STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarms.json")
SNOOZE_MINUTES = 5
POLL_SECONDS = 1


# ---------------------------------------------------------------------------
# Pure helpers (unit-tested in test_alarm.py)
# ---------------------------------------------------------------------------

def parse_time(value):
    """Parse 'HH:MM' (24h), '7:30am' or '7am' into an (hour, minute) tuple."""
    text = value.strip().lower().replace(" ", "")
    for fmt in ("%H:%M", "%I:%M%p", "%I%p"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.hour, dt.minute
        except ValueError:
            continue
    raise ValueError(f"Unrecognised time: {value!r} (try 07:30 or 7:30am)")


def format_time(hour, minute):
    """Render an (hour, minute) tuple as 'HH:MM'."""
    return f"{hour:02d}:{minute:02d}"


def next_occurrence(hour, minute, now=None):
    """Next datetime strictly after `now` that matches hour:minute.

    Returns today's slot if it is still ahead, otherwise tomorrow's.
    """
    now = now or datetime.now()
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def add_minutes(hour, minute, minutes):
    """Add minutes to a time, rolling over midnight correctly."""
    base = datetime(2000, 1, 1, hour, minute)
    shifted = base + timedelta(minutes=minutes)
    return shifted.hour, shifted.minute


# ---------------------------------------------------------------------------
# Persistence: one small JSON file next to the script
# ---------------------------------------------------------------------------

def load_alarms():
    if not os.path.exists(STORE):
        return []
    with open(STORE, "r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError:
            return []


def save_alarms(alarms):
    with open(STORE, "w", encoding="utf-8") as fh:
        json.dump(alarms, fh, indent=2)


def _label_suffix(alarm):
    return f" - {alarm['label']}" if alarm.get("label") else ""


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_set(args):
    hour, minute = parse_time(args.time)
    alarms = load_alarms()
    alarms.append({
        "time": format_time(hour, minute),
        "label": args.label or "",
        "daily": bool(args.daily),
    })
    save_alarms(alarms)
    extras = (f" ({args.label})" if args.label else "") + (" [daily]" if args.daily else "")
    print(f"Alarm set for {format_time(hour, minute)}{extras}")


def cmd_list(args):
    alarms = load_alarms()
    if not alarms:
        print("No alarms set.")
        return
    for i, alarm in enumerate(alarms, start=1):
        daily = " [daily]" if alarm.get("daily") else ""
        print(f"{i}. {alarm['time']}{_label_suffix(alarm)}{daily}")


def cmd_dismiss(args):
    alarms = load_alarms()
    if not 1 <= args.index <= len(alarms):
        print("No alarm with that index. Run `python3 alarm.py list` first.")
        return
    removed = alarms.pop(args.index - 1)
    save_alarms(alarms)
    print(f"Dismissed {removed['time']}{_label_suffix(removed)}")


def cmd_snooze(args):
    alarms = load_alarms()
    if not 1 <= args.index <= len(alarms):
        print("No alarm with that index. Run `python3 alarm.py list` first.")
        return
    alarm = alarms[args.index - 1]
    hour, minute = map(int, alarm["time"].split(":"))
    alarm["time"] = format_time(*add_minutes(hour, minute, args.minutes))
    save_alarms(alarms)
    print(f"Snoozed to {alarm['time']} (+{args.minutes} min)")


def cmd_run(args):
    print("Watching alarms. Press Ctrl+C to stop.")
    fired = set()
    while True:
        alarms = load_alarms()
        now = datetime.now()
        for i, alarm in enumerate(alarms):
            key = (i, alarm["time"])
            if key in fired:
                continue
            hour, minute = map(int, alarm["time"].split(":"))
            if now.hour == hour and now.minute == minute and now.second < 2:
                print(f"\a\aALARM {alarm['time']}{_label_suffix(alarm)}")
                answer = input("Snooze 5 min? [s]nooze / [d]ismiss: ").strip().lower()
                if answer.startswith("s"):
                    alarms[i]["time"] = format_time(*add_minutes(hour, minute, SNOOZE_MINUTES))
                    save_alarms(alarms)
                    print(f"Snoozed to {alarms[i]['time']}")
                elif answer.startswith("d"):
                    if not alarm.get("daily"):
                        alarms.pop(i)
                        save_alarms(alarms)
                    print("Dismissed.")
                fired.add(key)
        time.sleep(POLL_SECONDS)


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(description="A tiny CLI alarm clock.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set", help="add an alarm (e.g. set 07:30 or set 7:30am)")
    p_set.add_argument("time")
    p_set.add_argument("--label", default="")
    p_set.add_argument("--daily", action="store_true", help="keep the alarm after it rings")
    p_set.set_defaults(func=cmd_set)

    p_list = sub.add_parser("list", help="show all alarms")
    p_list.set_defaults(func=cmd_list)

    p_dismiss = sub.add_parser("dismiss", help="remove alarm by index")
    p_dismiss.add_argument("index", type=int)
    p_dismiss.set_defaults(func=cmd_dismiss)

    p_snooze = sub.add_parser("snooze", help="push an alarm back by N minutes")
    p_snooze.add_argument("index", type=int)
    p_snooze.add_argument("--minutes", type=int, default=SNOOZE_MINUTES)
    p_snooze.set_defaults(func=cmd_snooze)

    p_run = sub.add_parser("run", help="watch alarms and ring when they fire")
    p_run.set_defaults(func=cmd_run)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except ValueError as exc:
        raise SystemExit(f"Error: {exc}")


if __name__ == "__main__":
    main()
