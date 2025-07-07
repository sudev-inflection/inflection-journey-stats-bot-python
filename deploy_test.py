#!/usr/bin/env python3
"""Deployment test script to verify Railway deployment configuration."""

import os
import sys
import subprocess
import time
import requests
import json
from pathlib import Path


def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking environment variables...")

    required_vars = ["INFLECTION_EMAIL", "INFLECTION_PASSWORD"]
    missing_vars = []

    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        print(
            f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file or environment")
        return False

    print("✅ All required environment variables are set")
    return True


def check_files():
    """Check if all required deployment files exist."""
    print("\n🔍 Checking deployment files...")

    required_files = [
        "railway.toml",
        "nixpacks.toml",
        "Procfile",
        "requirements.txt",
        "web_server.py"
    ]

    missing_files = []

    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False

    print("✅ All required deployment files exist")
    return True


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("\n🔍 Checking dependencies...")

    try:
        import fastapi
        import uvicorn
        import httpx
        import pydantic
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False


def start_server():
    """Start the web server in the background."""
    print("\n🚀 Starting web server...")

    try:
        # Start the server in the background
        process = subprocess.Popen(
            [sys.executable, "web_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait a bit for the server to start
        time.sleep(3)

        # Check if process is still running
        if process.poll() is None:
            print("✅ Web server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return None

    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None


def test_endpoints(server_process):
    """Test all endpoints."""
    print("\n🔍 Testing endpoints...")

    base_url = "http://localhost:8000"
    tests = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/health", "Health check"),
        ("GET", "/tools", "Tools listing"),
    ]

    results = []

    for method, endpoint, description in tests:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{base_url}{endpoint}", timeout=10)

            if response.status_code == 200:
                print(f"✅ {description}: OK")
                results.append(True)
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                results.append(False)

        except Exception as e:
            print(f"❌ {description}: Error - {e}")
            results.append(False)

    return results


def test_mcp_protocol():
    """Test MCP protocol endpoint."""
    print("\n🔍 Testing MCP protocol...")

    try:
        payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/list",
            "params": {}
        }

        response = requests.post(
            "http://localhost:8000/mcp",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if "result" in data and "tools" in data["result"]:
                print(
                    f"✅ MCP protocol: OK ({len(data['result']['tools'])} tools)")
                return True
            else:
                print(f"❌ MCP protocol: Invalid response format")
                return False
        else:
            print(f"❌ MCP protocol: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ MCP protocol: Error - {e}")
        return False


def cleanup(server_process):
    """Clean up the server process."""
    if server_process:
        print("\n🧹 Cleaning up...")
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped")


def main():
    """Run the deployment test."""
    print("🚀 Railway Deployment Test")
    print("=" * 50)

    # Check prerequisites
    if not check_environment():
        return False

    if not check_files():
        return False

    if not check_dependencies():
        return False

    # Start server
    server_process = start_server()
    if not server_process:
        return False

    try:
        # Test endpoints
        endpoint_results = test_endpoints(server_process)

        # Test MCP protocol
        mcp_result = test_mcp_protocol()

        # Summary
        print("\n" + "=" * 50)
        print("📊 DEPLOYMENT TEST SUMMARY")
        print("=" * 50)

        total_tests = len(endpoint_results) + 1
        passed_tests = sum(endpoint_results) + (1 if mcp_result else 0)

        print(
            f"Endpoint tests: {sum(endpoint_results)}/{len(endpoint_results)} passed")
        print(f"MCP protocol: {'PASSED' if mcp_result else 'FAILED'}")
        print(f"Overall: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("\n🎉 All tests passed! Ready for Railway deployment.")
            print("\nNext steps:")
            print("1. Push your code to GitHub")
            print("2. Connect your repository to Railway.app")
            print("3. Set environment variables in Railway dashboard")
            print("4. Deploy!")
            return True
        else:
            print("\n⚠️  Some tests failed. Please check the errors above.")
            return False

    finally:
        cleanup(server_process)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
