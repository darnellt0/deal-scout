"""Tests for notification channels with mocking."""

import pytest
from unittest.mock import patch, MagicMock

from app.notify.channels import send_email, send_discord, send_sms


class TestEmailNotifications:
    """Test email sending."""

    @patch("app.notify.channels.smtplib.SMTP_SSL")
    def test_send_email_success(self, mock_smtp):
        """Successful email send should return True."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = send_email(subject="Test", html="<p>Test</p>", to="user@example.com")

        assert result is True
        mock_server.send_message.assert_called_once()

    @patch("app.notify.channels.smtplib.SMTP_SSL")
    def test_send_email_failure_retries(self, mock_smtp):
        """Failed email send should retry."""
        mock_smtp.side_effect = Exception("SMTP Error")

        result = send_email(subject="Test", html="<p>Test</p>", to="user@example.com")

        assert result is False
        # Should have retried 3 times
        assert mock_smtp.call_count >= 3

    @patch("app.notify.channels.smtplib.SMTP_SSL")
    def test_send_email_with_auth(self, mock_smtp):
        """Email with credentials should login."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        with patch("app.notify.channels.get_settings") as mock_settings:
            settings = MagicMock()
            settings.smtp_user = "testuser"
            settings.smtp_password = "testpass"
            settings.smtp_use_tls = True
            settings.smtp_host = "smtp.example.com"
            settings.smtp_port = 587
            settings.email_from = "from@example.com"
            mock_settings.return_value = settings

            send_email(subject="Test", html="<p>Test</p>", to="user@example.com")

            mock_server.login.assert_called_once_with("testuser", "testpass")


class TestDiscordNotifications:
    """Test Discord webhook sending."""

    @patch("app.notify.channels.httpx.Client")
    def test_send_discord_success(self, mock_client):
        """Successful Discord send should return True."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        result = send_discord("Test message")

        assert result is True

    @patch("app.notify.channels.httpx.Client")
    def test_send_discord_not_configured(self, mock_client):
        """Discord send without webhook should return False."""
        with patch("app.notify.channels.get_settings") as mock_settings:
            settings = MagicMock()
            settings.discord_webhook_url = ""
            mock_settings.return_value = settings

            result = send_discord("Test message")

            assert result is False
            mock_client.assert_not_called()

    @patch("app.notify.channels.httpx.Client")
    def test_send_discord_with_embed(self, mock_client):
        """Discord message with embed should include embed."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        embed = {"title": "Test", "url": "https://example.com"}
        send_discord("Test message", embed=embed)

        call_args = mock_client.return_value.__enter__.return_value.post.call_args
        assert call_args[1]["json"]["embeds"] == [embed]


class TestSMSNotifications:
    """Test SMS sending."""

    @patch("app.notify.channels.TwilioClient")
    def test_send_sms_success(self, mock_twilio):
        """Successful SMS send should return True."""
        mock_client = MagicMock()
        mock_twilio.return_value = mock_client

        with patch("app.notify.channels.get_settings") as mock_settings:
            settings = MagicMock()
            settings.twilio_account_sid = "test_sid"
            settings.twilio_auth_token = "test_token"
            settings.twilio_from = "+1234567890"
            settings.alert_sms_to = "+9876543210"
            mock_settings.return_value = settings

            result = send_sms("Test message")

            assert result is True
            mock_client.messages.create.assert_called_once()

    @patch("app.notify.channels.TwilioClient")
    def test_send_sms_not_configured(self, mock_twilio):
        """SMS send without credentials should return False."""
        with patch("app.notify.channels.get_settings") as mock_settings:
            settings = MagicMock()
            settings.twilio_account_sid = ""
            settings.twilio_auth_token = ""
            settings.twilio_from = ""
            settings.alert_sms_to = ""
            mock_settings.return_value = settings

            result = send_sms("Test message")

            assert result is False
            mock_twilio.assert_not_called()

    @patch("app.notify.channels.TwilioClient")
    def test_send_sms_with_custom_number(self, mock_twilio):
        """SMS with custom number should use that number."""
        mock_client = MagicMock()
        mock_twilio.return_value = mock_client

        with patch("app.notify.channels.get_settings") as mock_settings:
            settings = MagicMock()
            settings.twilio_account_sid = "test_sid"
            settings.twilio_auth_token = "test_token"
            settings.twilio_from = "+1234567890"
            settings.alert_sms_to = "+9876543210"
            mock_settings.return_value = settings

            send_sms("Test message", to_number="+5555555555")

            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["to"] == "+5555555555"

    @patch("app.notify.channels.TwilioClient")
    def test_send_sms_failure_retries(self, mock_twilio):
        """Failed SMS send should retry."""
        from twilio.base.exceptions import TwilioException

        mock_twilio.side_effect = TwilioException("API Error")

        with patch("app.notify.channels.get_settings") as mock_settings:
            settings = MagicMock()
            settings.twilio_account_sid = "test_sid"
            settings.twilio_auth_token = "test_token"
            settings.twilio_from = "+1234567890"
            settings.alert_sms_to = "+9876543210"
            mock_settings.return_value = settings

            result = send_sms("Test message")

            assert result is False
            # Should have retried 3 times
            assert mock_twilio.call_count >= 3
