"""Input validation utilities."""

import re
from typing import Any, Dict, Optional

from pydantic import BaseModel, ValidationError


class ValidationError(Exception):
    """Custom validation error."""
    pass


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False

    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_journey_id(journey_id: str) -> bool:
    """Validate journey ID format."""
    if not journey_id:
        return False

    # Journey ID should be alphanumeric with possible hyphens/underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, journey_id))


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> bool:
    """Validate date range format."""
    if not start_date and not end_date:
        return True

    # Basic date format validation (YYYY-MM-DD)
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'

    if start_date and not re.match(date_pattern, start_date):
        return False

    if end_date and not re.match(date_pattern, end_date):
        return False

    return True


def sanitize_filters(filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Sanitize and validate API filters."""
    if not filters:
        return {}

    sanitized = {}
    allowed_keys = {
        'start_date', 'end_date', 'page', 'page_size', 'status',
        'limit', 'offset', 'sort_by', 'sort_order'
    }

    for key, value in filters.items():
        if key in allowed_keys:
            # Basic type validation
            if key in ['page', 'page_size', 'limit', 'offset']:
                try:
                    sanitized[key] = int(value)
                except (ValueError, TypeError):
                    continue
            elif key in ['start_date', 'end_date']:
                if validate_date_range(value, None):
                    sanitized[key] = value
            elif key == 'sort_order':
                if value in ['asc', 'desc']:
                    sanitized[key] = value
            else:
                sanitized[key] = str(value)

    return sanitized


def validate_model_data(model_class: type[BaseModel], data: Dict[str, Any]) -> BaseModel:
    """Validate data against a Pydantic model."""
    try:
        return model_class(**data)
    except ValidationError as e:
        raise ValidationError(f"Validation failed: {e}")


def validate_required_fields(data: Dict[str, Any], required_fields: list[str]) -> None:
    """Validate that required fields are present and not empty."""
    missing_fields = []

    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            missing_fields.append(field)

    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}")


def validate_string_length(value: str, max_length: int, field_name: str) -> None:
    """Validate string length."""
    if len(value) > max_length:
        raise ValidationError(
            f"{field_name} exceeds maximum length of {max_length} characters")


def validate_numeric_range(value: int, min_value: int, max_value: int, field_name: str) -> None:
    """Validate numeric value is within range."""
    if value < min_value or value > max_value:
        raise ValidationError(
            f"{field_name} must be between {min_value} and {max_value}")
