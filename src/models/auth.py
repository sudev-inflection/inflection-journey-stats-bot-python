"""Authentication data models."""

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field


class Account(BaseModel):
    """Account information from API response."""
    id: int = Field(..., description="Account ID")
    organisation_id: int = Field(..., description="Organization ID")
    name: str = Field(..., description="Account name")
    email: str = Field(..., description="Account email")
    is_active: bool = Field(..., description="Account active status")
    is_email_verified: bool = Field(...,
                                    description="Email verification status")
    is_federated_user: bool = Field(..., description="Federated user status")
    time_created: str = Field(..., description="Account creation time")
    time_updated: str = Field(..., description="Account update time")


class Role(BaseModel):
    """Role information from API response."""
    role_id: int = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role name")


class Organisation(BaseModel):
    """Organization information from API response."""
    id: int = Field(..., description="Organization ID")
    name: str = Field(..., description="Organization name")
    slug: str = Field(..., description="Organization slug")
    domain: str = Field(..., description="Organization domain")
    is_active: bool = Field(..., description="Organization active status")
    time_created: str = Field(..., description="Organization creation time")
    time_updated: str = Field(..., description="Organization update time")


class Session(BaseModel):
    """Session information from API response."""
    refresh_token: str = Field(..., description="Refresh token")
    access_token: str = Field(..., description="Access token")
    created_at: str = Field(..., description="Session creation time")
    status: str = Field(..., description="Session status")
    session_id: str = Field(..., description="Session ID")
    refresh_expires_at: str = Field(...,
                                    description="Refresh token expiration")
    access_expires_at: str = Field(..., description="Access token expiration")


class AuthResponse(BaseModel):
    """Authentication response from Inflection.io API."""

    account: Account = Field(..., description="Account information")
    roles: list[Role] = Field(..., description="User roles")
    organisation: Organisation = Field(...,
                                       description="Organization information")
    session: Session = Field(..., description="Session information")

    @property
    def token(self) -> str:
        """Get the access token from session."""
        return self.session.access_token

    @property
    def user_id(self) -> str:
        """Get the user ID from account."""
        return str(self.account.id)

    @property
    def expires_at(self) -> str:
        """Get the token expiration time."""
        return self.session.access_expires_at

    @property
    def refresh_token(self) -> str:
        """Get the refresh token from session."""
        return self.session.refresh_token

    class Config:
        json_schema_extra = {
            "example": {
                "account": {
                    "id": 344,
                    "organisation_id": 115,
                    "name": "sudev suresh",
                    "email": "sudev+1@inflection.io",
                    "is_active": True,
                    "is_email_verified": True,
                    "is_federated_user": False,
                    "time_created": "2023-11-29T05:29:05",
                    "time_updated": "2023-11-29T05:30:53"
                },
                "roles": [
                    {
                        "role_id": 2,
                        "role_name": "CUSTOMER_ORG_ADMIN"
                    }
                ],
                "organisation": {
                    "id": 115,
                    "name": "pmteam",
                    "slug": "pmteam-com",
                    "domain": "pmteam.com",
                    "is_active": True,
                    "time_created": "2023-09-18T11:02:17",
                    "time_updated": "2023-09-18T11:02:47"
                },
                "session": {
                    "refresh_token": "d7b00e30bf7d42da_d31b273b8cbe46bcb06c0bc39478be7f",
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "created_at": "2025-07-04T08:12:44.940413",
                    "status": "ACTIVE",
                    "session_id": "d7b00e30bf7d42da",
                    "refresh_expires_at": "2025-07-06T08:12:44+00:00",
                    "access_expires_at": "2025-07-04T09:12:44+00:00"
                }
            }
        }


class AuthState:
    """Authentication state manager."""

    def __init__(self):
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.expires_at: Optional[datetime] = None
        self.refresh_token: Optional[str] = None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated and token is valid."""
        if not self.token:
            return False

        if not self.expires_at:
            return True  # Assume valid if no expiration provided

        # Add 5 minute buffer before expiration
        buffer_time = datetime.utcnow() + timedelta(minutes=5)
        return self.expires_at > buffer_time

    def update_from_response(self, response: AuthResponse) -> None:
        """Update authentication state from API response."""
        self.token = response.token
        self.user_id = response.user_id
        self.refresh_token = response.refresh_token

        if response.expires_at:
            try:
                self.expires_at = datetime.fromisoformat(
                    response.expires_at.replace('Z', '+00:00')
                )
            except ValueError:
                # If parsing fails, set expiration to 1 hour from now
                self.expires_at = datetime.utcnow() + timedelta(hours=1)
        else:
            # Default to 1 hour if no expiration provided
            self.expires_at = datetime.utcnow() + timedelta(hours=1)

    def clear(self) -> None:
        """Clear authentication state."""
        self.token = None
        self.user_id = None
        self.expires_at = None
        self.refresh_token = None

    def get_auth_headers(self) -> dict:
        """Get authentication headers for API requests."""
        if not self.token:
            raise ValueError("No authentication token available")

        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
