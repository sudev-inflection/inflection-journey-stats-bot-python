# Railway Deployment Guide for Inflection.io MCP Server

This guide will help you deploy the Inflection.io MCP Server as a standalone web service on Railway.app.

## Prerequisites

1. A Railway.app account
2. Inflection.io account credentials
3. Git repository with this code

## Quick Deployment

### 1. Connect to Railway

1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### 2. Configure Environment Variables

In your Railway project dashboard, go to the "Variables" tab and add these required environment variables:

```bash
# Required Authentication
INFLECTION_EMAIL=your_email@inflection.io
INFLECTION_PASSWORD=your_password

# Optional Configuration (defaults are recommended)
INFLECTION_API_BASE_URL_AUTH=https://auth.inflection.io/api/v1
INFLECTION_API_BASE_URL_CAMPAIGN=https://campaign.inflection.io/api/v2
INFLECTION_API_BASE_URL_CAMPAIGN_V3=https://campaign.inflection.io/api/v3
LOG_LEVEL=INFO
API_TIMEOUT=10000
MAX_REQUESTS_PER_MINUTE=10
```

### 3. Deploy

Railway will automatically detect the Python project and deploy it using the configuration files:
- `railway.toml` - Railway-specific configuration
- `nixpacks.toml` - Build configuration
- `Procfile` - Process definition
- `requirements.txt` - Python dependencies

## Available Endpoints

Once deployed, your server will be available at `https://your-app-name.railway.app` with these endpoints:

### Health Check
```bash
GET /health
```
Returns server health status and authentication status.

### List Available Tools
```bash
GET /tools
```
Returns list of available MCP tools.

### List Marketing Journeys
```bash
POST /journeys
Content-Type: application/json

{
  "page_size": 30,
  "page_number": 1,
  "search_keyword": ""
}
```

### Get Email Reports
```bash
POST /reports
Content-Type: application/json

{
  "journey_id": "your_journey_id",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

### MCP Protocol Endpoint
```bash
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/list",
  "params": {}
}
```

## Testing the Deployment

### 1. Health Check
```bash
curl https://your-app-name.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000000",
  "authentication": "ok"
}
```

### 2. List Tools
```bash
curl https://your-app-name.railway.app/tools
```

### 3. List Journeys
```bash
curl -X POST https://your-app-name.railway.app/journeys \
  -H "Content-Type: application/json" \
  -d '{"page_size": 10, "page_number": 1}'
```

### 4. Get Email Reports
```bash
curl -X POST https://your-app-name.railway.app/reports \
  -H "Content-Type: application/json" \
  -d '{"journey_id": "your_journey_id"}'
```

## Configuration Files Explained

### railway.toml
- Specifies the build process and deployment settings
- Sets health check endpoint and timeout
- Configures restart policy

### nixpacks.toml
- Defines the build process using Nixpacks
- Installs Python 3.11 and dependencies
- Sets the start command

### Procfile
- Alternative process definition for Railway
- Defines the web process

### web_server.py
- FastAPI-based web server
- Combines MCP functionality with HTTP endpoints
- Includes health check and error handling
- Supports CORS for cross-origin requests

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INFLECTION_EMAIL` | Yes | - | Your Inflection.io email |
| `INFLECTION_PASSWORD` | Yes | - | Your Inflection.io password |
| `INFLECTION_API_BASE_URL_AUTH` | No | `https://auth.inflection.io/api/v1` | Authentication API base URL |
| `INFLECTION_API_BASE_URL_CAMPAIGN` | No | `https://campaign.inflection.io/api/v2` | Campaign API base URL |
| `INFLECTION_API_BASE_URL_CAMPAIGN_V3` | No | `https://campaign.inflection.io/api/v3` | Campaign API v3 base URL |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `API_TIMEOUT` | No | `10000` | API timeout in milliseconds |
| `MAX_REQUESTS_PER_MINUTE` | No | `10` | Rate limiting |

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check that `INFLECTION_EMAIL` and `INFLECTION_PASSWORD` are set correctly
   - Verify your Inflection.io credentials are valid

2. **Build Failed**
   - Check Railway logs for Python version compatibility
   - Ensure all dependencies are in `requirements.txt`

3. **Health Check Failing**
   - Check Railway logs for startup errors
   - Verify environment variables are set

4. **API Timeouts**
   - Increase `API_TIMEOUT` value
   - Check Inflection.io API status

### Viewing Logs

In Railway dashboard:
1. Go to your project
2. Click on the service
3. Go to "Logs" tab
4. Check for error messages

### Restarting the Service

In Railway dashboard:
1. Go to your project
2. Click on the service
3. Click "Redeploy" button

## Security Considerations

1. **Environment Variables**: Never commit credentials to Git
2. **HTTPS**: Railway provides HTTPS by default
3. **CORS**: Configure CORS origins appropriately for production
4. **Rate Limiting**: Consider implementing additional rate limiting
5. **Logging**: Sensitive data is not logged

## Scaling

Railway automatically scales based on traffic. You can also:
1. Set custom scaling rules in Railway dashboard
2. Configure resource limits
3. Set up monitoring and alerts

## Monitoring

Railway provides:
- Built-in monitoring and metrics
- Health check status
- Log aggregation
- Performance metrics

## Support

For issues with:
- **Railway**: Check Railway documentation and support
- **Inflection.io API**: Contact Inflection.io support
- **MCP Server**: Check the main README.md for development setup 