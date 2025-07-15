#!/usr/bin/env python3
"""Run the Inflection.io MCP Server."""

import os
import sys
import asyncio
import argparse
from pathlib import Path
import json
from typing import Optional, Any

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


async def run_tcp_server(host: str, port: int):
    """Run the MCP server over TCP."""
    from src.server_new import InflectionMCPServer
    import mcp.server
    import mcp.types
    import json
    import asyncio
    from typing import Optional, Any

    print(f"Starting MCP server on {host}:{port}")

    # Create the MCP server
    mcp_server = mcp.server.Server("inflection-mcp-server")

    # Import and set up the server handlers
    inflection_server = InflectionMCPServer()

    # Register handlers using decorators
    @mcp_server.list_tools()
    async def list_tools_handler():
        return await inflection_server.handle_list_tools()

    @mcp_server.call_tool()
    async def call_tool_handler(name: str, arguments: dict):
        if name == "list_journeys":
            content = await inflection_server.list_journeys(
                page_size=arguments.get("page_size", 30),
                page_number=arguments.get("page_number", 1),
                search_keyword=arguments.get("search_keyword", "")
            )
            return [content]
        elif name == "get_email_reports":
            journey_id = arguments.get("journey_id")
            if not journey_id:
                content = mcp.types.TextContent(
                    type="text",
                    text="❌ Journey ID is required. Please provide a valid journey_id parameter."
                )
            else:
                content = await inflection_server.get_email_reports(
                    journey_id=journey_id,
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date")
                )
            return [content]
        else:
            return [mcp.types.TextContent(type="text", text=f"❌ Unknown tool: {name}")]

    async def handle_client(reader, writer):
        """Handle individual client connections."""
        try:
            print(f"Client connected from {writer.get_extra_info('peername')}")

            # Simple HTTP MCP handler
            async def handle_mcp_request(request_data):
                """Handle MCP requests and return responses."""
                method = request_data.get('method')
                request_id = request_data.get('id')
                params = request_data.get('params', {})

                print(f"Handling MCP request: {method}")

                if method == 'initialize':
                    # Return initialization response
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": "2025-06-18",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "inflection-mcp-server",
                                "version": "0.1.0"
                            }
                        }
                    }
                    return response

                elif method == 'tools/list':
                    # Return list of available tools
                    tools = await inflection_server.handle_list_tools()
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "tools": [
                                {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "inputSchema": tool.inputSchema
                                }
                                for tool in tools
                            ]
                        }
                    }
                    return response

                elif method == 'tools/call':
                    # Handle tool calls
                    tool_name = params.get('name')
                    tool_args = params.get('arguments', {})

                    if tool_name == "list_journeys":
                        content = await inflection_server.list_journeys(
                            page_size=tool_args.get("page_size", 30),
                            page_number=tool_args.get("page_number", 1),
                            search_keyword=tool_args.get("search_keyword", "")
                        )
                    elif tool_name == "get_email_reports":
                        journey_id = tool_args.get("journey_id")
                        if not journey_id:
                            content = mcp.types.TextContent(
                                type="text",
                                text="❌ Journey ID is required. Please provide a valid journey_id parameter."
                            )
                        else:
                            content = await inflection_server.get_email_reports(
                                journey_id=journey_id,
                                start_date=tool_args.get("start_date"),
                                end_date=tool_args.get("end_date")
                            )
                    else:
                        content = mcp.types.TextContent(
                            type="text", text=f"❌ Unknown tool: {tool_name}")

                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": content.type,
                                    "text": content.text
                                }
                            ]
                        }
                    }
                    return response

                else:
                    # Unknown method
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                    return response

            # Read HTTP request
            request_line = await reader.readline()
            if not request_line:
                return

            print(f"HTTP Request: {request_line.decode().strip()}")

            # Read HTTP headers
            headers = {}
            while True:
                header_line = await reader.readline()
                if not header_line or header_line == b'\r\n':
                    break
                if b':' in header_line:
                    key, value = header_line.decode().split(':', 1)
                    headers[key.strip().lower()] = value.strip()

            # Read HTTP body
            content_length = int(headers.get('content-length', 0))
            if content_length > 0:
                body_data = await reader.readexactly(content_length)
                request_data = json.loads(body_data.decode('utf-8'))
                print(f"Received: {request_data.get('method', 'unknown')}")
                print(f"JSON data: {json.dumps(request_data, indent=2)}")

                # Handle the MCP request
                response_data = await handle_mcp_request(request_data)

                # Send HTTP response
                response_json = json.dumps(response_data)
                response_bytes = response_json.encode('utf-8')

                http_response = f"""HTTP/1.1 200 OK\r
Content-Type: application/json\r
Content-Length: {len(response_bytes)}\r
\r
"""
                print(f"DEBUG: Sending HTTP response: {http_response}")
                writer.write(http_response.encode())
                writer.write(response_bytes)
                await writer.drain()

                print(f"Sent: {response_data.get('method', 'unknown')}")

        except Exception as e:
            print(f"Client connection error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("Client disconnected")
            writer.close()
            await writer.wait_closed()

    # Start the TCP server
    server = await asyncio.start_server(
        handle_client,
        host,
        port,
        reuse_address=True
    )

    print(f"✅ MCP server listening on {host}:{port}")
    print("💡 Press Ctrl+C to stop the server")

    async with server:
        await server.serve_forever()


async def run_stdio_server():
    """Run the MCP server over stdio."""
    from src.server_new import main as server_main
    await server_main()


def main():
    parser = argparse.ArgumentParser(description="Run Inflection MCP server.")
    parser.add_argument('--host', type=str, default=os.environ.get(
        'MCP_SERVER_HOST', 'localhost'), help='Host to bind the MCP server')
    parser.add_argument('--port', type=int, default=int(os.environ.get(
        'MCP_SERVER_PORT', 8000)), help='Port to bind the MCP server')
    parser.add_argument('--stdio', action='store_true',
                        help='Run in stdio mode (default)')
    args = parser.parse_args()

    # If stdio flag is set or no host/port specified, run in stdio mode
    if args.stdio or (args.host == 'localhost' and args.port == 8000 and not any(sys.argv[1:])):
        print("Starting MCP server in stdio mode")
        asyncio.run(run_stdio_server())
    else:
        # Run in TCP mode
        asyncio.run(run_tcp_server(args.host, args.port))


if __name__ == "__main__":
    print("🚀 Starting Inflection.io MCP Server...")
    print("📋 Available tools: list_journeys, get_email_reports")
    print("🔐 Using authentication from environment variables")
    print("⏳ Initializing server...")

    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        print("🔍 Check your environment variables and network connection")
        sys.exit(1)
