#!/usr/bin/env python3
"""Test script for the web server functionality."""

import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test configuration
BASE_URL = "http://localhost:8000"


async def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing health check...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200


async def test_list_tools():
    """Test the tools listing endpoint."""
    print("\n🔍 Testing tools listing...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/tools")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200


async def test_list_journeys():
    """Test the journeys listing endpoint."""
    print("\n🔍 Testing journeys listing...")
    async with httpx.AsyncClient() as client:
        payload = {
            "page_size": 5,
            "page_number": 1,
            "search_keyword": ""
        }
        response = await client.post(f"{BASE_URL}/journeys", json=payload)
        print(f"Status: {response.status_code}")
        # Truncate for readability
        print(f"Response: {response.text[:500]}...")
        return response.status_code == 200


async def test_mcp_protocol():
    """Test the MCP protocol endpoint."""
    print("\n🔍 Testing MCP protocol...")
    async with httpx.AsyncClient() as client:
        # Test tools/list
        payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/list",
            "params": {}
        }
        response = await client.post(f"{BASE_URL}/mcp", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200


async def test_root_endpoint():
    """Test the root endpoint."""
    print("\n🔍 Testing root endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200


async def main():
    """Run all tests."""
    print("🚀 Starting web server tests...")
    print(f"Testing against: {BASE_URL}")

    # Check if required environment variables are set
    if not os.environ.get("INFLECTION_EMAIL") or not os.environ.get("INFLECTION_PASSWORD"):
        print(
            "❌ INFLECTION_EMAIL and INFLECTION_PASSWORD environment variables are required")
        print("Please set them in your .env file or environment")
        return

    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("Health Check", test_health_check),
        ("List Tools", test_list_tools),
        ("List Journeys", test_list_journeys),
        ("MCP Protocol", test_mcp_protocol),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The web server is ready for deployment.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
