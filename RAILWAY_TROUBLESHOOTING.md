# Railway Deployment Troubleshooting Guide

This guide helps resolve common deployment issues on Railway.app, including the externally managed environment error.

## Common Issues and Solutions

### 1. Externally Managed Environment Error

**Error:**
```
error: externally-managed-environment
× This environment is externally managed
╰─> This command has been disabled as it tries to modify the immutable
    `/nix/store` filesystem.
```

**Solution 1: Use Virtual Environment (Recommended)**
The updated `nixpacks.toml` now creates a virtual environment:

```toml
[phases.setup]
nixPkgs = ["python311", "python311Packages.pip", "python311Packages.virtualenv"]

[phases.install]
cmds = [
  "python -m venv venv",
  "source venv/bin/activate && pip install -r requirements.txt"
]

[start]
cmd = "source venv/bin/activate && python web_server.py"
```

**Solution 2: Use Docker (Alternative)**
If the virtual environment approach doesn't work, use Docker:

1. Rename `railway-docker.toml` to `railway.toml`
2. Railway will use the `Dockerfile` for building

### 2. Build Failures

**Check these common issues:**

1. **Python Version Compatibility**
   - Ensure `PYTHON_VERSION = "3.11"` in railway.toml
   - Check that all dependencies support Python 3.11

2. **Missing Dependencies**
   - Verify all required packages are in `requirements.txt`
   - Check for version conflicts

3. **Environment Variables**
   - Ensure `INFLECTION_EMAIL` and `INFLECTION_PASSWORD` are set
   - Check Railway dashboard Variables tab

### 3. Runtime Errors

**Common runtime issues:**

1. **Port Configuration**
   - Railway sets `PORT` environment variable
   - Ensure your app uses `os.environ.get("PORT", 8000)`

2. **Health Check Failures**
   - Verify `/health` endpoint returns 200
   - Check server startup logs

3. **Authentication Errors**
   - Verify Inflection.io credentials
   - Check API endpoint accessibility

## Deployment Methods

### Method 1: Nixpacks with Virtual Environment (Default)

**Files needed:**
- `railway.toml` (uses nixpacks)
- `nixpacks.toml` (virtual environment setup)
- `requirements.txt`
- `web_server.py`

**Steps:**
1. Push code to GitHub
2. Connect repository to Railway
3. Set environment variables
4. Deploy

### Method 2: Docker (Alternative)

**Files needed:**
- `railway.toml` (uses dockerfile)
- `Dockerfile`
- `requirements.txt`
- `web_server.py`

**Steps:**
1. Rename `railway-docker.toml` to `railway.toml`
2. Push code to GitHub
3. Connect repository to Railway
4. Set environment variables
5. Deploy

## Environment Variables

**Required:**
```bash
INFLECTION_EMAIL=your_email@inflection.io
INFLECTION_PASSWORD=your_password
```

**Optional:**
```bash
INFLECTION_API_BASE_URL_AUTH=https://auth.inflection.io/api/v1
INFLECTION_API_BASE_URL_CAMPAIGN=https://campaign.inflection.io/api/v2
INFLECTION_API_BASE_URL_CAMPAIGN_V3=https://campaign.inflection.io/api/v3
LOG_LEVEL=INFO
API_TIMEOUT=10000
MAX_REQUESTS_PER_MINUTE=10
```

## Testing Before Deployment

### Local Testing

```bash
# Test virtual environment setup
python -m venv test_venv
source test_venv/bin/activate
pip install -r requirements.txt
python web_server.py

# Test Docker build
docker build -t inflection-mcp .
docker run -p 8000:8000 -e INFLECTION_EMAIL=test -e INFLECTION_PASSWORD=test inflection-mcp
```

### Deployment Testing

```bash
# Test health endpoint
curl https://your-app.railway.app/health

# Test SSE endpoint
curl -N https://your-app.railway.app/sse/events

# Test MCP endpoint
curl -X POST https://your-app.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": "1", "method": "tools/list", "params": {}}'
```

## Debugging Steps

### 1. Check Railway Logs

1. Go to Railway dashboard
2. Select your project
3. Click on the service
4. Go to "Logs" tab
5. Look for error messages

### 2. Check Build Logs

1. In Railway dashboard, go to "Deployments"
2. Click on the latest deployment
3. Check build logs for errors

### 3. Test Locally

```bash
# Test the exact deployment setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PORT=8000 python web_server.py
```

### 4. Verify Environment Variables

```bash
# Check if variables are set
echo $INFLECTION_EMAIL
echo $INFLECTION_PASSWORD
```

## Common Error Messages

### "Module not found"
- Check `requirements.txt` includes all dependencies
- Verify Python version compatibility

### "Permission denied"
- Docker builds run as non-root user
- Check file permissions in Dockerfile

### "Connection refused"
- Check if server is binding to `0.0.0.0`
- Verify port configuration

### "Authentication failed"
- Check Inflection.io credentials
- Verify API endpoints are accessible

## Performance Optimization

### 1. Build Optimization

- Use `.dockerignore` to exclude unnecessary files
- Order Dockerfile commands for better caching
- Use multi-stage builds if needed

### 2. Runtime Optimization

- Use connection pooling for HTTP clients
- Implement proper error handling
- Add request timeouts

### 3. Monitoring

- Use Railway's built-in monitoring
- Check health endpoint regularly
- Monitor SSE connection status

## Support

### Railway Support
- Check [Railway Documentation](https://docs.railway.app/)
- Join Railway Discord community
- Contact Railway support

### Python/Nix Issues
- Check [Nixpkgs Python Documentation](https://nixos.org/manual/nixpkgs/stable/#python)
- Use virtual environments or Docker
- Consider alternative deployment platforms

### Application Issues
- Check server logs for specific errors
- Test locally with same environment
- Verify all dependencies are compatible

## Alternative Deployment Platforms

If Railway continues to have issues, consider:

1. **Heroku** - Similar deployment model
2. **DigitalOcean App Platform** - Container-based deployment
3. **Google Cloud Run** - Serverless containers
4. **AWS ECS** - Container orchestration
5. **Vercel** - Serverless functions

## Quick Fix Commands

### Reset Railway Project
```bash
# In Railway dashboard
1. Delete the project
2. Create new project
3. Connect to GitHub repository
4. Set environment variables
5. Deploy
```

### Force Rebuild
```bash
# In Railway dashboard
1. Go to Deployments
2. Click "Redeploy"
3. Select "Clear cache and deploy"
```

### Check Configuration
```bash
# Verify all required files exist
ls -la railway.toml nixpacks.toml requirements.txt web_server.py
```

Your deployment should work with the updated configuration! 🚀 