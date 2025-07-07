"""Login tool for Inflection.io MCP Server."""

from typing import Any, Dict

import structlog
from mcp import TextContent

from ..auth.inflection import InflectionAuth
from ..models.auth import AuthState
from ..utils.validation import validate_email

logger = structlog.get_logger(__name__)


async def inflection_login(
    email: str,
    password: str,
    auth_state: AuthState
) -> TextContent:
    """
    Authenticate with Inflection.io using email and password.

    Args:
        email: User's email address
        password: User's password
        auth_state: Authentication state manager

    Returns:
        TextContent with authentication result
    """
    logger.info("MCP tool called: inflection_login", email=email)

    try:
        # Validate inputs
        if not validate_email(email):
            return TextContent(
                type="text",
                text="❌ Authentication failed: Invalid email format"
            )

        if not password or not password.strip():
            return TextContent(
                type="text",
                text="❌ Authentication failed: Password is required"
            )

        # Attempt authentication
        auth_manager = InflectionAuth(auth_state)
        auth_response = await auth_manager.login(email, password)

        # Format success response
        success_message = f"""✅ Authentication successful!

**User ID:** {auth_response.user_id or 'Not provided'}
**Token Expires:** {auth_response.expires_at or 'Not specified'}

You can now use other Inflection.io tools to access your marketing data."""

        logger.info("Login successful", user_id=auth_response.user_id)
        return TextContent(type="text", text=success_message)

    except ValueError as e:
        logger.warning("Login validation failed", error=str(e))
        return TextContent(
            type="text",
            text=f"❌ Authentication failed: {str(e)}"
        )
    except Exception as e:
        logger.error("Login failed", error=str(e))
        return TextContent(
            type="text",
            text=f"❌ Authentication failed: {str(e)}"
        )
