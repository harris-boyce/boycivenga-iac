# NetBox to Terraform tfvars Mapping

This document describes how NetBox intent export data is mapped to Terraform variable files (tfvars).

## Overview

The `render_tfvars.py` script converts NetBox intent-export JSON files into Terraform variable (tfvars) files, one per site. The output is deterministic and suitable for version control and automated workflows.

## Conversion Process

```
NetBox Export Data (JSON)
    ↓
render_tfvars.py
    ↓
Site-specific tfvars files
```

### Input Sources

The script accepts NetBox data from two sources:

1. **Directory of separate files** (from `export_intent.py`):
   - `artifacts/intent-export/sites.json`
   - `artifacts/intent-export/prefixes.json`
   - `artifacts/intent-export/vlans.json`
   - `artifacts/intent-export/tags.json`

2. **Single consolidated file** (like `intent-minimal-schema.json`):
   - Contains all sites, prefixes, vlans, and tags in one JSON file

### NetBox API Compatibility

The script handles both **minimal schema format** (simple values) and **NetBox API format** (nested objects):

#### Status Fields
NetBox API returns status as an object:
```json
{
  "status": {
    "label": "Reserved",
    "value": "reserved"
  }
}
```

The script automatically extracts just the `value` field:
```json
{
  "status": "reserved"
}
```

#### VLAN ID Fields
NetBox API may use `vid` instead of `vlan_id`. The script handles both:
```json
// NetBox API format
{"vid": 10, "name": "Home LAN"}

// Minimal schema format
{"vlan_id": 10, "name": "Home LAN"}

// Both convert to:
{"vlan_id": 10, "name": "Home LAN"}
```

#### VLAN Associations in Prefixes
Prefixes may reference VLANs as integers or nested objects:
```json
// Simple integer (minimal schema)
{"prefix": "10.0.0.0/24", "vlan": 10}

// Nested object (NetBox API)
{"prefix": "10.0.0.0/24", "vlan": {"vid": 10, "name": "LAN"}}

// Both extract to:
{"cidr": "10.0.0.0/24", "vlan_id": 10}
```

### Validation and Error Handling

The script enforces Terraform Input Contract requirements:

**Required Fields:**
- VLAN `vlan_id` must not be null or missing
- If a VLAN has null `vlan_id`, the script fails with a clear error message:
  ```
  Error: VLAN 'CFC_Home_General' (site: count-fleet-court) has no VLAN ID assigned.
  Please assign VLAN ID in NetBox before rendering.
  ```

**NetBox Data Requirements:**
Before running the render script, ensure:
- All VLANs have VLAN IDs assigned (not in "planned" status without IDs)
- Site associations are properly configured
- Network prefixes are defined if subnets are needed

### Output Structure

The script generates one tfvars file per site:
- `artifacts/tfvars/site-pennington.tfvars.json`
- `artifacts/tfvars/site-countfleetcourt.tfvars.json`
- etc.

## Field Mapping

### Site Fields

| NetBox Field | Terraform Variable | Description | Required |
|-------------|-------------------|-------------|----------|
| `name` | `site_name` | Human-readable site name | Yes |
| `slug` | `site_slug` | URL-safe site identifier | Yes |
| `description` | `site_description` | Site description text | No |

**Example:**
```json
// NetBox
{
  "name": "site-pennington",
  "slug": "site-pennington",
  "description": "Primary residence"
}

// Terraform tfvars
{
  "site_name": "site-pennington",
  "site_slug": "site-pennington",
  "site_description": "Primary residence"
}
```

### Prefix Fields (IP Prefixes/Subnets)

Prefixes are grouped by site and included in the site's tfvars file.

| NetBox Field | Terraform Variable | Description | Required |
|-------------|-------------------|-------------|----------|
| `prefix` | `prefixes[].cidr` | IP prefix in CIDR notation (e.g., 192.168.10.0/24) | Yes |
| `vlan` | `prefixes[].vlan_id` | Associated VLAN ID (integer or nested object) | No |
| `description` | `prefixes[].description` | Prefix description | No |
| `status` | `prefixes[].status` | Prefix status string (extracts `.value` from objects) | No |

**Example (Minimal Schema):**
```json
// NetBox
{
  "site": "site-pennington",
  "prefix": "192.168.10.0/24",
  "vlan": 10,
  "description": "Home LAN",
  "status": "active"
}

// Terraform tfvars
{
  "prefixes": [
    {
      "cidr": "192.168.10.0/24",
      "vlan_id": 10,
      "description": "Home LAN",
      "status": "active"
    }
  ]
}
```

