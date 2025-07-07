# Inflection.io MCP Server (Simplified)

A simplified Model Context Protocol (MCP) server for Inflection.io marketing automation platform, built following a working pattern for Claude Desktop integration.

## Features

- **Authentication**: Automatic login using environment variables
- **Journey Management**: List and search marketing journeys
- **Email Analytics**: Get comprehensive email performance reports
- **Token Management**: Automatic token refresh and expiration handling
- **Structured Logging**: Comprehensive logging with structlog
- **Web Server**: HTTP endpoints for standalone deployment
- **Railway Deployment**: Ready for cloud deployment on Railway.app
- **SSE Support**: Real-time Server-Sent Events for n8n integration
- **n8n Integration**: Ready for workflow automation

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and update with your credentials:

```bash
cp env.example .env
```

Edit `.env` and add your Inflection.io credentials:

```bash
INFLECTION_EMAIL=your_email@inflection.io
INFLECTION_PASSWORD=your_password
```

### 3. Test the Server

Run the test script to verify everything works:

```bash
python test_new_server.py
```

### 4. Start the MCP Server

```bash
python src/server_new.py
```

## Railway Deployment

This server can be deployed as a standalone web service on Railway.app. See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed deployment instructions.

### Quick Railway Deployment

1. **Connect to Railway**: Go to [Railway.app](https://railway.app) and create a new project from your GitHub repository

2. **Set Environment Variables**: Add these required variables in Railway dashboard:
   ```bash
   INFLECTION_EMAIL=your_email@inflection.io
   INFLECTION_PASSWORD=your_password
   ```

3. **Deploy**: Railway will automatically deploy using the configuration files

4. **Test**: Your server will be available at `https://your-app-name.railway.app`

### Web Server Endpoints

When deployed, the server provides these HTTP endpoints:

- `GET /health` - Health check and authentication status
- `GET /tools` - List available MCP tools
- `POST /journeys` - List marketing journeys
- `POST /reports` - Get email reports for a journey
- `POST /mcp` - Full MCP protocol endpoint
- `GET /sse` - SSE information
- `GET /sse/events` - Real-time SSE updates
- `POST /sse/trigger` - Trigger SSE events

### Local Web Server Testing

To test the web server locally before deployment:

```bash
# Start the web server
python web_server.py

# In another terminal, run tests
python test_web_server.py
```

## n8n Integration with SSE

This server supports real-time integration with n8n using Server-Sent Events (SSE). See [N8N_INTEGRATION.md](N8N_INTEGRATION.md) for complete integration guide.

### Quick n8n Setup

1. **Deploy to Railway** using the instructions above
2. **In n8n**, add a Webhook node with URL: `https://your-app.railway.app/sse/events`
3. **Configure** the webhook to handle SSE events
4. **Create workflows** that respond to real-time updates

### Available SSE Events

- `journey_update` - Real-time journey status updates (every 5 minutes)
- `health_check` - Server health status (every minute)
- `error` - Error notifications
- `connection` - Connection establishment

### Testing SSE Locally

```bash
# Test SSE functionality
python test_sse.py

# Test deployment readiness
python deploy_test.py
```

## MCP Tools

### 1. `list_journeys`

List all marketing journeys from your Inflection.io account.

**Parameters:**
- `page_size` (optional): Number of journeys per page (default: 30, max: 100)
- `page_number` (optional): Page number to retrieve (default: 1)
- `search_keyword` (optional): Search keyword to filter journeys by name

**Example:**
```json
{
  "page_size": 10,
  "page_number": 1,
  "search_keyword": "onboarding"
}
```

### 2. `get_email_reports`

Get comprehensive email performance reports for a specific journey.

**Parameters:**
- `journey_id` (required): The ID of the journey to get reports for
- `start_date` (optional): Start date for the report period (YYYY-MM-DD format)
- `end_date` (optional): End date for the report period (YYYY-MM-DD format)

**Example:**
```json
{
  "journey_id": "67b9bd0a699f2660099ae910",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31"
}
```

## Authentication

The server uses environment variables for authentication:

- `INFLECTION_EMAIL`: Your Inflection.io account email
- `INFLECTION_PASSWORD`: Your Inflection.io account password

The server automatically:
- Logs in using these credentials on startup
- Refreshes tokens when they expire
- Handles authentication errors gracefully

## API Endpoints

The server integrates with multiple Inflection.io API endpoints:

- **Auth API**: `https://auth.inflection.io/api/v1`
- **Campaign API v2**: `https://campaign.inflection.io/api/v2`
- **Campaign API v3**: `https://campaign.inflection.io/api/v3`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `INFLECTION_EMAIL` | Your Inflection.io email | Required |
| `INFLECTION_PASSWORD` | Your Inflection.io password | Required |
| `INFLECTION_API_BASE_URL_AUTH` | Auth API base URL | `https://auth.inflection.io/api/v1` |
| `INFLECTION_API_BASE_URL_CAMPAIGN` | Campaign API v2 base URL | `https://campaign.inflection.io/api/v2` |
| `INFLECTION_API_BASE_URL_CAMPAIGN_V3` | Campaign API v3 base URL | `https://campaign.inflection.io/api/v3` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Error Handling

The server includes comprehensive error handling:

- **Authentication Errors**: Clear messages when login fails
- **API Errors**: Graceful handling of API failures
- **Network Errors**: Timeout and connection error handling
- **Validation Errors**: Input validation with helpful messages

## Logging

The server uses structured logging with `structlog`:

- **Log Level**: Configurable via `LOG_LEVEL` environment variable
- **Structured Output**: JSON-formatted logs for easy parsing
- **Context**: Request IDs and operation tracking
- **Security**: No sensitive data logged (passwords, tokens)

## Development

### Running Tests

```bash
python test_new_server.py
```

### Code Structure

```
src/
├── server_new.py          # Main MCP server (simplified)
├── auth/                  # Authentication modules
├── tools/                 # MCP tool implementations
├── models/                # Data models
├── utils/                 # Utility functions
└── config/                # Configuration settings
```

### Adding New Tools

1. Create a new tool function in `server_new.py`
2. Add the tool to the `tools` list
3. Add a handler in `handle_call_tool`
4. Update the API client if needed

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify your email and password in `.env`
   - Check that your Inflection.io account is active

2. **API Errors**
   - Check your internet connection
   - Verify the API endpoints are accessible
   - Check the logs for detailed error messages

3. **Token Expiration**
   - The server should automatically refresh tokens
   - If issues persist, restart the server

### Debug Mode

Set `LOG_LEVEL=DEBUG` in your `.env` file for detailed logging:

```bash
LOG_LEVEL=DEBUG
```

## Security Considerations

- **Environment Variables**: Never commit `.env` files to version control
- **Token Storage**: Tokens are stored in memory only, not persisted
- **Logging**: No sensitive data is logged
- **HTTPS**: All API calls use HTTPS

## License

This project is licensed under the MIT License. 