"""Inflection.io authentication handling."""

from typing import Optional

import structlog

from ..models.auth import AuthResponse, AuthState
from ..utils.api_client import InflectionAPIClient
from ..utils.validation import validate_email

logger = structlog.get_logger(__name__)


class InflectionAuth:
    """Inflection.io authentication manager."""

    def __init__(self, auth_state: AuthState):
        self.auth_state = auth_state

    async def login(self, email: str, password: str) -> AuthResponse:
        """Authenticate with Inflection.io API."""
        logger.info("Attempting login", email=email)

        # Validate email format
        if not validate_email(email):
            raise ValueError("Invalid email format")

        # Validate password is not empty
        if not password or not password.strip():
            raise ValueError("Password is required")

        try:
            async with InflectionAPIClient(self.auth_state) as client:
                response_data = await client.login(email, password)

                # Parse response with our model
                auth_response = AuthResponse(**response_data)

                # Update authentication state
                self.auth_state.update_from_response(auth_response)

                logger.info("Login successful", user_id=auth_response.user_id)
                return auth_response

        except Exception as e:
            logger.error("Login failed", error=str(e))
            # Clear any partial authentication state
            self.auth_state.clear()
            raise

    async def refresh_token(self) -> Optional[AuthResponse]:
        """Refresh authentication token if refresh token is available."""
        if not self.auth_state.refresh_token:
            logger.warning("No refresh token available")
            return None

        logger.info("Attempting token refresh")

        try:
            # This would need to be implemented based on Inflection.io's refresh endpoint
            # For now, we'll return None to indicate refresh is not available
            logger.warning("Token refresh not implemented")
            return None

        except Exception as e:
            logger.error("Token refresh failed", error=str(e))
            self.auth_state.clear()
            return None

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return self.auth_state.is_authenticated()

    def get_auth_headers(self) -> dict:
        """Get authentication headers for API requests."""
        return self.auth_state.get_auth_headers()

    def logout(self) -> None:
        """Clear authentication state."""
        logger.info("Logging out user")
        self.auth_state.clear()

    async def ensure_authenticated(self) -> bool:
        """Ensure user is authenticated, attempting refresh if needed."""
        if self.is_authenticated():
            return True

        # Try to refresh token
        auth_response = await self.refresh_token()
        if auth_response:
            return True

        logger.warning("User is not authenticated and refresh failed")
        return False
