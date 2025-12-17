# NetBox Schema and Configuration

This document provides information about NetBox API configuration, data models, and integration patterns for the infrastructure as code repository.

## Table of Contents

- [Minimal Intent Schema](#minimal-intent-schema)
- [API Configuration](#api-configuration)
- [Authentication](#authentication)
- [Environment Configuration](#environment-configuration)
- [Data Models](#data-models)
- [Integration Patterns](#integration-patterns)
- [Multi-Environment Support](#multi-environment-support)

## Minimal Intent Schema

This section documents the minimal set of NetBox objects required for basic network infrastructure management in a home lab or small deployment environment. This simplified schema focuses on essential networking constructs without the full complexity of enterprise DCIM (Data Center Infrastructure Management) features.

### Overview

The minimal intent schema includes four core object types:

1. **Sites** - Physical locations where network infrastructure is deployed
2. **VLANs** - Virtual LANs for network segmentation
3. **Prefixes** - IP address ranges (subnets) associated with networks
4. **Tags** - Metadata labels for organizing and categorizing resources

This minimal model is sufficient for:
- Home network management across multiple physical locations
- Lab environments with basic network segmentation
- Small deployments requiring IP address management (IPAM)
- Network intent documentation and automation

### Core Objects

#### Sites

Sites represent physical locations where network infrastructure is deployed. Each site serves as a container for other resources like VLANs and IP prefixes.

**Required Attributes:**
- `name` - Human-readable name (e.g., "site-pennington")
- `slug` - URL-friendly identifier (e.g., "site-pennington")

**Optional Attributes:**
- `description` - Detailed description of the site's purpose
- `comments` - Additional notes or documentation
- `facility` - Building or facility identifier
- `asn` - Autonomous System Number for BGP (if applicable)
- `time_zone` - IANA timezone identifier

**Example:**
```yaml
sites:
  - name: site-pennington
    slug: site-pennington
    description: Primary residence
```

**API Endpoint:** `dcim/sites/`

#### VLANs

VLANs (Virtual Local Area Networks) provide network segmentation and are typically associated with a specific site.

**Required Attributes:**
- `vid` - VLAN ID (1-4094)
- `name` - VLAN name (e.g., "Home LAN")

**Optional Attributes:**
- `site` - Associated site ID
- `status` - Operational status (active, reserved, deprecated)
- `description` - Purpose or function of the VLAN
- `tenant` - Multi-tenancy association (if applicable)
- `role` - VLAN role classification

**Example:**
```yaml
vlans:
  - vlan_id: 10
    name: Home LAN
    description: Default VLAN for primary residence
    status: active
    site: site-pennington
```

**API Endpoint:** `ipam/vlans/`

#### Prefixes

Prefixes represent IP address ranges (subnets) and can be associated with sites and VLANs.

**Required Attributes:**
- `prefix` - IP network in CIDR notation (e.g., "192.168.10.0/24")

**Optional Attributes:**
- `site` - Associated site ID
- `vlan` - Associated VLAN ID
- `status` - Operational status (active, reserved, deprecated, container)
- `description` - Purpose or function of the network
- `is_pool` - Whether this prefix is an IP address pool
- `mark_utilized` - Whether to track IP utilization

**Example:**
```yaml
prefixes:
  - prefix: 192.168.10.0/24
    vlan: 10
    description: Home LAN
    status: active
    site: site-pennington
```

**API Endpoint:** `ipam/prefixes/`

#### Tags

Tags provide a flexible way to categorize and organize NetBox resources. Tags can be applied to any object type.

**Required Attributes:**
- `name` - Tag name (e.g., "home-network")
- `slug` - URL-friendly identifier (e.g., "home-network")

**Optional Attributes:**
- `color` - Hexadecimal color code (e.g., "2196f3")
- `description` - Purpose or meaning of the tag

**Example:**
```yaml
tags:
  - name: home-network
    slug: home-network
    description: Resources related to home network infrastructure
    color: 2196f3
```

**API Endpoint:** `extras/tags/`

### Example: Multi-Site Home Lab

This example demonstrates the minimal schema for a two-site home lab environment:

**YAML Format** (`netbox-client/examples/intent-minimal-schema.yaml`):
```yaml
sites:
  - name: site-pennington
    slug: site-pennington
    description: Primary residence
  - name: site-countfleetcourt
    slug: site-countfleetcourt
    description: Secondary lab site

prefixes:
  - site: site-pennington
    prefix: 192.168.10.0/24
    vlan: 10
    description: Home LAN
    status: active
  - site: site-countfleetcourt
    prefix: 192.168.20.0/24
    vlan: 20
    description: Lab network
    status: active

vlans:
  - site: site-pennington
    vlan_id: 10
    name: Home LAN
    description: Default VLAN for primary residence
    status: active
  - site: site-countfleetcourt
    vlan_id: 20
    name: Guest VLAN
    description: Guest network for lab site
    status: active

tags:
  - name: home-network
    slug: home-network
    description: Resources related to home network infrastructure
    color: 2196f3
```

**JSON Format** (`netbox-client/examples/intent-minimal-schema.json`):
```json
{
  "sites": [
    {
      "name": "site-pennington",
      "slug": "site-pennington",
      "description": "Primary residence"
    }
  ],
  "vlans": [
    {
      "vlan_id": 10,
      "name": "Home LAN",
      "description": "Default VLAN",
      "status": "active"
    }
  ],
  "prefixes": [
    {
      "prefix": "192.168.10.0/24",
      "vlan": 10,
      "description": "Home LAN",
      "status": "active"
    }
  ]
}
```

### CRUD Operations

The repository provides example scripts for performing CRUD operations on the minimal intent schema:

#### Basic CRUD Script

`netbox-client/scripts/post_minimal_intent.py` demonstrates basic Create, Read, Update, and Delete operations:

```python
import requests
import os

NETBOX_URL = os.getenv("NETBOX_URL", "http://localhost:8000/api/")
TOKEN = os.getenv("NETBOX_API_TOKEN")
headers = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}

# CREATE: Example site POST
resp = requests.post(
    f"{NETBOX_URL}dcim/sites/",
    json={"name": "site-pennington", "slug": "site-pennington"},
    headers=headers
)
print(resp.json())

# READ: Get all sites
resp = requests.get(f"{NETBOX_URL}dcim/sites/", headers=headers)
sites = resp.json()["results"]

# UPDATE: Modify a site
site_id = sites[0]["id"]
resp = requests.patch(
    f"{NETBOX_URL}dcim/sites/{site_id}/",
    json={"description": "Updated description"},
    headers=headers
)

# DELETE: Remove a site (use with caution!)
resp = requests.delete(f"{NETBOX_URL}dcim/sites/{site_id}/", headers=headers)
```

**Usage:**
```bash
export NETBOX_URL="http://localhost:8000/api/"
export NETBOX_API_TOKEN="0123456789abcdef0123456789abcdef01234567"
python netbox-client/scripts/post_minimal_intent.py
```

#### Production-Ready Seeding Script

For more robust operations including idempotency and error handling, use `netbox-client/scripts/seed_netbox.py`:

```bash
python netbox-client/scripts/seed_netbox.py \
    netbox-client/examples/intent-minimal-schema.yaml
```

### Relationship Model

The minimal intent schema follows these relationships:

```
Sites
  └── VLANs (many-to-one: each VLAN belongs to one site)
  └── Prefixes (many-to-one: each prefix can be associated with one site)

VLANs
  └── Prefixes (one-to-many: each VLAN can have multiple prefixes)

Tags
  └── Can be applied to any object type (many-to-many)
```

### Schema Extensibility

This minimal schema can be extended in the future to include additional NetBox objects:

**DCIM Extensions:**
- Device Types - Templates for network equipment
- Devices - Physical network devices (switches, routers, access points)
- Interfaces - Network interfaces on devices
- Cables - Physical connectivity between interfaces
- Racks - Physical rack layouts
- Power - Power distribution and monitoring

**IPAM Extensions:**
- IP Addresses - Individual IP address assignments
- VRFs - Virtual Routing and Forwarding instances
- Route Targets - BGP route target communities
- RIRs - Regional Internet Registries
- Aggregates - Supernets for IP space planning

**Organization Extensions:**
- Tenants - Multi-tenancy support
- Contact Roles - Organizational contacts
- Custom Fields - User-defined metadata

**Circuits:**
- Providers - ISPs and service providers
- Circuit Types - Categories of circuits
- Circuits - WAN connections and links

### Best Practices

1. **Consistent Naming:** Use descriptive, consistent names for sites and networks
2. **Slug Generation:** Always provide slugs or use consistent generation rules
3. **Status Fields:** Use appropriate status values (active, reserved, deprecated)
4. **Descriptions:** Document the purpose of each resource
5. **Idempotency:** Check for existing resources before creating new ones
6. **Tags:** Use tags to categorize resources for filtering and reporting
7. **Validation:** Validate CIDR notation for prefixes before API calls

### API Response Structure

All NetBox API responses follow a consistent structure:

**List Responses:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    { "id": 1, "name": "site-pennington", ... },
    { "id": 2, "name": "site-countfleetcourt", ... }
  ]
}
```

**Detail Responses:**
```json
{
  "id": 1,
  "name": "site-pennington",
  "slug": "site-pennington",
  "description": "Primary residence",
  "created": "2024-01-15T10:30:00Z",
  "last_updated": "2024-01-15T10:30:00Z",
  "url": "http://localhost:8000/api/dcim/sites/1/"
}
```

### Additional Resources

- Example files: `netbox-client/examples/intent-minimal-schema.yaml`
- Example scripts: `netbox-client/scripts/post_minimal_intent.py`
- Production script: `netbox-client/scripts/seed_netbox.py`
- NetBox API docs: https://docs.netbox.dev/en/stable/integrations/rest-api/

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
