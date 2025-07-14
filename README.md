# Inflection.io MCP Server (Simplified)

A simplified Model Context Protocol (MCP) server for Inflection.io marketing automation platform, built following a working pattern for Claude Desktop integration.

## Features

- **Authentication**: Manual login using MCP tools with email and password
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

### 2. Configure Environment Variables (Optional)

Copy the example environment file and update with your credentials for automatic authentication:

```bash
cp env.example .env
```

Edit `.env` and add your Inflection.io credentials:

```bash
INFLECTION_EMAIL=your_email@inflection.io
INFLECTION_PASSWORD=your_password
```

**Note**: Environment variables are optional. You can also authenticate manually using the `inflection_login` MCP tool.

### 3. Test the Server

Run the test script to verify everything works:

```bash
python test_mcp_tools.py
```

### 4. Start the MCP Server

```bash
python src/server_new.py
```

## Railway Deployment

This server can be deployed as a standalone web service on Railway.app. See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed deployment instructions.

### Quick Railway Deployment

1. **Connect to Railway**: Go to [Railway.app](https://railway.app) and create a new project from your GitHub repository

2. **Set Environment Variables** (Optional): Add these variables in Railway dashboard for automatic authentication:
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
- `POST /mcp` - Full MCP protocol endpoint
- `GET /sse` - SSE information
- `GET /sse/events` - Real-time SSE updates
- `POST /sse/trigger` - Trigger SSE events

**Note**: Direct API endpoints (`/journeys` and `/reports`) have been removed. All data access must go through MCP tools.

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

- `status_update` - Server status updates (every 5 minutes)
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

### 1. `inflection_login`

Authenticate with Inflection.io using email and password.

**Parameters:**
- `email` (required): Your Inflection.io account email
- `password` (required): Your Inflection.io account password

**Example:**
```json
{
  "email": "your_email@inflection.io",
  "password": "your_password"
}
```

**Note**: You must use this tool first before accessing any other tools.

### 2. `list_journeys`

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

### 3. `get_email_reports`

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

## Authentication Flow

The server supports two authentication methods:

### Method 1: Manual Authentication (Recommended)
1. Use the `inflection_login` MCP tool with your email and password
2. The server will store your authentication token
3. Use other tools as needed
4. If the token expires, use `inflection_login` again

### Method 2: Environment Variables (Optional)
1. Set `INFLECTION_EMAIL` and `INFLECTION_PASSWORD` environment variables
2. The server will automatically authenticate on startup
3. If authentication fails, you'll need to use the manual method

## API Endpoints

The server integrates with multiple Inflection.io API endpoints:

- **Auth API**: `https://auth.inflection.io/api/v1`
- **Campaign API v2**: `https://campaign.inflection.io/api/v2`
- **Campaign API v3**: `https://campaign.inflection.io/api/v3`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `INFLECTION_EMAIL` | Your Inflection.io email (optional) | None |
| `INFLECTION_PASSWORD` | Your Inflection.io password (optional) | None |
| `INFLECTION_API_BASE_URL_AUTH` | Auth API base URL | `https://auth.inflection.io/api/v1` |
| `INFLECTION_API_BASE_URL_CAMPAIGN` | Campaign API v2 base URL | `https://campaign.inflection.io/api/v2` |
| `INFLECTION_API_BASE_URL_CAMPAIGN_V3` | Campaign API v3 base URL | `https://campaign.inflection.io/api/v3` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Error Handling

The server includes comprehensive error handling:

- **Authentication Errors**: Clear messages when login fails or tokens expire
- **HTTP Errors**: Specific handling for 401, 403, 404, and other status codes
- **Network Errors**: Graceful handling of connection issues
- **Validation Errors**: Input validation with helpful error messages

### Common Error Messages

- `❌ Not authenticated. Please use the 'inflection_login' tool first` - You need to authenticate before using other tools
- `❌ Authentication failed (401 Unauthorized)` - Invalid credentials or expired token
- `❌ Access forbidden (403)` - Your account doesn't have permission
- `❌ Journey not found (404)` - Invalid journey ID or no access to the journey 