# Render Pipeline Documentation

## Overview

The render pipeline is an automated GitHub Actions workflow that reads data from the NetBox API, generates configuration artifacts, and makes them available for review and manual deployment. This pipeline is **read-only** and does not apply any infrastructure changes.

## Purpose

The render pipeline serves as a bridge between NetBox (the source of truth for network intent) and various infrastructure-as-code tools. It:

1. **Exports** network intent data from NetBox
2. **Transforms** that data into tool-specific formats (Terraform, UniFi)
3. **Publishes** artifacts for human review and manual deployment
4. **Documents** each generation run with a summary PR

## Workflow File

**Location:** `.github/workflows/render-artifacts.yaml`

### Triggers

The workflow can be triggered in three ways:

1. **Manual Trigger (workflow_dispatch):**
   - Use the GitHub Actions UI to manually trigger a run
   - Go to: Actions → Render Artifacts → Run workflow

2. **Scheduled Execution:**
   - Runs automatically daily at 2:00 AM UTC
   - Ensures artifacts stay synchronized with NetBox

3. **Push to Main:**
   - Runs when changes are pushed to the `main` branch
   - Only if changes affect `netbox-client/scripts/` or the workflow file itself

### Required Secrets

The workflow requires two repository secrets to be configured:

| Secret | Description | Example |
|--------|-------------|---------|
| `NETBOX_URL` | NetBox API endpoint URL (must end with `/api/`) | `https://netbox.example.com/api/` |
| `NETBOX_API_TOKEN` | NetBox API authentication token | `a1b2c3d4e5f6...` |

**⚠️ Security Note:** These secrets should be for a dedicated NetBox API user with **read-only** permissions. The pipeline only needs to read data, not modify it.

#### Setting Up Secrets

1. Go to your GitHub repository
2. Navigate to: Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add both `NETBOX_URL` and `NETBOX_API_TOKEN`

#### Generating a NetBox API Token

1. Log into your NetBox instance
2. Navigate to: Admin → Users → API Tokens
3. Create a new token with read permissions for:
   - DCIM (Sites)
   - IPAM (Prefixes, VLANs)
   - Extras (Tags)
4. Copy the token value and add it as a GitHub secret

## Pipeline Stages

The workflow consists of the following stages:

### 1. Setup

- Checks out the repository
- Sets up Python 3.x
- Installs required dependencies (`requests`, `pyyaml`)
- Creates artifact directories

### 2. Export NetBox Intent Data

**Script:** `netbox-client/scripts/export_intent.py`

Exports the following resources from NetBox:
- **Sites** - Physical locations and data centers
- **Prefixes** - IP address ranges and subnets
- **VLANs** - Virtual LAN configurations
- **Tags** - Metadata tags for organizing resources

**Output Location:** `artifacts/intent-export/`

**Output Files:**
- `sites.json` / `sites.yaml`
- `prefixes.json` / `prefixes.yaml`
- `vlans.json` / `vlans.yaml`
- `tags.json` / `tags.yaml`

### 3. Render Terraform tfvars

**Script:** `netbox-client/scripts/render_tfvars.py`

Converts NetBox intent data into Terraform variable files, one per site.

**Input:** `artifacts/intent-export/`

**Output Location:** `artifacts/tfvars/`

**Output Files:** `site-{slug}.tfvars.json` (one per site)

**Features:**
- Deterministic output (same input → same output)
- Site-specific resource grouping
- Terraform-ready JSON format
- Sorted keys for consistent version control

**Field Mapping:** See [netbox-tfvars-mapping.md](netbox-tfvars-mapping.md) for complete details.

### 4. Render UniFi Configurations

**Script:** `netbox-client/scripts/render_unifi.py`

Converts NetBox intent data into UniFi controller configuration files, one per site.

**Input:** `artifacts/intent-export/`

**Output Location:** `artifacts/unifi/`

**Output Files:** `site-{slug}.json` (one per site)

**Features:**
- Deterministic output
- Site-specific configurations
- UniFi-compatible JSON structure

**⚠️ Warning:** Generated UniFi configs represent intended state only. They are not ready for direct UniFi controller ingestion without review and validation.

### 5. Generate Summary

Creates a comprehensive summary document with:
- Generation timestamp
- Workflow run link
- File listings for each artifact type
- Notes about read-only nature

**Output:** `artifacts/SUMMARY.md`

### 6. Upload Artifacts

All generated artifacts are uploaded to the GitHub Actions workflow run with a 30-day retention period:

| Artifact Name | Contents | Retention |
|---------------|----------|-----------|
| `netbox-intent-export` | Raw NetBox exports (JSON/YAML) | 30 days |
| `terraform-tfvars` | Terraform variable files | 30 days |
| `unifi-configurations` | UniFi controller configs | 30 days |
| `artifact-summary` | Generation summary | 30 days |

### 7. Create Documentation PR

