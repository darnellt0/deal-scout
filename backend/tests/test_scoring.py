"""Tests for deal scoring logic."""

import pytest
from datetime import datetime, timedelta

from app.core.scoring import compute_deal_score


class TestDealScoring:
    """Test deal scoring computation."""

    def test_free_item_perfect_condition(self):
        """Free items in excellent condition should score highest."""
        score = compute_deal_score(
            price=0,
            condition="excellent",
            is_free=True,
            recency_hours=1,
            has_photo=True,
            keyword_match=True,
            distance_mi=5,
        )
        assert score > 90

    def test_expensive_item_poor_condition(self):
        """Expensive items in poor condition should score lowest."""
        score = compute_deal_score(
            price=500,
            condition="poor",
            is_free=False,
            recency_hours=48,
            has_photo=False,
            keyword_match=False,
            distance_mi=50,
        )
        assert score < 30

    def test_moderate_score(self):
        """Moderate listings should score in the middle."""
        score = compute_deal_score(
            price=150,
            condition="good",
            is_free=False,
            recency_hours=12,
            has_photo=True,
            keyword_match=True,
            distance_mi=25,
        )
        assert 40 < score < 80

    def test_old_listings_penalized(self):
        """Old listings should be penalized."""
        recent_score = compute_deal_score(
            price=100,
            condition="good",
            is_free=False,
            recency_hours=1,
            has_photo=True,
            keyword_match=True,
            distance_mi=10,
        )
        old_score = compute_deal_score(
            price=100,
            condition="good",
            is_free=False,
            recency_hours=72,
            has_photo=True,
            keyword_match=True,
            distance_mi=10,
        )
        assert recent_score > old_score

    def test_distance_affects_score(self):
        """Closer listings should score higher."""
        close_score = compute_deal_score(
            price=100,
            condition="good",
            is_free=False,
            recency_hours=12,
            has_photo=True,
            keyword_match=True,
            distance_mi=5,
        )
        far_score = compute_deal_score(
            price=100,
            condition="good",
            is_free=False,
            recency_hours=12,
            has_photo=True,
            keyword_match=True,
            distance_mi=45,
        )
        assert close_score > far_score

    def test_photos_increase_score(self):
        """Listings with photos should score higher."""
        with_photo = compute_deal_score(
            price=100,
            condition="good",
            is_free=False,
            recency_hours=12,
            has_photo=True,
            keyword_match=True,
            distance_mi=10,
        )
        without_photo = compute_deal_score(
            price=100,
            condition="good",
            is_free=False,
            recency_hours=12,
            has_photo=False,
            keyword_match=True,
            distance_mi=10,
        )
        assert with_photo > without_photo

    def test_keyword_match_increases_score(self):
        """Listings matching keywords should score higher."""
        with_match = compute_deal_score(
            price=100,
            condition="good",
            is_free=False,
            recency_hours=12,
            has_photo=True,
            keyword_match=True,
            distance_mi=10,
        )
        without_match = compute_deal_score(
            price=100,
            condition="good",
            is_free=False,
            recency_hours=12,
            has_photo=True,
            keyword_match=False,
            distance_mi=10,
        )
        assert with_match > without_match

    @pytest.mark.parametrize("condition", ["poor", "fair", "good", "great", "excellent"])
    def test_condition_ordering(self, condition):
        """Higher condition should always score higher."""
        score = compute_deal_score(
            price=100,
            condition=condition,
            is_free=False,
            recency_hours=12,
            has_photo=True,
            keyword_match=True,
            distance_mi=10,
        )
        assert 0 <= score <= 100
