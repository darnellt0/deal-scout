import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.config import get_settings
from app.notify.channels import send_discord, send_email, send_sms


class DummySMTP:
    def __init__(self, *_, **__):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def send_message(self, _):
        pass


def test_send_email_without_error(monkeypatch):
    settings = get_settings()
    settings.smtp_host = "mailhog"
    monkeypatch.setattr("smtplib.SMTP", DummySMTP)
    send_email("Subject", "<strong>Body</strong>")


def test_send_discord_skipped_when_not_configured():
    settings = get_settings()
    settings.discord_webhook_url = ""
    send_discord("hello")


def test_send_sms_skipped_without_credentials(monkeypatch):
    settings = get_settings()
    settings.twilio_account_sid = ""
    settings.alert_sms_to = ""
    send_sms("hi there")
