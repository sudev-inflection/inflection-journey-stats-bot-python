#!/usr/bin/env python3
"""Run the Inflection.io MCP Server."""

from server_new import main
import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Check for required environment variables
if not os.environ.get("INFLECTION_EMAIL"):
    print("❌ INFLECTION_EMAIL environment variable is required")
    print("Please set it in your .env file or environment")
    sys.exit(1)

if not os.environ.get("INFLECTION_PASSWORD"):
    print("❌ INFLECTION_PASSWORD environment variable is required")
    print("Please set it in your .env file or environment")
    sys.exit(1)

# Import and run the server

if __name__ == "__main__":
    print("🚀 Starting Inflection.io MCP Server...")
    print("📋 Available tools: list_journeys, get_email_reports")
    print("🔐 Using authentication from environment variables")
    print("⏳ Initializing server...")

    try:
        import asyncio
        print("✅ Server initialized successfully")
        print("🔄 Server is running and ready for connections...")
        print("💡 Press Ctrl+C to stop the server")
        print("-" * 50)

        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        print("🔍 Check your environment variables and network connection")
        sys.exit(1)
