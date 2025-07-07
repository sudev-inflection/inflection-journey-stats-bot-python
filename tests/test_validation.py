"""Tests for validation utilities."""

import pytest

from src.utils.validation import (
    validate_email,
    validate_journey_id,
    validate_date_range,
    sanitize_filters,
    validate_required_fields,
    validate_string_length,
    validate_numeric_range,
)


class TestEmailValidation:
    """Test email validation functions."""

    def test_valid_emails(self):
        """Test valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@numbers.com",
        ]

        for email in valid_emails:
            assert validate_email(email) is True

    def test_invalid_emails(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "",
            "invalid-email",
            "@example.com",
            "user@",
            "user..name@example.com",
        ]

        for email in invalid_emails:
            assert validate_email(email) is False


class TestJourneyIDValidation:
    """Test journey ID validation functions."""

    def test_valid_journey_ids(self):
        """Test valid journey IDs."""
        valid_ids = [
            "journey_123",
            "journey-456",
            "welcome_series",
            "onboarding_flow_2024",
            "123456",
        ]

        for journey_id in valid_ids:
            assert validate_journey_id(journey_id) is True

    def test_invalid_journey_ids(self):
        """Test invalid journey IDs."""
        invalid_ids = [
            "",
            "journey@123",
            "journey#456",
            "journey space",
            "journey.123",
        ]

        for journey_id in invalid_ids:
            assert validate_journey_id(journey_id) is False


class TestDateRangeValidation:
    """Test date range validation functions."""

    def test_valid_date_ranges(self):
        """Test valid date ranges."""
        valid_ranges = [
            ("2024-01-01", "2024-01-31"),
            ("2024-12-31", None),
            (None, "2024-12-31"),
            (None, None),
        ]

        for start_date, end_date in valid_ranges:
            assert validate_date_range(start_date, end_date) is True

    def test_invalid_date_ranges(self):
        """Test invalid date ranges."""
        invalid_ranges = [
            ("2024/01/01", "2024-01-31"),
            ("2024-13-01", "2024-01-31"),
            ("invalid", "2024-01-31"),
        ]

        for start_date, end_date in invalid_ranges:
            assert validate_date_range(start_date, end_date) is False


class TestFilterSanitization:
    """Test filter sanitization functions."""

    def test_sanitize_filters(self):
        """Test filter sanitization."""
        input_filters = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "page": "1",
            "page_size": "10",
            "status": "active",
            "invalid_key": "should_be_removed",
            "sort_order": "asc",
        }

        expected = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "page": 1,
            "page_size": 10,
            "status": "active",
            "sort_order": "asc",
        }

        result = sanitize_filters(input_filters)
        assert result == expected

    def test_sanitize_empty_filters(self):
        """Test sanitizing empty filters."""
        assert sanitize_filters({}) == {}
        assert sanitize_filters(None) == {}


class TestRequiredFieldsValidation:
    """Test required fields validation functions."""

    def test_valid_required_fields(self):
        """Test valid required fields."""
        data = {"name": "test", "email": "test@example.com"}
        required_fields = ["name", "email"]

        # Should not raise an exception
        validate_required_fields(data, required_fields)

    def test_missing_required_fields(self):
        """Test missing required fields."""
        data = {"name": "test"}
        required_fields = ["name", "email"]

        with pytest.raises(Exception) as exc_info:
            validate_required_fields(data, required_fields)

        assert "Missing required fields" in str(exc_info.value)


class TestStringLengthValidation:
    """Test string length validation functions."""

    def test_valid_string_length(self):
        """Test valid string length."""
        # Should not raise an exception
        validate_string_length("test", 10, "test_field")

    def test_invalid_string_length(self):
        """Test invalid string length."""
        with pytest.raises(Exception) as exc_info:
            validate_string_length("very_long_string", 5, "test_field")

        assert "exceeds maximum length" in str(exc_info.value)


class TestNumericRangeValidation:
    """Test numeric range validation functions."""

    def test_valid_numeric_range(self):
        """Test valid numeric range."""
        # Should not raise an exception
        validate_numeric_range(5, 1, 10, "test_field")

    def test_invalid_numeric_range(self):
        """Test invalid numeric range."""
        with pytest.raises(Exception) as exc_info:
            validate_numeric_range(15, 1, 10, "test_field")

        assert "must be between" in str(exc_info.value)
