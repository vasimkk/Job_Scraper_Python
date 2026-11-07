import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
import requests

from scraper_agent.verification.models import (
    VerificationAction,
    VerificationReason,
    JobVerificationResult,
)
from scraper_agent.verification.checker import JobAvailabilityChecker
from scraper_agent.verification.verifier import JobBatchVerifier


class TestVerificationRules(unittest.TestCase):

    def setUp(self):
        self.checker = JobAvailabilityChecker(request_timeout=2, max_retries=2, backoff_seconds=0.01)

    # -------------------------------------------------------------------------
    # Rule 1: URL Active + Job Open -> Keep job Active
    # -------------------------------------------------------------------------
    def test_rule_1_url_active_job_open(self):
        html_doc = """
        <html>
            <body>
                <h1>Senior Backend Software Engineer</h1>
                <p>Build scalable Python services.</p>
                <a href="#apply" class="btn btn-primary">Apply Now</a>
                <div id="apply">
                    <form action="/apply">
                        <input type="text" name="first_name" />
                        <input type="email" name="email" />
                        <input type="file" name="resume" />
                        <button type="submit">Submit</button>
                    </form>
                </div>
            </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://company.com/jobs/1234"
        mock_resp.text = html_doc

        with patch.object(self.checker, "fetch_with_retry", return_value=(mock_resp, 0, None)):
            res = self.checker.verify_job("https://company.com/jobs/1234")
            self.assertEqual(res.action, VerificationAction.KEEP_ACTIVE)
            self.assertEqual(res.reason, VerificationReason.JOB_OPEN)
            self.assertEqual(res.target_db_status, "OPEN")
            self.assertTrue(res.details.url_opens)
            self.assertTrue(res.details.job_status_active)

    # -------------------------------------------------------------------------
    # Rule 2: URL Active + Job Closed -> Mark job Closed
    # -------------------------------------------------------------------------
    def test_rule_2_closed_phrase_job_closed(self):
        html_doc = """
        <html>
            <body>
                <h1>Frontend Engineer</h1>
                <div class="alert alert-warning">This job is closed</div>
            </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://company.com/jobs/1234"
        mock_resp.text = html_doc

        with patch.object(self.checker, "fetch_with_retry", return_value=(mock_resp, 0, None)):
            res = self.checker.verify_job("https://company.com/jobs/1234")
            self.assertEqual(res.action, VerificationAction.MARK_CLOSED)
            self.assertEqual(res.reason, VerificationReason.JOB_CLOSED_MESSAGE)
            self.assertEqual(res.target_db_status, "CLOSED")

    def test_rule_2_closed_phrase_no_longer_accepting(self):
        html_doc = """
        <html>
            <body>
                <h1>Machine Learning Engineer</h1>
                <p>We are no longer accepting applications for this role.</p>
            </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://company.com/jobs/1234"
        mock_resp.text = html_doc

        with patch.object(self.checker, "fetch_with_retry", return_value=(mock_resp, 0, None)):
            res = self.checker.verify_job("https://company.com/jobs/1234")
            self.assertEqual(res.action, VerificationAction.MARK_CLOSED)
            self.assertEqual(res.reason, VerificationReason.JOB_CLOSED_MESSAGE)
            self.assertEqual(res.target_db_status, "CLOSED")

    def test_rule_2_closed_phrase_position_filled(self):
        html_doc = """
        <html>
            <body>
                <h1>Data Scientist</h1>
                <div class="banner">This position has been filled.</div>
            </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://company.com/jobs/1234"
        mock_resp.text = html_doc

        with patch.object(self.checker, "fetch_with_retry", return_value=(mock_resp, 0, None)):
            res = self.checker.verify_job("https://company.com/jobs/1234")
            self.assertEqual(res.action, VerificationAction.MARK_CLOSED)
            self.assertEqual(res.reason, VerificationReason.JOB_CLOSED_MESSAGE)
            self.assertEqual(res.target_db_status, "CLOSED")

    def test_rule_2_closed_via_redirect_to_career_home(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://company.com/careers"
        mock_resp.text = "<html><body><h1>Careers at Company</h1></body></html>"

        with patch.object(self.checker, "fetch_with_retry", return_value=(mock_resp, 0, None)):
            res = self.checker.verify_job("https://company.com/careers/staff-engineer-5432")
            self.assertEqual(res.action, VerificationAction.MARK_CLOSED)
            self.assertEqual(res.reason, VerificationReason.REDIRECTED_TO_CAREER_HOME)
            self.assertEqual(res.target_db_status, "CLOSED")

    def test_rule_2_closed_via_schema_expiration(self):
        expired = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        html_doc = f"""
        <html>
            <head>
                <script type="application/ld+json">
                {{
                    "@context": "https://schema.org",
                    "@type": "JobPosting",
                    "title": "Site Reliability Engineer",
                    "validThrough": "{expired}"
                }}
                </script>
            </head>
            <body>
                <h1>Site Reliability Engineer</h1>
            </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://company.com/jobs/1234"
        mock_resp.text = html_doc

        with patch.object(self.checker, "fetch_with_retry", return_value=(mock_resp, 0, None)):
            res = self.checker.verify_job("https://company.com/jobs/1234")
            self.assertEqual(res.action, VerificationAction.MARK_CLOSED)
            self.assertEqual(res.reason, VerificationReason.SCHEMA_EXPIRED)
            self.assertEqual(res.target_db_status, "CLOSED")

    # -------------------------------------------------------------------------
    # Rule 3: URL Active + Status Unclear -> Keep existing status; do not mark Closed
    # -------------------------------------------------------------------------
    def test_rule_3_status_unclear_preserves_status(self):
        # 200 OK, no explicit closed text, but no standard HTML apply button found
        html_doc = """
        <html>
            <body>
                <div id="root">
                    <p>Loading application portal...</p>
                </div>
            </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://company.com/jobs/1234"
        mock_resp.text = html_doc

        with patch.object(self.checker, "fetch_with_retry", return_value=(mock_resp, 0, None)):
            res = self.checker.verify_job("https://company.com/jobs/1234")
            # IMPORTANT: Must be KEEP_STATUS, and target_db_status must be None (do NOT mark closed)
            self.assertEqual(res.action, VerificationAction.KEEP_STATUS)
            self.assertEqual(res.reason, VerificationReason.STATUS_UNCLEAR)
            self.assertIsNone(res.target_db_status)
            self.assertNotEqual(res.target_db_status, "CLOSED")

    # -------------------------------------------------------------------------
    # Rule 4: URL Inaccessible -> Retry verification before changing status
    # -------------------------------------------------------------------------
    def test_rule_4_retry_recovers_from_transient_error(self):
        mock_503 = MagicMock()
        mock_503.status_code = 503

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.url = "https://company.com/jobs/1234"
        mock_200.text = "<html><body><h1>DevOps</h1><a href='/apply'>Apply Now</a></body></html>"

        with patch.object(self.checker.session, "get", side_effect=[mock_503, mock_200]):
            resp, retries, exc = self.checker.fetch_with_retry("https://company.com/jobs/1234")
            self.assertIsNotNone(resp)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(retries, 1)

    def test_rule_4_and_6_inaccessible_404_after_retries_marks_closed(self):
        mock_404 = MagicMock()
        mock_404.status_code = 404
        mock_404.url = "https://company.com/jobs/9999"
        mock_404.text = "404 Not Found"

        with patch.object(self.checker, "fetch_with_retry", return_value=(mock_404, 0, None)):
            res = self.checker.verify_job("https://company.com/jobs/9999")
            self.assertEqual(res.action, VerificationAction.MARK_CLOSED)
            self.assertEqual(res.reason, VerificationReason.URL_NOT_FOUND_404)
            self.assertEqual(res.target_db_status, "CLOSED")

    # -------------------------------------------------------------------------
    # Rule 5: CAPTCHA / Login / Network Error -> Do not change job status
    # -------------------------------------------------------------------------
    def test_rule_5_captcha_blocked_does_not_change_status(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.url = "https://company.com/jobs/1234"
        mock_resp.text = "<html><head><title>Attention Required! | Cloudflare</title></head><body>Verify you are human</body></html>"

        with patch.object(self.checker, "fetch_with_retry", return_value=(mock_resp, 0, None)):
            res = self.checker.verify_job("https://company.com/jobs/1234")
            # IMPORTANT: Do not change job status!
            self.assertEqual(res.action, VerificationAction.NO_CHANGE)
            self.assertEqual(res.reason, VerificationReason.CAPTCHA_BLOCKED)
            self.assertIsNone(res.target_db_status)

    def test_rule_5_login_required_does_not_change_status(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.url = "https://company.com/login?redirect=/jobs/1234"
        mock_resp.text = "<html><body>Please sign in to apply</body></html>"

        with patch.object(self.checker, "fetch_with_retry", return_value=(mock_resp, 0, None)):
            res = self.checker.verify_job("https://company.com/jobs/1234")
            # IMPORTANT: Do not change job status!
            self.assertEqual(res.action, VerificationAction.NO_CHANGE)
            self.assertEqual(res.reason, VerificationReason.LOGIN_REQUIRED)
            self.assertIsNone(res.target_db_status)

    def test_rule_5_network_error_after_retries_does_not_change_status(self):
        exc = requests.exceptions.Timeout("Connection timed out after retries")
        with patch.object(self.checker, "fetch_with_retry", return_value=(None, 3, exc)):
            res = self.checker.verify_job("https://company.com/jobs/1234")
            # IMPORTANT: Do not change job status!
            self.assertEqual(res.action, VerificationAction.NO_CHANGE)
            self.assertEqual(res.reason, VerificationReason.NETWORK_ERROR)
            self.assertIsNone(res.target_db_status)


if __name__ == "__main__":
    unittest.main()

