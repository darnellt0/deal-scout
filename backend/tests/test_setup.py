"""Unit tests for First-Run Checklist setup endpoints."""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest
import redis
from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    return MagicMock(spec=redis.Redis)


class TestSetupStatus:
    """Tests for GET /setup/status endpoint."""

    def test_status_endpoint_returns_200(self, client):
        """Test that /setup/status returns 200 OK."""
        response = client.get("/setup/status")
        assert response.status_code == 200

    def test_status_response_structure(self, client):
        """Test that /setup/status returns expected JSON structure."""
        response = client.get("/setup/status")
        data = response.json()

        # Check top-level keys
        assert "ok" in data
        assert "checks" in data
        assert "progress" in data
        assert "timestamp" in data

        # Check that ok is boolean
        assert isinstance(data["ok"], bool)

        # Check progress is float between 0 and 1
        assert isinstance(data["progress"], float)
        assert 0.0 <= data["progress"] <= 1.0

        # Check timestamp is ISO format
        assert "T" in data["timestamp"]

    def test_status_checks_structure(self, client):
        """Test that each check has required fields."""
        response = client.get("/setup/status")
        data = response.json()
        checks = data["checks"]

        # Should have multiple checks
        assert len(checks) > 0

        # Each check should have required fields
        required_fields = {"id", "label", "status", "details"}
        for check in checks:
            assert all(field in check for field in required_fields)
            # Status should be one of: ok, warn, fail
            assert check["status"] in ("ok", "warn", "fail")

    def test_status_has_critical_checks(self, client):
        """Test that critical checks (db, redis) are present."""
        response = client.get("/setup/status")
        data = response.json()
        check_ids = {check["id"] for check in data["checks"]}

        # Critical checks should be present
        assert "db" in check_ids
        assert "redis" in check_ids

    def test_status_has_expected_checks(self, client):
        """Test that expected checks are present."""
        response = client.get("/setup/status")
        data = response.json()
        check_ids = {check["id"] for check in data["checks"]}

        expected_checks = {
            "db",
            "redis",
            "worker",
            "scheduler",
            "ebay",
            "craigslist",
            "email",
            "discord",
            "sms",
            "demo",
            "comps",
            "vision",
            "static",
        }
        assert expected_checks == check_ids

    @patch("app.setup.router.check_database")
    @patch("app.setup.router.check_redis")
    def test_status_ok_when_critical_ok(self, mock_redis, mock_db, client):
        """Test that 'ok' is true when critical checks pass."""
        from app.setup.router import CheckStatus

        # Mock critical checks as ok
        mock_db.return_value = CheckStatus("db", "Database connected", "ok")
        mock_redis.return_value = CheckStatus("redis", "Redis connected", "ok")

        response = client.get("/setup/status")
        data = response.json()

        # Should be ok if critical checks pass
        assert data["ok"] is True

    @patch("app.setup.router.check_database")
    def test_status_not_ok_when_db_fails(self, mock_db, client):
        """Test that 'ok' is false when critical check fails."""
        from app.setup.router import CheckStatus

        # Mock critical check as failed
        mock_db.return_value = CheckStatus("db", "Database connected", "fail", "Connection refused")

        response = client.get("/setup/status")
        data = response.json()

        # Should not be ok if critical check fails
        assert data["ok"] is False

    def test_progress_calculation(self, client):
        """Test that progress is calculated correctly."""
        response = client.get("/setup/status")
        data = response.json()

        # Count ok checks
        ok_count = sum(1 for check in data["checks"] if check["status"] == "ok")
        total_count = len(data["checks"])

        expected_progress = ok_count / total_count if total_count > 0 else 0.0
        assert data["progress"] == expected_progress


