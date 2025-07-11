#!/usr/bin/env python3
"""
Setup script for Inflection.io MCP Server in Replit environment.
This script helps users configure the required environment variables.
"""

import os
import sys
from pathlib import Path


def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking environment configuration...")

    # MCP Server required variables
    mcp_required_vars = ["INFLECTION_EMAIL", "INFLECTION_PASSWORD"]

    # Slack Bot required variables (optional for basic MCP functionality)
    slack_required_vars = ["SLACK_BOT_TOKEN",
                           "SLACK_SIGNING_SECRET", "OPENAI_API_KEY"]

    missing_mcp_vars = []
    missing_slack_vars = []

    # Check MCP variables
    for var in mcp_required_vars:
        if not os.environ.get(var):
            missing_mcp_vars.append(var)

    # Check Slack variables
    for var in slack_required_vars:
        if not os.environ.get(var):
            missing_slack_vars.append(var)

    if missing_mcp_vars:
        print("❌ Missing required MCP server environment variables:")
        for var in missing_mcp_vars:
            print(f"   - {var}")
        print("\n📝 Please set these in Replit's Secrets tab:")
        print("   1. Go to the 'Secrets' tab in the left sidebar")
        print("   2. Add the following secrets:")
        print("      - INFLECTION_EMAIL: your_email@inflection.io")
        print("      - INFLECTION_PASSWORD: your_password")
        print("   3. Restart the repl after adding secrets")
        return False

    if missing_slack_vars:
        print("⚠️  Missing Slack bot environment variables (optional):")
        for var in missing_slack_vars:
            print(f"   - {var}")
        print("\n📝 To enable Slack bot functionality, add these to Replit Secrets:")
        print("   - SLACK_BOT_TOKEN: Your Slack bot token")
        print("   - SLACK_SIGNING_SECRET: Your Slack app signing secret")
        print("   - OPENAI_API_KEY: Your OpenAI API key")
        print("   The MCP server will still work without these.")

    print("✅ All required environment variables are set!")
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n📦 Checking dependencies...")

    try:
        import mcp
        import httpx
        import structlog
        import fastapi
        import uvicorn
        print("✅ All required dependencies are installed!")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing dependencies...")
        os.system("pip install -r requirements.txt")
        return True


def test_imports():
    """Test if the server modules can be imported."""
    print("\n🧪 Testing imports...")

    try:
        # Test basic imports first
        import mcp
        import httpx
        import structlog
        import fastapi
        import uvicorn
        print("✅ Core dependencies imported successfully!")

        # Test MCP server modules
        try:
            from src.server_new import InflectionMCPServer, InflectionAPIClient
            print("✅ MCP server modules imported successfully!")
        except ImportError as e:
            print(f"❌ MCP server import error: {e}")
            return False

        # Try to import Slack bot modules (optional)
        try:
            from fastagent_slack_server import app as slack_app
            print("✅ Slack bot modules imported successfully!")
        except ImportError as e:
            print(f"⚠️  Slack bot modules not available: {e}")
            print("   This is normal if Slack environment variables are not set.")

        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try running: pip install -r requirements.txt")
        return False


def show_next_steps():
    """Show next steps for the user."""
    print("\n🎉 Setup complete! Next steps:")
    print("1. Make sure your Inflection.io credentials are set in Replit Secrets")
    print("2. Click the 'Run' button to start the combined server")
    print("3. The server will be available at the URL shown in the webview")
    print("\n📋 Available endpoints:")
    print("   - GET  /health - Health check")
    print("   - GET  /mcp - MCP server endpoints")
    print("   - GET  /slack - Slack bot endpoints (if configured)")
    print("   - POST /mcp/journeys - List marketing journeys")
    print("   - POST /mcp/reports - Get email reports")
    print("   - POST /slack/events - Slack event handling")


def main():
    """Main setup function."""
    print("🚀 Inflection.io Combined MCP + Slack Bot Server Setup")
    print("=" * 55)

    # Check environment
    env_ok = check_environment()

    # Check dependencies
    deps_ok = check_dependencies()

    # Test imports
    imports_ok = test_imports()

    if env_ok and deps_ok and imports_ok:
        show_next_steps()
        return True
    else:
        print("\n❌ Setup incomplete. Please fix the issues above and try again.")
        print("💡 If you're having dependency issues, try:")
        print("   1. pip install -r requirements.txt")
        print("   2. pip install rpds-py")
        print("   3. Restart the repl")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
