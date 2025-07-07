"""Email reports tool for Inflection.io MCP Server."""

from typing import Any, Dict, Optional
from datetime import datetime

import structlog
from mcp.types import TextContent, Tool

from ..auth.inflection import InflectionAuth
from ..models.auth import AuthState
from ..utils.api_client import InflectionAPIClient
from ..utils.validation import validate_journey_id, sanitize_filters

logger = structlog.get_logger(__name__)


def get_email_reports_tool() -> Tool:
    """Create the get_email_reports tool."""
    return Tool(
        name="get_email_reports",
        description="Get comprehensive email performance reports for a specific journey from Inflection.io",
        inputSchema={
            "type": "object",
            "properties": {
                "journey_id": {
                    "type": "string",
                    "description": "Journey ID to get reports for (required)"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date filter in YYYY-MM-DD format (optional, defaults to 30 days ago)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date filter in YYYY-MM-DD format (optional, defaults to today)"
                },
                "include_details": {
                    "type": "boolean",
                    "description": "Whether to include detailed breakdowns like bounce analysis, email clients, and top links (default: true)",
                    "default": True
                }
            },
            "required": ["journey_id"]
        }
    )


async def get_email_reports(
    journey_id: str,
    auth_state: AuthState,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_details: bool = True
) -> TextContent:
    """
    Get comprehensive email performance reports for a specific journey.

    Args:
        journey_id: Journey ID to get reports for
        auth_state: Authentication state manager
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        include_details: Whether to include detailed breakdowns

    Returns:
        TextContent with comprehensive email report data
    """
    logger.info(
        "MCP tool called: get_email_reports",
        journey_id=journey_id,
        start_date=start_date,
        end_date=end_date,
        include_details=include_details
    )

    try:
        # Validate journey ID
        if not validate_journey_id(journey_id):
            return TextContent(
                type="text",
                text="❌ Invalid journey ID format"
            )

        # Check authentication
        auth_manager = InflectionAuth(auth_state)
        if not await auth_manager.ensure_authenticated():
            return TextContent(
                type="text",
                text="❌ Authentication required. Please use the `inflection_login` tool first."
            )

        # Fetch comprehensive report data
        async with InflectionAPIClient(auth_state) as client:
            # Get aggregate stats (main performance metrics)
            aggregate_data = await client.get_aggregate_stats(journey_id, start_date, end_date)

            # Get report runs list
            runs_data = await client.get_report_runs_list(journey_id, start_date, end_date)

            # Build main report
            report_text = f"""📊 **Comprehensive Email Performance Report** - Journey `{journey_id}`

**📅 Date Range:** {start_date or 'Last 30 days'} to {end_date or 'Today'}

**📈 Aggregate Performance Metrics:**
{_format_aggregate_stats(aggregate_data)}

**📋 Report Runs Summary:**
{_format_runs_summary(runs_data)}"""

            # Add detailed breakdowns if requested
            if include_details:
                try:
                    # Get bounce statistics
                    bounce_data = await client.get_bounce_stats(journey_id, start_date, end_date)
                    report_text += f"\n\n**📤 Bounce Analysis:**\n{_format_bounce_stats(bounce_data)}"
                except Exception as e:
                    logger.warning(
                        "Failed to fetch bounce stats", error=str(e))
                    report_text += "\n\n**📤 Bounce Analysis:** Data unavailable"

                try:
                    # Get top email clients
                    top_clients_click = await client.get_top_email_client_click_stats(journey_id, start_date, end_date)
                    top_clients_open = await client.get_top_email_client_open_stats(journey_id, start_date, end_date)
                    report_text += f"\n\n**💻 Top Email Clients:**\n{_format_email_clients(top_clients_click, top_clients_open)}"
                except Exception as e:
                    logger.warning(
                        "Failed to fetch email client stats", error=str(e))
                    report_text += "\n\n**💻 Top Email Clients:** Data unavailable"

                try:
                    # Get top links
                    top_links = await client.get_top_link_stats(journey_id, start_date, end_date)
                    report_text += f"\n\n**🔗 Top Performing Links:**\n{_format_top_links(top_links)}"
                except Exception as e:
                    logger.warning("Failed to fetch top links", error=str(e))
                    report_text += "\n\n**🔗 Top Performing Links:** Data unavailable"

            logger.info(
                "Comprehensive email report generated successfully", journey_id=journey_id)
            return TextContent(type="text", text=report_text)

    except Exception as e:
        logger.error("Failed to get email reports", error=str(e))
        return TextContent(
            type="text",
            text=f"❌ Failed to retrieve email reports: {str(e)}"
        )


