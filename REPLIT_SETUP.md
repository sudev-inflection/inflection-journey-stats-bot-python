# Inflection.io Combined MCP + Slack Bot Server - Replit Setup Guide

This guide will help you set up and run the combined Inflection.io MCP Server and Slack Bot in Replit.

## Quick Start

### 1. Set Up Environment Variables

The server requires your Inflection.io credentials. Set them in Replit's Secrets:

1. **Go to the Secrets tab** in the left sidebar (🔒 icon)
2. **Add these required secrets:**
   - `INFLECTION_EMAIL`: Your Inflection.io email address
   - `INFLECTION_PASSWORD`: Your Inflection.io password

3. **Optional: Add Slack bot secrets** (for Slack integration):
   - `SLACK_BOT_TOKEN`: Your Slack bot token
   - `SLACK_SIGNING_SECRET`: Your Slack app signing secret
   - `OPENAI_API_KEY`: Your OpenAI API key

### 2. Run the Server

1. **Click the "Run" button** at the top of the Replit interface
2. **Wait for setup** - The script will:
   - Check your environment configuration
   - Install dependencies
   - Start the combined server
3. **Access your server** - The URL will appear in the webview

## What the Server Does

This combined server provides:

- **MCP Server**: Model Context Protocol server for Inflection.io integration
  - Marketing Journey Management: List and search your Inflection.io marketing journeys
  - Email Analytics: Get detailed email performance reports
  - Real-time Updates: Server-Sent Events (SSE) for real-time data
  - Web API: HTTP endpoints for integration with other tools

- **Slack Bot**: AI-powered Slack integration
  - Natural language processing of Slack messages
  - Integration with Inflection.io data through MCP tools
  - Real-time responses in Slack channels and DMs

## Available Endpoints

Once running, you can access these endpoints:

### MCP Server Endpoints (at `/mcp`)
- `GET /mcp/health` - Health check and authentication status
- `GET /mcp/tools` - List available MCP tools
- `POST /mcp/journeys` - List marketing journeys
- `POST /mcp/reports` - Get email reports for a journey
- `POST /mcp/mcp` - Full MCP protocol endpoint
- `GET /mcp/sse/events` - Real-time SSE updates

### Slack Bot Endpoints (at `/slack`)
- `GET /slack/health` - Slack bot health check
- `POST /slack/events` - Slack event handling
- `POST /slack/chat` - Direct chat endpoint for testing

### Combined Server Endpoints
- `GET /health` - Overall server health check
- `GET /` - Server information and available endpoints

## Testing the Server

### Health Check
Visit `/health` to verify the combined server is running.

### MCP Server Testing
Send a POST request to `/mcp/journeys`:
```json
{
  "page_size": 10,
  "page_number": 1,
  "search_keyword": ""
}
```

### Slack Bot Testing
Send a POST request to `/slack/chat`:
```json
{
  "message": "List my marketing journeys",
  "user_id": "test_user",
  "channel_id": "test_channel"
}
```

## Slack Bot Configuration

To enable the Slack bot functionality:

1. **Create a Slack App** at https://api.slack.com/apps
2. **Add bot token scopes**: `chat:write`, `app_mentions:read`, `channels:history`, `im:history`
3. **Set up event subscriptions** for:
   - `app_mention` - When someone mentions your bot
   - `message.im` - Direct messages to your bot
4. **Add the bot to your workspace**
5. **Set the secrets** in Replit:
   - `SLACK_BOT_TOKEN`: Your bot token (starts with `xoxb-`)
   - `SLACK_SIGNING_SECRET`: Your app signing secret
   - `OPENAI_API_KEY`: Your OpenAI API key

## Troubleshooting

### "Missing required environment variables"
- Make sure you've added `INFLECTION_EMAIL` and `INFLECTION_PASSWORD` to Replit Secrets
- Restart the repl after adding secrets

### "Authentication failed"
- Check that your Inflection.io credentials are correct
- Verify your account has access to the Inflection.io platform

### "Slack bot not working"
- Ensure all Slack environment variables are set
- Check that your Slack app is properly configured
- Verify the bot has the required permissions

### "Import errors"
- The setup script will automatically install dependencies
- If issues persist, try running `pip install -r requirements.txt` manually

### "Server won't start"
- Check the console output for error messages
- Make sure port 8000 is available (Replit should handle this automatically)

## Integration with AI Assistants

This server can be used with:
- **Claude Desktop**: Configure as an MCP server
- **Slack**: Direct integration through the Slack bot
- **n8n**: Use the SSE endpoints for workflow automation
- **Custom applications**: Use the HTTP API endpoints

## Next Steps

1. **Test the MCP endpoints** using the examples above
2. **Configure Slack bot** if you want Slack integration
3. **Explore the API** by visiting `/mcp/tools` to see available functionality
4. **Integrate with your workflow** using the HTTP endpoints or SSE
5. **Deploy to production** using Railway or another hosting service

## Support

- Check the main [README.md](README.md) for detailed documentation
- Review [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for production deployment
- See [N8N_INTEGRATION.md](N8N_INTEGRATION.md) for workflow automation examples
- Check [SLACK_BOT_DEPLOYMENT.md](SLACK_BOT_DEPLOYMENT.md) for Slack setup details 