# NetBox Client Scripts

This directory contains Python scripts for interacting with NetBox and managing network intent data.

## Available Scripts

### `export_intent.py`
Export NetBox intent data (sites, prefixes, VLANs, tags) to JSON and YAML files.

**Usage:**
```bash
export NETBOX_URL="http://localhost:8000/api/"
export NETBOX_API_TOKEN="your-token-here"

python export_intent.py
python export_intent.py --output-dir /tmp/export
```

**Output:** `artifacts/intent-export/` with `sites.json`, `prefixes.json`, `vlans.json`, `tags.json`

### `render_tfvars.py`
Convert NetBox intent-export data to Terraform tfvars files (one per site).

**Usage:**
```bash
# From export directory
python render_tfvars.py --input-dir artifacts/intent-export

# From single file
python render_tfvars.py --input-file examples/intent-minimal-schema.json
```

**Output:** `artifacts/tfvars/site-{slug}.tfvars.json`

**Features:**
- Deterministic output (sorted keys)
- Site-specific resource grouping
- Terraform-ready JSON format

**Documentation:** See [docs/netbox-tfvars-mapping.md](../../docs/netbox-tfvars-mapping.md)

### `seed_netbox.py`
Seed NetBox with data from YAML configuration files.

**Usage:**
```bash
export NETBOX_URL="http://localhost:8000/api/"
export NETBOX_API_TOKEN="your-token-here"

python seed_netbox.py examples/site-pennington.yaml
python seed_netbox.py examples/*.yaml
```

**Input:** YAML files with site, prefix, and VLAN definitions

### `post_minimal_intent.py`
Post minimal intent data to NetBox from JSON/YAML files.

**Usage:**
```bash
python post_minimal_intent.py examples/intent-minimal-schema.json
```

### `test_render_tfvars.py`
Test suite for `render_tfvars.py` to verify conversion logic and determinism.

**Usage:**
```bash
python test_render_tfvars.py
```

**Tests:**
- Site slug extraction
- Tfvars rendering
- Deterministic output
- File I/O operations
- JSON key sorting

## Common Workflows

### Complete Export and Render Pipeline
```bash
# 1. Export from NetBox
export NETBOX_URL="http://localhost:8000/api/"
export NETBOX_API_TOKEN="your-token-here"
python export_intent.py

# 2. Render Terraform tfvars
python render_tfvars.py --input-dir artifacts/intent-export

# 3. Use with Terraform
terraform plan -var-file=artifacts/tfvars/site-pennington.tfvars.json
```

### Local Development with Example Data
```bash
# Use example data (no NetBox required)
python render_tfvars.py --input-file ../examples/intent-minimal-schema.json

# Review generated files
ls -lh artifacts/tfvars/
cat artifacts/tfvars/site-pennington.tfvars.json
```

### Seed and Export Workflow
```bash
# 1. Seed local NetBox with examples
python seed_netbox.py ../examples/*.yaml

# 2. Export from NetBox
python export_intent.py

# 3. Render tfvars
python render_tfvars.py --input-dir artifacts/intent-export
```

## Configuration

All scripts that interact with NetBox use environment variables for configuration:

- `NETBOX_URL` - NetBox API endpoint (default: `http://localhost:8000/api/`)
- `NETBOX_API_TOKEN` - NetBox API authentication token (required)

You can set these in your shell or use a `.env` file (not tracked in git).

## Development

### Running Tests
```bash
# Test render_tfvars.py
python test_render_tfvars.py
```

### Code Quality
All scripts follow:
- Black formatting
- isort import sorting
- flake8 linting (max line length: 88)

Run pre-commit hooks:
```bash
pre-commit run --files netbox-client/scripts/*.py
```

## See Also

- [netbox-client README](../README.md) - Full documentation for NetBox client tools
- [docs/netbox-tfvars-mapping.md](../../docs/netbox-tfvars-mapping.md) - Field mapping details
- [docs/netbox-schema.md](../../docs/netbox-schema.md) - NetBox schema documentation
