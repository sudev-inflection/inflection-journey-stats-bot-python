# Automatic Retry Mechanism with Re-authentication

## Overview

The Inflection.io MCP server now includes an automatic retry mechanism that handles 401 Unauthorized errors by automatically re-authenticating and retrying the request. This ensures a seamless user experience without exposing authentication errors to the client.

## How It Works

### 1. Request Flow
When an MCP tool makes an API call:

1. **Initial Request**: The system makes the API request with current authentication
2. **401 Detection**: If a 401 Unauthorized error is received, the retry mechanism activates
3. **Re-authentication**: The system clears the current auth state and attempts to re-authenticate
4. **Retry**: The original request is retried with the new authentication token
5. **Success/Failure**: If successful, the result is returned; if failed after max retries, a user-friendly error is shown

### 2. Retry Configuration
- **Max Retries**: 2 attempts (3 total requests including the original)
- **Retry Conditions**: Only 401 Unauthorized errors trigger retries
- **Other Errors**: Non-401 errors are not retried and are returned immediately

### 3. Authentication Flow
The re-authentication process:

1. Clears current authentication state (tokens, expiration, etc.)
2. Attempts to login using environment variables (`INFLECTION_EMAIL`, `INFLECTION_PASSWORD`)
3. Updates authentication headers for all API clients
4. Retries the original request

## Implementation Details

### Core Method: `_make_authenticated_request`

```python
async def _make_authenticated_request(self, method: str, url: str, **kwargs) -> httpx.Response:
    """
    Make an authenticated request with automatic retry on 401 errors.
    """
    max_retries = 2
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            # Ensure authentication
            if not await self.ensure_authenticated():
                raise ValueError("Authentication required")
            
            # Make request
            response = await client.request(method, url, **kwargs)
            
            # Handle 401 errors
            if response.status_code == 401 and retry_count < max_retries:
                # Clear auth state and re-authenticate
                # Retry the request
                retry_count += 1
                continue
            
            return response
            
        except httpx.HTTPStatusError as e:
            # Handle 401 errors in exception form
            if e.response.status_code == 401 and retry_count < max_retries:
                # Re-authenticate and retry
                retry_count += 1
                continue
            raise
```

### API Methods Using Retry Mechanism

All API methods that require authentication now use the retry mechanism:

- `get_journeys()` - Lists marketing journeys
- `get_email_reports()` - Gets email performance reports
- All individual endpoint calls within `get_email_reports()`

## Logging

The retry mechanism provides detailed logging:

- **Warning**: When 401 errors are detected and retry is initiated
- **Info**: When re-authentication starts and completes successfully
- **Error**: When re-authentication fails or max retries are exceeded

Example log entries:
```
WARNING: Received 401 Unauthorized, attempting automatic re-authentication (attempt 1/2)
INFO: Initiating automatic re-authentication...
INFO: Automatic re-authentication successful, retrying request
INFO: Request successful after 1 retry attempts
```

## Error Handling

### Client-Facing Errors
The system provides user-friendly error messages instead of exposing technical details:

- **401 Errors**: "Authentication failed. Please try using the 'inflection_login' tool again with your credentials."
- **Re-authentication Failed**: "Unable to automatically re-authenticate. Please use the 'inflection_login' tool again with your credentials."
- **Max Retries**: "Request failed after multiple attempts. Please try again or use the 'inflection_login' tool to refresh your authentication."

### Internal Error Handling
- Authentication failures are logged with full details for debugging
- Network errors and other exceptions are handled appropriately
- Sensitive information (tokens, passwords) is never logged

## Testing

Use the `test_retry_mechanism.py` script to verify the retry mechanism:

```bash
python test_retry_mechanism.py
```

This script tests:
1. Initial authentication
2. Normal API calls
3. Automatic re-authentication after token expiration
4. Email reports with retry mechanism

## Benefits

1. **Seamless User Experience**: Users don't see 401 errors or need to manually re-authenticate
2. **Automatic Recovery**: System automatically handles token expiration
3. **Robust Error Handling**: Graceful degradation with user-friendly messages
4. **Comprehensive Logging**: Full visibility into retry attempts for debugging
5. **Security**: Sensitive authentication details are never exposed to clients

## Configuration

The retry mechanism can be configured by modifying:

- `max_retries` in `_make_authenticated_request()` method
- Environment variables for authentication credentials
- Logging levels for different verbosity

## Troubleshooting

If you encounter issues:

1. **Check Logs**: Look for retry mechanism log entries
2. **Verify Credentials**: Ensure `INFLECTION_EMAIL` and `INFLECTION_PASSWORD` are set
3. **Test Authentication**: Use the test script to verify functionality
4. **Check Network**: Ensure API endpoints are accessible

The retry mechanism is designed to be transparent to users while providing robust error handling and automatic recovery from authentication issues. 