The workflow automatically creates or updates a Pull Request with:
- Summary of the latest run
- Links to artifacts
- Generation timestamp
- Workflow run details

**Branch Name:** `render-artifacts/run-{run_number}`

**PR Contents:**
- Updates `docs/render-pipeline-latest-run.md` with the latest summary
- Links to download all artifacts
- Clear indication this is a read-only pipeline

## Downloading Artifacts

### From GitHub Actions UI

1. Go to: Actions → Render Artifacts
2. Click on the latest workflow run
3. Scroll down to the "Artifacts" section
4. Click on any artifact to download a ZIP file

### Using GitHub CLI

```bash
# List artifacts for the latest run
gh run list --workflow=render-artifacts.yaml --limit 1

# Download all artifacts from a specific run
gh run download <run-id>

# Download a specific artifact
gh run download <run-id> --name netbox-intent-export
```

## Using Generated Artifacts

### Terraform tfvars

```bash
# Download the terraform-tfvars artifact
gh run download <run-id> --name terraform-tfvars

# Use with Terraform
terraform plan -var-file=artifacts/tfvars/site-pennington.tfvars.json
terraform apply -var-file=artifacts/tfvars/site-pennington.tfvars.json
```

### UniFi Configurations

```bash
# Download the unifi-configurations artifact
gh run download <run-id> --name unifi-configurations

# Review the configuration
cat artifacts/unifi/site-pennington.json

# Manual steps required to apply to UniFi controller
# (See UniFi controller documentation for import process)
```

## What This Pipeline Does NOT Do

This pipeline is explicitly designed to be **read-only** and **non-destructive**:

- ❌ Does NOT run `terraform apply`
- ❌ Does NOT modify infrastructure
- ❌ Does NOT push to UniFi controllers
- ❌ Does NOT make changes to NetBox
- ❌ Does NOT automatically deploy anything

All generated artifacts are for **manual review and deployment** only.

## Why Read-Only?

The read-only design is intentional for several reasons:

1. **Safety:** Infrastructure changes should be reviewed by humans before application
2. **Compliance:** Many environments require change approval processes
3. **Flexibility:** Users can review artifacts and choose when/how to deploy
4. **Testing:** Artifacts can be validated before deployment
5. **Auditability:** All artifacts are versioned and traceable

## Troubleshooting

### Workflow Fails During NetBox Export

**Symptoms:** Export step fails with authentication or connection errors.

**Possible Causes:**
- `NETBOX_URL` or `NETBOX_API_TOKEN` secrets not set
- NetBox API is unreachable from GitHub Actions
- API token has expired or insufficient permissions

**Solutions:**
1. Verify secrets are set: Settings → Secrets and variables → Actions
2. Test NetBox API connectivity:
   ```bash
   curl -H "Authorization: Token YOUR_TOKEN" https://netbox.example.com/api/
   ```
3. Check NetBox token permissions in NetBox UI
4. Verify NetBox URL ends with `/api/`

### No Artifacts Generated

**Symptoms:** Workflow completes but no artifacts appear.

**Possible Causes:**
- NetBox has no data to export
- Scripts failed silently
- Upload step encountered an error

**Solutions:**
1. Check workflow logs for each step
2. Verify NetBox instance has sites, prefixes, and VLANs configured
3. Run scripts locally to reproduce:
   ```bash
   export NETBOX_URL="https://netbox.example.com/api/"
   export NETBOX_API_TOKEN="your-token"
   python netbox-client/scripts/export_intent.py
   ```

### PR Creation Fails

**Symptoms:** Artifacts are generated but no PR is created.

**Possible Causes:**
- GitHub token permissions insufficient
- Branch already exists with no changes
- Rate limiting

**Solutions:**
1. Verify workflow has `contents: write` and `pull-requests: write` permissions
2. Check if a PR already exists for the branch
3. Review GitHub Actions logs for the PR creation step

### Artifacts Are Empty or Incomplete

**Symptoms:** Artifacts download but contain no files or partial data.

**Possible Causes:**
- NetBox export returned no results
- Rendering scripts encountered errors
- Data format incompatibility

**Solutions:**
1. Check NetBox for expected data (sites, prefixes, VLANs)
2. Review workflow logs for script output
3. Verify NetBox data follows expected schema
4. Test rendering scripts locally with sample data:
   ```bash
   python netbox-client/scripts/render_tfvars.py \
     --input-file netbox-client/examples/intent-minimal-schema.json
   ```

## Local Development and Testing

### Testing the Pipeline Locally

You can test each stage of the pipeline locally before running it in GitHub Actions:

