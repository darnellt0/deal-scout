"""Tests for input validation."""

import pytest

from app.core.validation import (
    ValidationError,
    sanitize_html,
    sanitize_sql_identifier,
    validate_email,
    validate_json_dict,
    validate_phone_number,
    validate_price,
    validate_string_length,
    validate_url,
)


class TestEmailValidation:
    """Test email validation."""

    def test_valid_email(self):
        """Valid emails should pass."""
        assert validate_email("user@example.com") == "user@example.com"

    def test_email_normalized(self):
        """Emails should be normalized to lowercase."""
        assert validate_email("User@Example.COM") == "user@example.com"

    def test_invalid_email(self):
        """Invalid emails should raise error."""
        with pytest.raises(ValidationError):
            validate_email("not-an-email")

    def test_empty_email(self):
        """Empty email should raise error."""
        with pytest.raises(ValidationError):
            validate_email("")


class TestPhoneValidation:
    """Test phone number validation."""

    def test_valid_phone(self):
        """Valid phone numbers should pass."""
        result = validate_phone_number("5551234567")
        assert "55512345" in result

    def test_phone_with_formatting(self):
        """Phone numbers with formatting should be normalized."""
        result = validate_phone_number("(555) 123-4567")
        assert "55512345" in result

    def test_phone_too_short(self):
        """Too-short phone numbers should raise error."""
        with pytest.raises(ValidationError):
            validate_phone_number("123")


class TestPriceValidation:
    """Test price validation."""

    def test_valid_price(self):
        """Valid prices should pass."""
        assert validate_price(99.99) == 99.99

    def test_price_zero(self):
        """Zero price should be valid."""
        assert validate_price(0) == 0

    def test_price_negative(self):
        """Negative prices should raise error."""
        with pytest.raises(ValidationError):
            validate_price(-10)

    def test_price_too_high(self):
        """Prices above max should raise error."""
        with pytest.raises(ValidationError):
            validate_price(2000000)


class TestURLValidation:
    """Test URL validation."""

    def test_valid_https_url(self):
        """Valid HTTPS URLs should pass."""
        url = "https://example.com/path"
        assert validate_url(url) == url

    def test_valid_http_url(self):
        """Valid HTTP URLs should pass."""
        url = "http://example.com"
        assert validate_url(url) == url

    def test_invalid_url_no_protocol(self):
        """URLs without protocol should raise error."""
        with pytest.raises(ValidationError):
            validate_url("example.com")

    def test_url_too_long(self):
        """URLs over 2000 chars should raise error."""
        long_url = "https://example.com/" + "a" * 2000
        with pytest.raises(ValidationError):
            validate_url(long_url)


class TestStringValidation:
    """Test string validation."""

    def test_valid_string(self):
        """Valid strings should pass."""
        result = validate_string_length("hello", min_length=1, max_length=10)
        assert result == "hello"

    def test_string_stripped(self):
        """Strings should be stripped."""
        result = validate_string_length("  hello  ", min_length=1, max_length=10)
        assert result == "hello"

    def test_string_too_short(self):
        """Strings below min length should raise error."""
        with pytest.raises(ValidationError):
            validate_string_length("", min_length=1, max_length=10)

    def test_string_too_long(self):
        """Strings above max length should raise error."""
        with pytest.raises(ValidationError):
            validate_string_length("a" * 100, min_length=1, max_length=10)


class TestHTMLSanitization:
    """Test HTML sanitization."""

    def test_remove_script_tags(self):
        """Script tags should be removed."""
        html = '<div>Safe</div><script>alert("xss")</script>'
        result = sanitize_html(html)
        assert "<script>" not in result
        assert "Safe" in result

    def test_remove_event_handlers(self):
        """Event handlers should be removed."""
        html = '<img src="x" onerror="alert(1)">'
        result = sanitize_html(html)
        assert "onerror" not in result


class TestSQLIdentifierSanitization:
    """Test SQL identifier sanitization."""

    def test_valid_identifier(self):
        """Valid identifiers should pass."""
        assert sanitize_sql_identifier("users_table") == "users_table"

    def test_remove_invalid_characters(self):
        """Invalid characters should be removed."""
        assert sanitize_sql_identifier("users-table!") == "userstable"

    def test_identifier_empty_after_sanitization(self):
        """Identifiers with no valid chars should raise error."""
        with pytest.raises(ValidationError):
            sanitize_sql_identifier("!@#$%")


class TestDictValidation:
    """Test dictionary validation."""

    def test_valid_dict(self):
        """Valid dicts should pass."""
        data = {"key": "value"}
        assert validate_json_dict(data) == data

    def test_dict_with_required_keys(self):
        """Dicts with required keys should pass."""
        data = {"id": 1, "name": "test"}
        assert validate_json_dict(data, required_keys=["id", "name"]) == data

    def test_dict_missing_required_keys(self):
        """Dicts missing required keys should raise error."""
        data = {"id": 1}
        with pytest.raises(ValidationError):
            validate_json_dict(data, required_keys=["id", "name"])

    def test_not_a_dict(self):
        """Non-dict values should raise error."""
        with pytest.raises(ValidationError):
            validate_json_dict("not a dict")
