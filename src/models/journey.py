"""Journey data models."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class CreatedBy(BaseModel):
    """Creator information."""
    id: int = Field(..., description="Creator ID")
    name: str = Field(..., description="Creator name")


class Schedule(BaseModel):
    """Schedule information."""
    next_run_time: Optional[str] = Field(None, description="Next run time")


class Journey(BaseModel):
    """Journey data model matching the actual API response."""

    campaign_id: str = Field(..., description="Campaign/Journey ID")
    name: str = Field(..., description="Journey name")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp")
    active: Optional[bool] = Field(
        None, description="Whether the journey is active")
    draft: Optional[bool] = Field(
        None, description="Whether the journey is in draft mode")
    campaign_type: Optional[str] = Field(None, description="Campaign type")
    campaign_context: Optional[str] = Field(
        None, description="Campaign context")
    override_email_limits: Optional[bool] = Field(
        None, description="Email limits override")
    override_email_limits_type: Optional[str] = Field(
        None, description="Email limits override type")
    created_by: Optional[CreatedBy] = Field(
        None, description="Creator information")
    schedule: Optional[Schedule] = Field(
        None, description="Schedule information")

    @property
    def id(self) -> str:
        """Get the journey ID (alias for campaign_id)."""
        return self.campaign_id

    @property
    def status(self) -> str:
        """Get the journey status based on active and draft fields."""
        if self.draft:
            return "Draft"
        elif self.active:
            return "Active"
        else:
            return "Inactive"

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "68397ac4f62591f7d196b010",
                "name": "test-naman",
                "created_at": "2025-05-30T09:30:44.743505+00:00",
                "updated_at": "2025-07-15T04:47:45.547185+00:00",
                "active": False,
                "draft": True,
                "campaign_type": "BATCH_CAMPAIGN",
                "campaign_context": "person"
            }
        }


class JourneyList(BaseModel):
    """List of journeys response matching the actual API response."""

    records: List[Journey] = Field(..., description="List of journeys")
    page_count: int = Field(..., description="Total number of pages")
    record_count: int = Field(..., description="Total number of records")

    class Config:
        json_schema_extra = {
            "example": {
                "records": [
                    {
                        "campaign_id": "68397ac4f62591f7d196b010",
                        "name": "test-naman",
                        "active": False,
                        "draft": True
                    }
                ],
                "page_count": 96,
                "record_count": 192
            }
        }
