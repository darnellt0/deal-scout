"""Tests for live scan blocking endpoint."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Skip all tests in this file - buyer/scan features are parked in seller-first MVP
pytestmark = pytest.mark.skip(reason="Buyer/scan endpoints parked in seller-first MVP refactor")


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestLiveScanBlocking:
    """Tests for POST /scan/run with blocking parameter."""

    @patch("app.buyer.scan_exec.run_scan")
    def test_scan_run_blocking_returns_counts(self, mock_run_scan, client):
        """Test that blocking scan returns count summary."""
        # Mock run_scan to return empty list (no matches filtered)
        mock_run_scan.return_value = []

        response = client.post("/scan/run?live=1&blocking=1")
        assert response.status_code == 200

        data = response.json()
        assert data["mode"] == "blocking"
        assert data["live"] is True
        assert "total" in data
        assert "new" in data
        assert "updated" in data
        assert "skipped" in data

    @patch("app.buyer.scan_exec.run_scan")
    def test_scan_run_blocking_counts_correct(self, mock_run_scan, client):
        """Test that blocking scan counts are correct."""
        # Mock ListingMatch objects
        from app.buyer.search import ListingMatch

        matches = [
            ListingMatch(
                id=1,
                title="Test Item 1",
                price=100.0,
                condition="good",
                category="furniture>sofas",
                url="http://example.com/1",
                thumbnail_url="http://example.com/1.jpg",
                distance_mi=5.0,
                deal_score=80,
                is_free=False,
                source="craigslist",
                auto_message="Test message",
            ),
            ListingMatch(
                id=2,
                title="Test Item 2",
                price=50.0,
                condition="fair",
                category="furniture>sofas",
                url="http://example.com/2",
                thumbnail_url="http://example.com/2.jpg",
                distance_mi=10.0,
                deal_score=85,
                is_free=False,
                source="craigslist",
                auto_message="Test message",
            ),
        ]

        mock_run_scan.return_value = matches

        response = client.post("/scan/run?live=1&blocking=1")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 2  # 2 matches returned
        # new/updated counts depend on DB state (may vary)
        assert isinstance(data["new"], int)
        assert isinstance(data["updated"], int)

    def test_scan_run_blocking_vs_async(self, client):
        """Test that blocking=0 uses async mode (returns task_id)."""
        with patch("app.worker.celery_app.send_task") as mock_send_task:
            mock_task = MagicMock()
            mock_task.id = "test-task-123"
            mock_send_task.return_value = mock_task

            response = client.post("/scan/run?live=1&blocking=0")
            assert response.status_code == 200

            data = response.json()
            assert data["mode"] == "enqueued"
            assert "task_id" in data
            assert data["live"] is True

    def test_scan_run_default_async(self, client):
        """Test that default (no blocking param) uses async mode."""
        with patch("app.worker.celery_app.send_task") as mock_send_task:
            mock_task = MagicMock()
            mock_task.id = "test-task-456"
            mock_send_task.return_value = mock_task

            response = client.post("/scan/run?live=0")
            assert response.status_code == 200

            data = response.json()
            assert data["mode"] == "enqueued"
            assert "task_id" in data

    @patch("app.buyer.scan_exec.run_scan")
    def test_scan_run_respects_live_flag(self, mock_run_scan, client):
        """Test that live=1 passes to run_scan correctly."""
        mock_run_scan.return_value = []

        # Call with live=1
        response = client.post("/scan/run?live=1&blocking=1")
        assert response.status_code == 200

        # Verify run_scan was called with live=True
        mock_run_scan.assert_called()
        call_args = mock_run_scan.call_args
        assert call_args[1]["use_live"] is True

    @patch("app.buyer.scan_exec.run_scan")
    def test_scan_run_demo_mode_when_live_0(self, mock_run_scan, client):
        """Test that live=0 passes to run_scan as False."""
        mock_run_scan.return_value = []

        # Call with live=0
        response = client.post("/scan/run?live=0&blocking=1")
        assert response.status_code == 200

        # Verify run_scan was called with live=False
        mock_run_scan.assert_called()
        call_args = mock_run_scan.call_args
        assert call_args[1]["use_live"] is False


class TestScanExec:
    """Tests for scan_exec module."""

    @patch("app.buyer.scan_exec.run_scan")
    @patch("app.buyer.scan_exec.get_session")
    def test_scan_now_returns_dict(self, mock_get_session, mock_run_scan):
        """Test that scan_now returns correct dictionary structure."""
        from app.buyer.scan_exec import scan_now

        # Mock run_scan to return empty list
        mock_run_scan.return_value = []
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        result = scan_now(live=True)

        assert isinstance(result, dict)
        assert set(result.keys()) == {"total", "new", "updated", "skipped"}
        assert all(isinstance(v, int) for v in result.values())

    @patch("app.buyer.scan_exec.run_scan")
    @patch("app.buyer.scan_exec.get_session")
    def test_scan_now_counts_matches(self, mock_get_session, mock_run_scan):
        """Test that scan_now counts total matches correctly."""
        from app.buyer.scan_exec import scan_now
        from app.buyer.search import ListingMatch

        # Mock 3 matches
        matches = [
            ListingMatch(
                id=1,
                title="Item 1",
                price=100.0,
                condition="good",
                category="furniture",
                url="http://example.com/1",
                thumbnail_url=None,
                distance_mi=5.0,
                deal_score=80,
                is_free=False,
                source="craigslist",
                auto_message="Test",
            ),
            ListingMatch(
                id=2,
                title="Item 2",
                price=150.0,
                condition="good",
                category="furniture",
                url="http://example.com/2",
                thumbnail_url=None,
                distance_mi=10.0,
                deal_score=85,
                is_free=False,
                source="craigslist",
                auto_message="Test",
            ),
            ListingMatch(
                id=3,
                title="Item 3",
                price=200.0,
                condition="fair",
                category="furniture",
                url="http://example.com/3",
                thumbnail_url=None,
                distance_mi=15.0,
                deal_score=75,
                is_free=False,
                source="craigslist",
                auto_message="Test",
            ),
        ]

        mock_run_scan.return_value = matches
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = None
        mock_get_session.return_value.__enter__.return_value = mock_session

        result = scan_now(live=True)

        assert result["total"] == 3

    @patch("app.buyer.scan_exec.run_scan")
    def test_scan_now_respects_live_flag(self, mock_run_scan):
        """Test that scan_now respects live parameter."""
        from app.buyer.scan_exec import scan_now
        from unittest.mock import patch

        mock_run_scan.return_value = []

        with patch("app.buyer.scan_exec.get_session"):
            # Call with live=True
            scan_now(live=True)
            mock_run_scan.assert_called_with(use_live=True)

            # Call with live=False
            mock_run_scan.reset_mock()
            scan_now(live=False)
            mock_run_scan.assert_called_with(use_live=False)


class TestScanIntegration:
    """Integration tests for scan functionality."""

    @patch("app.buyer.scan_exec.run_scan")
    @patch("app.buyer.scan_exec.get_session")
    def test_full_blocking_scan_flow(self, mock_get_session, mock_run_scan, client):
        """Test complete flow of blocking scan from endpoint to result."""
        from app.buyer.search import ListingMatch

        # Setup mocks
        match = ListingMatch(
            id=1,
            title="Couch",
            price=50.0,
            condition="good",
            category="furniture>sofas",
            url="http://example.com/couch",
            thumbnail_url="http://example.com/couch.jpg",
            distance_mi=5.0,
            deal_score=90,
            is_free=True,
            source="craigslist",
            auto_message="Great deal",
        )

        mock_run_scan.return_value = [match]
        mock_session = MagicMock()
        mock_listing = MagicMock()
        mock_listing.id = 1
        mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = (
            mock_listing
        )
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Call endpoint
        response = client.post("/scan/run?live=1&blocking=1")
        assert response.status_code == 200

        data = response.json()
        assert data["mode"] == "blocking"
        assert data["total"] == 1
        assert data["live"] is True