```bash
# 1. Set up environment
export NETBOX_URL="http://localhost:8000/api/"
export NETBOX_API_TOKEN="0123456789abcdef0123456789abcdef01234567"

# 2. Install dependencies
pip install requests pyyaml

# 3. Create artifact directories
mkdir -p artifacts/{intent-export,tfvars,unifi}

# 4. Run export
python netbox-client/scripts/export_intent.py --output-dir artifacts/intent-export

# 5. Render tfvars
python netbox-client/scripts/render_tfvars.py \
  --input-dir artifacts/intent-export \
  --output-dir artifacts/tfvars

# 6. Render UniFi configs
python netbox-client/scripts/render_unifi.py \
  --input-dir artifacts/intent-export \
  --output-dir artifacts/unifi

# 7. Review outputs
ls -lah artifacts/*/
```

### Testing with Example Data

You can test the rendering scripts without a running NetBox instance:

```bash
# Use the example minimal schema
python netbox-client/scripts/render_tfvars.py \
  --input-file netbox-client/examples/intent-minimal-schema.json \
  --output-dir /tmp/tfvars-test

python netbox-client/scripts/render_unifi.py \
  --input-file netbox-client/examples/intent-minimal-schema.json \
  --output-dir /tmp/unifi-test
```

### Running Tests

The repository includes test suites for the rendering scripts:

```bash
# Test Terraform tfvars rendering
python netbox-client/scripts/test_render_tfvars.py

# Test UniFi config rendering
python netbox-client/scripts/test_render_unifi.py
```

## Pipeline Maintenance

### Updating Python Dependencies

If you need to add new Python dependencies:

1. Update the "Install Python dependencies" step in the workflow
2. Document new dependencies in this file
3. Test locally first
4. Consider adding them to `requirements.txt` if one is created

### Modifying Export or Render Logic

When updating `export_intent.py`, `render_tfvars.py`, or `render_unifi.py`:

1. Make changes to the script
2. Run local tests
3. Update tests if needed
4. Document any output format changes
5. Update this documentation if behavior changes
6. Test the workflow end-to-end

### Changing Workflow Triggers

To modify when the workflow runs:

1. Edit the `on:` section in `.github/workflows/render-artifacts.yaml`
2. Consider impact on NetBox API load
3. Balance freshness needs vs. resource usage
4. Document any changes in this file

## Security Considerations

### API Token Security

- ✅ **DO:** Use repository secrets for tokens
- ✅ **DO:** Use a dedicated read-only NetBox API user
- ✅ **DO:** Rotate tokens periodically
- ✅ **DO:** Audit token usage in NetBox
- ❌ **DON'T:** Commit tokens to code
- ❌ **DON'T:** Use tokens with write permissions
- ❌ **DON'T:** Share tokens between environments

### Artifact Security

Generated artifacts may contain:
- Network topology information
- IP address allocations
- VLAN configurations
- Site names and locations

**Recommendations:**
1. Set appropriate artifact retention periods (default: 30 days)
2. Review artifacts before sharing externally
3. Consider who has access to workflow runs
4. Be mindful of sensitive data in NetBox descriptions

## Extending the Pipeline

### Adding New Artifact Types

To add a new type of artifact generation:

1. Create a new rendering script in `netbox-client/scripts/`
2. Add a new step in the workflow:
   ```yaml
   - name: Render New Artifact Type
     run: |
       python netbox-client/scripts/render_new_type.py \
         --input-dir artifacts/intent-export \
         --output-dir artifacts/new-type
   ```
3. Add a new upload step for the artifact
4. Update the summary generation
5. Document the new artifact type in this file

### Integrating with Other Systems

The pipeline can be extended to integrate with other systems:

- **Slack/Teams Notifications:** Add notification steps
- **S3/Blob Storage:** Upload artifacts to cloud storage
- **JIRA/ServiceNow:** Create tickets for review
- **GitOps Workflows:** Commit artifacts to GitOps repositories

Example notification step:

```yaml
- name: Send Slack Notification
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "Render pipeline completed: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
      }
```

## Related Documentation

- [NetBox Client README](../netbox-client/README.md) - NetBox tools and scripts
- [NetBox Scripts README](../netbox-client/scripts/README.md) - Detailed script documentation
- [NetBox Schema](netbox-schema.md) - NetBox data models
- [NetBox tfvars Mapping](netbox-tfvars-mapping.md) - Field mapping details
- [Repository README](../README.md) - Repository overview

## Support and Contribution

### Getting Help

If you encounter issues with the render pipeline:

1. Check this documentation first
2. Review workflow run logs in GitHub Actions
3. Test scripts locally to isolate the issue
4. Check [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines

### Contributing Improvements

To contribute to the render pipeline:

1. Follow the development guidelines in [CONTRIBUTING.md](../CONTRIBUTING.md)
2. Test changes locally before submitting
3. Update documentation for any behavioral changes
4. Ensure scripts remain deterministic and idempotent
5. Maintain backward compatibility when possible

## Changelog

### Initial Implementation
- Created `.github/workflows/render-artifacts.yaml`
- Integrated NetBox export, Terraform tfvars, and UniFi rendering
- Added artifact uploads with 30-day retention
- Implemented automatic PR creation for documentation
- Created comprehensive documentation in `docs/render-pipeline.md`
