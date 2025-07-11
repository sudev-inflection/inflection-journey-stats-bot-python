from fastapi import FastAPI
from web_server import app as mcp_app  # MCP FastAPI app
from fastagent_slack_server import app as slack_app  # Slack bot FastAPI app
import uvicorn
import os

print("=== Starting combined_server.py ===")

app = FastAPI(title="Combined MCP + Slack Bot Server")

# Mount the MCP server at /mcp
app.mount("/mcp", mcp_app)

# Mount the Slack bot at /slack
app.mount("/slack", slack_app)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Combined MCP + Slack bot server running",
        "endpoints": {
            "mcp": "/mcp",
            "slack": "/slack",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


def main():
    """Main function to run the combined server."""
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"🚀 Starting Combined MCP + Slack Bot Server on {host}:{port}")
    print("📋 Available endpoints:")
    print("   - GET  /health - Health check")
    print("   - GET  /mcp - MCP server endpoints")
    print("   - GET  /slack - Slack bot endpoints")
    print("🔐 Using authentication from environment variables")

    uvicorn.run(
        "combined_server:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
