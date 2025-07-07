"""Data models for Inflection.io MCP Server."""

from .auth import AuthResponse, AuthState
from .journey import Journey, JourneyList
from .report import EmailReport, EmailReportList

__all__ = [
    "AuthResponse",
    "AuthState",
    "Journey",
    "JourneyList",
    "EmailReport",
    "EmailReportList",
]
