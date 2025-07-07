#!/usr/bin/env python3
"""Test script for the new Inflection.io MCP Server."""

from server_new import api_client, list_journeys, get_email_reports
import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_authentication():
    """Test authentication with environment variables."""
    print("🔐 Testing authentication...")

    if not os.environ.get("INFLECTION_EMAIL") or not os.environ.get("INFLECTION_PASSWORD"):
        print(
            "❌ INFLECTION_EMAIL and INFLECTION_PASSWORD environment variables are required")
        return False

    try:
        # Test login
        await api_client.login(
            os.environ["INFLECTION_EMAIL"],
            os.environ["INFLECTION_PASSWORD"]
        )
        print("✅ Authentication successful")
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False


async def test_list_journeys():
    """Test listing journeys."""
    print("\n📋 Testing list_journeys...")

    try:
        result = await list_journeys({
            "page_size": 5,
            "page_number": 1,
            "search_keyword": ""
        })
        print("✅ list_journeys successful")
        print(f"Response preview: {result.text[:200]}...")
        return True
    except Exception as e:
        print(f"❌ list_journeys failed: {e}")
        return False


async def test_get_email_reports():
    """Test getting email reports."""
    print("\n📧 Testing get_email_reports...")

    # Use a test journey ID from the examples
    test_journey_id = "67b9bd0a699f2660099ae910"

    try:
        result = await get_email_reports({
            "journey_id": test_journey_id,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31"
        })
        print("✅ get_email_reports successful")
        print(f"Response preview: {result.text[:200]}...")
        return True
    except Exception as e:
        print(f"❌ get_email_reports failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Testing Inflection.io MCP Server")
    print("=" * 50)

    # Test authentication
    auth_success = await test_authentication()
    if not auth_success:
        print("\n❌ Authentication failed. Cannot proceed with other tests.")
        return

    # Test list journeys
    await test_list_journeys()

    # Test get email reports
    await test_get_email_reports()

    print("\n" + "=" * 50)
    print("✅ All tests completed!")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
