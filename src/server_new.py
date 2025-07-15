"""Main MCP server for Inflection.io integration following the working pattern."""

import asyncio
import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone

import httpx
import structlog
from mcp.server import Server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)
import mcp.server.stdio
import sys
import pytz

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
except Exception as e:
    print(f"DEBUG: Error loading .env file: {e}", file=sys.stderr)

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

# Configuration from environment variables
API_BASE_URL_AUTH = os.environ.get(
    "INFLECTION_API_BASE_URL_AUTH", "https://auth.inflection.io/api/v1")
API_BASE_URL_CAMPAIGN = os.environ.get(
    "INFLECTION_API_BASE_URL_CAMPAIGN", "https://campaign.inflection.io/api/v2")
API_BASE_URL_CAMPAIGN_V1 = os.environ.get(
    "INFLECTION_API_BASE_URL_CAMPAIGN_V1", "https://campaign.inflection.io/api/v1")
API_BASE_URL_CAMPAIGN_V3 = os.environ.get(
    "INFLECTION_API_BASE_URL_CAMPAIGN_V3", "https://campaign.inflection.io/api/v3")
INFLECTION_EMAIL = os.environ.get("INFLECTION_EMAIL")
INFLECTION_PASSWORD = os.environ.get("INFLECTION_PASSWORD")

# Global state for authentication
auth_state = {
    "access_token": None,
    "refresh_token": None,
    "expires_at": None,
    "is_authenticated": False
}

print("DEBUG: server_new.py loaded!", file=sys.stderr)


