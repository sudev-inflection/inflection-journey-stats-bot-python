# n8n Integration Guide for Inflection.io MCP Server

This guide explains how to integrate the Inflection.io MCP Server with n8n using Server-Sent Events (SSE) for real-time automation workflows.

## What is SSE (Server-Sent Events)?

SSE is a web standard that allows a server to push real-time updates to clients over HTTP. It's perfect for n8n integration because:

- **Real-time updates**: Get instant notifications when journeys or email reports change
- **HTTP-based**: Works through firewalls and proxies
- **Automatic reconnection**: n8n handles connection drops gracefully
- **Simple format**: Easy to parse and process in workflows

## Prerequisites

1. Deployed Inflection.io MCP Server on Railway
2. n8n instance (self-hosted or cloud)
3. Inflection.io account credentials configured

## Available SSE Events

Your MCP server provides these real-time events:

### 1. `journey_update`
Triggered every 5 minutes with journey status updates.

```json
{
  "type": "journey_update",
  "timestamp": "2024-01-01T12:00:00.000000",
  "summary": "Retrieved 10 active journeys..."
}
```

### 2. `health_check`
Triggered every minute with server health status.

```json
{
  "status": "healthy",
  "authentication": "ok",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### 3. `error`
Triggered when errors occur.

```json
{
  "type": "error",
  "message": "Authentication failed",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### 4. `connection`
Triggered when SSE connection is established.

```json
{
  "type": "connection_established",
  "message": "SSE connection established",
  "timestamp": "2024-01-01T12:00:00.000000",
  "connection_id": "uuid-here"
}
```

## n8n Integration Setup

### Method 1: Webhook Node (Recommended)

1. **Add Webhook Node**
   - In your n8n workflow, add a "Webhook" node
   - Set the HTTP method to `GET`
   - Set the URL to: `https://your-app.railway.app/sse/events`

2. **Configure Headers**
   ```
   Accept: text/event-stream
   Cache-Control: no-cache
   ```

3. **Test Connection**
   - Click "Test step" to verify the connection
   - You should see SSE events flowing in

### Method 2: HTTP Request Node

1. **Add HTTP Request Node**
   - Set method to `GET`
   - Set URL to: `https://your-app.railway.app/sse/events`
   - Set response format to `text`

2. **Configure for SSE**
   - Add custom headers for SSE compatibility
   - Handle the streaming response

## Workflow Examples

### Example 1: Journey Status Monitoring

```javascript
// n8n workflow to monitor journey status
{
  "nodes": [
    {
      "type": "webhook",
      "name": "SSE Connection",
      "url": "https://your-app.railway.app/sse/events"
    },
    {
      "type": "if",
      "name": "Check Event Type",
      "conditions": {
        "string": [
          {
            "value1": "={{ $json.event }}",
            "value2": "journey_update"
          }
        ]
      }
    },
    {
      "type": "slack",
      "name": "Send Alert",
      "channel": "#marketing",
      "text": "Journey update received: {{ $json.data.summary }}"
    }
  ]
}
```

### Example 2: Health Monitoring

```javascript
// n8n workflow to monitor server health
{
  "nodes": [
    {
      "type": "webhook",
      "name": "SSE Connection",
      "url": "https://your-app.railway.app/sse/events"
    },
    {
      "type": "if",
      "name": "Check Health Status",
      "conditions": {
        "string": [
          {
            "value1": "={{ $json.event }}",
            "value2": "health_check"
          }
        ]
      }
    },
    {
      "type": "if",
      "name": "Is Unhealthy",
      "conditions": {
        "string": [
          {
            "value1": "={{ $json.data.status }}",
            "value2": "unhealthy"
          }
        ]
      }
    },
    {
      "type": "email",
      "name": "Send Alert",
      "to": "admin@company.com",
      "subject": "MCP Server Health Alert",
      "text": "Server is unhealthy: {{ $json.data }}"
    }
  ]
}
```

### Example 3: Error Handling

```javascript
// n8n workflow to handle errors
{
  "nodes": [
    {
      "type": "webhook",
      "name": "SSE Connection",
      "url": "https://your-app.railway.app/sse/events"
    },
    {
      "type": "if",
      "name": "Check for Errors",
      "conditions": {
        "string": [
          {
            "value1": "={{ $json.event }}",
            "value2": "error"
          }
        ]
      }
    },
    {
      "type": "discord",
      "name": "Send Discord Alert",
      "channel": "alerts",
      "message": "🚨 MCP Server Error: {{ $json.data.message }}"
    }
  ]
}
```

## Advanced n8n Configuration

### Custom Event Filtering

```javascript
// Filter specific events
const eventType = $json.event;
const allowedEvents = ['journey_update', 'error'];

if (allowedEvents.includes(eventType)) {
  // Process the event
  return $json;
} else {
  // Skip this event
  return null;
}
```

### Data Transformation

```javascript
// Transform SSE data for n8n processing
const transformedData = {
  event_type: $json.event,
  timestamp: $json.data.timestamp,
  payload: $json.data,
  processed_at: new Date().toISOString()
};

return transformedData;
```

### Error Handling

```javascript
// Handle SSE connection errors
try {
  const eventData = $json;
  
  if (!eventData || !eventData.event) {
    throw new Error('Invalid SSE event format');
  }
  
  return eventData;
} catch (error) {
  // Log error and continue
  console.error('SSE processing error:', error);
  return null;
}
```

## Testing the Integration

### 1. Test SSE Connection

```bash
# Test SSE endpoint
curl -N https://your-app.railway.app/sse/events
```

### 2. Test Event Triggering

```bash
# Trigger a test event
curl -X POST https://your-app.railway.app/sse/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test_event",
    "data": {
      "message": "Test from n8n",
      "timestamp": "2024-01-01T12:00:00.000000"
    }
  }'
```

### 3. Monitor in n8n

1. Set up the webhook node in n8n
2. Trigger test events using the API
3. Verify events are received in n8n
4. Test your workflow logic

## Troubleshooting

### Common Issues

1. **No Events Received**
   - Check if the server is running
   - Verify the SSE endpoint URL
   - Check n8n webhook configuration

2. **Connection Drops**
   - SSE automatically reconnects
   - Check server logs for errors
   - Verify network connectivity

3. **Event Format Issues**
   - Check the event structure in n8n
   - Verify JSON parsing
   - Test with curl first

### Debugging Steps

1. **Check Server Status**
   ```bash
   curl https://your-app.railway.app/health
   ```

2. **Test SSE Endpoint**
   ```bash
   curl -N https://your-app.railway.app/sse/events
   ```

3. **Check n8n Logs**
   - Look for webhook errors
   - Check event processing logs
   - Verify data transformation

## Best Practices

### 1. Event Filtering
- Only process relevant events in n8n
- Use conditional nodes to filter events
- Avoid processing unnecessary data

### 2. Error Handling
- Always handle connection errors
- Implement retry logic for failed operations
- Log errors for debugging

### 3. Performance
- Keep workflows efficient
- Avoid blocking operations in event handlers
- Use async processing when possible

### 4. Security
- Use HTTPS for all connections
- Validate event data in n8n
- Implement rate limiting if needed

## Monitoring and Alerts

### 1. Health Monitoring
- Monitor SSE connection status
- Alert on connection failures
- Track event processing metrics

### 2. Performance Monitoring
- Monitor event processing time
- Track workflow execution metrics
- Alert on performance issues

### 3. Error Monitoring
- Monitor for SSE errors
- Track workflow failures
- Implement error reporting

## Support

For issues with:
- **n8n**: Check n8n documentation and community
- **SSE**: Verify server configuration and network
- **MCP Server**: Check server logs and health endpoint
- **Integration**: Test individual components first

## Next Steps

1. Deploy your MCP server to Railway
2. Set up n8n webhook nodes
3. Create automation workflows
4. Test with real data
5. Monitor and optimize

Your Inflection.io MCP Server is now ready for n8n integration with real-time SSE events! 🚀 