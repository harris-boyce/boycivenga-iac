# NetBox Example Data Files

This directory contains example YAML configuration files for seeding NetBox with multi-site home lab data.

## Available Example Sites

### site-pennington.yaml
Primary residence configuration:
- **Site Name**: pennington
- **Description**: Primary residence
- **Network**: 192.168.10.0/24
- **VLAN ID**: 10 (Home VLAN)

### site-countfleetcourt.yaml
Secondary site configuration:
- **Site Name**: count-fleet-court
- **Description**: Secondary site
- **Network**: 192.168.20.0/24
- **VLAN ID**: 20 (Secondary VLAN)

## Usage

Use these files with the `seed_netbox.py` script to populate your NetBox instance:

```bash
# Seed a single site
python netbox-client/scripts/seed_netbox.py netbox-client/examples/site-pennington.yaml

# Seed all sites
python netbox-client/scripts/seed_netbox.py netbox-client/examples/*.yaml
```

## File Format

Each YAML file follows this structure:

```yaml
site:
  name: site-name           # Required: Display name of the site
  slug: site-slug           # Required: URL-friendly identifier
  description: Description  # Optional: Site description

prefixes:
  - prefix: 192.168.10.0/24  # Required: IP prefix in CIDR notation
    vlan: 10                  # Optional: VLAN ID to associate with
    description: Description  # Optional: Prefix description
    status: active            # Optional: Status (default: active)

vlans:
  - vlan_id: 10               # Required: VLAN ID (1-4094)
    name: VLAN Name           # Required: Display name
    description: Description  # Optional: VLAN description
    status: active            # Optional: Status (default: active)
```

## Creating Custom Examples

To create your own site configuration:

1. Copy an existing example file:
   ```bash
   cp netbox-client/examples/site-pennington.yaml netbox-client/examples/site-mylab.yaml
   ```

2. Edit the file to match your requirements:
   - Update the site name and slug
   - Change the IP prefixes to match your network
   - Adjust VLAN IDs and names

3. Validate the YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('netbox-client/examples/site-mylab.yaml'))"
   ```

4. Seed NetBox with your custom configuration:
   ```bash
   python netbox-client/scripts/seed_netbox.py netbox-client/examples/site-mylab.yaml
   ```

## Future Extensibility

These example files can be extended to include additional NetBox objects:

- **Devices**: Server hardware, network equipment, PDUs
- **Device Types**: Manufacturer and model information
- **Racks**: Physical rack layouts and elevations
- **IP Addresses**: Specific IP assignments within prefixes
- **Interfaces**: Network interfaces on devices
- **Cables**: Physical connections between devices
- **Circuits**: ISP and WAN connections
- **Virtual Machines**: VM inventory

Example future structure:

```yaml
site:
  name: site-example
  slug: site-example

devices:
  - name: switch01
    device_type: cisco-catalyst-9300
    device_role: access-switch
    site: site-example

racks:
  - name: rack01
    site: site-example
    height: 42

ip_addresses:
  - address: 192.168.10.1/24
    status: active
    description: Gateway
```

## Notes

- The seeding script is **idempotent** - it checks if objects exist before creating them
- Running the script multiple times is safe and won't create duplicates
- All objects created will be associated with the specified site
- For local development, use the default NetBox token: `0123456789abcdef0123456789abcdef01234567`
- For production, always use a dedicated API token with appropriate permissions

## Exporting NetBox Intent Data

After seeding NetBox with these example configurations, you can export the data using the `export_intent.py` script. This creates structured JSON and YAML files containing all sites, prefixes, VLANs, and tags.

### Export Example

```bash
# 1. Seed NetBox with example data
python netbox-client/scripts/seed_netbox.py netbox-client/examples/*.yaml

# 2. Export the data
python netbox-client/scripts/export_intent.py

# 3. View exported files
ls -lh artifacts/intent-export/
```

### Export Output Structure

The export script generates the following files in `artifacts/intent-export/`:

**Sites** (`sites.json`, `sites.yaml`):
```json
[
  {
    "id": 1,
    "name": "site-pennington",
    "slug": "site-pennington",
    "description": "Primary residence",
    "status": {"value": "active", "label": "Active"},
    ...
  },
  {
    "id": 2,
    "name": "site-countfleetcourt",
    "slug": "site-countfleetcourt",
    "description": "Secondary site",
    "status": {"value": "active", "label": "Active"},
    ...
  }
]
```

**VLANs** (`vlans.json`, `vlans.yaml`):
```json
[
  {
    "id": 1,
    "vid": 10,
    "name": "Home VLAN",
    "site": {
      "id": 1,
      "name": "site-pennington",
      "slug": "site-pennington"
    },
    "description": "Main LAN",
    "status": {"value": "active", "label": "Active"},
    ...
  },
  ...
]
```

**Prefixes** (`prefixes.json`, `prefixes.yaml`):
```json
[
  {
    "id": 1,
    "prefix": "192.168.10.0/24",
    "site": {
      "id": 1,
      "name": "site-pennington",
      "slug": "site-pennington"
    },
    "vlan": {
      "id": 1,
      "vid": 10,
      "name": "Home VLAN"
    },
    "description": "LAN",
    "status": {"value": "active", "label": "Active"},
    ...
  },
  ...
]
```

**Tags** (`tags.json`, `tags.yaml`):
```json
[
  {
    "id": 1,
    "name": "home-network",
    "slug": "home-network",
    "color": "2196f3",
    "description": "Resources related to home network infrastructure",
    ...
  },
  ...
]
```

### API Endpoints Used by Export Script

The export script queries the following NetBox API endpoints:
- `GET /api/dcim/sites/` - List all sites
- `GET /api/ipam/prefixes/` - List all IP prefixes
- `GET /api/ipam/vlans/` - List all VLANs
- `GET /api/extras/tags/` - List all tags

See the parent directory README (`netbox-client/README.md`) for detailed usage instructions.

## See Also

- [NetBox API Documentation](https://docs.netbox.dev/en/stable/integrations/rest-api/)
- [NetBox Data Models](https://docs.netbox.dev/en/stable/models/)
- Parent directory README: `netbox-client/README.md`
