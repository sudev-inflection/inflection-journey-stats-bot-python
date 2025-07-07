"""Email report data models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class EmailReport(BaseModel):
    """Email report data model."""

    journey_id: str = Field(..., description="Journey ID")
    report_date: datetime = Field(..., description="Report date")
    sent_count: int = Field(0, description="Number of emails sent")
    delivered_count: Optional[int] = Field(
        None, description="Number of emails delivered")
    open_count: int = Field(0, description="Number of opens")
    click_count: int = Field(0, description="Number of clicks")
    bounce_count: int = Field(0, description="Number of bounces")
    unsubscribe_count: int = Field(0, description="Number of unsubscribes")
    spam_count: Optional[int] = Field(
        None, description="Number of spam reports")
    open_rate: Optional[float] = Field(
        None, description="Open rate percentage")
    click_rate: Optional[float] = Field(
        None, description="Click rate percentage")
    bounce_rate: Optional[float] = Field(
        None, description="Bounce rate percentage")
    unsubscribe_rate: Optional[float] = Field(
        None, description="Unsubscribe rate percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "journey_id": "journey_123",
                "report_date": "2024-01-15T00:00:00Z",
                "sent_count": 1000,
                "delivered_count": 980,
                "open_count": 250,
                "click_count": 75,
                "bounce_count": 20,
                "unsubscribe_count": 5,
                "spam_count": 1,
                "open_rate": 25.5,
                "click_rate": 7.5,
                "bounce_rate": 2.0,
                "unsubscribe_rate": 0.5
            }
        }


class EmailReportList(BaseModel):
    """List of email reports response."""

    reports: List[EmailReport] = Field(...,
                                       description="List of email reports")
    journey_id: str = Field(..., description="Journey ID")
    total_count: int = Field(..., description="Total number of reports")
    date_range: Optional[dict] = Field(
        None, description="Date range for reports")

    class Config:
        json_schema_extra = {
            "example": {
                "reports": [
                    {
                        "journey_id": "journey_123",
                        "report_date": "2024-01-15T00:00:00Z",
                        "sent_count": 1000,
                        "open_count": 250,
                        "click_count": 75
                    }
                ],
                "journey_id": "journey_123",
                "total_count": 1,
                "date_range": {
                    "start": "2024-01-01",
                    "end": "2024-01-31"
                }
            }
        }
