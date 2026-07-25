import datetime as dt
import unittest

from scripts.fetch_contributions import (
    account_for_refresh_commit,
    apply_count_overrides,
    derive,
)


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

    def test_pending_commit_survives_github_indexing_lag(self) -> None:
        fetched = [
            day("2026-07-24", 1, 1),
            day("2026-07-25", 8, 1),
        ]
        previously_committed = [
            day("2026-07-24", 1, 1),
            day("2026-07-25", 9, 2),
        ]

        account_for_refresh_commit(
            fetched,
            dt.date(2026, 7, 25),
            previously_committed,
        )
        result = derive(fetched, dt.date(2026, 7, 25))

        self.assertEqual(result["days"][-1]["count"], 10)
        self.assertEqual(result["total"], 11)

    def test_user_confirmed_count_override_sets_best_day(self) -> None:
        days = [
            day("2026-07-22", 33, 4),
            day("2026-07-23", 34, 4),
            day("2026-07-24", 9, 2),
        ]

        apply_count_overrides(days)
        result = derive(days, dt.date(2026, 7, 24))

        self.assertEqual(result["total"], 96)
        self.assertEqual(result["best"], {"date": "2026-07-23", "count": 54})
        self.assertEqual(result["days"][1]["level"], 5)


if __name__ == "__main__":
    unittest.main()
