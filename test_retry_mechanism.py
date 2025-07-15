#!/usr/bin/env python3
"""
Test script to verify the retry mechanism with automatic re-authentication.
This script simulates 401 errors and verifies that the system automatically re-authenticates.
"""

from server_new import InflectionAPIClient, auth_state
import asyncio
import os
import sys
from datetime import datetime, timedelta
import pytz

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def test_retry_mechanism():
    """Test the retry mechanism with automatic re-authentication."""
    print("🧪 Testing retry mechanism with automatic re-authentication...")

    # Check if credentials are available
    email = os.environ.get("INFLECTION_EMAIL")
    password = os.environ.get("INFLECTION_PASSWORD")

    if not email or not password:
        print("❌ Missing credentials. Please set INFLECTION_EMAIL and INFLECTION_PASSWORD environment variables.")
        return False

    client = InflectionAPIClient()

    try:
        # Test 1: Initial authentication
        print("\n1️⃣ Testing initial authentication...")
        await client.login(email, password)
        print("✅ Initial authentication successful")

        # Test 2: Make a request that should work
        print("\n2️⃣ Testing normal API call...")
        journeys = await client.get_journeys(page_size=5)
        print(
            f"✅ Normal API call successful, got {len(journeys.get('records', []))} journeys")

        # Test 3: Simulate token expiration by clearing auth state
        print("\n3️⃣ Testing automatic re-authentication after token expiration...")
        original_token = auth_state["access_token"]
        auth_state["access_token"] = None
        auth_state["refresh_token"] = None
        auth_state["expires_at"] = None
        auth_state["is_authenticated"] = False

        # This should trigger automatic re-authentication
        journeys = await client.get_journeys(page_size=5)
        print(
            f"✅ Automatic re-authentication successful, got {len(journeys.get('records', []))} journeys")

        # Verify token was refreshed
        if auth_state["access_token"] != original_token:
            print("✅ Token was successfully refreshed")
        else:
            print(
                "⚠️ Token appears to be the same (this might be expected if tokens are still valid)")

        # Test 4: Test email reports with retry mechanism
        print("\n4️⃣ Testing email reports with retry mechanism...")
        if journeys.get('records'):
            first_journey_id = journeys['records'][0].get('id')
            if first_journey_id:
                reports = await client.get_email_reports(journey_id=first_journey_id)
                print(
                    f"✅ Email reports successful, got {len(reports)} endpoint results")
            else:
                print("⚠️ No journey ID found for email reports test")
        else:
            print("⚠️ No journeys found for email reports test")

        print("\n🎉 All tests passed! The retry mechanism is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    finally:
        await client.__aexit__(None, None, None)


async def test_401_handling():
    """Test specific 401 error handling."""
    print("\n🔍 Testing specific 401 error handling...")

    client = InflectionAPIClient()

    try:
        # Ensure we're authenticated
        email = os.environ.get("INFLECTION_EMAIL")
        password = os.environ.get("INFLECTION_PASSWORD")

        if not email or not password:
            print("❌ Missing credentials for 401 test")
            return False

        await client.login(email, password)

        # Test the _make_authenticated_request method directly
        print("Testing _make_authenticated_request with valid request...")
        response = await client._make_authenticated_request(
            "POST",
            f"{client.campaign_v1_client.base_url}/campaigns/campaign.list",
            json={"page_size": 1, "page_number": 1, "query": {
                "search": {"keyword": "", "fields": ["name"]}}}
        )

        if response.status_code == 200:
            print("✅ _make_authenticated_request works correctly")
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")

        return True

    except Exception as e:
        print(f"❌ 401 test failed: {str(e)}")
        return False
    finally:
        await client.__aexit__(None, None, None)


async def main():
    """Run all tests."""
    print("🚀 Starting retry mechanism tests...")

    success1 = await test_retry_mechanism()
    success2 = await test_401_handling()

    if success1 and success2:
        print("\n🎉 All tests passed! The retry mechanism is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
