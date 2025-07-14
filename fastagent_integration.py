#!/usr/bin/env python3
"""Fast-Agent integration script for Slack bot."""

import os
import sys
import asyncio
import json
import subprocess
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class FastAgentIntegration:
    """Integration class for Fast-Agent with MCP servers."""

    def __init__(self):
        self.mcp_server_url = os.environ.get(
            "MCP_SERVER_URL", "https://inflection-journey-stats-bot-python-production.up.railway.app")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

    def create_fastagent_config(self) -> Dict[str, Any]:
        """Create Fast-Agent configuration."""
        return {
            "default_model": "openai",
            "models": {
                "openai": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "temperature": 0.7,
                    "max_tokens": 4000
                }
            },
            "mcp_servers": {
                "inflection": {
                    "url": f"{self.mcp_server_url}/mcp",
                    "description": "Inflection.io marketing automation tools"
                }
            }
        }

    def write_config_file(self, config: Dict[str, Any]) -> str:
        """Write configuration to a temporary file."""
        config_content = f"""# Fast-Agent Configuration
default_model: openai

models:
  openai:
    provider: openai
    model: gpt-4o
    temperature: 0.7
    max_tokens: 4000

mcp_servers:
  inflection:
    url: {self.mcp_server_url}/mcp
    description: "Inflection.io marketing automation tools"
"""

        # Create temporary config file
        config_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False)
        config_file.write(config_content)
        config_file.close()

        return config_file.name

    async def call_fastagent(self, message: str) -> str:
        """Call Fast-Agent with the given message."""
        try:
            # Set environment variables for Fast-Agent
            env = os.environ.copy()
            env["OPENAI_API_KEY"] = self.openai_api_key

            # Use the direct URL approach as the user mentioned
            cmd = [
                "fast-agent", "go",
                "--url", f"{self.mcp_server_url}/mcp",
                "--message", message
            ]

            # Run Fast-Agent
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error running Fast-Agent: {result.stderr}"

        except subprocess.TimeoutExpired:
            return "Request timed out. Please try again."
        except FileNotFoundError:
            return "Fast-Agent CLI not found. Please install it first."
        except Exception as e:
            return f"Error calling Fast-Agent: {str(e)}"

    async def call_fastagent_http(self, message: str) -> str:
        """Call Fast-Agent via HTTP if available."""
        try:
            # Try to call Fast-Agent via HTTP endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/chat",
                    json={
                        "message": message,
                        "config": self.create_fastagent_config()
                    },
                    timeout=60.0
                )

                if response.status_code == 200:
                    return response.json().get("response", "No response")
                else:
                    return f"HTTP Error: {response.status_code}"

        except Exception as e:
            # Fall back to CLI method
            return await self.call_fastagent(message)


async def main():
    """Main function for testing."""
    if len(sys.argv) < 2:
        print("Usage: python fastagent_integration.py <message>")
        sys.exit(1)

    message = " ".join(sys.argv[1:])

    integration = FastAgentIntegration()
    response = await integration.call_fastagent(message)
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
