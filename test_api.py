#!/usr/bin/env python3
"""
Inflection.io API Testing Script

This script tests the Inflection.io APIs to understand the response formats
before building the MCP server. It validates authentication, journey listing,
and email reports endpoints.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import structlog
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


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
    """Authentication response model."""
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


class Journey(BaseModel):
    """Journey data model."""
    id: str = Field(..., description="Journey ID")
    name: str = Field(..., description="Journey name")
    status: Optional[str] = Field(None, description="Journey status")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp")


class EmailReport(BaseModel):
    """Email report data model."""
    journey_id: str = Field(..., description="Journey ID")
    sent_count: Optional[int] = Field(
        None, description="Number of emails sent")
    open_count: Optional[int] = Field(None, description="Number of opens")
    click_count: Optional[int] = Field(None, description="Number of clicks")
    bounce_count: Optional[int] = Field(None, description="Number of bounces")
    unsubscribe_count: Optional[int] = Field(
        None, description="Number of unsubscribes")
    report_date: Optional[str] = Field(None, description="Report date")


class InflectionAPITester:
    """Test Inflection.io APIs and save response examples."""

    def __init__(self, timeout: int = 30):
        # Get API URLs from environment
        self.auth_base_url = os.getenv(
            "INFLECTION_API_BASE_URL_AUTH", "https://auth.inflection.io/api/v1")
        self.campaign_base_url = os.getenv(
            "INFLECTION_API_BASE_URL_CAMPAIGN", "https://campaign.inflection.io/api/v2")
        self.campaign_v3_base_url = os.getenv(
            "INFLECTION_API_BASE_URL_CAMPAIGN_V3", "https://campaign.inflection.io/api/v3")

        # Get endpoints from environment
        self.login_endpoint = os.getenv(
            "INFLECTION_LOGIN_ENDPOINT", "/accounts/login")
        self.journeys_endpoint = os.getenv(
            "INFLECTION_JOURNEYS_ENDPOINT", "/campaigns/campaign.list")

        self.timeout = timeout
        self.token: Optional[str] = None
        self.examples_dir = Path("examples")
        self.examples_dir.mkdir(exist_ok=True)

        # Create examples subdirectories
        (self.examples_dir / "auth").mkdir(exist_ok=True)
        (self.examples_dir / "journeys").mkdir(exist_ok=True)
        (self.examples_dir / "reports").mkdir(exist_ok=True)

    async def test_login(self, email: str, password: str) -> bool:
        """Test login API and store JWT token."""
        logger.info("Testing login API", email=email,
                    auth_base_url=self.auth_base_url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.auth_base_url.rstrip('/')}{self.login_endpoint}"
                response = await client.post(
                    url,
                    json={"email": email, "password": password},
                    headers={"Content-Type": "application/json"}
                )

                logger.info(
                    "Login response received",
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info("Login successful", user_id=data.get(
                        "account", {}).get("id"))

                    # Try to parse with our model
                    try:
                        auth_response = AuthResponse(**data)
                        self.token = auth_response.token
                        logger.info("Token stored successfully",
                                    user_id=auth_response.user_id)
                    except Exception as e:
                        logger.warning(
                            "Failed to parse auth response with model", error=str(e))
                        # Fallback: try to extract token from nested structure
                        session_data = data.get("session", {})
                        self.token = session_data.get("access_token")
                        if not self.token:
                            logger.error(
                                "Could not extract access token from response")
                            return False
                        logger.info("Token extracted using fallback method")

                    # Save response example
                    self._save_example("auth", "login_success.json", data)
                    return True
                else:
                    logger.error(
                        "Login failed",
                        status_code=response.status_code,
                        response_text=response.text
                    )
                    self._save_example("auth", "login_failure.json", {
                        "status_code": response.status_code,
                        "response": response.text
                    })
                    return False

        except httpx.TimeoutException:
            logger.error("Login request timed out")
            return False
        except httpx.RequestError as e:
            logger.error("Login request failed", error=str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error during login", error=str(e))
            return False

    async def test_journeys(self) -> bool:
        """Test journey listing API."""
        if not self.token:
            logger.error("No authentication token available")
            return False

        logger.info("Testing journeys API")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.campaign_base_url.rstrip('/')}{self.journeys_endpoint}"

                # Build the payload according to the API specification
                payload = {
                    "page_size": 30,
                    "page_number": 1,
                    "query": {
                        "search": {
                            "keyword": "",
                            "fields": ["name"]
                        }
                    }
                }

                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    }
                )

                logger.info(
                    "Journeys response received",
                    status_code=response.status_code
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info("Journeys retrieved successfully",
                                count=len(data.get("journeys", [])))

                    # Try to parse with our model
                    try:
                        journeys = [Journey(**journey)
                                    for journey in data.get("journeys", [])]
                        logger.info("Journeys parsed successfully",
                                    count=len(journeys))
                    except Exception as e:
                        logger.warning(
                            "Failed to parse journeys with model", error=str(e))

                    self._save_example("journeys", "journeys_list.json", data)
                    return True
                else:
                    logger.error(
                        "Journeys request failed",
                        status_code=response.status_code,
                        response_text=response.text
                    )
                    self._save_example("journeys", "journeys_failure.json", {
                        "status_code": response.status_code,
                        "response": response.text
                    })
                    return False

        except httpx.TimeoutException:
            logger.error("Journeys request timed out")
            return False
        except httpx.RequestError as e:
            logger.error("Journeys request failed", error=str(e))
            return False
        except Exception as e:
            logger.error(
                "Unexpected error during journeys request", error=str(e))
            return False

    async def test_journeys_with_search(self, search_keyword: str = "test") -> bool:
        """Test journey listing API with search."""
        if not self.token:
            logger.error("No authentication token available")
            return False

        logger.info("Testing journeys API with search",
                    search_keyword=search_keyword)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.campaign_base_url.rstrip('/')}{self.journeys_endpoint}"

                # Build the payload with search
                payload = {
                    "page_size": 10,
                    "page_number": 1,
                    "query": {
                        "search": {
                            "keyword": search_keyword,
                            "fields": ["name"]
                        }
                    }
                }

                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    }
                )

                logger.info(
                    "Journeys search response received",
                    status_code=response.status_code,
                    search_keyword=search_keyword
                )

                if response.status_code == 200:
                    data = response.json()
                    journeys_count = len(data.get("journeys", []))
                    logger.info("Journeys search successful",
                                count=journeys_count,
                                search_keyword=search_keyword)

                    # Try to parse with our model
                    try:
                        journeys = [Journey(**journey)
                                    for journey in data.get("journeys", [])]
                        logger.info("Journeys parsed successfully",
                                    count=len(journeys))
                    except Exception as e:
                        logger.warning(
                            "Failed to parse journeys with model", error=str(e))

                    self._save_example(
                        "journeys", f"journeys_search_{search_keyword}.json", data)
                    return True
                else:
                    logger.error(
                        "Journeys search request failed",
                        status_code=response.status_code,
                        response_text=response.text,
                        search_keyword=search_keyword
                    )
                    self._save_example("journeys", f"journeys_search_{search_keyword}_failure.json", {
                        "status_code": response.status_code,
                        "response": response.text
                    })
                    return False

        except httpx.TimeoutException:
            logger.error("Journeys search request timed out")
            return False
        except httpx.RequestError as e:
            logger.error("Journeys search request failed", error=str(e))
            return False
        except Exception as e:
            logger.error(
                "Unexpected error during journeys search request", error=str(e))
            return False

    async def test_email_reports(self, journey_id: str) -> bool:
        """Test email reports API using the new v2/v3 endpoints."""
        if not self.token:
            logger.error("No authentication token available")
            return False

        logger.info("Testing email reports API", journey_id=journey_id)

        # Test multiple report endpoints
        endpoints_to_test = [
            {
                "name": "Report Runs List",
                "url": "https://campaign.inflection.io/api/v2/campaigns/reports/runs.list",
                "payload": {
                    "campaign_id": journey_id,
                    "start_date": "2025-06-07T12:38:40+05:30",
                    "end_date": "2025-07-07T12:38:40+05:30",
                    "page_number": 1,
                    "page_size": 15,
                    "show_non_empty_runs": False
                }
            },
            {
                "name": "Recipient Engagement Stats",
                "url": "https://campaign.inflection.io/api/v2/campaigns/reports/stats.recipient_engagement",
                "payload": {
                    "campaign_id": journey_id,
                    "start_date": "2025-06-07T12:38:40+05:30",
                    "end_date": "2025-07-07T12:38:40+05:30",
                    "query": {
                        "search": {
                            "keyword": "",
                            "fields": ["email", "name"]
                        }
                    },
                    "page_number": 1,
                    "page_size": 15
                }
            },
            {
                "name": "Aggregate Stats",
                "url": "https://campaign.inflection.io/api/v2/campaigns/reports/stats.aggregate",
                "payload": {
                    "campaign_id": journey_id,
                    "start_date": "2025-06-07T12:38:40+05:30",
                    "end_date": "2025-07-07T12:38:40+05:30"
                }
            },
            {
                "name": "Top Email Client Click Stats",
                "url": "https://campaign.inflection.io/api/v2/campaigns/reports/stats.top_email_client.click",
                "payload": {
                    "campaign_id": journey_id,
                    "start_date": "2025-06-07T12:38:40+05:30",
                    "end_date": "2025-07-07T12:38:40+05:30",
                    "page_number": 1,
                    "page_size": 1000
                }
            },
            {
                "name": "Top Email Client Open Stats",
                "url": "https://campaign.inflection.io/api/v2/campaigns/reports/stats.top_email_client.open",
                "payload": {
                    "campaign_id": journey_id,
                    "start_date": "2025-06-07T12:38:40+05:30",
                    "end_date": "2025-07-07T12:38:40+05:30",
                    "page_number": 1,
                    "page_size": 1000
                }
            },
            {
                "name": "Top Link Stats",
                "url": "https://campaign.inflection.io/api/v2/campaigns/reports/stats.top_link",
                "payload": {
                    "campaign_id": journey_id,
                    "start_date": "2025-06-07T12:38:40+05:30",
                    "end_date": "2025-07-07T12:38:40+05:30",
                    "page_number": 1,
                    "page_size": 5
                }
            }
        ]

        success_count = 0
        total_endpoints = len(endpoints_to_test)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for endpoint_info in endpoints_to_test:
                    try:
                        logger.info(
                            f"Testing {endpoint_info['name']}", url=endpoint_info['url'])

                        response = await client.post(
                            endpoint_info['url'],
                            json=endpoint_info['payload'],
                            headers={
                                "Authorization": f"Bearer {self.token}",
                                "Content-Type": "application/json"
                            }
                        )

                        logger.info(
                            f"{endpoint_info['name']} response received",
                            status_code=response.status_code
                        )

                        if response.status_code == 200:
                            data = response.json()
                            logger.info(
                                f"{endpoint_info['name']} retrieved successfully")

                            # Save successful response
                            safe_name = endpoint_info['name'].lower().replace(
                                ' ', '_')
                            self._save_example(
                                "reports", f"{safe_name}_{journey_id}.json", data)
                            success_count += 1
                        else:
                            logger.error(
                                f"{endpoint_info['name']} request failed",
                                status_code=response.status_code,
                                response_text=response.text
                            )
                            # Save failed response
                            safe_name = endpoint_info['name'].lower().replace(
                                ' ', '_')
                            self._save_example("reports", f"{safe_name}_{journey_id}_failure.json", {
                                "status_code": response.status_code,
                                "response": response.text
                            })

                    except httpx.TimeoutException:
                        logger.error(
                            f"{endpoint_info['name']} request timed out")
                    except httpx.RequestError as e:
                        logger.error(
                            f"{endpoint_info['name']} request failed", error=str(e))
                    except Exception as e:
                        logger.error(
                            f"Unexpected error during {endpoint_info['name']} request", error=str(e))

                # Test v3 API endpoints (GET requests)
                v3_endpoints = [
                    {
                        "name": "Bounce Stats",
                        "url": f"https://campaign.inflection.io/api/v3/campaigns/{journey_id}/stats?view=aggregate&group_by=bounce_classification&event=bounce&start_date=2025-06-07T12%3A38%3A40%2B05%3A30&end_date=2025-07-07T12%3A38%3A40%2B05%3A30"
                    },
                    {
                        "name": "Bounce Classifications",
                        "url": "https://campaign.inflection.io/api/v3/campaigns/stats/bounce_classifications"
                    }
                ]

                for endpoint_info in v3_endpoints:
                    try:
                        logger.info(
                            f"Testing {endpoint_info['name']}", url=endpoint_info['url'])

                        response = await client.get(
                            endpoint_info['url'],
                            headers={
                                "Authorization": f"Bearer {self.token}",
                                "Content-Type": "application/json"
                            }
                        )

                        logger.info(
                            f"{endpoint_info['name']} response received",
                            status_code=response.status_code
                        )

                        if response.status_code == 200:
                            data = response.json()
                            logger.info(
                                f"{endpoint_info['name']} retrieved successfully")

                            # Save successful response
                            safe_name = endpoint_info['name'].lower().replace(
                                ' ', '_')
                            self._save_example(
                                "reports", f"{safe_name}_{journey_id}.json", data)
                            success_count += 1
                        else:
                            logger.error(
                                f"{endpoint_info['name']} request failed",
                                status_code=response.status_code,
                                response_text=response.text
                            )
                            # Save failed response
                            safe_name = endpoint_info['name'].lower().replace(
                                ' ', '_')
                            self._save_example("reports", f"{safe_name}_{journey_id}_failure.json", {
                                "status_code": response.status_code,
                                "response": response.text
                            })

                    except httpx.TimeoutException:
                        logger.error(
                            f"{endpoint_info['name']} request timed out")
                    except httpx.RequestError as e:
                        logger.error(
                            f"{endpoint_info['name']} request failed", error=str(e))
                    except Exception as e:
                        logger.error(
                            f"Unexpected error during {endpoint_info['name']} request", error=str(e))

                total_endpoints += len(v3_endpoints)

        except Exception as e:
            logger.error(
                "Unexpected error during email reports testing", error=str(e))
            return False

        # Consider the test successful if at least some endpoints work
        success_rate = success_count / total_endpoints if total_endpoints > 0 else 0
        logger.info(f"Email reports test completed",
                    success_count=success_count,
                    total_endpoints=total_endpoints,
                    success_rate=f"{success_rate:.1%}")

        return success_count > 0  # Return True if at least one endpoint worked

    def _save_example(self, category: str, filename: str, data: Dict[str, Any]) -> None:
        """Save API response example to file."""
        filepath = self.examples_dir / category / filename
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info("Example saved", filepath=str(filepath))
        except Exception as e:
            logger.error("Failed to save example",
                         filepath=str(filepath), error=str(e))


async def main():
    """Main test function."""
    # Get configuration from environment
    email = os.getenv("INFLECTION_EMAIL")
    password = os.getenv("INFLECTION_PASSWORD")
    test_journey_id = os.getenv(
        "INFLECTION_TEST_JOURNEY_ID", "test-journey-123")

    # Validate required environment variables
    if not email or not password:
        logger.error(
            "Missing required environment variables",
            required=["INFLECTION_EMAIL", "INFLECTION_PASSWORD"]
        )
        print("\nPlease set the following environment variables in your .env file:")
        print("  INFLECTION_EMAIL=your-email@example.com")
        print("  INFLECTION_PASSWORD=your-password")
        print("\nAlso ensure your .env file has the correct API endpoints from env.example")
        sys.exit(1)

    logger.info("Starting Inflection.io API tests")

    # Initialize tester
    tester = InflectionAPITester()

    # Test authentication
    logger.info("=== Testing Authentication ===")
    auth_success = await tester.test_login(email, password)

    if not auth_success:
        logger.error("Authentication failed - cannot proceed with other tests")
        sys.exit(1)

    # Test journey listing
    logger.info("=== Testing Journey Listing ===")
    journeys_success = await tester.test_journeys()

    # Test journey listing with search
    logger.info("=== Testing Journey Listing with Search ===")
    journeys_search_success = await tester.test_journeys_with_search("test")

    # Test email reports
    logger.info("=== Testing Email Reports ===")
    reports_success = await tester.test_email_reports(test_journey_id)

    # Summary
    logger.info("=== Test Summary ===")
    logger.info(
        "API test results",
        authentication=auth_success,
        journeys=journeys_success,
        journeys_search=journeys_search_success,
        email_reports=reports_success
    )

    if auth_success and journeys_success and journeys_search_success and reports_success:
        logger.info("All API tests passed successfully!")
        print("\n✅ All API tests passed! Check the 'examples/' directory for response samples.")
    else:
        logger.warning("Some API tests failed")
        print("\n⚠️  Some API tests failed. Check the logs above for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
