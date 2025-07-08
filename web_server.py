#!/usr/bin/env python3
"""Web server for Inflection.io MCP Server with HTTP endpoints for Railway deployment."""

from src.server_new import InflectionMCPServer
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
import httpx
import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime
import time
import uuid
from contextlib import asynccontextmanager

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Check for required environment variables
if not os.environ.get("INFLECTION_EMAIL"):
    print("❌ INFLECTION_EMAIL environment variable is required")
    print("Please set it in your Railway environment variables")
    sys.exit(1)

if not os.environ.get("INFLECTION_PASSWORD"):
    print("❌ INFLECTION_PASSWORD environment variable is required")
    print("Please set it in your Railway environment variables")
    sys.exit(1)

# Global state for SSE connections and background tasks
sse_connections: List[asyncio.Queue] = []
background_tasks: List[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    print("🚀 Starting Inflection.io MCP Server with SSE support...")

    # Start background tasks
    background_tasks.append(asyncio.create_task(periodic_journey_updates()))
    background_tasks.append(asyncio.create_task(periodic_health_checks()))

    yield

    # Shutdown
    print("🛑 Shutting down server...")
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)

# Import our MCP server

# Create FastAPI app
app = FastAPI(
    title="Inflection.io MCP Server",
    description="MCP Server for Inflection.io marketing automation platform with SSE support",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the MCP server
mcp_server = InflectionMCPServer()

# Pydantic models for request/response


class JourneyListRequest(BaseModel):
    page_size: Optional[int] = 30
    page_number: Optional[int] = 1
    search_keyword: Optional[str] = ""


class EmailReportsRequest(BaseModel):
    journey_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class SSEEventRequest(BaseModel):
    event_type: str
    data: Dict[str, Any]


async def send_sse_event(event_type: str, data: Dict[str, Any]):
    """Send SSE event to all connected clients."""
    event_id = str(uuid.uuid4())
    event_data = {
        "id": event_id,
        "event": event_type,
        "data": json.dumps(data),
        "timestamp": datetime.utcnow().isoformat()
    }

    # Format SSE message
    sse_message = f"id: {event_id}\n"
    sse_message += f"event: {event_type}\n"
    sse_message += f"data: {json.dumps(data)}\n"
    sse_message += f"timestamp: {datetime.utcnow().isoformat()}\n\n"

    # Send to all connected clients
    disconnected = []
    for queue in sse_connections:
        try:
            await queue.put(sse_message)
        except Exception:
            disconnected.append(queue)

    # Remove disconnected clients
    for queue in disconnected:
        sse_connections.remove(queue)


async def periodic_journey_updates():
    """Periodically check for journey updates and send SSE events."""
    while True:
        try:
            # Get current journeys
            content = await mcp_server.list_journeys(page_size=10, page_number=1)

            # Parse the content to extract journey data
            # This is a simplified version - you might want to parse the actual response
            journey_data = {
                "type": "journey_update",
                "timestamp": datetime.utcnow().isoformat(),
                # Truncated for demo
                "summary": f"Retrieved {content.text[:100]}..."
            }

            await send_sse_event("journey_update", journey_data)

        except Exception as e:
            error_data = {
                "type": "error",
                "message": f"Journey update failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
            await send_sse_event("error", error_data)

        # Wait 5 minutes before next update
        await asyncio.sleep(300)


async def periodic_health_checks():
    """Periodically send health check events."""
    while True:
        try:
            from src.server_new import InflectionAPIClient
            async with InflectionAPIClient() as client:
                is_authenticated = await client.ensure_authenticated()

            health_data = {
                "status": "healthy" if is_authenticated else "unhealthy",
                "authentication": "ok" if is_authenticated else "failed",
                "timestamp": datetime.utcnow().isoformat()
            }

            await send_sse_event("health_check", health_data)

        except Exception as e:
            error_data = {
                "type": "error",
                "message": f"Health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
            await send_sse_event("error", error_data)

        # Wait 1 minute before next health check
        await asyncio.sleep(60)


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "Inflection.io MCP Server",
        "version": "1.0.0",
        "status": "running",
        "description": "MCP Server for Inflection.io marketing automation platform",
        "endpoints": {
            "health": "/health",
            "tools": "/tools",
            "mcp": "/mcp",
            "journeys": "/journeys",
            "reports": "/reports"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/tools")
async def list_tools():
    """List available MCP tools."""
    try:
        tools = await mcp_server.handle_list_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/journeys")
async def list_journeys(request: JourneyListRequest):
    """List marketing journeys."""
    try:
        content = await mcp_server.list_journeys(
            page_size=request.page_size,
            page_number=request.page_number,
            search_keyword=request.search_keyword
        )
        return {"content": content.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reports")
async def get_email_reports(request: EmailReportsRequest):
    """Get email reports for a journey."""
    try:
        content = await mcp_server.get_email_reports(
            journey_id=request.journey_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return {"content": content.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest):
    """Handle MCP protocol requests."""
    try:
        if request.method == "initialize":
            response = MCPResponse(
                id=request.id,
                result={
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "inflection-mcp-server",
                        "version": "1.0.0"
                    }
                }
            )
            return response

        elif request.method == "tools/list":
            tools = await mcp_server.handle_list_tools()
            response = MCPResponse(
                id=request.id,
                result={
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools
                    ]
                }
            )
            return response

        elif request.method == "tools/call":
            params = request.params or {}
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            if tool_name == "list_journeys":
                content = await mcp_server.list_journeys(
                    page_size=tool_args.get("page_size", 30),
                    page_number=tool_args.get("page_number", 1),
                    search_keyword=tool_args.get("search_keyword", "")
                )
            elif tool_name == "get_email_reports":
                content = await mcp_server.get_email_reports(
                    journey_id=tool_args.get("journey_id", ""),
                    start_date=tool_args.get("start_date"),
                    end_date=tool_args.get("end_date")
                )
            else:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {tool_name}"
                    }
                )

            response = MCPResponse(
                id=request.id,
                result={
                    "content": [
                        {
                            "type": content.type,
                            "text": content.text
                        }
                    ]
                }
            )
            return response

        else:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {request.method}"
                }
            )

    except Exception as e:
        return MCPResponse(
            id=request.id,
            error={
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


def main():
    """Main function to run the server."""
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"🚀 Starting Inflection.io MCP Server on {host}:{port}")
    print("📋 Available endpoints:")
    print("   - GET  /health - Health check")
    print("   - GET  /tools - List available tools")
    print("   - POST /journeys - List marketing journeys")
    print("   - POST /reports - Get email reports")
    print("   - POST /mcp - MCP protocol endpoint")
    print("🔐 Using authentication from environment variables")

    uvicorn.run(
        "web_server:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
