"""Unit tests for alarm.py - run with: python3 -m unittest -v"""

import os
import tempfile
import unittest
from datetime import datetime

import alarm


class TestParseTime(unittest.TestCase):
    def test_24h(self):
        self.assertEqual(alarm.parse_time("07:30"), (7, 30))
        self.assertEqual(alarm.parse_time("23:59"), (23, 59))

    def test_12h(self):
        self.assertEqual(alarm.parse_time("7:30am"), (7, 30))
        self.assertEqual(alarm.parse_time("7:30PM"), (19, 30))
        self.assertEqual(alarm.parse_time("12:00am"), (0, 0))
        self.assertEqual(alarm.parse_time("12:15pm"), (12, 15))

    def test_invalid(self):
        for bad in ("not-a-time", "25:00", "13:99pm", ""):
            with self.assertRaises(ValueError):
                alarm.parse_time(bad)


class TestFormatTime(unittest.TestCase):
    def test_padding(self):
        self.assertEqual(alarm.format_time(7, 5), "07:05")
        self.assertEqual(alarm.format_time(23, 59), "23:59")


class TestAddMinutes(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(alarm.add_minutes(7, 30, 5), (7, 35))

    def test_midnight_rollover(self):
        self.assertEqual(alarm.add_minutes(23, 58, 5), (0, 3))

    def test_hour_rollover(self):
        self.assertEqual(alarm.add_minutes(7, 59, 1), (8, 0))


class TestNextOccurrence(unittest.TestCase):
    def test_later_today(self):
        now = datetime(2026, 10, 5, 6, 0)
        self.assertEqual(alarm.next_occurrence(7, 30, now), datetime(2026, 10, 5, 7, 30))

    def test_rolls_to_tomorrow(self):
        now = datetime(2026, 10, 5, 8, 0)
        self.assertEqual(alarm.next_occurrence(7, 30, now), datetime(2026, 10, 6, 7, 30))

    def test_same_minute_is_in_the_future(self):
        now = datetime(2026, 10, 5, 7, 30, 0)
        self.assertEqual(alarm.next_occurrence(7, 30, now), datetime(2026, 10, 6, 7, 30))


class TestStore(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = alarm.STORE
            alarm.STORE = os.path.join(tmp, "alarms.json")
            try:
                self.assertEqual(alarm.load_alarms(), [])
                alarm.save_alarms([{"time": "07:30", "label": "test", "daily": False}])
                loaded = alarm.load_alarms()
                self.assertEqual(len(loaded), 1)
                self.assertEqual(loaded[0]["time"], "07:30")
            finally:
                alarm.STORE = original

    def test_corrupt_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = alarm.STORE
            alarm.STORE = os.path.join(tmp, "alarms.json")
            try:
                with open(alarm.STORE, "w", encoding="utf-8") as fh:
                    fh.write("{not json")
                self.assertEqual(alarm.load_alarms(), [])
            finally:
                alarm.STORE = original


if __name__ == "__main__":
    unittest.main()
