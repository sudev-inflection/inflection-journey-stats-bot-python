#!/usr/bin/env python3
"""Test script for SSE (Server-Sent Events) functionality."""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Test configuration
BASE_URL = "http://localhost:8000"


async def test_sse_connection():
    """Test SSE connection and event reception."""
    print("🔍 Testing SSE connection...")

    try:
        async with aiohttp.ClientSession() as session:
            # Connect to SSE endpoint
            async with session.get(f"{BASE_URL}/sse/events") as response:
                print(f"SSE Connection Status: {response.status}")

                if response.status == 200:
                    print("✅ SSE connection established")

                    # Read events for 30 seconds
                    events_received = []
                    timeout = 30
                    start_time = datetime.now()

                    async for line in response.content:
                        line = line.decode('utf-8').strip()

                        if line.startswith('event:'):
                            event_type = line.split(':', 1)[1].strip()
                            print(f"📡 Received event: {event_type}")
                            events_received.append(event_type)

                        elif line.startswith('data:'):
                            try:
                                data = json.loads(
                                    line.split(':', 1)[1].strip())
                                print(f"   Data: {json.dumps(data, indent=2)}")
                            except:
                                pass

                        # Check timeout
                        if (datetime.now() - start_time).seconds > timeout:
                            break

                    print(
                        f"📊 Received {len(events_received)} events in {timeout} seconds")
                    return len(events_received) > 0
                else:
                    print(f"❌ SSE connection failed: {response.status}")
                    return False

    except Exception as e:
        print(f"❌ SSE test failed: {e}")
        return False


async def test_sse_info():
    """Test SSE information endpoint."""
    print("\n🔍 Testing SSE info endpoint...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/sse") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ SSE info: {json.dumps(data, indent=2)}")
                    return True
                else:
                    print(f"❌ SSE info failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ SSE info test failed: {e}")
        return False


async def test_sse_trigger():
    """Test SSE event triggering."""
    print("\n🔍 Testing SSE event trigger...")

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "event_type": "test_event",
                "data": {
                    "message": "Test event from n8n",
                    "source": "test_script",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            async with session.post(f"{BASE_URL}/sse/trigger", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ SSE trigger: {json.dumps(data, indent=2)}")
                    return True
                else:
                    print(f"❌ SSE trigger failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ SSE trigger test failed: {e}")
        return False


async def test_n8n_integration_scenario():
    """Test a realistic n8n integration scenario."""
    print("\n🔍 Testing n8n integration scenario...")

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Get server info
            async with session.get(f"{BASE_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(
                        f"✅ Server info: SSE support = {data.get('sse_support', False)}")
                    print(
                        f"✅ n8n integration = {data.get('n8n_integration', False)}")

            # 2. Check health
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check: {data.get('status')}")
                    print(
                        f"✅ SSE connections: {data.get('sse_connections', 0)}")

            # 3. Get available tools
            async with session.get(f"{BASE_URL}/tools") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Available tools: {len(data.get('tools', []))}")

            return True

    except Exception as e:
        print(f"❌ n8n integration test failed: {e}")
        return False


async def main():
    """Run all SSE tests."""
    print("🚀 Starting SSE Tests for n8n Integration")
    print("=" * 60)

    # Check if required environment variables are set
    if not os.environ.get("INFLECTION_EMAIL") or not os.environ.get("INFLECTION_PASSWORD"):
        print(
            "❌ INFLECTION_EMAIL and INFLECTION_PASSWORD environment variables are required")
        print("Please set them in your .env file or environment")
        return

    tests = [
        ("SSE Info", test_sse_info),
        ("n8n Integration", test_n8n_integration_scenario),
        ("SSE Trigger", test_sse_trigger),
        ("SSE Connection", test_sse_connection),
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
    print("\n" + "=" * 60)
    print("📊 SSE TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All SSE tests passed! Ready for n8n integration.")
        print("\n📋 n8n Integration Instructions:")
        print("1. Deploy to Railway using the existing configuration")
        print("2. In n8n, use the 'Webhook' node to connect to your SSE endpoint")
        print("3. Set the webhook URL to: https://your-app.railway.app/sse/events")
        print("4. Configure n8n to handle SSE events for automation workflows")
        print("\n📡 Available SSE Events:")
        print("   - journey_update: Real-time journey status updates")
        print("   - health_check: Server health status")
        print("   - error: Error notifications")
        print("   - connection: Connection establishment")
    else:
        print("\n⚠️  Some SSE tests failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