**Example (NetBox API Format):**
```json
// NetBox API
{
  "site": "count-fleet-court",
  "prefix": "10.2.10.0/24",
  "vlan": {
    "vid": 10,
    "name": "CFC_Home_General"
  },
  "description": "Home/General VLAN subnet",
  "status": {
    "label": "Reserved",
    "value": "reserved"
  }
}

// Terraform tfvars (status.value extracted, vlan.vid extracted)
{
  "prefixes": [
    {
      "cidr": "10.2.10.0/24",
      "vlan_id": 10,
      "description": "Home/General VLAN subnet",
      "status": "reserved"
    }
  ]
}
```

### VLAN Fields

VLANs are grouped by site and included in the site's tfvars file.

| NetBox Field | Terraform Variable | Description | Required |
|-------------|-------------------|-------------|----------|
| `vlan_id` or `vid` | `vlans[].vlan_id` | VLAN ID number (1-4094) | **Yes** (must not be null) |
| `name` | `vlans[].name` | VLAN name | Yes |
| `description` | `vlans[].description` | VLAN description | No |
| `status` | `vlans[].status` | VLAN status string (extracts `.value` from objects) | No |

**Important:** VLANs must have VLAN IDs assigned. If a VLAN has `null` or missing `vlan_id`/`vid`, the script will fail with an error message indicating which VLAN and site need attention.

**Example (Minimal Schema):**
```json
// NetBox
{
  "site": "site-pennington",
  "vlan_id": 10,
  "name": "Home LAN",
  "description": "Default VLAN for primary residence",
  "status": "active"
}

// Terraform tfvars
{
  "vlans": [
    {
      "vlan_id": 10,
      "name": "Home LAN",
      "description": "Default VLAN for primary residence",
      "status": "active"
    }
  ]
}
```

**Example (NetBox API Format):**
```json
// NetBox API
{
  "site": "count-fleet-court",
  "vid": 10,
  "name": "CFC_Home_General",
  "description": "Family devices, phones, tablets, printers",
  "status": {
    "label": "Reserved",
    "value": "reserved"
  }
}

// Terraform tfvars (vid → vlan_id, status.value extracted)
{
  "vlans": [
    {
      "vlan_id": 10,
      "name": "CFC_Home_General",
      "description": "Family devices, phones, tablets, printers",
      "status": "reserved"
    }
  ]
}
```

### Tag Fields

Tags are **not** site-specific and are included in **all** site tfvars files. This allows tags to be referenced consistently across all Terraform deployments.