def _format_aggregate_stats(data: Dict[str, Any]) -> str:
    """Format aggregate statistics."""
    try:
        stats = data.get('data', {})

        # Extract key metrics
        sent = stats.get('sent', 0)
        delivered = stats.get('delivered', 0)
        opened = stats.get('opened', 0)
        clicked = stats.get('clicked', 0)
        bounced = stats.get('bounced', 0)
        unsubscribed = stats.get('unsubscribed', 0)

        # Calculate rates
        delivery_rate = (delivered / sent * 100) if sent > 0 else 0
        open_rate = (opened / delivered * 100) if delivered > 0 else 0
        click_rate = (clicked / delivered * 100) if delivered > 0 else 0
        bounce_rate = (bounced / sent * 100) if sent > 0 else 0
        unsubscribe_rate = (unsubscribed / delivered *
                            100) if delivered > 0 else 0

        return f"""📧 **Sent:** {sent:,}
✅ **Delivered:** {delivered:,} ({delivery_rate:.1f}%)
👁️ **Opened:** {opened:,} ({open_rate:.1f}%)
🔗 **Clicked:** {clicked:,} ({click_rate:.1f}%)
📤 **Bounced:** {bounced:,} ({bounce_rate:.1f}%)
🚫 **Unsubscribed:** {unsubscribed:,} ({unsubscribe_rate:.1f}%)"""

    except Exception as e:
        logger.warning("Failed to format aggregate stats", error=str(e))
        return "Data unavailable"


def _format_runs_summary(data: Dict[str, Any]) -> str:
    """Format report runs summary."""
    try:
        runs = data.get('data', {}).get('runs', [])
        total_count = data.get('data', {}).get('total_count', len(runs))

        if not runs:
            return "No report runs found for the specified date range."

        summary_lines = [f"**Total Runs:** {total_count}"]

        # Show recent runs (up to 5)
        for i, run in enumerate(runs[:5], 1):
            run_id = run.get('id', 'Unknown')
            status = run.get('status', 'Unknown')
            created_at = run.get('created_at', 'Unknown')

            # Format date if available
            if created_at and created_at != 'Unknown':
                try:
                    # Parse ISO date and format nicely
                    dt = datetime.fromisoformat(
                        created_at.replace('Z', '+00:00'))
                    created_at = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass

            summary_lines.append(
                f"{i}. **{run_id}** - {status} ({created_at})")

        if len(runs) > 5:
            summary_lines.append(f"... and {len(runs) - 5} more runs")

        return "\n".join(summary_lines)

    except Exception as e:
        logger.warning("Failed to format runs summary", error=str(e))
        return "Data unavailable"


def _format_bounce_stats(data: Dict[str, Any]) -> str:
    """Format bounce statistics."""
    try:
        bounces = data.get('data', [])

        if not bounces:
            return "No bounce data available for the specified date range."

        lines = []
        total_bounces = 0

        for bounce in bounces:
            classification = bounce.get('bounce_classification', 'Unknown')
            count = bounce.get('count', 0)
            total_bounces += count

            lines.append(f"• **{classification}:** {count:,}")

        if total_bounces > 0:
            lines.insert(0, f"**Total Bounces:** {total_bounces:,}")

        return "\n".join(lines)

    except Exception as e:
        logger.warning("Failed to format bounce stats", error=str(e))
        return "Data unavailable"


def _format_email_clients(click_data: Dict[str, Any], open_data: Dict[str, Any]) -> str:
    """Format email client statistics."""
    try:
        click_clients = click_data.get('data', [])
        open_clients = open_data.get('data', [])

        lines = []

        # Top email clients for clicks
        if click_clients:
            lines.append("**Top Email Clients (Clicks):**")
            for i, client in enumerate(click_clients[:3], 1):
                name = client.get('email_client', 'Unknown')
                count = client.get('count', 0)
                lines.append(f"{i}. {name}: {count:,} clicks")

        # Top email clients for opens
        if open_clients:
            if lines:
                lines.append("")
            lines.append("**Top Email Clients (Opens):**")
            for i, client in enumerate(open_clients[:3], 1):
                name = client.get('email_client', 'Unknown')
                count = client.get('count', 0)
                lines.append(f"{i}. {name}: {count:,} opens")

        if not lines:
            return "No email client data available."

        return "\n".join(lines)

    except Exception as e:
        logger.warning("Failed to format email clients", error=str(e))
        return "Data unavailable"


def _format_top_links(data: Dict[str, Any]) -> str:
    """Format top performing links."""
    try:
        links = data.get('data', [])

        if not links:
            return "No link performance data available for the specified date range."

        lines = []
        for i, link in enumerate(links, 1):
            url = link.get('url', 'Unknown')
            clicks = link.get('clicks', 0)

            # Truncate long URLs for display
            display_url = url if len(url) <= 60 else url[:57] + "..."
            lines.append(f"{i}. **{display_url}** - {clicks:,} clicks")

        return "\n".join(lines)

    except Exception as e:
        logger.warning("Failed to format top links", error=str(e))
        return "Data unavailable"
