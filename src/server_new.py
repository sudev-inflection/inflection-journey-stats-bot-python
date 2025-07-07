"""Main MCP server for Inflection.io integration following the working pattern."""

import asyncio
import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

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
        self.campaign_v3_client = httpx.AsyncClient(
            base_url=API_BASE_URL_CAMPAIGN_V3,
            headers={"Content-Type": "application/json"},
            timeout=30.0
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.auth_client.aclose()
        await self.campaign_client.aclose()
        await self.campaign_v3_client.aclose()

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login to Inflection.io and get authentication tokens."""
        logger.info("Attempting login", email=email)

        payload = {
            "email": email,
            "password": password
        }

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

    def _update_auth_headers(self):
        """Update authentication headers for all clients."""
        if auth_state["access_token"]:
            auth_header = {
                "Authorization": f"Bearer {auth_state['access_token']}"}
            self.campaign_client.headers.update(auth_header)
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

        # Try to login with environment variables
        if INFLECTION_EMAIL and INFLECTION_PASSWORD:
            try:
                await self.login(INFLECTION_EMAIL, INFLECTION_PASSWORD)
                return True
            except Exception as e:
                logger.error(
                    "Failed to authenticate with environment variables", error=str(e))

        return False

    async def get_journeys(self, page_size: int = 30, page_number: int = 1, search_keyword: str = "") -> Dict[str, Any]:
        """Get list of marketing journeys."""
        if not await self.ensure_authenticated():
            raise ValueError("Authentication required")

        params = {
            "page_size": page_size,
            "page_number": page_number
        }

        if search_keyword:
            params["search_keyword"] = search_keyword

        response = await self.campaign_client.get("/campaigns/campaign.list", params=params)
        response.raise_for_status()

        return response.json()

    async def get_email_reports(self, journey_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get email reports for a specific journey."""
        if not await self.ensure_authenticated():
            raise ValueError("Authentication required")

        # Get aggregate stats
        params = {"campaign_id": journey_id}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = await self.campaign_client.get("/campaigns/reports/stats.aggregate", params=params)
        response.raise_for_status()

        aggregate_stats = response.json()

        # Get recipient engagement stats
        response = await self.campaign_client.get("/campaigns/reports/stats.recipient_engagement", params=params)
        response.raise_for_status()

        engagement_stats = response.json()

        # Get top link stats
        response = await self.campaign_client.get("/campaigns/reports/stats.top_link", params=params)
        response.raise_for_status()

        link_stats = response.json()

        # Get bounce stats (v3 API)
        v3_params = {"campaign_id": journey_id}
        if start_date:
            v3_params["start_date"] = start_date
        if end_date:
            v3_params["end_date"] = end_date

        try:
            response = await self.campaign_v3_client.get(f"/campaigns/{journey_id}/stats", params=v3_params)
            response.raise_for_status()
            bounce_stats = response.json()
        except Exception as e:
            logger.warning("Failed to get bounce stats", error=str(e))
            bounce_stats = {"stats": {}}

        return {
            "aggregate_stats": aggregate_stats,
            "engagement_stats": engagement_stats,
            "link_stats": link_stats,
            "bounce_stats": bounce_stats
        }


class InflectionMCPServer:
    """MCP Server for Inflection.io integration."""

    def __init__(self):
        self.api_client = InflectionAPIClient()
        self.tools: List[Tool] = [
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
                description="Get email performance reports for a specific journey",
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
            if request.name == "list_journeys":
                result = await self.list_journeys(
                    page_size=request.arguments.get("page_size", 30),
                    page_number=request.arguments.get("page_number", 1),
                    search_keyword=request.arguments.get("search_keyword", "")
                )
            elif request.name == "get_email_reports":
                result = await self.get_email_reports(
                    journey_id=request.arguments.get("journey_id", ""),
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
            error_result = TextContent(
                type="text",
                text=f"❌ Error executing {request.name}: {str(e)}"
            )
            return CallToolResult(content=[error_result])

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

            # Parse journeys from response
            journeys_data = response.get("records", [])

            if not journeys_data:
                return TextContent(
                    type="text",
                    text="📭 No journeys found."
                )

            # Format journey list
            journey_list = []
            for i, journey in enumerate(journeys_data, 1):
                name = journey.get("name", "Unnamed Journey")
                campaign_id = journey.get("campaign_id", "Unknown ID")
                active = journey.get("active", False)
                draft = journey.get("draft", False)
                created_at = journey.get("created_at", "Unknown")

                status = "Active" if active else "Inactive"
                if draft:
                    status = "Draft"

                journey_list.append(
                    f"{i}. **{name}** (ID: `{campaign_id}`)\n"
                    f"   - Status: {status}\n"
                    f"   - Created: {created_at}"
                )

            # Add pagination info
            total_count = response.get("total_count", len(journeys_data))
            total_pages = response.get("total_pages", 1)

            summary = (
                f"📊 Found {len(journeys_data)} journeys (Page {page_number} of {total_pages}, "
                f"Total: {total_count})"
            )

            if search_keyword:
                summary += f" matching '{search_keyword}'"

            response_text = f"{summary}\n\n" + "\n\n".join(journey_list)

            logger.info(
                "Journeys listed successfully",
                count=len(journeys_data),
                page=page_number,
                total_pages=total_pages,
                total_count=total_count
            )

            return TextContent(type="text", text=response_text)

        except ValueError as e:
            logger.error("Authentication error", error=str(e))
            return TextContent(
                type="text",
                text=f"❌ Authentication error: {str(e)}"
            )
        except Exception as e:
            logger.error("Failed to list journeys", error=str(e))
            return TextContent(
                type="text",
                text=f"❌ Failed to list journeys: {str(e)}"
            )

    async def get_email_reports(self, journey_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> TextContent:
        """Get email performance reports for a specific journey."""
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

            # Extract aggregate stats
            aggregate_stats = reports.get(
                "aggregate_stats", {}).get("stats", {})

            # Build report summary
            report_parts = [
                f"📧 **Email Report for Journey: {journey_id}**\n"
            ]

            if start_date or end_date:
                period = f"Period: {start_date or 'Start'} to {end_date or 'End'}"
                report_parts.append(period + "\n")

            # Aggregate statistics
            report_parts.append("### 📊 Aggregate Statistics")
            report_parts.append(
                f"- **Total Emails**: {aggregate_stats.get('total_count', 0)}")
            report_parts.append(
                f"- **Delivered**: {aggregate_stats.get('delivered_count', 0)}")
            report_parts.append(
                f"- **Opens**: {aggregate_stats.get('total_open_count', 0)} (Unique: {aggregate_stats.get('unique_open_count', 0)})")
            report_parts.append(
                f"- **Clicks**: {aggregate_stats.get('total_click_count', 0)} (Unique: {aggregate_stats.get('unique_click_count_by_email', 0)})")
            report_parts.append(
                f"- **Bounces**: {aggregate_stats.get('bounce_count', 0)}")
            report_parts.append(
                f"- **Unsubscribes**: {aggregate_stats.get('unsub_count', 0)}")
            report_parts.append(
                f"- **Spam Reports**: {aggregate_stats.get('spamreport_count', 0)}")

            # Calculate rates
            total_count = aggregate_stats.get('total_count', 0)
            if total_count > 0:
                open_rate = (aggregate_stats.get(
                    'unique_open_count', 0) / total_count) * 100
                click_rate = (aggregate_stats.get(
                    'unique_click_count_by_email', 0) / total_count) * 100
                bounce_rate = (aggregate_stats.get(
                    'bounce_count', 0) / total_count) * 100

                report_parts.append(f"\n### 📈 Performance Rates")
                report_parts.append(f"- **Open Rate**: {open_rate:.2f}%")
                report_parts.append(f"- **Click Rate**: {click_rate:.2f}%")
                report_parts.append(f"- **Bounce Rate**: {bounce_rate:.2f}%")

            # Top links (if available)
            link_stats = reports.get("link_stats", {}).get("stats", [])
            if link_stats:
                report_parts.append(f"\n### 🔗 Top Links")
                for i, link in enumerate(link_stats[:5], 1):
                    url = link.get("url", "Unknown URL")
                    clicks = link.get("click_count", 0)
                    report_parts.append(f"{i}. {url} - {clicks} clicks")

            # Bounce statistics (if available)
            bounce_stats = reports.get("bounce_stats", {}).get("stats", {})
            if bounce_stats:
                report_parts.append(f"\n### 📤 Bounce Statistics")
                report_parts.append(
                    f"- **Hard Bounces**: {bounce_stats.get('hard_bounce_count', 0)}")
                report_parts.append(
                    f"- **Soft Bounces**: {bounce_stats.get('soft_bounce_count', 0)}")
                report_parts.append(
                    f"- **Block Bounces**: {bounce_stats.get('block_bounce_count', 0)}")

            response_text = "\n".join(report_parts)

            logger.info(
                "Email reports retrieved successfully",
                journey_id=journey_id,
                total_emails=total_count
            )

            return TextContent(type="text", text=response_text)

        except ValueError as e:
            logger.error("Authentication error", error=str(e))
            return TextContent(
                type="text",
                text=f"❌ Authentication error: {str(e)}"
            )
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
        # Convert the call_tool signature to match our handler
        request = CallToolRequest(
            params=CallToolRequest.Params(name=name, arguments=arguments))
        result = await server.handle_call_tool(request)
        return result.content

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
