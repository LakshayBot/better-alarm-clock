# Alarm Clock (Python CLI)

A small command-line alarm clock built as a take-home exercise. Python 3.8+,
standard library only, no database, no web UI.

## Quickstart

```bash
python3 alarm.py set 07:30 --label "Standup"     # 24h format
python3 alarm.py set 7:30am --daily              # 12h format, repeats
python3 alarm.py list                            # show all alarms
python3 alarm.py snooze 1 --minutes 5            # push alarm 1 back 5 min
python3 alarm.py dismiss 1                       # remove alarm 1
python3 alarm.py run                             # watch + ring
```

Run the tests:

```bash
python3 -m unittest -v
```

## How it works

- **Store**: alarms live in `alarms.json` next to the script. Each entry is
  `{time, label, daily}`.
- **Ring**: `run` polls the clock every second; when the wall clock matches an
  alarm, it rings (terminal bell + message) and asks for `s`nooze or `d`ismiss.
- **Snooze**: adds 5 minutes to the alarm and saves it back.
- **Daily alarms** are kept after ringing; one-shot alarms are removed on
  dismiss.

## Design decisions and trade-offs

1. **JSON file store instead of SQLite.** The brief says no database, and a
   single-user CLI does not need transactions. A flat file is inspectable with
   `cat`, has zero dependencies, and survives restarts. Trade-off: no locking
   for concurrent writers (not a real scenario here).

2. **Poll every second instead of sleeping until the next alarm.** Sleeping
   until the next fire time is more efficient, but it makes the watcher blind
   to changes (a snooze or a new alarm set from another terminal would not be
   picked up). A 1-second poll costs almost nothing and keeps the loop simple
   and responsive. This was a deliberate simplicity-over-cleverness call.

3. **Wall-clock local time only.** The spec does not mention timezones or DST;
   adding them would multiply complexity for a 30-minute exercise. The
   `next_occurrence` helper is timezone-naive by design and covered by tests.

4. **Blocking prompt when an alarm rings.** `input()` is the simplest possible
   snooze/dismiss UX in a terminal. Trade-off: the loop pauses while the alarm
   is ringing (acceptable for a single-user CLI).

5. **Pure functions separated from I/O.** `parse_time`, `format_time`,
   `add_minutes` and `next_occurrence` contain no side effects, so they are
   cheap to unit test. The command handlers stay thin.

## Deliberately cut (and why)

- Web UI, desktop notifications, audio files - out of scope per the brief.
- Weekday recurrence (Mon-Fri only) - `--daily` covers the common case; a
  recurrence grammar was not worth the extra surface in 30 minutes.
- Editing an existing alarm - `dismiss` + `set` covers it.
- Timezone/DST handling - see decision 3.

## What I would add next

- `edit` command and a `--at HH:MM` one-shot timer mode.
- Weekday recurrence flags (`--mon --wed --fri`).
- A `--daemon`/background mode with desktop notifications.
- Configurable snooze length stored per alarm.

## Project layout

```
alarm.py        # CLI, scheduler loop, persistence
test_alarm.py   # unit tests (parsing, rollover, next-occurrence, store)
README.md       # this file
```
