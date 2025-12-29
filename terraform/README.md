# Terraform Configuration

This directory contains Terraform configurations for managing UniFi network infrastructure based on NetBox intent data.

## Structure

- `main.tf` - Main Terraform configuration with UniFi provider and resources
- `variables.tf` - Variable definitions for site-specific inputs
- `terraform.tf` - Provider version constraints and backend configuration
- `terraform.tfvars.example` - Example variable values for testing

## Usage

### Prerequisites

1. **Attested Artifacts**: Terraform must only consume artifacts with valid SLSA provenance attestations. See [../docs/phase3/terraform-boundary.md](../docs/phase3/terraform-boundary.md)

2. **UniFi Controller Access**:
   - UniFi controller URL
   - Admin credentials (username and password)
   - Network connectivity to the controller

### Running Terraform Plan

The recommended way to run Terraform plan is through the CI workflow, which:
1. Downloads attested tfvars artifacts
2. Verifies attestations
3. Runs `terraform plan` with provider schema validation
4. Generates both binary plan and JSON output

**Manual execution** (for development only):

```bash
# Set UniFi credentials (or use stub values for validation)
export TF_VAR_unifi_username="admin"
export TF_VAR_unifi_password="password"
export TF_VAR_unifi_api_url="https://unifi.local:8443"
export TF_VAR_unifi_allow_insecure="true"

# Initialize Terraform and download providers
terraform init

# Validate configuration against provider schema
terraform validate

# Run plan with attested tfvars file
terraform plan -var-file=../artifacts/tfvars/site-pennington.tfvars.json

# Generate JSON output
terraform show -json terraform.tfplan > plan.json
```

### Provider Configuration

The UniFi provider is configured via variables that can be set through:

1. **Environment Variables** (recommended for credentials):
   - `TF_VAR_unifi_username`
   - `TF_VAR_unifi_password`
   - `TF_VAR_unifi_api_url`
   - `TF_VAR_unifi_allow_insecure`

2. **Stub Configuration** (for plan-only validation in CI):
   ```bash
   # Use empty/stub values when only validating schema
   export TF_VAR_unifi_username=""
   export TF_VAR_unifi_password=""
   ```

### Artifact Attestation Requirement

**IMPORTANT**: This Terraform configuration must only consume artifacts that have been cryptographically attested. This ensures:

- Provenance: Proof that artifacts originate from trusted CI/CD workflows
- Integrity: Assurance that artifacts have not been tampered with
- Supply chain security: Protection against unauthorized modifications

Before using any tfvars file:

```bash
# Verify the artifact attestation
gh attestation verify ../artifacts/tfvars/site-pennington.tfvars.json \
  --owner harris-boyce \
  --repo boycivenga-iac
```

See [Trust Boundary Documentation](../docs/phase3/terraform-boundary.md) for complete details.

## Site-Specific Configuration

Each site has its own tfvars file generated from NetBox exports:

- `site-pennington.tfvars.json` - Configuration for Pennington site
- `site-count-fleet-court.tfvars.json` - Configuration for Count Fleet Court site

These files contain:
- Site metadata (name, slug, description)
- VLANs for network segmentation
- IP prefixes (network ranges)
- Tags for resource organization

## Provider Documentation

This configuration uses the [paultyng/unifi](https://registry.terraform.io/providers/paultyng/unifi/latest/docs) Terraform provider.

**Key Resources**:
- `unifi_network` - Manages UniFi networks (VLANs)

## Validation

The configuration is automatically validated in CI:

```bash
# Check formatting
terraform fmt -check

# Initialize without backend
terraform init -backend=false

# Validate configuration and provider schema
terraform validate
```

## Security Notes

1. **Never commit credentials** - Use environment variables or secure secret management
2. **Always verify attestations** - Only use attested tfvars files
3. **Use TLS** - Set `unifi_allow_insecure = false` for production
4. **Audit trail** - All plans should be traceable to workflow runs

## Related Documentation

- [Render Pipeline](../docs/render-pipeline.md) - How artifacts are generated
- [Trust Boundary](../docs/phase3/terraform-boundary.md) - Attestation requirements
- [Attestation Guide](../docs/phase3/attestation.md) - Complete attestation documentation
