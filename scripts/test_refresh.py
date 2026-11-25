"""Test calculations that would otherwise publish misleading profile statistics."""
from datetime import date
import unittest
from unittest.mock import patch
from refresh_data import parse_calendar, streaks, normalize_event, main, ROOT


def days(*levels):
    return [{"date": f"2026-11-{20+i:02d}", "level": level} for i,level in enumerate(levels)]


class PublicDataTests(unittest.TestCase):
    def test_today_without_activity_does_not_break_yesterday_streak(self):
        result = streaks(days(0, 1, 2, 0), date(2026,11,23))
        self.assertEqual(result["current"], 2)
        self.assertEqual(result["longest_in_grid"], 2)

    def test_inactive_yesterday_breaks_streak_and_future_is_ignored(self):
        result = streaks(days(1, 2, 0, 0, 4), date(2026,11,23))
        self.assertEqual(result["current"], 0)
        self.assertEqual(result["longest_in_grid"], 2)

    def test_stale_calendar_cannot_report_current_streak(self):
        self.assertEqual(streaks(days(1, 2), date(2026,11,25))["current"], 0)

    def test_single_contribution_and_zero_days_parse(self):
        text = '<h2 id="js-contribution-activity-description">1 contribution in 2026</h2><td data-date="2026-11-20" data-level="0"></td><td data-date="2026-11-21" data-level="1"></td>'
        total, calendar = parse_calendar(text, full_grid=False)
        self.assertEqual(total, 1)
        self.assertEqual([d["level"] for d in calendar], [0, 1])

    def test_partial_grid_and_duplicate_dates_are_rejected(self):
        heading = '<h2 id="js-contribution-activity-description">12 contributions</h2>'
        cell = '<td data-date="2026-11-20" data-level="1"></td>'
        with self.assertRaises(ValueError):
            parse_calendar(heading+cell)
        with self.assertRaises(ValueError):
            parse_calendar(heading+cell+cell, full_grid=False)

    def test_push_without_commit_count_does_not_invent_one(self):
        event = normalize_event({"type":"PushEvent", "repo":{"name":"owner/repo"}, "created_at":"2026-11-25T00:00:00Z", "payload":{"ref":"refs/heads/main", "head":"abc"}})
        self.assertEqual(event["summary"], "Pushed to main")
        self.assertEqual(event["url"], "https://github.com/owner/repo/commit/abc")

    def test_network_failure_leaves_snapshot_unchanged(self):
        target = ROOT/"data/profile.json"
        before = target.read_bytes()
        with patch("refresh_data.api", side_effect=RuntimeError("Unavailable")):
            with self.assertRaises(RuntimeError):
                main()
        self.assertEqual(target.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
