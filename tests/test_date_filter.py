import unittest
from datetime import datetime, timezone, timedelta
from scraper_agent.classifiers.date_filter import (
    get_freshness_cutoff,
    is_job_in_date_window,
    format_freshness_window_description,
)


class TestDateFilter(unittest.TestCase):

    def test_cutoff_calculation(self):
        cutoff = get_freshness_cutoff()
        now = datetime.now(timezone.utc)
        self.assertEqual(cutoff.day, 1)
        self.assertEqual(cutoff.hour, 0)
        self.assertEqual(cutoff.minute, 0)
        # Should be strictly before or equal to current month 1st
        self.assertLess(cutoff, now)

    def test_job_in_date_window(self):
        cutoff = get_freshness_cutoff()

        # Job from today (Current month) -> valid
        today_job = datetime.now(timezone.utc)
        is_valid, _ = is_job_in_date_window(today_job, cutoff)
        self.assertTrue(is_valid)

        # Job from middle of previous month -> valid
        mid_prev_month = cutoff + timedelta(days=10)
        is_valid, _ = is_job_in_date_window(mid_prev_month, cutoff)
        self.assertTrue(is_valid)

        # Job from 90 days ago (Stale) -> invalid
        stale_job = cutoff - timedelta(days=10)
        is_valid, _ = is_job_in_date_window(stale_job, cutoff)
        self.assertFalse(is_valid)

        # Job with None date (e.g. evergreen active) -> valid
        is_valid, _ = is_job_in_date_window(None, cutoff)
        self.assertTrue(is_valid)


if __name__ == "__main__":
    unittest.main()

