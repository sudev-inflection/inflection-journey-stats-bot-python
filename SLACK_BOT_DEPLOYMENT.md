# Fast-Agent Slack Bot Deployment Guide

This guide will help you deploy the Fast-Agent Slack Bot on Railway.app to integrate with your existing Inflection.io MCP server.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Slack Workspace │    │ Fast-Agent Slack │    │ Inflection MCP  │
│                 │◄──►│ Bot (Railway)    │◄──►│ Server (Railway) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Prerequisites

1. **Slack App Setup**: You need to create a Slack app and get the required tokens
2. **OpenAI API Key**: For the AI model
3. **Existing MCP Server**: Your Inflection.io MCP server already deployed on Railway
4. **Railway Account**: For hosting the Slack bot

## Step 1: Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Give it a name like "Inflection Fast-Agent Bot"
4. Select your workspace

### Configure Bot Token Scopes

In your Slack app settings, go to "OAuth & Permissions" and add these scopes:

**Bot Token Scopes:**
- `chat:write` - Send messages
- `chat:write.public` - Send messages to public channels
- `app_mentions:read` - Read mentions
- `channels:history` - Read channel messages
- `im:history` - Read direct messages
- `im:read` - Access direct messages
- `im:write` - Send direct messages

### Get Required Tokens

1. **Bot User OAuth Token**: Starts with `xoxb-` (found in OAuth & Permissions)
2. **Signing Secret**: Found in "Basic Information" → "App Credentials"
3. **Verification Token**: Found in "Basic Information" → "App Credentials"

## Step 2: Configure Slack Events

1. Go to "Event Subscriptions" in your Slack app
2. Enable Events
3. Set Request URL to: `https://your-slack-bot-app.railway.app/slack/events`
4. Subscribe to these bot events:
   - `app_mention` - When someone mentions your bot
   - `message.im` - Direct messages to your bot

## Step 3: Deploy to Railway

### Option A: Deploy from GitHub

1. Create a new repository for the Slack bot
2. Copy these files to the repository:
   - `fastagent_slack_server.py`
   - `Procfile.slack` (rename to `Procfile`)
   - `requirements-slack.txt` (rename to `requirements.txt`)
   - `env.slack.example`

3. Connect to Railway:
   - Go to [Railway.app](https://railway.app)
   - Create new project
   - Deploy from GitHub repo

### Option B: Deploy from Local Files

1. Create a new Railway project
2. Upload the files manually

## Step 4: Configure Environment Variables

In your Railway project dashboard, add these environment variables:

```bash
# Required Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_VERIFICATION_TOKEN=your-verification-token-here

# Required OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# MCP Server URL (your existing deployment)
MCP_SERVER_URL=https://inflection-journey-stats-bot-python-production.up.railway.app

# Optional Configuration
HOST=0.0.0.0
PORT=8000
```

## Step 5: Install Bot to Workspace

1. Go to "OAuth & Permissions" in your Slack app
2. Click "Install to Workspace"
3. Authorize the app

## Step 6: Test the Bot

1. In Slack, mention your bot: `@YourBotName list my journeys`
2. The bot should respond with journey information from your Inflection.io account

## Usage Examples

### List Journeys
```
@YourBotName list my marketing journeys
```

### Get Email Reports
```
@YourBotName get email reports for journey ABC123
```

### General Questions
```
@YourBotName what can you help me with?
```

## Troubleshooting

### Bot Not Responding

1. Check Railway logs for errors
2. Verify Slack app configuration
3. Ensure environment variables are set correctly
4. Check that the bot is installed to your workspace

### MCP Server Connection Issues

1. Verify `MCP_SERVER_URL` is correct
2. Check that your MCP server is running
3. Test the MCP endpoint directly: `curl -X POST https://your-mcp-server.railway.app/mcp`

### OpenAI API Issues

1. Verify `OPENAI_API_KEY` is valid
2. Check OpenAI account for rate limits or billing issues

## Security Considerations

1. **Never commit tokens to Git**: Use environment variables
2. **Use HTTPS**: Railway provides this automatically
3. **Validate Slack requests**: The code includes basic validation
4. **Rate limiting**: Consider implementing rate limiting for bot usage

## Monitoring

- **Railway Logs**: Monitor application logs in Railway dashboard
- **Slack App Analytics**: Check usage in Slack app dashboard
- **Health Endpoint**: Use `/health` endpoint to check service status

## Scaling Considerations

- **Railway Auto-scaling**: Railway handles basic scaling
- **Database**: Consider adding a database for conversation history
- **Caching**: Add Redis for caching frequent requests
- **Load Balancing**: Railway handles this automatically

## Cost Optimization

- **Railway**: Pay per usage
- **OpenAI**: Monitor API usage and costs
- **Slack**: Free tier includes most features

## Next Steps

1. **Add Conversation History**: Store chat history in a database
2. **Implement Rate Limiting**: Prevent abuse
3. **Add User Authentication**: Restrict access to specific users
4. **Enhanced Error Handling**: Better error messages and recovery
5. **Analytics Dashboard**: Track usage and performance 