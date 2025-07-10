from fastapi import FastAPI
# from web_server import app as mcp_app  # MCP FastAPI app
# from fastagent_slack_server import app as slack_app  # Slack bot FastAPI app

print("=== Starting combined_server.py ===")

app = FastAPI(title="Combined MCP + Slack Bot Server")

# Mount the MCP server at /mcp
# app.mount("/mcp", mcp_app)

# # Mount the Slack bot at /slack
# app.mount("/slack", slack_app)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Combined MCP + Slack bot server running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
