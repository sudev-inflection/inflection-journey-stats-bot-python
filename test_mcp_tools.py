#!/usr/bin/env python3
"""Test script for MCP tools with improved authentication handling."""

from src.server_new import InflectionMCPServer
import asyncio
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_login():
    """Test the login tool."""
    print("\n🔐 Testing inflection_login...")

    # Get credentials from environment or prompt user
    email = os.environ.get("INFLECTION_EMAIL")
    password = os.environ.get("INFLECTION_PASSWORD")

    if not email or not password:
        print(
            "❌ INFLECTION_EMAIL and INFLECTION_PASSWORD environment variables are required")
        return False

    try:
        server = InflectionMCPServer()
        result = await server.login(email, password)
        print(f"Result: {result.text}")
        return "✅" in result.text
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False


async def test_list_journeys():
    """Test listing journeys."""
    print("\n📋 Testing list_journeys...")

    try:
        server = InflectionMCPServer()
        result = await server.list_journeys(page_size=5, page_number=1)
        print(f"Result: {result.text}")
        return "❌" not in result.text
    except Exception as e:
        print(f"❌ list_journeys failed: {e}")
        return False


async def test_get_email_reports():
    """Test getting email reports."""
    print("\n📧 Testing get_email_reports...")

    # Use a test journey ID - you'll need to replace this with a real one
    test_journey_id = "test_journey_id"  # Replace with actual journey ID

    try:
        server = InflectionMCPServer()
        result = await server.get_email_reports(journey_id=test_journey_id)
        print(f"Result: {result.text}")
        return "❌" not in result.text
    except Exception as e:
        print(f"❌ get_email_reports failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Testing Inflection.io MCP Tools")
    print("=" * 50)

    # Test login first
    login_success = await test_login()

    if login_success:
        print("\n✅ Login successful! Testing other tools...")

        # Test list journeys
        await test_list_journeys()

        # Test get email reports (will likely fail without a real journey ID)
        await test_get_email_reports()
    else:
        print("\n❌ Login failed. Cannot test other tools without authentication.")
        print("Please check your INFLECTION_EMAIL and INFLECTION_PASSWORD environment variables.")

    print("\n" + "=" * 50)
    print("🏁 Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
