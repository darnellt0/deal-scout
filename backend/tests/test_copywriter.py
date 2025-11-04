"""Unit tests for copywriter module."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from app.seller.copywriter import (
    generate_copy,
    _build_fallback_title,
    _build_fallback_description,
    _build_fallback_highlights,
    _build_fallback_tags,
)


class TestGenerateCopy:
    """Tests for generate_copy function."""

    def test_generate_copy_without_openai(self):
        """Test that generate_copy returns fallback when OpenAI is not configured."""
        with patch("app.seller.copywriter.settings") as mock_settings:
            mock_settings.openai_api_key = ""

            result = generate_copy(
                category="laptop",
                attributes={"brand": "Dell", "model": "XPS 13"},
                condition="good",
                price=500.0,
                photos_count=3,
            )

            # Should return dict with required keys
            assert "title" in result
            assert "description" in result
            assert "highlights" in result
            assert "tags" in result
            assert "confidence" in result

            # Check data types
            assert isinstance(result["title"], str)
            assert isinstance(result["description"], str)
            assert isinstance(result["highlights"], list)
            assert isinstance(result["tags"], list)
            assert isinstance(result["confidence"], float)

            # Title should contain brand and model
            assert "Dell" in result["title"]
            assert "XPS 13" in result["title"]

    @patch("app.seller.copywriter.openai")
    def test_generate_copy_with_openai_success(self, mock_openai):
        """Test that generate_copy uses OpenAI when configured."""
        with patch("app.seller.copywriter.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"

            # Mock OpenAI response
            mock_response = {
                "choices": [
                    {
                        "message": {
                            "content": """{
                                "title": "Dell XPS 13 Laptop - Good Condition",
                                "description": "High quality Dell XPS 13 laptop in good condition. Perfect for work and personal use.",
                                "highlights": ["Dell XPS 13 model", "Good condition", "Fast performance"],
                                "tags": ["laptop", "dell", "xps", "computer", "electronics"]
                            }"""
                        }
                    }
                ]
            }
            mock_openai.ChatCompletion.create.return_value = mock_response

            result = generate_copy(
                category="laptop",
                attributes={"brand": "Dell", "model": "XPS 13"},
                condition="good",
                price=500.0,
                photos_count=3,
            )

            # Should call OpenAI
            mock_openai.ChatCompletion.create.assert_called_once()

            # Should return parsed response
            assert "Dell XPS 13" in result["title"]
            assert "Good condition" in result["highlights"]
            assert "laptop" in result["tags"]
            assert result["confidence"] == 0.9

    @patch("app.seller.copywriter.openai")
    def test_generate_copy_openai_error_fallback(self, mock_openai):
        """Test that generate_copy falls back on OpenAI error."""
        with patch("app.seller.copywriter.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"

            # Mock OpenAI error
            mock_openai.ChatCompletion.create.side_effect = Exception("API Error")

            result = generate_copy(
                category="laptop",
                attributes={"brand": "Dell"},
                condition="good",
            )

            # Should still return valid result
            assert "title" in result
            assert "description" in result
            assert "highlights" in result
            assert "tags" in result
            assert result["confidence"] == 0.5

    def test_generate_copy_title_length_limit(self):
        """Test that generated titles respect 80 character limit."""
        with patch("app.seller.copywriter.settings") as mock_settings:
            mock_settings.openai_api_key = ""

            result = generate_copy(
                category="laptop",
                attributes={
                    "brand": "Dell",
                    "model": "XPS 13 with Extra Long Model Name That Should Be Truncated",
                },
                condition="excellent",
            )

            # Title should be limited to 80 chars
            assert len(result["title"]) <= 80

    def test_generate_copy_highlights_limit(self):
        """Test that highlights are limited to 5 items."""
        with patch("app.seller.copywriter.settings") as mock_settings:
            mock_settings.openai_api_key = ""

            result = generate_copy(
                category="laptop",
                attributes={"brand": "Dell", "model": "XPS 13"},
                condition="good",
            )

            # Highlights should be limited to 5 items
            assert len(result["highlights"]) <= 5

    def test_generate_copy_tags_limit(self):
        """Test that tags are limited to 10 items."""
        with patch("app.seller.copywriter.settings") as mock_settings:
            mock_settings.openai_api_key = ""

            result = generate_copy(
                category="laptop",
                attributes={"brand": "Dell"},
                condition="good",
            )

            # Tags should be limited to 10 items
            assert len(result["tags"]) <= 10


class TestFallbackFunctions:
    """Tests for fallback helper functions."""

    def test_build_fallback_title_with_brand(self):
        """Test fallback title includes brand."""
        title = _build_fallback_title(
            "laptop", {"brand": "Dell", "model": "XPS 13"}
        )

        assert "Dell" in title
        assert "XPS 13" in title
        assert len(title) <= 80

    def test_build_fallback_title_without_brand(self):
        """Test fallback title without brand."""
        title = _build_fallback_title("laptop", {})

        assert "Laptop" in title
        assert len(title) <= 80

    def test_build_fallback_description(self):
        """Test fallback description structure."""
        desc = _build_fallback_description(
            "laptop", {"brand": "Dell", "model": "XPS 13"}, "good", 500.0
        )

        assert "laptop" in desc.lower()
        assert "good condition" in desc.lower()
        assert "$500" in desc
        assert "Dell" in desc

    def test_build_fallback_highlights(self):
        """Test fallback highlights generation."""
        highlights = _build_fallback_highlights(
            {"brand": "Dell", "model": "XPS 13", "color": "Silver"}, "good"
        )

        assert isinstance(highlights, list)
        assert len(highlights) >= 3
        assert len(highlights) <= 5
        assert any("good" in h.lower() for h in highlights)

    def test_build_fallback_tags(self):
        """Test fallback tags generation."""
        tags = _build_fallback_tags("laptop", {"brand": "Dell", "model": "XPS 13"})

        assert isinstance(tags, list)
        assert len(tags) <= 10
        assert "laptop" in tags
        assert "dell" in tags

    def test_build_fallback_tags_lowercase(self):
        """Test that fallback tags are lowercase."""
        tags = _build_fallback_tags("Laptop", {"brand": "DELL"})

        # All tags should be lowercase
        assert all(tag == tag.lower() for tag in tags)