class TestTestNotification:
    """Tests for POST /setup/test-notification endpoint."""

    def test_test_notification_returns_200(self, client):
        """Test that /setup/test-notification returns 200 OK."""
        with patch("app.setup.router.send_test_notification") as mock_send:
            mock_send.return_value = {
                "email": {"sent": False, "details": "Not configured"},
                "discord": {"sent": False, "details": "Not configured"},
                "sms": {"sent": False, "details": "Not configured"},
            }
            response = client.post("/setup/test-notification")
            assert response.status_code == 200

    def test_test_notification_response_structure(self, client):
        """Test that /setup/test-notification returns expected structure."""
        with patch("app.setup.router.send_test_notification") as mock_send:
            mock_send.return_value = {
                "email": {"sent": False, "details": ""},
                "discord": {"sent": False, "details": ""},
                "sms": {"sent": False, "details": ""},
            }
            response = client.post("/setup/test-notification")
            data = response.json()

            # Check required fields
            assert "success" in data
            assert "details" in data
            assert "timestamp" in data

            # Check details structure
            assert "email" in data["details"]
            assert "discord" in data["details"]
            assert "sms" in data["details"]

            # Check each channel has sent and details
            for channel in ["email", "discord", "sms"]:
                assert "sent" in data["details"][channel]
                assert "details" in data["details"][channel]

    def test_test_notification_success_when_any_sent(self, client):
        """Test that success is true if any notification was sent."""
        with patch("app.setup.router.send_test_notification") as mock_send:
            mock_send.return_value = {
                "email": {"sent": True, "details": "Email sent"},
                "discord": {"sent": False, "details": "Not configured"},
                "sms": {"sent": False, "details": "Not configured"},
            }
            response = client.post("/setup/test-notification")
            data = response.json()

            assert data["success"] is True

    def test_test_notification_failure_when_none_sent(self, client):
        """Test that success is false if no notification was sent."""
        with patch("app.setup.router.send_test_notification") as mock_send:
            mock_send.return_value = {
                "email": {"sent": False, "details": "Not configured"},
                "discord": {"sent": False, "details": "Not configured"},
                "sms": {"sent": False, "details": "Not configured"},
            }
            response = client.post("/setup/test-notification")
            data = response.json()

            assert data["success"] is False

    @patch("app.setup.router.send_email")
    @patch("app.setup.router.settings")
    def test_email_notification_called(self, mock_settings, mock_send_email, client):
        """Test that email notification is attempted when SMTP is configured."""
        # Configure settings to have SMTP
        mock_settings.smtp_host = "mailhog"
        mock_settings.smtp_port = 1025
        mock_settings.discord_webhook_url = ""
        mock_settings.twilio_account_sid = ""

        mock_send_email.return_value = True

        with patch("app.setup.router.send_test_notification") as mock_send:
            from app.setup.router import send_test_notification

            result = send_test_notification()

            # Email channel should be in results
            assert "email" in result

    @patch("app.setup.router.send_discord")
    @patch("app.setup.router.settings")
    def test_discord_notification_called(self, mock_settings, mock_send_discord, client):
        """Test that Discord notification is attempted when webhook is configured."""
        # Configure settings to have Discord
        mock_settings.smtp_host = ""
        mock_settings.discord_webhook_url = "https://discord.com/api/webhooks/..."
        mock_settings.twilio_account_sid = ""

        mock_send_discord.return_value = True

        with patch("app.setup.router.send_test_notification") as mock_send:
            from app.setup.router import send_test_notification

            result = send_test_notification()

            # Discord channel should be in results
            assert "discord" in result


class TestDismissChecklist:
    """Tests for POST /setup/dismiss endpoint."""

    def test_dismiss_returns_200(self, client):
        """Test that /setup/dismiss returns 200 OK."""
        with patch("app.setup.router.redis.from_url") as mock_redis_url:
            mock_redis_instance = MagicMock()
            mock_redis_url.return_value = mock_redis_instance

            response = client.post("/setup/dismiss")
            assert response.status_code == 200

    def test_dismiss_response_structure(self, client):
        """Test that /setup/dismiss returns expected structure."""
        with patch("app.setup.router.redis.from_url") as mock_redis_url:
            mock_redis_instance = MagicMock()
            mock_redis_url.return_value = mock_redis_instance

            response = client.post("/setup/dismiss")
            data = response.json()

            # Check required fields
            assert "dismissed" in data
            assert "timestamp" in data
            assert data["dismissed"] is True

    def test_dismiss_sets_redis_key(self, client):
        """Test that dismiss sets Redis key."""
        with patch("app.setup.router.redis.from_url") as mock_redis_url:
            mock_redis_instance = MagicMock()
            mock_redis_url.return_value = mock_redis_instance

            response = client.post("/setup/dismiss")

            # Verify Redis.set was called with the correct key
            mock_redis_instance.set.assert_called_once()
            call_args = mock_redis_instance.set.call_args
            # First argument should be the key "setup:dismissed"
            assert call_args[0][0] == "setup:dismissed"


