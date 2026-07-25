import datetime as dt
import unittest

from scripts.fetch_contributions import account_for_refresh_commit, derive


def day(date: str, count: int, level: int = 0) -> dict:
    return {"date": date, "count": count, "level": level}


class ContributionStatsTests(unittest.TestCase):
    def test_pending_commit_updates_total_and_streaks(self) -> None:
        days = [
            day("2026-07-22", 2, 1),
            day("2026-07-23", 3, 2),
            day("2026-07-24", 1, 1),
            day("2026-07-25", 0),
        ]

        account_for_refresh_commit(days, dt.date(2026, 7, 25))
        result = derive(days, dt.date(2026, 7, 25))

        self.assertEqual(result["total"], 7)
        self.assertEqual(result["streak_current"], 4)
        self.assertEqual(result["streak_longest"], 4)
        self.assertEqual(result["streak_longest_start"], "2026-07-22")
        self.assertEqual(result["streak_longest_end"], "2026-07-25")

    def test_empty_today_does_not_break_yesterdays_current_streak(self) -> None:
        days = [
            day("2026-07-23", 2, 1),
            day("2026-07-24", 1, 1),
            day("2026-07-25", 0),
        ]

        result = derive(days, dt.date(2026, 7, 25))

        self.assertEqual(result["streak_current"], 2)
        self.assertEqual(result["streak_current_start"], "2026-07-23")
        self.assertEqual(result["streak_current_end"], "2026-07-24")


if __name__ == "__main__":
    unittest.main()
