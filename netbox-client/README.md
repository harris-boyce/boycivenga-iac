# netbox-client

Tools and scripts for interacting with the NetBox API and managing network intent data.

## Structure

- `scripts/` – Python scripts and utilities for NetBox operations
- `examples/` – Example configurations and usage patterns

## Configuration

### NetBox API Access

Scripts in this directory connect to NetBox using environment-based configuration. This allows seamless switching between local development and remote NetBox instances.

#### Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NETBOX_API_TOKEN` | NetBox API authentication token (required) | None |
| `NETBOX_URL` | NetBox API endpoint URL | `http://localhost:8000/api/` |

#### Local Development Setup

1. **Generate a NetBox API Token:**
   - Access your NetBox instance (local or remote)
   - Navigate to: Admin → Users → API Tokens
   - Create a new token with appropriate permissions
   - Copy the token value

2. **Configure Environment Variables:**

   **Option A: Using .env file (recommended)**
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env and set your token
   # NETBOX_API_TOKEN=your-actual-token-here
   ```

   **Option B: Export in your shell**
   ```bash
   # For local NetBox instance
   export NETBOX_API_TOKEN="your-token-here"
   export NETBOX_URL="http://localhost:8000/api/"

   # For remote NetBox instance
   export NETBOX_API_TOKEN="your-token-here"
   export NETBOX_URL="https://netbox.example.com/api/"
   ```

3. **Verify Configuration:**
   ```python
   from netbox_client.scripts.nb_config import NETBOX_URL, TOKEN
   print(f"Connecting to: {NETBOX_URL}")
   # TOKEN is available for authentication
   ```

#### GitHub Actions / CI Setup

For CI/CD pipelines, configure NetBox credentials as repository secrets:

1. **Add Repository Secrets:**
   - Go to: Repository Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `NETBOX_API_TOKEN`: Your NetBox API token
     - `NETBOX_URL`: Your NetBox API endpoint (if not using default)

2. **Use in Workflows:**
   ```yaml
   - name: Run NetBox Script
     env:
       NETBOX_API_TOKEN: ${{ secrets.NETBOX_API_TOKEN }}
       NETBOX_URL: ${{ secrets.NETBOX_URL }}
     run: |
       python netbox-client/scripts/your_script.py
   ```

#### Security Best Practices

- ✅ **DO:** Store tokens in environment variables or secure secret managers
- ✅ **DO:** Use `.env` files for local development (already in `.gitignore`)
- ✅ **DO:** Use repository secrets for GitHub Actions
- ❌ **DON'T:** Commit tokens or `.env` files to version control
- ❌ **DON'T:** Share tokens in plain text (Slack, email, etc.)
- ❌ **DON'T:** Use production tokens for local development

#### Switching Between Environments

**Local Development:**
```bash
export NETBOX_URL="http://localhost:8000/api/"
export NETBOX_API_TOKEN="dev-token-here"
```

**Staging Environment:**
```bash
export NETBOX_URL="https://netbox-staging.example.com/api/"
export NETBOX_API_TOKEN="staging-token-here"
```

**Production Environment:**
```bash
export NETBOX_URL="https://netbox.example.com/api/"
export NETBOX_API_TOKEN="prod-token-here"
```

## Usage Example

```python
#!/usr/bin/env python3
"""Example script demonstrating NetBox API access."""

from netbox_client.scripts.nb_config import NETBOX_URL, TOKEN
import requests

def get_devices():
    """Fetch devices from NetBox."""
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.get(f"{NETBOX_URL}dcim/devices/", headers=headers)
    response.raise_for_status()

    return response.json()

if __name__ == "__main__":
    devices = get_devices()
    print(f"Found {devices['count']} devices")
```

## Troubleshooting

### "NetBox API token required" Error

**Cause:** The `NETBOX_API_TOKEN` environment variable is not set.

**Solution:**
```bash
# Set the token
export NETBOX_API_TOKEN="your-token-here"

# Or create a .env file
cp .env.example .env
# Edit .env and add your token
```

### Connection Refused / Network Errors

**Cause:** NetBox instance is not accessible at the configured URL.

**Solutions:**
- Verify NetBox is running: `curl http://localhost:8000/api/`
- Check firewall/network settings
- Verify the URL is correct (including `/api/` suffix)

### Authentication Errors (401/403)

**Cause:** Invalid or expired token, or insufficient permissions.

**Solutions:**
- Verify token is correct and not expired
- Check token permissions in NetBox UI
- Generate a new token if needed

## Additional Resources

- [NetBox API Documentation](https://docs.netbox.dev/en/stable/integrations/rest-api/)
- [pynetbox Library](https://github.com/netbox-community/pynetbox) - Python client for NetBox
- See `docs/netbox-schema.md` for schema documentation and data models