class TestIsDismissed:
    """Tests for GET /setup/is-dismissed endpoint."""

    def test_is_dismissed_returns_200(self, client):
        """Test that /setup/is-dismissed returns 200 OK."""
        with patch("app.setup.router.redis.from_url") as mock_redis_url:
            mock_redis_instance = MagicMock()
            mock_redis_instance.get.return_value = None
            mock_redis_url.return_value = mock_redis_instance

            response = client.get("/setup/is-dismissed")
            assert response.status_code == 200

    def test_is_dismissed_response_structure(self, client):
        """Test that /setup/is-dismissed returns expected structure."""
        with patch("app.setup.router.redis.from_url") as mock_redis_url:
            mock_redis_instance = MagicMock()
            mock_redis_instance.get.return_value = None
            mock_redis_url.return_value = mock_redis_instance

            response = client.get("/setup/is-dismissed")
            data = response.json()

            # Check required fields
            assert "dismissed" in data
            assert "dismissed_at" in data

    def test_is_dismissed_false_when_not_set(self, client):
        """Test that dismissed is false when flag is not set."""
        with patch("app.setup.router.redis.from_url") as mock_redis_url:
            mock_redis_instance = MagicMock()
            mock_redis_instance.get.return_value = None
            mock_redis_url.return_value = mock_redis_instance

            response = client.get("/setup/is-dismissed")
            data = response.json()

            assert data["dismissed"] is False
            assert data["dismissed_at"] is None

    def test_is_dismissed_true_when_set(self, client):
        """Test that dismissed is true when flag is set."""
        import time

        with patch("app.setup.router.redis.from_url") as mock_redis_url:
            mock_redis_instance = MagicMock()
            # Return a timestamp as bytes
            current_time = int(time.time())
            mock_redis_instance.get.return_value = str(current_time).encode()
            mock_redis_url.return_value = mock_redis_instance

            response = client.get("/setup/is-dismissed")
            data = response.json()

            assert data["dismissed"] is True
            assert data["dismissed_at"] is not None
            assert "T" in data["dismissed_at"]  # ISO format


