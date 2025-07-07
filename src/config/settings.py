"""Configuration settings for Inflection.io MCP Server."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration - Updated to match HAR file analysis
    inflection_api_base_url_auth: str = Field(
        default="https://auth.inflection.io/api/v1",
        description="Inflection.io Auth API base URL"
    )
    inflection_api_base_url_campaign: str = Field(
        default="https://campaign.inflection.io/api/v2",
        description="Inflection.io Campaign API base URL (v2)"
    )
    inflection_api_base_url_campaign_v3: str = Field(
        default="https://campaign.inflection.io/api/v3",
        description="Inflection.io Campaign API base URL (v3)"
    )

    # API Endpoints - Updated based on HAR file analysis
    inflection_login_endpoint: str = Field(
        default="/accounts/login",
        description="Login endpoint"
    )
    inflection_journeys_endpoint: str = Field(
        default="/campaigns/campaign.list",
        description="Journeys listing endpoint"
    )

    # Report Endpoints from HAR file
    inflection_reports_runs_list: str = Field(
        default="/campaigns/reports/runs.list",
        description="Report runs list endpoint"
    )
    inflection_reports_runs_stats: str = Field(
        default="/campaigns/reports/runs.list.stats",
        description="Report runs stats endpoint"
    )
    inflection_reports_recipient_engagement: str = Field(
        default="/campaigns/reports/stats.recipient_engagement",
        description="Recipient engagement stats endpoint"
    )
    inflection_reports_aggregate: str = Field(
        default="/campaigns/reports/stats.aggregate",
        description="Aggregate stats endpoint"
    )
    inflection_reports_top_email_client_click: str = Field(
        default="/campaigns/reports/stats.top_email_client.click",
        description="Top email client click stats endpoint"
    )
    inflection_reports_top_email_client_open: str = Field(
        default="/campaigns/reports/stats.top_email_client.open",
        description="Top email client open stats endpoint"
    )
    inflection_reports_top_link: str = Field(
        default="/campaigns/reports/stats.top_link",
        description="Top link stats endpoint"
    )

    # V3 API Endpoints
    inflection_reports_bounce_stats: str = Field(
        default="/campaigns/{campaign_id}/stats",
        description="Bounce stats endpoint (v3)"
    )
    inflection_reports_bounce_classifications: str = Field(
        default="/campaigns/stats/bounce_classifications",
        description="Bounce classifications endpoint (v3)"
    )

    # Authentication
    inflection_email: Optional[str] = Field(
        default=None,
        description="Inflection.io account email"
    )
    inflection_password: Optional[str] = Field(
        default=None,
        description="Inflection.io account password"
    )

    # Testing Configuration
    inflection_test_journey_id: str = Field(
        default="test-journey-123",
        description="Test journey ID for API testing"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    # Server Configuration
    mcp_server_host: str = Field(
        default="localhost",
        description="MCP server host"
    )
    mcp_server_port: int = Field(
        default=8000,
        description="MCP server port"
    )

    # HTTP Client Configuration
    api_timeout: int = Field(
        default=10000,
        description="API request timeout in milliseconds"
    )
    max_requests_per_minute: int = Field(
        default=10,
        description="Maximum requests per minute"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
