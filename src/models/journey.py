"""Journey data models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Journey(BaseModel):
    """Journey data model."""

    id: str = Field(..., description="Journey ID")
    name: str = Field(..., description="Journey name")
    status: Optional[str] = Field(None, description="Journey status")
    description: Optional[str] = Field(None, description="Journey description")
    created_at: Optional[datetime] = Field(
        None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(
        None, description="Last update timestamp")
    metadata: Optional[dict] = Field(
        None, description="Additional journey metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "journey_123",
                "name": "Welcome Series",
                "status": "active",
                "description": "Welcome email series for new users",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T12:00:00Z",
                "metadata": {
                    "category": "onboarding",
                    "tags": ["welcome", "new-user"]
                }
            }
        }


class JourneyList(BaseModel):
    """List of journeys response."""

    journeys: List[Journey] = Field(..., description="List of journeys")
    total_count: int = Field(..., description="Total number of journeys")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(
        None, description="Number of items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "journeys": [
                    {
                        "id": "journey_123",
                        "name": "Welcome Series",
                        "status": "active"
                    }
                ],
                "total_count": 1,
                "page": 1,
                "page_size": 10
            }
        }
