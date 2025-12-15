# NetBox Schema and Configuration

This document provides information about NetBox API configuration, data models, and integration patterns for the infrastructure as code repository.

## Table of Contents

- [API Configuration](#api-configuration)
- [Authentication](#authentication)
- [Environment Configuration](#environment-configuration)
- [Data Models](#data-models)
- [Integration Patterns](#integration-patterns)
- [Multi-Environment Support](#multi-environment-support)

## API Configuration

NetBox provides a RESTful API for programmatic access to network infrastructure data. This repository uses environment-based configuration to support multiple environments.

### Base Configuration

The base configuration is provided by `netbox-client/scripts/nb_config.py`:

```python
import os

NETBOX_URL = os.getenv("NETBOX_URL", "http://localhost:8000/api/")
TOKEN = os.getenv("NETBOX_API_TOKEN")

assert TOKEN, "NetBox API token required. Set NETBOX_API_TOKEN."
```

### Configuration Parameters

| Parameter | Environment Variable | Default | Description |
|-----------|---------------------|---------|-------------|
| API URL | `NETBOX_URL` | `http://localhost:8000/api/` | NetBox API endpoint with `/api/` suffix |
| API Token | `NETBOX_API_TOKEN` | None (required) | Authentication token from NetBox |

## Authentication

### Token-Based Authentication

NetBox uses token-based authentication for API access. All API requests must include the token in the `Authorization` header:

```python
headers = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json",
}
```

### Generating API Tokens

1. **Access NetBox UI:**
   - Navigate to your NetBox instance
   - Log in with administrative credentials

2. **Create Token:**
   - Go to: Admin → Users → API Tokens
   - Click "Add" to create a new token
   - Configure token properties:
     - **User**: Select the user account
     - **Expires**: Set expiration date (optional)
     - **Write enabled**: Enable if write access is needed
     - **Description**: Document the token's purpose

3. **Copy Token:**
   - Copy the generated token immediately (it won't be shown again)
   - Store securely in environment variables or secret manager

### Token Permissions

Token permissions are inherited from the associated user account. Ensure the user has appropriate permissions:

- **Read-only access**: For querying device data, IP addresses, etc.
- **Write access**: For creating/updating/deleting resources
- **Admin access**: For managing NetBox configuration

## Environment Configuration

### Local Development

For local development with a NetBox instance running on the same machine:

```bash
# .env file
NETBOX_URL=http://localhost:8000/api/
NETBOX_API_TOKEN=your-local-dev-token
```

```bash
# Shell export
export NETBOX_URL="http://localhost:8000/api/"
export NETBOX_API_TOKEN="your-local-dev-token"
```

### Remote NetBox Instance

For connecting to a remote NetBox instance:

```bash
# .env file
NETBOX_URL=https://netbox.example.com/api/
NETBOX_API_TOKEN=your-remote-token
```

```bash
# Shell export
export NETBOX_URL="https://netbox.example.com/api/"
export NETBOX_API_TOKEN="your-remote-token"
```

### GitHub Actions

Configure NetBox access in GitHub Actions using repository secrets:

```yaml
name: NetBox Integration
on: [push]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Run NetBox Script
        env:
          NETBOX_URL: ${{ secrets.NETBOX_URL }}
          NETBOX_API_TOKEN: ${{ secrets.NETBOX_API_TOKEN }}
        run: |
          python netbox-client/scripts/your_script.py
```

**Repository Secret Configuration:**
1. Navigate to: Repository → Settings → Secrets and variables → Actions
2. Add secrets:
   - `NETBOX_URL`: Your NetBox API endpoint
   - `NETBOX_API_TOKEN`: Your NetBox API token

## Data Models

NetBox organizes data into several core models. Here are the most commonly used:

### DCIM (Data Center Infrastructure Management)

- **Sites**: Physical locations
- **Racks**: Equipment racks within sites
- **Devices**: Network equipment (switches, routers, servers)
- **Device Types**: Templates for devices
- **Interfaces**: Network interfaces on devices
- **Cables**: Physical cable connections

### IPAM (IP Address Management)

- **IP Addresses**: IPv4 and IPv6 addresses
- **Prefixes**: IP address ranges and subnets
- **VLANs**: Virtual LANs
- **VRFs**: Virtual Routing and Forwarding instances
- **Aggregates**: Supernets for IP space planning

### Circuits

- **Providers**: Service providers
- **Circuit Types**: Categories of circuits (Internet, MPLS, etc.)
- **Circuits**: Specific circuit instances

### Organization

- **Tenants**: Multi-tenancy support
- **Tags**: Flexible tagging system
- **Custom Fields**: User-defined metadata

## Integration Patterns

### Basic API Query

```python
from netbox_client.scripts.nb_config import NETBOX_URL, TOKEN
import requests

def query_netbox(endpoint):
    """Query NetBox API endpoint."""
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/json",
    }

    url = f"{NETBOX_URL}{endpoint}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()

# Example: Get all devices
devices = query_netbox("dcim/devices/")
```

### Using pynetbox Library

For more advanced usage, consider the `pynetbox` library:

```python
from netbox_client.scripts.nb_config import NETBOX_URL, TOKEN
import pynetbox

# Initialize API connection
nb = pynetbox.api(NETBOX_URL.rstrip("/api/"), token=TOKEN)

# Query devices
devices = nb.dcim.devices.all()
for device in devices:
    print(f"{device.name}: {device.device_type.model}")

# Filter queries
switches = nb.dcim.devices.filter(device_type="switch")

# Create resources
new_device = nb.dcim.devices.create(
    name="switch-01",
    device_type=1,
    site=1,
    device_role=1,
)
```

### Error Handling

Implement robust error handling for API interactions:

```python
import requests
from netbox_client.scripts.nb_config import NETBOX_URL, TOKEN

def safe_query(endpoint, params=None):
    """Query NetBox API with error handling."""
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        url = f"{NETBOX_URL}{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to NetBox at {NETBOX_URL}")
        raise

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Error: Invalid API token")
        elif e.response.status_code == 403:
            print("Error: Insufficient permissions")
        elif e.response.status_code == 404:
            print(f"Error: Endpoint not found: {endpoint}")
        raise

    except requests.exceptions.RequestException as e:
        print(f"Error: Request failed: {e}")
        raise
```

## Multi-Environment Support

### Environment-Specific Configuration

For managing multiple NetBox environments (dev, staging, production):

```python
# netbox-client/scripts/multi_env_config.py
import os

ENVIRONMENTS = {
    "local": {
        "url": "http://localhost:8000/api/",
        "description": "Local development instance",
    },
    "staging": {
        "url": "https://netbox-staging.example.com/api/",
        "description": "Staging environment",
    },
    "production": {
        "url": "https://netbox.example.com/api/",
        "description": "Production environment",
    },
}

def get_environment_config(env_name=None):
    """Get configuration for specified environment."""
    env_name = env_name or os.getenv("NETBOX_ENV", "local")

    if env_name not in ENVIRONMENTS:
        raise ValueError(f"Unknown environment: {env_name}")

    config = ENVIRONMENTS[env_name].copy()
    config["url"] = os.getenv("NETBOX_URL", config["url"])
    config["token"] = os.getenv("NETBOX_API_TOKEN")

    assert config["token"], f"Token required for {env_name} environment"

    return config
```

Usage:

```bash
# Select environment
export NETBOX_ENV="staging"
export NETBOX_API_TOKEN="staging-token"

# Or override URL directly
export NETBOX_URL="https://custom-netbox.example.com/api/"
export NETBOX_API_TOKEN="custom-token"
```

### Future Extensibility: OIDC Support

For organizations using OpenID Connect (OIDC) for authentication, the configuration can be extended:

```python
# Future: OIDC authentication support
NETBOX_AUTH_METHOD = os.getenv("NETBOX_AUTH_METHOD", "token")  # token or oidc

if NETBOX_AUTH_METHOD == "oidc":
    OIDC_CLIENT_ID = os.getenv("NETBOX_OIDC_CLIENT_ID")
    OIDC_CLIENT_SECRET = os.getenv("NETBOX_OIDC_CLIENT_SECRET")
    OIDC_ISSUER = os.getenv("NETBOX_OIDC_ISSUER")
    # OIDC token acquisition logic here
```

## Best Practices

### Security

1. **Never commit tokens**: Always use environment variables or secret managers
2. **Rotate tokens regularly**: Implement token rotation policies
3. **Use least privilege**: Grant minimal required permissions
4. **Audit access**: Monitor API token usage in NetBox logs

### Performance

1. **Use filtering**: Apply filters to reduce response size
2. **Implement pagination**: Handle large datasets efficiently
3. **Cache responses**: Cache static data to reduce API calls
4. **Batch operations**: Group related operations when possible

### Reliability

1. **Implement retries**: Handle transient failures gracefully
2. **Use timeouts**: Set appropriate request timeouts
3. **Validate responses**: Check response structure before processing
4. **Log operations**: Maintain audit logs for troubleshooting

## Additional Resources

- [NetBox Documentation](https://docs.netbox.dev/)
- [NetBox REST API Guide](https://docs.netbox.dev/en/stable/integrations/rest-api/)
- [pynetbox Documentation](https://pynetbox.readthedocs.io/)
- [NetBox GitHub Repository](https://github.com/netbox-community/netbox)

## Support and Troubleshooting

For issues with NetBox API configuration:

1. Verify NetBox is accessible: `curl -I http://localhost:8000/api/`
2. Check token validity in NetBox UI: Admin → Users → API Tokens
3. Review NetBox logs for authentication errors
4. Consult `netbox-client/README.md` for configuration examples
5. Open an issue in this repository for IaC-specific problems
