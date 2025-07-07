"""Main MCP server for Inflection.io integration."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
from mcp import Server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

from .auth.inflection import AuthState
from .config.settings import settings
from .tools.journeys import list_journeys, list_journeys_tool
from .tools.login import inflection_login, inflection_login_tool
from .tools.reports import get_email_reports, get_email_reports_tool

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


class InflectionMCPServer:
    """MCP Server for Inflection.io integration."""

    def __init__(self):
        self.auth_state = AuthState()
        self.tools: List[Tool] = [
            inflection_login_tool(),
            list_journeys_tool(),
            get_email_reports_tool()
        ]

    async def handle_list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """Handle list tools request."""
        logger.info("Listing tools", tool_count=len(self.tools))
        return ListToolsResult(tools=self.tools)

    async def handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool call request."""
        logger.info(
            "Tool call requested",
            tool_name=request.name,
            arguments=request.arguments
        )

        try:
            if request.name == "inflection_login":
                result = await inflection_login(
                    self.auth_state,
                    request.arguments.get("email", ""),
                    request.arguments.get("password", "")
                )
            elif request.name == "list_journeys":
                result = await list_journeys(
                    self.auth_state,
                    page_size=request.arguments.get("page_size", 30),
                    page_number=request.arguments.get("page_number", 1),
                    search_keyword=request.arguments.get("search_keyword", "")
                )
            elif request.name == "get_email_reports":
                result = await get_email_reports(
                    request.arguments.get("journey_id", ""),
                    self.auth_state,
                    start_date=request.arguments.get("start_date"),
                    end_date=request.arguments.get("end_date"),
                    include_details=request.arguments.get(
                        "include_details", True)
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


async def main():
    """Main server entry point."""
    logger.info("Starting Inflection.io MCP Server")

    # Create server instance
    server = InflectionMCPServer()

    # Create MCP server
    mcp_server = Server("inflection-mcp-server")

    # Register handlers
    mcp_server.list_tools(server.handle_list_tools)
    mcp_server.call_tool(server.handle_call_tool)

    # Run server
    logger.info("MCP Server ready")
    await mcp_server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Server failed", error=str(e), exc_info=True)
        sys.exit(1)