class InflectionAPIClient:
    """HTTP client for Inflection.io API with authentication handling."""

    def __init__(self):
        self.auth_client = httpx.AsyncClient(
            base_url=API_BASE_URL_AUTH,
            headers={"Content-Type": "application/json"},
            timeout=30.0
        )
        self.campaign_client = httpx.AsyncClient(
            base_url=API_BASE_URL_CAMPAIGN,
            headers={"Content-Type": "application/json"},
            timeout=30.0
        )
        self.campaign_v1_client = httpx.AsyncClient(
            base_url=API_BASE_URL_CAMPAIGN_V1,
            headers={"Content-Type": "application/json"},
            timeout=30.0
        )
        self.campaign_v3_client = httpx.AsyncClient(
            base_url=API_BASE_URL_CAMPAIGN_V3,
            headers={"Content-Type": "application/json"},
            timeout=30.0
        )

        # If we already have auth state, update headers immediately
        if auth_state["access_token"]:
            self._update_auth_headers()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.auth_client.aclose()
        await self.campaign_client.aclose()
        await self.campaign_v1_client.aclose()
        await self.campaign_v3_client.aclose()

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login to Inflection.io and get authentication tokens."""
        logger.info("Attempting login", email=email)

        payload = {
            "email": email,
            "password": password
        }
        try:
            response = await self.auth_client.post("/accounts/login", json=payload)
            response.raise_for_status()
            data = response.json()

            # Update global auth state
            auth_state["access_token"] = data["session"]["access_token"]
            auth_state["refresh_token"] = data["session"]["refresh_token"]
            auth_state["expires_at"] = data["session"]["access_expires_at"]
            auth_state["is_authenticated"] = True

            # Update client headers
            self._update_auth_headers()

            logger.info("Login successful", user_id=data["account"]["id"])
            return data
        except Exception as e:
            # Clear auth state on failure
            auth_state["access_token"] = None
            auth_state["refresh_token"] = None
            auth_state["expires_at"] = None
            auth_state["is_authenticated"] = False
            logger.error("Login failed", error=str(e))
            raise

    def _update_auth_headers(self):
        """Update authentication headers for all clients."""
        if auth_state["access_token"]:
            auth_header = {
                "Authorization": f"Bearer {auth_state['access_token']}"}
            self.campaign_client.headers.update(auth_header)
            self.campaign_v1_client.headers.update(auth_header)
            self.campaign_v3_client.headers.update(auth_header)

    def is_token_expired(self) -> bool:
        """Check if the current token is expired."""
        if not auth_state["expires_at"]:
            return True

        try:
            expires_at = datetime.fromisoformat(
                auth_state["expires_at"].replace('Z', '+00:00'))
            return datetime.now(expires_at.tzinfo) >= expires_at
        except Exception:
            return True

    async def ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication token."""
        if auth_state["is_authenticated"] and not self.is_token_expired():
            return True

        # Check for missing credentials
        if not INFLECTION_EMAIL or not INFLECTION_PASSWORD:
            logger.error(
                "Missing credentials: INFLECTION_EMAIL and/or INFLECTION_PASSWORD not set in environment"
            )
            return False

        # Try to login with environment variables
        try:
            await self.login(INFLECTION_EMAIL, INFLECTION_PASSWORD)
            return True
        except Exception as e:
            logger.error(
                "Failed to authenticate with environment variables", error=str(e)
            )
            return False

    async def _make_authenticated_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Make an authenticated request with automatic retry on 401 errors.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            **kwargs: Additional arguments to pass to httpx request

        Returns:
            httpx.Response object

        Raises:
            Exception: If authentication fails or request fails after retry
        """
        max_retries = 2
        retry_count = 0

        while retry_count <= max_retries:
            try:
                # Ensure we have valid authentication
                if not await self.ensure_authenticated():
                    raise ValueError("Authentication required")

                # Make the request
                async with httpx.AsyncClient(timeout=30.0, headers=self.campaign_client.headers) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, **kwargs)
                    elif method.upper() == "POST":
                        response = await client.post(url, **kwargs)
                    elif method.upper() == "PUT":
                        response = await client.put(url, **kwargs)
                    elif method.upper() == "DELETE":
                        response = await client.delete(url, **kwargs)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                # If successful, return the response
                if response.status_code != 401:
                    if retry_count > 0:
                        logger.info(f"Request successful after {retry_count} retry attempts",
                                    method=method, url=url, status_code=response.status_code)
                    return response

                # If we get a 401 and this is not the last retry, re-authenticate and try again
                if retry_count < max_retries:
                    logger.warning(f"Received 401 Unauthorized, attempting automatic re-authentication (attempt {retry_count + 1}/{max_retries})",
                                   method=method, url=url)

                    # Clear current auth state
                    auth_state["access_token"] = None
                    auth_state["refresh_token"] = None
                    auth_state["expires_at"] = None
                    auth_state["is_authenticated"] = False

                    # Try to re-authenticate
                    logger.info("Initiating automatic re-authentication...")
                    if not await self.ensure_authenticated():
                        logger.error("Automatic re-authentication failed")
                        raise ValueError("Re-authentication failed")

                    logger.info(
                        "Automatic re-authentication successful, retrying request")
                    retry_count += 1
                    continue

                # If we've exhausted retries, raise the 401 error
                logger.error(f"Request failed after {max_retries} retry attempts",
                             method=method, url=url, status_code=response.status_code)
                response.raise_for_status()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401 and retry_count < max_retries:
                    logger.warning(f"Received 401 Unauthorized, attempting automatic re-authentication (attempt {retry_count + 1}/{max_retries})",
                                   method=method, url=url)

                    # Clear current auth state
                    auth_state["access_token"] = None
                    auth_state["refresh_token"] = None
                    auth_state["expires_at"] = None
                    auth_state["is_authenticated"] = False

                    # Try to re-authenticate
                    logger.info("Initiating automatic re-authentication...")
                    if not await self.ensure_authenticated():
                        logger.error("Automatic re-authentication failed")
                        raise ValueError("Re-authentication failed")

                    logger.info(
                        "Automatic re-authentication successful, retrying request")
                    retry_count += 1
                    continue
                else:
                    # Re-raise the error if it's not a 401 or we've exhausted retries
                    logger.error(f"Request failed with status {e.response.status_code}",
                                 method=method, url=url, error=str(e))
                    raise
            except Exception as e:
                # For any other exception, don't retry
                logger.error(f"Request failed with exception",
                             method=method, url=url, error=str(e))
                raise

        # This should never be reached, but just in case
        logger.error(f"Max retries exceeded for request",
                     method=method, url=url)
        raise Exception("Max retries exceeded")

    async def get_journeys(self, page_size: int = 30, page_number: int = 1, search_keyword: str = "") -> Dict[str, Any]:
        """Get list of marketing journeys."""
        payload = {
            "page_size": page_size,
            "page_number": page_number,
            "query": {
                "search": {
                    "keyword": search_keyword,
                    "fields": ["name"]
                }
            }
        }

        response = await self._make_authenticated_request(
            "POST",
            f"{API_BASE_URL_CAMPAIGN_V1}/campaigns/campaign.list",
            json=payload
        )
        return response.json()

    async def get_email_reports(self, journey_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive email reports for a specific journey using all endpoints from test_api.py."""
        tz = pytz.timezone("Asia/Kolkata")
        now = datetime.now(tz)
        if not end_date:
            end_date = now.replace(microsecond=0).isoformat()
        if not start_date:
            start_date = (now - timedelta(days=30)
                          ).replace(microsecond=0).isoformat()

        # Define all endpoints to call (matching test_api.py exactly)
        endpoints_to_call = [
            {
                "name": "aggregate_stats",
                "method": "POST",
                "url": "https://campaign.inflection.io/api/v2/campaigns/reports/stats.aggregate",
                "payload": {
                    "campaign_id": journey_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            },
            {
                "name": "recipient_engagement",
                "method": "POST",
                "url": "https://campaign.inflection.io/api/v2/campaigns/reports/stats.recipient_engagement",
                "payload": {
                    "campaign_id": journey_id,
                    "start_date": start_date,
                    "end_date": end_date,
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
                "name": "report_runs_list",
                "method": "POST",
                "url": "https://campaign.inflection.io/api/v2/campaigns/reports/runs.list",
                "payload": {
                    "campaign_id": journey_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "page_number": 1,
                    "page_size": 15,
                    "show_non_empty_runs": False
                }
            },
            {
                "name": "top_email_client_click",
                "method": "POST",
                "url": "https://campaign.inflection.io/api/v2/campaigns/reports/stats.top_email_client.click",
                "payload": {
                    "campaign_id": journey_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "page_number": 1,
                    "page_size": 1000
                }
            },
            {
                "name": "top_email_client_open",
                "method": "POST",
                "url": "https://campaign.inflection.io/api/v2/campaigns/reports/stats.top_email_client.open",
                "payload": {
                    "campaign_id": journey_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "page_number": 1,
                    "page_size": 1000
                }
            },
            {
                "name": "top_link_stats",
                "method": "POST",
                "url": "https://campaign.inflection.io/api/v2/campaigns/reports/stats.top_link",
                "payload": {
                    "campaign_id": journey_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "page_number": 1,
                    "page_size": 5
                }
            }
        ]

        # V3 API endpoints (GET requests) - matching test_api.py exactly
        v3_endpoints = [
            {
                "name": "bounce_stats",
                "method": "GET",
                "url": f"https://campaign.inflection.io/api/v3/campaigns/{journey_id}/stats?view=aggregate&group_by=bounce_classification&event=bounce&start_date={start_date.replace(':', '%3A').replace('+', '%2B')}&end_date={end_date.replace(':', '%3A').replace('+', '%2B')}"
            },
            {
                "name": "bounce_classifications",
                "method": "GET",
                "url": "https://campaign.inflection.io/api/v3/campaigns/stats/bounce_classifications"
            }
        ]

        results = {}

        # Call v2 endpoints (POST requests)
        for endpoint in endpoints_to_call:
            try:
                logger.info(f"Calling {endpoint['name']} endpoint")
                response = await self._make_authenticated_request(
                    endpoint["method"],
                    endpoint["url"],
                    json=endpoint["payload"]
                )
                results[endpoint["name"]] = response.json()
                logger.info(f"Successfully called {endpoint['name']} endpoint")
            except Exception as e:
                logger.warning(
                    f"Failed to call {endpoint['name']} endpoint", error=str(e))
                results[endpoint["name"]] = {"error": str(e)}

        # Call v3 endpoints (GET requests)
        for endpoint in v3_endpoints:
            try:
                logger.info(f"Calling {endpoint['name']} endpoint")
                response = await self._make_authenticated_request(
                    endpoint["method"],
                    endpoint["url"]
                )
                results[endpoint["name"]] = response.json()
                logger.info(f"Successfully called {endpoint['name']} endpoint")
            except Exception as e:
                logger.warning(
                    f"Failed to call {endpoint['name']} endpoint", error=str(e))
                results[endpoint["name"]] = {"error": str(e)}

        return results


class InflectionMCPServer:
    """MCP Server for Inflection.io integration."""

    def __init__(self):
        self.api_client = InflectionAPIClient()
        self.tools: List[Tool] = [
            Tool(
                name="inflection_login",
                description="Login to Inflection.io with email and password",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "Email address for Inflection.io account"
                        },
                        "password": {
                            "type": "string",
                            "description": "Password for Inflection.io account"
                        }
                    },
                    "required": ["email", "password"]
                }
            ),
            Tool(
                name="list_journeys",
                description="List all marketing journeys from Inflection.io",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_size": {
                            "type": "integer",
                            "description": "Number of journeys to return per page (default: 30, max: 100)",
                            "default": 30,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "page_number": {
                            "type": "integer",
                            "description": "Page number to retrieve (default: 1)",
                            "default": 1,
                            "minimum": 1
                        },
                        "search_keyword": {
                            "type": "string",
                            "description": "Search keyword to filter journeys by name (optional)",
                            "default": ""
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_email_reports",
                description="Get comprehensive email performance reports for a specific journey from multiple Inflection.io endpoints including aggregate stats, engagement metrics, email clients, top links, and bounce analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "journey_id": {
                            "type": "string",
                            "description": "The ID of the journey to get reports for"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date for the report period (YYYY-MM-DD format, optional)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date for the report period (YYYY-MM-DD format, optional)"
                        }
                    },
                    "required": ["journey_id"]
                }
            )
        ]

    async def handle_list_tools(self) -> List[Tool]:
        """Handle list tools request."""
        logger.info("Listing tools", tool_count=len(self.tools))
        return self.tools

    async def handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool call request."""
        logger.info(
            "Tool call requested",
            tool_name=request.name,
            arguments=request.arguments
        )

        try:
            if request.name == "inflection_login":
                result = await self.login(
                    email=request.arguments.get("email", ""),
                    password=request.arguments.get("password", "")
                )
                return CallToolResult(content=[TextContent(type="text", text=f"✅ Login successful!")])
            elif request.name == "list_journeys":
                result = await self.list_journeys(
                    page_size=request.arguments.get("page_size", 30),
                    page_number=request.arguments.get("page_number", 1),
                    search_keyword=request.arguments.get("search_keyword", "")
                )
            elif request.name == "get_email_reports":
                journey_id = request.arguments.get("journey_id")
                if not journey_id:
                    result = TextContent(
                        type="text",
                        text="❌ Journey ID is required. Please provide a valid journey_id parameter."
                    )
                else:
                    result = await self.get_email_reports(
                        journey_id=journey_id,
                        start_date=request.arguments.get("start_date"),
                        end_date=request.arguments.get("end_date")
                    )
            else:
                logger.error("Unknown tool requested", tool_name=request.name)
                result = TextContent(
                    type="text",
                    text=f"❌ Unknown tool: {request.name}"
                )

            logger.info("Tool call completed successfully",
                        tool_name=request.name)
            return CallToolResult(content=[result])

        except Exception as e:
            logger.error(
                "Tool call failed",
                tool_name=request.name,
                error=str(e),
                exc_info=True
            )

            # Provide user-friendly error messages
            error_message = str(e)

            # Handle specific authentication errors
            if "401" in error_message or "Unauthorized" in error_message:
                error_message = "Authentication failed. Please try using the 'inflection_login' tool again with your credentials."
            elif "Authentication required" in error_message:
                error_message = "Please use the 'inflection_login' tool first with your email and password."
            elif "Re-authentication failed" in error_message:
                error_message = "Unable to automatically re-authenticate. Please use the 'inflection_login' tool again with your credentials."
            elif "Max retries exceeded" in error_message:
                error_message = "Request failed after multiple attempts. Please try again or use the 'inflection_login' tool to refresh your authentication."

            error_result = TextContent(
                type="text",
                text=f"❌ Error executing {request.name}: {error_message}"
            )
            return CallToolResult(content=[error_result])

    async def login(self, email: str, password: str) -> TextContent:
        """Handle login tool call."""
        logger.info("Attempting login", email=email)
        try:
            await self.api_client.login(email, password)
            return TextContent(type="text", text=f"✅ Login successful!")
        except Exception as e:
            logger.error("Login failed", error=str(e))
            return TextContent(type="text", text=f"❌ Login failed: {str(e)}")

    async def list_journeys(self, page_size: int = 30, page_number: int = 1, search_keyword: str = "") -> TextContent:
        """List all marketing journeys from Inflection.io."""
        logger.info(
            "Listing journeys",
            page_size=page_size,
            page_number=page_number,
            search_keyword=search_keyword
        )

        try:
            response = await self.api_client.get_journeys(
                page_size=page_size,
                page_number=page_number,
                search_keyword=search_keyword
            )

            journeys_data = response.get("records", [])
            if not journeys_data or not isinstance(journeys_data, list):
                logger.warning(
                    "API did not return 'records' as expected", raw_response=response)
                return TextContent(
                    type="text",
                    text=f"❌ Unexpected API response. Could not find a list of journeys. Raw response: {json.dumps(response, indent=2)}"
                )

            journey_list = []
            for i, journey in enumerate(journeys_data, 1):
                name = journey.get("name", "Unnamed Journey")
                journey_id = journey.get(
                    "campaign_id", journey.get("id", "Unknown ID"))
                created_at = journey.get("created_at", "Unknown")
                updated_at = journey.get("updated_at", "Unknown")

                # Calculate status based on active and draft fields
                active = journey.get("active", False)
                draft = journey.get("draft", False)
                if draft:
                    status = "Draft"
                elif active:
                    status = "Active"
                else:
                    status = "Inactive"

                # Get creator information
                created_by = journey.get("created_by", {})
                creator_name = created_by.get(
                    "name", "Unknown") if created_by else "Unknown"

                journey_list.append(
                    f"{i}. **{name}** (ID: `{journey_id}`)\n"
                    f"   - Status: {status}\n"
                    f"   - Created: {created_at}\n"
                    f"   - Updated: {updated_at}\n"
                    f"   - Created by: {creator_name}"
                )

            total_count = len(journeys_data)
            summary = f"📊 Found {total_count} journeys"
            if search_keyword:
                summary += f" matching '{search_keyword}'"

            response_text = f"{summary}\n\n" + "\n\n".join(journey_list)
            return TextContent(type="text", text=response_text)

        except Exception as e:
            logger.error("Failed to list journeys", error=str(e))
            return TextContent(
                type="text",
                text=f"❌ Failed to list journeys: {str(e)}"
            )

    async def get_email_reports(self, journey_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> TextContent:
        """Get comprehensive email performance reports for a specific journey."""
        logger.info(
            "Getting email reports",
            journey_id=journey_id,
            start_date=start_date,
            end_date=end_date
        )

        try:
            reports = await self.api_client.get_email_reports(
                journey_id=journey_id,
                start_date=start_date,
                end_date=end_date
            )

            # Build comprehensive report
            report_parts = [
                f"📧 **Comprehensive Email Report for Journey: {journey_id}**\n"]

            # Date range
            date_range = f"📅 **Date Range:** {start_date or 'Last 30 days'} to {end_date or 'Today'}\n"
            report_parts.append(date_range)

            # Aggregate Statistics
            agg = reports.get("aggregate_stats", {})
            if "error" not in agg:
                report_parts.append(
                    "\n### 📊 **Aggregate Performance Metrics**")
                if isinstance(agg, dict):
                    for key, value in agg.items():
                        if isinstance(value, (int, float)):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value:,}")
                        elif isinstance(value, dict):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:**")
                            for sub_key, sub_value in value.items():
                                report_parts.append(
                                    f"  - {sub_key.replace('_', ' ').title()}: {sub_value}")
                else:
                    report_parts.append(
                        f"Raw data: {json.dumps(agg, indent=2)}")
            else:
                report_parts.append(
                    f"\n### 📊 **Aggregate Statistics:** Error - {agg['error']}")

            # Recipient Engagement
            eng = reports.get("recipient_engagement", {})
            if "error" not in eng:
                report_parts.append(
                    "\n### 👥 **Recipient Engagement Statistics**")
                if isinstance(eng, dict):
                    for key, value in eng.items():
                        if isinstance(value, (int, float)):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value:,}")
                        elif isinstance(value, list):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {len(value)} records")
                        else:
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value}")
                else:
                    report_parts.append(
                        f"Raw data: {json.dumps(eng, indent=2)}")
            else:
                report_parts.append(
                    f"\n### 👥 **Recipient Engagement:** Error - {eng['error']}")

            # Report Runs
            runs = reports.get("report_runs_list", {})
            if "error" not in runs:
                report_parts.append("\n### 🏃‍♂️ **Report Runs Summary**")
                if isinstance(runs, dict):
                    for key, value in runs.items():
                        if isinstance(value, (int, float)):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value:,}")
                        elif isinstance(value, list):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {len(value)} runs")
                        else:
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value}")
                else:
                    report_parts.append(
                        f"Raw data: {json.dumps(runs, indent=2)}")
            else:
                report_parts.append(
                    f"\n### 🏃‍♂️ **Report Runs:** Error - {runs['error']}")

            # Top Email Clients (Click)
            click_clients = reports.get("top_email_client_click", {})
            if "error" not in click_clients:
                report_parts.append("\n### 💻 **Top Email Clients (Clicks)**")
                if isinstance(click_clients, dict):
                    for key, value in click_clients.items():
                        if isinstance(value, (int, float)):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value:,}")
                        elif isinstance(value, list):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {len(value)} clients")
                        else:
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value}")
                else:
                    report_parts.append(
                        f"Raw data: {json.dumps(click_clients, indent=2)}")
            else:
                report_parts.append(
                    f"\n### 💻 **Top Email Clients (Clicks):** Error - {click_clients['error']}")

            # Top Email Clients (Open)
            open_clients = reports.get("top_email_client_open", {})
            if "error" not in open_clients:
                report_parts.append("\n### 💻 **Top Email Clients (Opens)**")
                if isinstance(open_clients, dict):
                    for key, value in open_clients.items():
                        if isinstance(value, (int, float)):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value:,}")
                        elif isinstance(value, list):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {len(value)} clients")
                        else:
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value}")
                else:
                    report_parts.append(
                        f"Raw data: {json.dumps(open_clients, indent=2)}")
            else:
                report_parts.append(
                    f"\n### 💻 **Top Email Clients (Opens):** Error - {open_clients['error']}")

            # Top Links
            top_links = reports.get("top_link_stats", {})
            if "error" not in top_links:
                report_parts.append("\n### 🔗 **Top Performing Links**")
                if isinstance(top_links, dict):
                    for key, value in top_links.items():
                        if isinstance(value, (int, float)):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value:,}")
                        elif isinstance(value, list):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {len(value)} links")
                        else:
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value}")
                else:
                    report_parts.append(
                        f"Raw data: {json.dumps(top_links, indent=2)}")
            else:
                report_parts.append(
                    f"\n### 🔗 **Top Links:** Error - {top_links['error']}")

            # Bounce Statistics
            bounce_stats = reports.get("bounce_stats", {})
            if "error" not in bounce_stats:
                report_parts.append("\n### 📤 **Bounce Analysis**")
                if isinstance(bounce_stats, dict):
                    for key, value in bounce_stats.items():
                        if isinstance(value, (int, float)):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value:,}")
                        elif isinstance(value, list):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {len(value)} classifications")
                        else:
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value}")
                else:
                    report_parts.append(
                        f"Raw data: {json.dumps(bounce_stats, indent=2)}")
            else:
                report_parts.append(
                    f"\n### 📤 **Bounce Analysis:** Error - {bounce_stats['error']}")

            # Bounce Classifications
            bounce_class = reports.get("bounce_classifications", {})
            if "error" not in bounce_class:
                report_parts.append("\n### 📤 **Bounce Classifications**")
                if isinstance(bounce_class, dict):
                    for key, value in bounce_class.items():
                        if isinstance(value, (int, float)):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value:,}")
                        elif isinstance(value, list):
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {len(value)} types")
                        else:
                            report_parts.append(
                                f"- **{key.replace('_', ' ').title()}:** {value}")
                else:
                    report_parts.append(
                        f"Raw data: {json.dumps(bounce_class, indent=2)}")
            else:
                report_parts.append(
                    f"\n### 📤 **Bounce Classifications:** Error - {bounce_class['error']}")

            response_text = "\n".join(report_parts)
            return TextContent(type="text", text=response_text)

        except Exception as e:
            logger.error("Failed to get email reports", error=str(e))
            return TextContent(
                type="text",
                text=f"❌ Failed to get email reports: {str(e)}"
            )


async def main():
    """Main server entry point."""
    logger.info("Starting Inflection.io MCP Server")

    # Create server instance
    server = InflectionMCPServer()

    # Create MCP server
    mcp_server = Server("inflection-mcp-server")

    # Register handlers using decorators
    @mcp_server.list_tools()
    async def list_tools_handler():
        return await server.handle_list_tools()

    @mcp_server.call_tool()
    async def call_tool_handler(name: str, arguments: dict):
        if name == "inflection_login":
            content = await server.login(
                email=arguments.get("email", ""),
                password=arguments.get("password", "")
            )
            return [content]
        elif name == "list_journeys":
            content = await server.list_journeys(
                page_size=arguments.get("page_size", 30),
                page_number=arguments.get("page_number", 1),
                search_keyword=arguments.get("search_keyword", "")
            )
            return [content]
        elif name == "get_email_reports":
            journey_id = arguments.get("journey_id")
            if not journey_id:
                content = TextContent(
                    type="text",
                    text="❌ Journey ID is required. Please provide a valid journey_id parameter."
                )
            else:
                content = await server.get_email_reports(
                    journey_id=journey_id,
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date")
                )
            return [content]
        else:
            return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]

    # Run server with stdio
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options(),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Server failed", error=str(e), exc_info=True)
