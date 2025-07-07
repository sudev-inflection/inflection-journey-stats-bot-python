# Inflection.io MCP Server

A Model Context Protocol (MCP) server for Inflection.io marketing automation platform. This server provides AI assistants with access to email marketing analytics and journey data through a standardized interface.

## Features

- 🔐 **Authentication**: Secure login with Inflection.io credentials
- 📊 **Journey Management**: List and filter marketing journeys
- 📈 **Email Analytics**: Get detailed email performance reports
- 🚀 **Async Operations**: Built with async/await for optimal performance
- 🛡️ **Type Safety**: Full type hints and Pydantic validation
- 📝 **Structured Logging**: Comprehensive logging with structlog

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .
```

### 2. Configure Environment

Copy the example environment file and add your credentials:

```bash
cp env.example .env
```

Edit `.env` with your Inflection.io credentials:

```env
INFLECTION_EMAIL=your-email@example.com
INFLECTION_PASSWORD=your-password
INFLECTION_API_URL=https://api.inflection.io
```

### 3. Test API Connection

Before running the MCP server, test your API connection:

```bash
python test_api.py
```

This will:
- Test authentication with your credentials
- Fetch sample journey data
- Get email reports for a test journey
- Save response examples to `examples/` directory

### 4. Run MCP Server

```bash
python -m src.server
```

## MCP Tools

### 1. `inflection_login`

Authenticate with Inflection.io using email and password.

**Input:**
- `email` (string): User's email address
- `password` (string): User's password

**Example:**
```json
{
  "email": "user@example.com",
  "password": "secure-password"
}
```

### 2. `list_journeys`

List available marketing journeys with optional filtering.

**Input:**
- `status_filter` (optional string): Filter by status ('active', 'draft', 'paused')
- `limit` (optional integer): Limit number of results (max 100)

**Example:**
```json
{
  "status_filter": "active",
  "limit": 10
}
```

### 3. `get_email_reports`

Get email performance reports for a specific journey.

**Input:**
- `journey_id` (string): Journey ID to get reports for
- `start_date` (optional string): Start date filter (YYYY-MM-DD)
- `end_date` (optional string): End date filter (YYYY-MM-DD)
- `limit` (optional integer): Limit number of reports (max 50)

**Example:**
```json
{
  "journey_id": "journey_123",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "limit": 20
}
```

## Project Structure

```
src/
├── __init__.py
├── server.py              # Main MCP server entry point
├── auth/
│   ├── __init__.py
│   └── inflection.py      # Authentication handling
├── tools/
│   ├── __init__.py
│   ├── login.py           # Login tool implementation
│   ├── journeys.py        # Journey listing tool
│   └── reports.py         # Email reports tool
├── utils/
│   ├── __init__.py
│   ├── api_client.py      # HTTP client utilities
│   └── validation.py      # Input validation helpers
├── models/
│   ├── __init__.py
│   ├── auth.py            # Authentication models
│   ├── journey.py         # Journey data models
│   └── report.py          # Report data models
└── config/
    ├── __init__.py
    └── settings.py        # Configuration and constants
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/

# Run tests
pytest
```

### Testing

```bash
# Run API tests
python test_api.py

# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `INFLECTION_API_URL` | Inflection.io API base URL | `https://api.inflection.io` |
| `INFLECTION_EMAIL` | User email for authentication | Required |
| `INFLECTION_PASSWORD` | User password for authentication | Required |
| `INFLECTION_TEST_JOURNEY_ID` | Test journey ID for API testing | `test-journey-123` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `HTTP_TIMEOUT` | HTTP request timeout (seconds) | `30` |
| `MAX_RETRIES` | Maximum HTTP retries | `3` |

### Logging

The server uses structured logging with JSON output. Log levels:

- `DEBUG`: Detailed debugging information
- `INFO`: General operational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages

## Error Handling

The server includes comprehensive error handling:

- **Authentication Errors**: Clear messages for login failures
- **API Errors**: Proper HTTP error handling with retries
- **Validation Errors**: Input validation with helpful messages
- **Network Errors**: Timeout and connection error handling

## Security Considerations

- JWT tokens are stored in memory only (not persisted)
- Passwords are never logged
- All API requests use HTTPS
- Input validation prevents injection attacks
- Rate limiting prevents abuse

## API Integration

The server integrates with Inflection.io APIs:

1. **Authentication**: `/auth/login` - JWT token-based auth
2. **Journeys**: `/journeys` - List marketing journeys
3. **Reports**: `/journeys/{id}/reports` - Email performance data

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify email and password in `.env`
   - Check API URL is correct
   - Ensure account has API access

2. **API Timeout**
   - Increase `HTTP_TIMEOUT` in settings
   - Check network connectivity
   - Verify API endpoint availability

3. **Invalid Journey ID**
   - Use `list_journeys` to get valid journey IDs
   - Check journey ID format (alphanumeric with hyphens/underscores)

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python -m src.server
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run code quality checks
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review API documentation
3. Open an issue on GitHub
4. Contact the development team 