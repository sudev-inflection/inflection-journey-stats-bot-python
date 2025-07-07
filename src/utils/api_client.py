"""HTTP API client utilities."""

import asyncio
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

import httpx
import structlog
from httpx import AsyncClient, Response

from ..config.settings import settings
from ..models.auth import AuthState

logger = structlog.get_logger(__name__)


class InflectionAPIClient:
    """Async HTTP client for Inflection.io API."""

    def __init__(self, auth_state: AuthState):
        self.auth_state = auth_state
        self.auth_base_url = settings.inflection_api_base_url_auth.rstrip('/')
        self.campaign_base_url = settings.inflection_api_base_url_campaign.rstrip(
            '/')
        self.campaign_v3_base_url = settings.inflection_api_base_url_campaign_v3.rstrip(
            '/')
        self.timeout = settings.api_timeout / 1000  # Convert ms to seconds
        self.max_requests_per_minute = settings.max_requests_per_minute
        self._client: Optional[AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = AsyncClient(
            timeout=self.timeout,
            headers={
                "User-Agent": "Inflection-MCP-Server/0.1.0",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            "User-Agent": "Inflection-MCP-Server/0.1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        if include_auth and self.auth_state.is_authenticated():
            headers.update(self.auth_state.get_auth_headers())

        return headers

    async def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        include_auth: bool = True,
        retry_count: int = 0
    ) -> Response:
        """Make HTTP request with retry logic."""
        if not self._client:
            raise RuntimeError(
                "Client not initialized. Use async context manager.")

        headers = self._get_headers(include_auth)

        logger.info(
            "Making API request",
            method=method,
            url=url,
            include_auth=include_auth,
            retry_count=retry_count
        )

        try:
            if method.upper() == "GET":
                response = await self._client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await self._client.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = await self._client.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = await self._client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            logger.info(
                "API response received",
                method=method,
                url=url,
                status_code=response.status_code,
                response_size=len(response.content)
            )

            return response

        except httpx.TimeoutException as e:
            logger.error("Request timed out", method=method,
                         url=url, error=str(e))
            if retry_count < 3:  # Max 3 retries
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self._make_request(method, url, data, include_auth, retry_count + 1)
            raise

        except httpx.RequestError as e:
            logger.error("Request failed", method=method,
                         url=url, error=str(e))
            if retry_count < 3:
                await asyncio.sleep(2 ** retry_count)
                return await self._make_request(method, url, data, include_auth, retry_count + 1)
            raise

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate with Inflection.io API."""
        url = f"{self.auth_base_url}{settings.inflection_login_endpoint}"
        data = {"email": email, "password": password}

        response = await self._make_request("POST", url, data, include_auth=False)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "Login failed",
                status_code=response.status_code,
                response_text=response.text
            )
            response.raise_for_status()

    async def get_journeys(self, page_size: int = 30, page_number: int = 1, search_keyword: str = "") -> Dict[str, Any]:
        """Get list of journeys using POST request with payload."""
        if not self.auth_state.is_authenticated():
            raise ValueError("Authentication required")

        url = f"{self.campaign_base_url}{settings.inflection_journeys_endpoint}"

        # Build the payload according to the API specification
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

        response = await self._make_request("POST", url, payload)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "Failed to get journeys",
                status_code=response.status_code,
                response_text=response.text
            )
            response.raise_for_status()

    def _prepare_date_range(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> tuple[str, str]:
        """Prepare date range for API requests."""
        if not start_date:
            # Default to 30 days ago
            start_date = (datetime.now() - timedelta(days=30)
                          ).strftime("%Y-%m-%dT%H:%M:%S%z")
        if not end_date:
            # Default to now
            end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")

        # Ensure timezone format matches API expectations
        if not start_date.endswith('+05:30'):
            start_date = f"{start_date}+05:30"
        if not end_date.endswith('+05:30'):
            end_date = f"{end_date}+05:30"

        return start_date, end_date

    async def get_report_runs_list(self, campaign_id: str, start_date: Optional[str] = None,
                                   end_date: Optional[str] = None, page_number: int = 1,
                                   page_size: int = 15, show_non_empty_runs: bool = False) -> Dict[str, Any]:
        """Get report runs list for a campaign."""
        if not self.auth_state.is_authenticated():
            raise ValueError("Authentication required")

        url = f"{self.campaign_base_url}{settings.inflection_reports_runs_list}"
        start_date, end_date = self._prepare_date_range(start_date, end_date)

        payload = {
            "campaign_id": campaign_id,
            "start_date": start_date,
            "end_date": end_date,
            "page_number": page_number,
            "page_size": page_size,
            "show_non_empty_runs": show_non_empty_runs
        }

        response = await self._make_request("POST", url, payload)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "Failed to get report runs list",
                campaign_id=campaign_id,
                status_code=response.status_code,
                response_text=response.text
            )
            response.raise_for_status()

    async def get_recipient_engagement_stats(self, campaign_id: str, start_date: Optional[str] = None,
                                             end_date: Optional[str] = None, page_number: int = 1,
                                             page_size: int = 15, search_keyword: str = "") -> Dict[str, Any]:
        """Get recipient engagement statistics."""
        if not self.auth_state.is_authenticated():
            raise ValueError("Authentication required")

        url = f"{self.campaign_base_url}{settings.inflection_reports_recipient_engagement}"
        start_date, end_date = self._prepare_date_range(start_date, end_date)

        payload = {
            "campaign_id": campaign_id,
            "start_date": start_date,
            "end_date": end_date,
            "query": {
                "search": {
                    "keyword": search_keyword,
                    "fields": ["email", "name"]
                }
            },
            "page_number": page_number,
            "page_size": page_size
        }

        response = await self._make_request("POST", url, payload)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "Failed to get recipient engagement stats",
                campaign_id=campaign_id,
                status_code=response.status_code,
                response_text=response.text
            )
            response.raise_for_status()

    async def get_aggregate_stats(self, campaign_id: str, start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregate statistics for a campaign."""
        if not self.auth_state.is_authenticated():
            raise ValueError("Authentication required")

        url = f"{self.campaign_base_url}{settings.inflection_reports_aggregate}"
        start_date, end_date = self._prepare_date_range(start_date, end_date)

        payload = {
            "campaign_id": campaign_id,
            "start_date": start_date,
            "end_date": end_date
        }

        response = await self._make_request("POST", url, payload)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "Failed to get aggregate stats",
                campaign_id=campaign_id,
                status_code=response.status_code,
                response_text=response.text
            )
            response.raise_for_status()

    async def get_bounce_stats(self, campaign_id: str, start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get bounce statistics using v3 API."""
        if not self.auth_state.is_authenticated():
            raise ValueError("Authentication required")

        start_date, end_date = self._prepare_date_range(start_date, end_date)

        # URL encode the dates
        import urllib.parse
        start_date_encoded = urllib.parse.quote(start_date)
        end_date_encoded = urllib.parse.quote(end_date)

        endpoint = settings.inflection_reports_bounce_stats.format(
            campaign_id=campaign_id)
        url = f"{self.campaign_v3_base_url}{endpoint}?view=aggregate&group_by=bounce_classification&event=bounce&start_date={start_date_encoded}&end_date={end_date_encoded}"

        response = await self._make_request("GET", url)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "Failed to get bounce stats",
                campaign_id=campaign_id,
                status_code=response.status_code,
                response_text=response.text
            )
            response.raise_for_status()

    async def get_bounce_classifications(self) -> Dict[str, Any]:
        """Get bounce classifications reference data."""
        if not self.auth_state.is_authenticated():
            raise ValueError("Authentication required")

        url = f"{self.campaign_v3_base_url}{settings.inflection_reports_bounce_classifications}"

        response = await self._make_request("GET", url)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "Failed to get bounce classifications",
                status_code=response.status_code,
                response_text=response.text
            )
            response.raise_for_status()

    async def get_top_email_client_click_stats(self, campaign_id: str, start_date: Optional[str] = None,
                                               end_date: Optional[str] = None, page_number: int = 1,
                                               page_size: int = 1000) -> Dict[str, Any]:
        """Get top email client click statistics."""
        if not self.auth_state.is_authenticated():
            raise ValueError("Authentication required")

        url = f"{self.campaign_base_url}{settings.inflection_reports_top_email_client_click}"
        start_date, end_date = self._prepare_date_range(start_date, end_date)

        payload = {
            "campaign_id": campaign_id,
            "start_date": start_date,
            "end_date": end_date,
            "page_number": page_number,
            "page_size": page_size
        }

        response = await self._make_request("POST", url, payload)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "Failed to get top email client click stats",
                campaign_id=campaign_id,
                status_code=response.status_code,
                response_text=response.text
            )
            response.raise_for_status()

    async def get_top_email_client_open_stats(self, campaign_id: str, start_date: Optional[str] = None,
                                              end_date: Optional[str] = None, page_number: int = 1,
                                              page_size: int = 1000) -> Dict[str, Any]:
        """Get top email client open statistics."""
        if not self.auth_state.is_authenticated():
            raise ValueError("Authentication required")

        url = f"{self.campaign_base_url}{settings.inflection_reports_top_email_client_open}"
        start_date, end_date = self._prepare_date_range(start_date, end_date)

        payload = {
            "campaign_id": campaign_id,
            "start_date": start_date,
            "end_date": end_date,
            "page_number": page_number,
            "page_size": page_size
        }

        response = await self._make_request("POST", url, payload)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "Failed to get top email client open stats",
                campaign_id=campaign_id,
                status_code=response.status_code,
                response_text=response.text
            )
            response.raise_for_status()

    async def get_top_link_stats(self, campaign_id: str, start_date: Optional[str] = None,
                                 end_date: Optional[str] = None, page_number: int = 1,
                                 page_size: int = 5) -> Dict[str, Any]:
        """Get top link statistics."""
        if not self.auth_state.is_authenticated():
            raise ValueError("Authentication required")

        url = f"{self.campaign_base_url}{settings.inflection_reports_top_link}"
        start_date, end_date = self._prepare_date_range(start_date, end_date)

        payload = {
            "campaign_id": campaign_id,
            "start_date": start_date,
            "end_date": end_date,
            "page_number": page_number,
            "page_size": page_size
        }

        response = await self._make_request("POST", url, payload)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "Failed to get top link stats",
                campaign_id=campaign_id,
                status_code=response.status_code,
                response_text=response.text
            )
            response.raise_for_status()

    async def get_report_runs_stats(self, campaign_id: str, run_ids: list[str]) -> Dict[str, Any]:
        """Get statistics for specific report runs."""
        if not self.auth_state.is_authenticated():
            raise ValueError("Authentication required")

        url = f"{self.campaign_base_url}{settings.inflection_reports_runs_stats}"

        payload = {
            "campaign_id": campaign_id,
            "run_ids": run_ids
        }

        response = await self._make_request("POST", url, payload)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "Failed to get report runs stats",
                campaign_id=campaign_id,
                status_code=response.status_code,
                response_text=response.text
            )
            response.raise_for_status()

    # Legacy method for backward compatibility
    async def get_email_reports(self, journey_id: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Legacy method - now uses aggregate stats as the main report."""
        return await self.get_aggregate_stats(journey_id,
                                              filters.get(
                                                  'start_date') if filters else None,
                                              filters.get('end_date') if filters else None)
