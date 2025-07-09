#!/usr/bin/env python3
"""Fast-Agent server with Slack integration for Railway deployment."""

import os
import sys
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import httpx
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Import our Fast-Agent integration
from fastagent_integration import FastAgentIntegration

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fast-Agent configuration
FASTAGENT_URL = os.environ.get("FASTAGENT_URL", "http://localhost:8000")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SLACK_VERIFICATION_TOKEN = os.environ.get("SLACK_VERIFICATION_TOKEN")

# MCP Server URL (your existing Railway deployment)
MCP_SERVER_URL = os.environ.get(
    "MCP_SERVER_URL", "https://inflection-journey-stats-bot-python-production.up.railway.app")

# OpenAI configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Validate required environment variables
required_vars = ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET", "OPENAI_API_KEY"]
missing_vars = [var for var in required_vars if not os.environ.get(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {missing_vars}")
    sys.exit(1)

# Initialize Fast-Agent integration
try:
    fastagent_integration = FastAgentIntegration()
except Exception as e:
    logger.error(f"Failed to initialize Fast-Agent integration: {e}")
    sys.exit(1)

app = FastAPI(
    title="Fast-Agent Slack Bot",
    description="Slack integration for Fast-Agent with Inflection.io MCP tools",
    version="1.0.0"
)


class SlackEvent(BaseModel):
    type: str
    user: Optional[str] = None
    text: Optional[str] = None
    channel: Optional[str] = None
    ts: Optional[str] = None
    thread_ts: Optional[str] = None


class SlackChallenge(BaseModel):
    challenge: str
    type: str = "url_verification"


class FastAgentRequest(BaseModel):
    message: str
    user_id: str
    channel_id: str
    thread_ts: Optional[str] = None


async def send_slack_message(channel: str, text: str, thread_ts: Optional[str] = None):
    """Send a message to Slack."""
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "channel": channel,
        "text": text
    }

    if thread_ts:
        payload["thread_ts"] = thread_ts

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=payload
        )
        return response.json()


async def call_fastagent(message: str) -> str:
    """Call Fast-Agent with the given message."""
    try:
        # Use the Fast-Agent integration
        response = await fastagent_integration.call_fastagent(message)
        return response

    except Exception as e:
        logger.error(f"Error calling Fast-Agent: {e}")
        return f"Sorry, I encountered an error: {str(e)}"


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Fast-Agent Slack Bot",
        "version": "1.0.0",
        "status": "running",
        "description": "Slack integration for Fast-Agent with Inflection.io MCP tools"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "services": {
            "slack": bool(SLACK_BOT_TOKEN),
            "openai": bool(OPENAI_API_KEY),
            "mcp_server": MCP_SERVER_URL,
            "fastagent_integration": True
        }
    }


@app.post("/slack/events")
async def handle_slack_events(request: Request):
    """Handle Slack events."""
    try:
        body = await request.body()
        data = json.loads(body)

        # Handle URL verification challenge
        if data.get("type") == "url_verification":
            return {"challenge": data.get("challenge")}

        # Handle events
        if data.get("type") == "event_callback":
            event = data.get("event", {})

            # Only handle message events
            if event.get("type") != "message":
                return {"status": "ignored"}

            # Ignore bot messages to prevent loops
            if event.get("bot_id"):
                return {"status": "ignored"}

            # Ignore message edits and deletions
            if event.get("subtype") in ["message_changed", "message_deleted"]:
                return {"status": "ignored"}

            # Get message details
            user_id = event.get("user")
            channel_id = event.get("channel")
            text = event.get("text", "").strip()
            thread_ts = event.get("thread_ts")

            # Only respond to messages that mention the bot or are in DMs
            if not text.startswith("<@") and not event.get("channel_type") == "im":
                return {"status": "ignored"}

            # Remove bot mention if present
            if text.startswith("<@"):
                text = text.split(">", 1)[1].strip()

            if not text:
                return {"status": "no_message"}

            # Process the message asynchronously
            asyncio.create_task(process_message(
                user_id, channel_id, text, thread_ts))

            return {"status": "processing"}

        return {"status": "unknown_event_type"}

    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_message(user_id: str, channel_id: str, text: str, thread_ts: Optional[str] = None):
    """Process a message asynchronously."""
    try:
        # Send typing indicator
        await send_typing_indicator(channel_id)

        # Call Fast-Agent
        response = await call_fastagent(text)

        # Send response back to Slack
        await send_slack_message(channel_id, response, thread_ts)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        error_message = "Sorry, I encountered an error while processing your request."
        await send_slack_message(channel_id, error_message, thread_ts)


async def send_typing_indicator(channel: str):
    """Send typing indicator to Slack."""
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "channel": channel,
        "type": "typing"
    }

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json=payload
            )
    except Exception as e:
        logger.error(f"Error sending typing indicator: {e}")


@app.post("/chat")
async def chat_endpoint(request: FastAgentRequest):
    """Direct chat endpoint for testing."""
    try:
        response = await call_fastagent(request.message)
        return {
            "response": response,
            "user_id": request.user_id,
            "channel_id": request.channel_id
        }
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    logger.info(f"Starting Fast-Agent Slack Bot on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
