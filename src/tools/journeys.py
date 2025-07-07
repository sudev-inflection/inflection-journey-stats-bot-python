"""Journeys tool for Inflection.io MCP Server."""

from typing import Any, Dict, List, Optional

import structlog
from mcp import TextContent
from mcp.types import Tool

from ..auth.inflection import InflectionAuth
from ..models.auth import AuthState
from ..models.journey import Journey, JourneyList
from ..utils.api_client import InflectionAPIClient

logger = structlog.get_logger(__name__)


def list_journeys_tool() -> Tool:
    """Create the list_journeys tool."""
    return Tool(
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
    )


async def list_journeys(
    auth_state: AuthState,
    page_size: int = 30,
    page_number: int = 1,
    search_keyword: str = ""
) -> TextContent:
    """List all marketing journeys from Inflection.io."""

    if not auth_state.is_authenticated():
        return TextContent(
            type="text",
            text="❌ Authentication required. Please use the inflection_login tool first."
        )

    logger.info(
        "Listing journeys",
        page_size=page_size,
        page_number=page_number,
        search_keyword=search_keyword
    )

    try:
        async with InflectionAPIClient(auth_state) as client:
            response = await client.get_journeys(
                page_size=page_size,
                page_number=page_number,
                search_keyword=search_keyword
            )

            # Parse journeys from response
            journeys_data = response.get("journeys", [])
            journeys = []

            for journey_data in journeys_data:
                try:
                    journey = Journey(**journey_data)
                    journeys.append(journey)
                except Exception as e:
                    logger.warning(
                        "Failed to parse journey data",
                        journey_data=journey_data,
                        error=str(e)
                    )

            # Build response text
            if not journeys:
                return TextContent(
                    type="text",
                    text="📭 No journeys found."
                )

            # Format journey list
            journey_list = []
            for i, journey in enumerate(journeys, 1):
                status = journey.status or "Unknown"
                created = journey.created_at or "Unknown"
                updated = journey.updated_at or "Unknown"

                journey_list.append(
                    f"{i}. **{journey.name}** (ID: `{journey.id}`)\n"
                    f"   - Status: {status}\n"
                    f"   - Created: {created}\n"
                    f"   - Updated: {updated}"
                )

            # Add pagination info
            total_count = response.get("total_count", len(journeys))
            total_pages = response.get("total_pages", 1)

            summary = (
                f"📊 Found {len(journeys)} journeys (Page {page_number} of {total_pages}, "
                f"Total: {total_count})"
            )

            if search_keyword:
                summary += f" matching '{search_keyword}'"

            response_text = f"{summary}\n\n" + "\n\n".join(journey_list)

            logger.info(
                "Journeys listed successfully",
                count=len(journeys),
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
