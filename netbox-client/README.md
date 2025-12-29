# netbox-client

Tools and scripts for interacting with the NetBox API and managing network intent data.

## Structure

- `scripts/` – Python scripts and utilities for NetBox operations
- `examples/` – Example configurations and usage patterns
- `docker-compose.yml` – Local NetBox instance for development/testing (⚠️ NOT FOR PRODUCTION)

## Local NetBox Development Environment

### ⚠️ WARNING: FOR LOCAL DEVELOPMENT/TESTING ONLY - DO NOT USE IN PRODUCTION

This directory includes a Docker Compose configuration that provides a minimal NetBox instance for local development and testing. **This setup is NOT suitable for production use.**

For production environments:
- Use a properly configured, hardened NetBox instance managed by your infrastructure team
- Follow [NetBox's official production deployment guide](https://docs.netbox.dev/en/stable/installation/)
- Implement proper security controls, backups, monitoring, and high availability
- Use environment-specific configuration and secrets management

### Quick Start - Local NetBox

#### Prerequisites

- Docker and Docker Compose installed on your system
- Ports 8000 available on localhost

#### Starting NetBox

```bash
# Navigate to the netbox-client directory
cd netbox-client

# Start NetBox and all required services
docker compose up -d

# Wait for services to be ready (first startup takes 1-2 minutes)
docker compose logs -f netbox

# Once you see "NetBox started" or similar, NetBox is ready at:
# http://localhost:8000
```

#### Default Credentials

**Web UI Login:**
- URL: http://localhost:8000
- Username: `admin`
- Password: `admin`

**API Access:**
- URL: http://localhost:8000/api/
- Default Token: `0123456789abcdef0123456789abcdef01234567`

**⚠️ Security Note:** These are default development credentials. Never use these in production!

#### Stopping NetBox

```bash
# Stop services (preserves data)
docker compose stop

# Stop and remove containers (preserves data volumes)
docker compose down
```

#### Resetting NetBox Data

To completely reset your local NetBox instance and start fresh:

```bash
# Stop and remove containers and volumes
docker compose down -v

# Start fresh
docker compose up -d
```

**Note:** This will delete all data including devices, sites, and custom configurations.

#### Seeding NetBox with Example Data

After starting or resetting your local NetBox instance, you can populate it with example data for the multi-site home lab using the seeding script.

**Prerequisites:**
- NetBox instance running (local or remote)
- Python 3.x installed
- Required Python packages: `requests`, `pyyaml`

```bash
# Install required Python packages
pip install requests pyyaml

# Set environment variables
export NETBOX_URL="http://localhost:8000/api/"
export NETBOX_API_TOKEN="0123456789abcdef0123456789abcdef01234567"

# Seed a specific site
python netbox-client/scripts/seed_netbox.py netbox-client/examples/site-pennington.yaml

# Seed all example sites
python netbox-client/scripts/seed_netbox.py netbox-client/examples/*.yaml
```

**Example Sites:**
- `pennington` - Primary residence with 192.168.10.0/24 network
- `count-fleet-court` - Secondary site with 192.168.20.0/24 network

**What gets created:**
- Sites with descriptions
- VLANs for each site
- IP prefixes associated with VLANs

**Resetting and Reseeding:**

To completely reset and reseed your local NetBox:

```bash
# Navigate to netbox-client directory
cd netbox-client

# Reset NetBox (removes all data)
docker compose down -v
docker compose up -d

# Wait for NetBox to be ready (1-2 minutes)
docker compose logs -f netbox

# Once ready, seed with example data
cd ..
export NETBOX_URL="http://localhost:8000/api/"
export NETBOX_API_TOKEN="0123456789abcdef0123456789abcdef01234567"
python netbox-client/scripts/seed_netbox.py netbox-client/examples/*.yaml
```

**Note:** The seeding script is idempotent - it checks if resources already exist before creating them, so it's safe to run multiple times.

#### Exporting NetBox Intent Data

The `export_intent.py` script allows you to export NetBox "intent" data (sites, prefixes, VLANs, tags) to JSON and YAML files. This is useful for backup, documentation, or migration purposes.

**Prerequisites:**
- NetBox instance running (local or remote)
- Python 3.x installed
- Required Python packages: `requests`, `pyyaml`

```bash
# Set environment variables
export NETBOX_URL="http://localhost:8000/api/"
export NETBOX_API_TOKEN="0123456789abcdef0123456789abcdef01234567"

# Export all intent data to default location (artifacts/intent-export/)
python netbox-client/scripts/export_intent.py

# Export to a custom directory
python netbox-client/scripts/export_intent.py --output-dir /tmp/netbox-export

# Export only specific resource types
python netbox-client/scripts/export_intent.py --sites --vlans
```

**What gets exported:**
- **Sites**: Physical locations and data centers
- **Prefixes**: IP address ranges and subnets
- **VLANs**: Virtual LAN configurations
- **Tags**: Metadata tags for organizing resources

**Output files** (generated in both JSON and YAML formats):
- `sites.json` / `sites.yaml` - Site configurations
- `prefixes.json` / `prefixes.yaml` - IP prefix allocations
- `vlans.json` / `vlans.yaml` - VLAN configurations
- `tags.json` / `tags.yaml` - Tag definitions

**API Endpoints Used:**
- `GET /api/dcim/sites/` - List all sites
- `GET /api/ipam/prefixes/` - List all IP prefixes
- `GET /api/ipam/vlans/` - List all VLANs
- `GET /api/extras/tags/` - List all tags

**Example workflow:**

```bash
# 1. Seed NetBox with example data
python netbox-client/scripts/seed_netbox.py netbox-client/examples/*.yaml

# 2. Export the data for backup or documentation
python netbox-client/scripts/export_intent.py

# 3. Review exported files
ls -lh artifacts/intent-export/

# 4. Render Terraform tfvars files from the export
python netbox-client/scripts/render_tfvars.py --input-dir artifacts/intent-export
```

#### Rendering Terraform tfvars Files

The `render_tfvars.py` script converts NetBox intent-export data into Terraform variable (tfvars) files, one per site. This enables infrastructure-as-code workflows with NetBox as the source of truth.

**Prerequisites:**
- NetBox export data (from `export_intent.py` or example files)
- Python 3.x installed

```bash
# Generate tfvars from NetBox export directory
python netbox-client/scripts/render_tfvars.py --input-dir artifacts/intent-export

# Generate from a single consolidated intent file
python netbox-client/scripts/render_tfvars.py \
  --input-file netbox-client/examples/intent-minimal-schema.json

# Specify custom output directory
python netbox-client/scripts/render_tfvars.py \
  --input-dir artifacts/intent-export \
  --output-dir /tmp/my-tfvars
```

**What gets generated:**
- One tfvars JSON file per site (e.g., `site-pennington.tfvars.json`)
- Deterministic output (same input always produces same output)
- Site-specific prefixes and VLANs
- Shared tags across all sites

**Output location:**
- Default: `artifacts/tfvars/`
- Files: `site-{slug}.tfvars.json`

**Features:**
- **Deterministic**: Sorted keys ensure consistent output for version control
- **Site-grouped**: Each site gets its own tfvars file with associated resources
- **Terraform-ready**: Output can be used directly with `terraform apply`

**Field mapping documentation:**
- See [docs/netbox-tfvars-mapping.md](../docs/netbox-tfvars-mapping.md) for complete field mapping details

**Complete workflow example:**

```bash
# 1. Export from NetBox
python netbox-client/scripts/export_intent.py

# 2. Render tfvars files
python netbox-client/scripts/render_tfvars.py --input-dir artifacts/intent-export

# 3. Use with Terraform
terraform plan -var-file=artifacts/tfvars/site-pennington.tfvars.json
terraform apply -var-file=artifacts/tfvars/site-pennington.tfvars.json
```

**Testing:**
Run the test suite to verify the conversion logic:
```bash
python netbox-client/scripts/test_render_tfvars.py
```

#### Checking Status

```bash
# View logs for all services
docker compose logs -f

# View logs for specific service
docker compose logs -f netbox

# Check service health
docker compose ps
```

#### Accessing the NetBox Shell

```bash
# Access NetBox management shell
docker compose exec netbox python /opt/netbox/netbox/manage.py shell

# Run management commands
docker compose exec netbox python /opt/netbox/netbox/manage.py <command>
```

### Using Local NetBox with Scripts

When running scripts against your local NetBox instance:

```bash
# Set environment variables
export NETBOX_URL="http://localhost:8000/api/"
export NETBOX_API_TOKEN="0123456789abcdef0123456789abcdef01234567"

# Or create a .env file (recommended)
cat > .env << EOF
NETBOX_URL=http://localhost:8000/api/
NETBOX_API_TOKEN=0123456789abcdef0123456789abcdef01234567
EOF

# Run your scripts
python scripts/example_usage.py
```

## Configuration

### NetBox API Access

Scripts in this directory connect to NetBox using environment-based configuration. This allows seamless switching between local development and remote/production NetBox instances.

**Important:** The local Docker Compose setup is ONLY for development and testing. For CI/CD pipelines and production workflows, always use a properly managed NetBox instance.

#### Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NETBOX_API_TOKEN` | NetBox API authentication token (required) | None |
| `NETBOX_URL` | NetBox API endpoint URL | `http://localhost:8000/api/` |

#### Local Development Setup

**Using Local Docker Compose NetBox (for development/testing only):**

1. **Start Local NetBox:**
   ```bash
   cd netbox-client
   docker compose up -d
   ```

2. **Configure Environment Variables:**
   ```bash
   # Use the default development token
   export NETBOX_URL="http://localhost:8000/api/"
   export NETBOX_API_TOKEN="0123456789abcdef0123456789abcdef01234567"
   ```

3. **Verify Configuration:**
   ```bash
   # Test API connectivity
   curl -H "Authorization: Token 0123456789abcdef0123456789abcdef01234567" \
        http://localhost:8000/api/
   ```

**Using Remote/Production NetBox:**

1. **Generate a NetBox API Token:**
   - Access your NetBox instance (production/staging)
   - Navigate to: Admin → Users → API Tokens
   - Create a new token with appropriate permissions
   - Copy the token value

2. **Configure Environment Variables:**

   **Option A: Using .env file (recommended)**
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env and set your token
   # NETBOX_URL=https://netbox.example.com/api/
   # NETBOX_API_TOKEN=your-actual-token-here
   ```

   **Option B: Export in your shell**
   ```bash
   # For production NetBox instance
   export NETBOX_API_TOKEN="your-production-token-here"
   export NETBOX_URL="https://netbox.example.com/api/"
   ```

3. **Verify Configuration:**
   ```python
   from netbox_client.scripts.nb_config import NETBOX_URL, TOKEN
   print(f"Connecting to: {NETBOX_URL}")
   # TOKEN is available for authentication
   ```

#### GitHub Actions / CI Setup

**⚠️ IMPORTANT:** Always use a dedicated, properly managed NetBox instance for CI/CD pipelines. Never use the local Docker Compose NetBox for automated workflows or production.

For CI/CD pipelines, configure NetBox credentials as repository secrets:

1. **Add Repository Secrets:**
   - Go to: Repository Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `NETBOX_API_TOKEN`: Your production/staging NetBox API token
     - `NETBOX_URL`: Your NetBox API endpoint (e.g., `https://netbox.example.com/api/`)

2. **Use in Workflows:**
   ```yaml
   - name: Run NetBox Script
     env:
       NETBOX_API_TOKEN: ${{ secrets.NETBOX_API_TOKEN }}
       NETBOX_URL: ${{ secrets.NETBOX_URL }}
     run: |
       python netbox-client/scripts/your_script.py
   ```

**Why not use local NetBox in CI?**
- CI/CD should use the authoritative source of truth (production NetBox)
- Local Docker NetBox has no real data and default credentials
- Production workflows should integrate with production systems
- Spinning up NetBox in CI is slow and unnecessary

#### Security Best Practices

- ✅ **DO:** Store tokens in environment variables or secure secret managers
- ✅ **DO:** Use `.env` files for local development (already in `.gitignore`)
- ✅ **DO:** Use repository secrets for GitHub Actions
- ❌ **DON'T:** Commit tokens or `.env` files to version control
- ❌ **DON'T:** Share tokens in plain text (Slack, email, etc.)
- ❌ **DON'T:** Use production tokens for local development

#### Switching Between Environments

**Local Development (Docker Compose):**
```bash
export NETBOX_URL="http://localhost:8000/api/"
export NETBOX_API_TOKEN="0123456789abcdef0123456789abcdef01234567"
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

**Tips:**
- Use `.env` files for each environment (`.env.local`, `.env.staging`, `.env.prod`)
- Load the appropriate file before running scripts: `source .env.staging`
- Never commit `.env` files with real credentials to version control

## Example Data Files

The `examples/` directory contains YAML files with example NetBox configurations for multi-site home lab setups. These files can be used with the `seed_netbox.py` script to populate a NetBox instance.

### Available Examples

#### `examples/site-pennington.yaml`
Primary residence configuration:
- Site: site-pennington
- Network: 192.168.10.0/24
- VLAN: 10 (Home VLAN)

#### `examples/site-countfleetcourt.yaml`
Secondary site configuration:
- Site: site-countfleetcourt
- Network: 192.168.20.0/24
- VLAN: 20 (Secondary VLAN)

### YAML File Format

Each example file follows this structure:

```yaml
site:
  name: site-name
  slug: site-slug
  description: Site description

prefixes:
  - prefix: 192.168.10.0/24
    vlan: 10
    description: Network description
    status: active

vlans:
  - vlan_id: 10
    name: VLAN name
    description: VLAN description
    status: active
```

### Creating Custom Examples

You can create your own YAML files following the same format:

1. Copy an existing example file
2. Modify the site name, networks, and VLANs
3. Save with a descriptive filename (e.g., `site-mylocation.yaml`)
4. Run the seeding script with your new file

### Extensibility

These examples can be extended to include additional NetBox objects in the future:
- Devices and device types
- Rack layouts
- IP addresses
- Interfaces and connections
- Circuits and providers

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

### Local Docker Compose Issues

#### Services won't start or fail health checks

**Cause:** Ports may be in use, or containers may be in a bad state.

**Solution:**
```bash
# Check what's using port 8000
lsof -i :8000

# Stop and remove everything, then restart
docker compose down
docker compose up -d

# Check service logs
docker compose logs
```

#### "Cannot connect to Docker daemon"

**Cause:** Docker is not running.

**Solution:**
- Ensure Docker Desktop or Docker daemon is running
- Check Docker status: `docker ps`

#### NetBox takes too long to start

**Cause:** First startup requires database initialization and migrations.

**Solution:**
- Wait 1-2 minutes for initial setup
- Monitor progress: `docker compose logs -f netbox`
- Look for "NetBox started" or similar success message

#### Need to completely reset

**Solution:**
```bash
# Nuclear option - removes all data
docker compose down -v
docker volume prune -f
docker compose up -d
```

### "NetBox API token required" Error

**Cause:** The `NETBOX_API_TOKEN` environment variable is not set.

**Solution:**
```bash
# For local development
export NETBOX_API_TOKEN="0123456789abcdef0123456789abcdef01234567"

# For remote NetBox, set your actual token
export NETBOX_API_TOKEN="your-token-here"

# Or create a .env file
cp .env.example .env
# Edit .env and add your token
```

### Connection Refused / Network Errors

**Cause:** NetBox instance is not accessible at the configured URL.

**Solutions:**
- **Local NetBox:** Verify containers are running: `docker compose ps`
- **Local NetBox:** Check NetBox is healthy: `curl http://localhost:8000/api/`
- **Remote NetBox:** Verify URL is correct (including `/api/` suffix)
- **Remote NetBox:** Check firewall/network settings and VPN if required

### Authentication Errors (401/403)

**Cause:** Invalid or expired token, or insufficient permissions.

**Solutions:**
- Verify token is correct and not expired
- Check token permissions in NetBox UI (Admin → API Tokens)
- For local NetBox, use default token: `0123456789abcdef0123456789abcdef01234567`
- Generate a new token if needed

## Additional Resources

- [NetBox API Documentation](https://docs.netbox.dev/en/stable/integrations/rest-api/)
- [NetBox Docker Repository](https://github.com/netbox-community/netbox-docker)
- [pynetbox Library](https://github.com/netbox-community/pynetbox) - Python client for NetBox
- See `docs/netbox-schema.md` for schema documentation and data models

## Extending the Local NetBox Setup

The Docker Compose configuration can be extended for additional testing scenarios:

### Adding NetBox Plugins

Edit `docker-compose.yml` to install plugins:

```yaml
netbox:
  environment:
    # Add plugin configuration
    PLUGINS: '["netbox_bgp", "netbox_topology_views"]'
  volumes:
    # Mount plugin configuration
    - ./plugins:/etc/netbox/config/plugins
```

### Pre-loading Test Data

```bash
# Create a script to populate test data
docker compose exec netbox python /opt/netbox/netbox/manage.py shell << EOF
from dcim.models import Site, Device, DeviceType, Manufacturer

# Create test data
manufacturer = Manufacturer.objects.create(name="Cisco", slug="cisco")
device_type = DeviceType.objects.create(
    manufacturer=manufacturer,
    model="Catalyst 9300",
    slug="catalyst-9300"
)
site = Site.objects.create(name="Lab", slug="lab")
EOF
```

### Custom Configuration

Mount a custom NetBox configuration file:

```yaml
netbox:
  volumes:
    - ./custom_configuration.py:/etc/netbox/config/configuration.py:ro
```

### Backup and Restore

```bash
# Backup database
docker compose exec postgres pg_dump -U netbox netbox > netbox_backup.sql

# Restore database
cat netbox_backup.sql | docker compose exec -T postgres psql -U netbox netbox
```

**Remember:** These extensions are for local development/testing only. Production NetBox should be managed by infrastructure teams with proper deployment practices.