class TestCheckStatus:
    """Tests for individual check functions."""

    @patch("app.setup.router.get_session")
    def test_database_check_success(self, mock_session):
        """Test database check when successful."""
        from app.setup.router import check_database
        from sqlalchemy.orm import MagicMock

        mock_session_instance = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session_instance)
        mock_session.__exit__ = MagicMock(return_value=None)

        check = check_database()

        assert check.id == "db"
        assert check.status == "ok"

    @patch("app.setup.router.get_session")
    def test_database_check_failure(self, mock_session):
        """Test database check when it fails."""
        from app.setup.router import check_database

        mock_session.side_effect = Exception("Connection refused")

        check = check_database()

        assert check.id == "db"
        assert check.status == "fail"

    @patch("app.setup.router.redis.from_url")
    def test_redis_check_success(self, mock_redis_url):
        """Test Redis check when successful."""
        from app.setup.router import check_redis

        mock_redis_instance = MagicMock()
        mock_redis_url.return_value = mock_redis_instance

        check = check_redis()

        assert check.id == "redis"
        assert check.status == "ok"

    @patch("app.setup.router.redis.from_url")
    def test_redis_check_failure(self, mock_redis_url):
        """Test Redis check when it fails."""
        from app.setup.router import check_redis

        mock_redis_url.side_effect = Exception("Connection refused")

        check = check_redis()

        assert check.id == "redis"
        assert check.status == "fail"

    def test_demo_mode_check(self):
        """Test demo mode check."""
        from app.setup.router import check_demo_mode

        check = check_demo_mode()

        assert check.id == "demo"
        assert check.status == "ok"
        # Details should show "on" or "off"
        assert check.details in ("on", "off")

    @patch("app.setup.router.settings")
    def test_craigslist_check_configured(self, mock_settings):
        """Test Craigslist check when configured."""
        from app.setup.router import check_craigslist_configured

        mock_settings.cl_region = "sfbay"

        check = check_craigslist_configured()

        assert check.id == "craigslist"
        assert check.status == "ok"
        assert check.details == "sfbay"

    @patch("app.setup.router.settings")
    def test_craigslist_check_not_configured(self, mock_settings):
        """Test Craigslist check when not configured."""
        from app.setup.router import check_craigslist_configured

        mock_settings.cl_region = ""

        check = check_craigslist_configured()

        assert check.id == "craigslist"
        assert check.status == "warn"

    @patch("app.setup.router.settings")
    def test_discord_check_configured(self, mock_settings):
        """Test Discord check when configured."""
        from app.setup.router import check_discord_configured

        mock_settings.discord_webhook_url = "https://discord.com/api/webhooks/..."

        check = check_discord_configured()

        assert check.id == "discord"
        assert check.status == "ok"

    @patch("app.setup.router.settings")
    def test_discord_check_not_configured(self, mock_settings):
        """Test Discord check when not configured."""
        from app.setup.router import check_discord_configured

        mock_settings.discord_webhook_url = ""

        check = check_discord_configured()

        assert check.id == "discord"
        assert check.status == "warn"

    @patch("app.setup.router.settings")
    def test_sms_check_configured(self, mock_settings):
        """Test SMS check when fully configured."""
        from app.setup.router import check_sms_configured

        mock_settings.twilio_account_sid = "ACxxxxxxxxxxxxxxx"
        mock_settings.twilio_auth_token = "authtoken"
        mock_settings.twilio_from = "+1234567890"
        mock_settings.alert_sms_to = "+0987654321"

        check = check_sms_configured()

        assert check.id == "sms"
        assert check.status == "ok"

    @patch("app.setup.router.settings")
    def test_sms_check_partially_configured(self, mock_settings):
        """Test SMS check when partially configured."""
        from app.setup.router import check_sms_configured

        mock_settings.twilio_account_sid = "ACxxxxxxxxxxxxxxx"
        mock_settings.twilio_auth_token = "authtoken"
        mock_settings.twilio_from = "+1234567890"
        mock_settings.alert_sms_to = ""  # Missing target

        check = check_sms_configured()

        assert check.id == "sms"
        assert check.status == "warn"

    @patch("app.setup.router.settings")
    def test_sms_check_not_configured(self, mock_settings):
        """Test SMS check when not configured."""
        from app.setup.router import check_sms_configured

        mock_settings.twilio_account_sid = ""
        mock_settings.twilio_auth_token = ""
        mock_settings.twilio_from = ""
        mock_settings.alert_sms_to = ""

        check = check_sms_configured()

        assert check.id == "sms"
        assert check.status == "warn"

    @patch("app.setup.router.settings")
    def test_vision_check_enabled(self, mock_settings):
        """Test vision check when enabled."""
        from app.setup.router import check_vision_pipeline

        mock_settings.vision_enabled = True
        mock_settings.rembg_enabled = True

        check = check_vision_pipeline()

        assert check.id == "vision"
        # Status could be ok or warn depending on imports
        assert check.status in ("ok", "warn")

    @patch("app.setup.router.settings")
    def test_vision_check_disabled(self, mock_settings):
        """Test vision check when disabled."""
        from app.setup.router import check_vision_pipeline

        mock_settings.vision_enabled = False
        mock_settings.rembg_enabled = False

        check = check_vision_pipeline()

        assert check.id == "vision"
        assert check.status == "warn"

    def test_static_samples_check(self):
        """Test static samples check."""
        from app.setup.router import check_static_samples

        check = check_static_samples()

        assert check.id == "static"
        # Status depends on whether files exist
        assert check.status in ("ok", "warn")