| NetBox Field | Terraform Variable | Description | Required |
|-------------|-------------------|-------------|----------|
| `name` | `tags[].name` | Tag name | Yes |
| `slug` | `tags[].slug` | URL-safe tag identifier | Yes |
| `description` | `tags[].description` | Tag description | No |
| `color` | `tags[].color` | Tag color (hex format without #) | No |

**Example:**
```json
// NetBox
{
  "name": "home-network",
  "slug": "home-network",
  "description": "Resources related to home network infrastructure",
  "color": "2196f3"
}

// Terraform tfvars (included in all site files)
{
  "tags": [
    {
      "name": "home-network",
      "slug": "home-network",
      "description": "Resources related to home network infrastructure",
      "color": "2196f3"
    }
  ]
}
```

## Complete Example

### Input: NetBox Export

```json
{
  "sites": [
    {
      "name": "site-pennington",
      "slug": "site-pennington",
      "description": "Primary residence"
    }
  ],
  "prefixes": [
    {
      "site": "site-pennington",
      "prefix": "192.168.10.0/24",
      "vlan": 10,
      "description": "Home LAN",
      "status": "active"
    }
  ],
  "vlans": [
    {
      "site": "site-pennington",
      "vlan_id": 10,
      "name": "Home LAN",
      "description": "Default VLAN for primary residence",
      "status": "active"
    }
  ],
  "tags": [
    {
      "name": "home-network",
      "slug": "home-network",
      "description": "Resources related to home network infrastructure",
      "color": "2196f3"
    }
  ]
}
```

### Output: Terraform tfvars (`site-pennington.tfvars.json`)

```json
{
  "prefixes": [
    {
      "cidr": "192.168.10.0/24",
      "description": "Home LAN",
      "status": "active",
      "vlan_id": 10
    }
  ],
  "site_description": "Primary residence",
  "site_name": "site-pennington",
  "site_slug": "site-pennington",
  "tags": [
    {
      "color": "2196f3",
      "description": "Resources related to home network infrastructure",
      "name": "home-network",
      "slug": "home-network"
    }
  ],
  "vlans": [
    {
      "description": "Default VLAN for primary residence",
      "name": "Home LAN",
      "status": "active",
      "vlan_id": 10
    }
  ]
}
```

## Usage

### Generate from NetBox export directory

```bash
# First, export NetBox data
python netbox-client/scripts/export_intent.py

# Then render tfvars
python netbox-client/scripts/render_tfvars.py --input-dir artifacts/intent-export
```

### Generate from consolidated intent file

```bash
python netbox-client/scripts/render_tfvars.py --input-file netbox-client/examples/intent-minimal-schema.json
```

### Custom output directory

```bash
python netbox-client/scripts/render_tfvars.py \
  --input-file netbox-client/examples/intent-minimal-schema.json \
  --output-dir /tmp/my-tfvars
```

## Features

### Deterministic Output

The script ensures deterministic output through:

1. **Sorted keys**: JSON keys are sorted alphabetically
2. **Consistent formatting**: 2-space indentation, trailing newline
3. **Same input → same output**: Running the script multiple times with the same input produces identical output (verified via SHA256 checksums)

This makes the output suitable for:
- Version control (git)
- Automated CI/CD pipelines
- Reproducible builds

### Site Grouping

Data is automatically grouped by site:
- Prefixes with matching `site` field are included in that site's tfvars
- VLANs with matching `site` field are included in that site's tfvars
- Tags are included in all site tfvars files

### Flexibility

The script handles both:
- **API export format**: Where `site` is an object with `name`, `slug`, etc.
- **Minimal schema format**: Where `site` is a string (slug or name)

## Validation

### Required Fields

The script validates that required fields are present:
- Sites must have `name` or `slug`
- Prefixes should have `prefix` (CIDR)
- VLANs should have `vlan_id`

### Output Format

Generated tfvars files are valid JSON that can be:
- Validated with JSON linters
- Parsed by Terraform
- Used in automated workflows

### Testing Determinism

You can verify deterministic output by running the script twice and comparing checksums:

```bash
# Generate tfvars
python netbox-client/scripts/render_tfvars.py --input-file input.json

# Get checksums
sha256sum artifacts/tfvars/*.json > checksums1.txt

# Regenerate
python netbox-client/scripts/render_tfvars.py --input-file input.json

# Compare checksums
sha256sum artifacts/tfvars/*.json > checksums2.txt
diff checksums1.txt checksums2.txt  # Should show no differences
```

## Integration with Terraform

The generated tfvars files can be used with Terraform:

```bash
# Use with terraform commands
terraform plan -var-file=artifacts/tfvars/site-pennington.tfvars.json

terraform apply -var-file=artifacts/tfvars/site-pennington.tfvars.json
```

Define corresponding variables in your Terraform configuration:

```hcl
variable "site_name" {
  type        = string
  description = "Site name"
}

variable "site_slug" {
  type        = string
  description = "Site slug (URL-safe identifier)"
}

variable "site_description" {
  type        = string
  description = "Site description"
}

variable "prefixes" {
  type = list(object({
    cidr        = string
    vlan_id     = number
    description = string
    status      = string
  }))
  description = "IP prefixes for the site"
}

variable "vlans" {
  type = list(object({
    vlan_id     = number
    name        = string
    description = string
    status      = string
  }))
  description = "VLANs for the site"
}

variable "tags" {
  type = list(object({
    name        = string
    slug        = string
    description = string
    color       = string
  }))
  description = "Tags (shared across all sites)"
}
```

## Troubleshooting

### No sites found

**Issue**: Script reports "No sites found in NetBox data"

**Solution**: Ensure your input file contains a `sites` array with at least one site.

### Site has no prefixes/VLANs

**Issue**: A site has empty `prefixes` or `vlans` arrays in the output

**Solution**: This is expected if the site has no associated prefixes or VLANs in NetBox. Verify the `site` field in prefixes/VLANs matches the site slug.

### Duplicate site slugs

**Issue**: Multiple sites have the same slug, causing files to overwrite each other

**Solution**: Ensure site slugs are unique in NetBox. Site slugs are used as filenames.

### File encoding issues

**Issue**: Special characters appear incorrectly in output files

**Solution**: The script uses UTF-8 encoding. Ensure your terminal and text editor support UTF-8.
