# Terraform Input Contract (Artifact Consumption Interface)

## Overview

This document defines the precise format, schema, and requirements for artifacts that Terraform consumes in this repository. The contract ensures stability, consistency, and security across all Terraform plan and apply operations.

**Status**: Stable as of Phase 4

**Last Updated**: 2025-12-19

## Contract Principles

### 1. One Artifact Per Site

**Requirement**: Each site deployment requires exactly one Terraform variable file (tfvars).

**Rationale**:
- Ensures clear separation of concerns per site
- Simplifies artifact attestation (one attestation per site artifact)
- Enables parallelization of Terraform operations across sites
- Makes it easy to track which configuration applies to which site

**Example**:
```
artifacts/tfvars/
├── site-pennington.tfvars.json
└── site-countfleetcourt.tfvars.json
```

Each file contains all required variables for deploying infrastructure to that specific site.

### 2. JSON Format (tfvars.json) as Canonical Input

**Requirement**: Terraform variable files MUST be in JSON format with `.tfvars.json` extension.

**Format Specification**:
- Valid JSON syntax conforming to [RFC 8259](https://tools.ietf.org/html/rfc8259)
- UTF-8 encoding
- Deterministic formatting: 2-space indentation, sorted keys, trailing newline
- No comments (JSON does not support comments)

**Rationale**:
- **Machine-readable**: JSON is easily parsed and validated programmatically
- **Deterministic**: Sorted keys and consistent formatting enable reproducible builds and accurate checksums
- **Attestation-friendly**: Deterministic output produces consistent SHA256 digests for attestation
- **Terraform native**: Terraform natively supports `.tfvars.json` files without conversion

**Why Not HCL?**
- HCL (`.tfvars`) supports multiple formatting styles, making deterministic output harder
- JSON is more widely supported by validation and schema tools
- Our artifact generation pipeline (Python-based) produces JSON naturally

**Usage**:
```bash
# Terraform natively reads .tfvars.json files
terraform plan -var-file="artifacts/tfvars/site-pennington.tfvars.json"
terraform apply -var-file="artifacts/tfvars/site-pennington.tfvars.json"
```

### 3. Explicit Required Fields

**Requirement**: All Terraform variable files MUST contain the following required fields.

Missing or invalid required fields MUST cause Terraform plan operations to fail.

#### Required Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `site_name` | string | **Yes** | Human-readable site name | `"site-pennington"` |
| `site_slug` | string | **Yes** | Machine-readable site identifier (URL-safe) | `"site-pennington"` |
| `site_description` | string | No | Site description text | `"Primary residence"` |
| `vlans` | array[object] | No | List of VLANs at this site | See schema below |
| `prefixes` | array[object] | No | List of network prefixes at this site | See schema below |
| `tags` | array[object] | No | List of tags (shared across sites) | See schema below |

#### VLAN Object Schema

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `vlan_id` | number | **Yes** | 1-4094 | VLAN ID |
| `name` | string | **Yes** | Non-empty | VLAN name |
| `description` | string | No | - | VLAN description |
| `status` | string | No | Valid values: `"active"`, `"reserved"`, `"deprecated"` | VLAN status |

#### Prefix Object Schema

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `cidr` | string | **Yes** | Valid CIDR notation | IP prefix (e.g., `"192.168.10.0/24"`) |
| `vlan_id` | number | No | 1-4094 | Associated VLAN ID |
| `description` | string | No | - | Prefix description |
| `status` | string | No | Valid values: `"active"`, `"reserved"`, `"deprecated"` | Prefix status |

#### Tag Object Schema

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | string | **Yes** | Non-empty | Tag name |
| `slug` | string | **Yes** | Non-empty, URL-safe | Tag slug identifier |
| `description` | string | No | - | Tag description |
| `color` | string | No | 6-character hex (without `#`) | Tag color |

### 4. Versioning and Stability Guarantees

**Requirement**: The contract MUST provide clear versioning and backward compatibility guarantees.

#### Contract Version

**Current Version**: `1.0.0`

**Version Format**: Semantic Versioning (MAJOR.MINOR.PATCH)

- **MAJOR**: Breaking changes to required fields or schema (incompatible with previous version)
- **MINOR**: New optional fields added (backward compatible)
- **PATCH**: Documentation clarifications or non-schema changes

#### Stability Guarantees

**STABLE (v1.0.0)**:
- ✅ Required fields (`site_name`, `site_slug`) will NOT be renamed or removed
- ✅ Existing field types will NOT change (e.g., `site_name` will always be a string)
- ✅ File naming convention (`site-{slug}.tfvars.json`) will NOT change
- ✅ JSON format requirement will NOT change
- ✅ One artifact per site will NOT change

**ADDITIONS ALLOWED**:
- ✅ New optional fields may be added in MINOR version updates
- ✅ New object types in arrays may be supported
- ✅ Additional validation rules may be added (with proper notice)

**DEPRECATION POLICY**:
- Any field removal or breaking change will be announced at least 30 days in advance
- Deprecated fields will continue to work for at least one MAJOR version
- Migration guides will be provided for breaking changes

## Complete Schema Definition

### JSON Schema (v1.0.0)

This JSON Schema provides formal validation rules for Terraform input artifacts:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Terraform Site Variables (tfvars)",
  "description": "Schema for site-specific Terraform variable files consumed by this repository",
  "type": "object",
  "required": ["site_name", "site_slug"],
  "properties": {
    "site_name": {
      "type": "string",
      "minLength": 1,
      "description": "Human-readable name of the site",
      "example": "site-pennington"
    },
    "site_slug": {
      "type": "string",
      "minLength": 1,
      "pattern": "^[a-z0-9-]+$",
      "description": "Machine-readable slug identifier for the site (lowercase, alphanumeric, hyphens only)",
      "example": "site-pennington"
    },
    "site_description": {
      "type": "string",
      "description": "Description of the site",
      "example": "Primary residence"
    },
    "vlans": {
      "type": "array",
      "description": "List of VLANs to configure at this site",
      "items": {
        "type": "object",
        "required": ["vlan_id", "name"],
        "properties": {
          "vlan_id": {
            "type": "integer",
            "minimum": 1,
            "maximum": 4094,
            "description": "VLAN ID number"
          },
          "name": {
            "type": "string",
            "minLength": 1,
            "description": "VLAN name"
          },
          "description": {
            "type": "string",
            "description": "VLAN description"
          },
          "status": {
            "type": "string",
            "enum": ["active", "reserved", "deprecated"],
            "description": "VLAN status"
          }
        }
      }
    },
    "prefixes": {
      "type": "array",
      "description": "List of network prefixes (IP ranges) for this site",
      "items": {
        "type": "object",
        "required": ["cidr"],
        "properties": {
          "cidr": {
            "type": "string",
            "pattern": "^([0-9]{1,3}\\.){3}[0-9]{1,3}/[0-9]{1,2}$",
            "description": "IP prefix in CIDR notation",
            "example": "192.168.10.0/24"
          },
          "vlan_id": {
            "type": "integer",
            "minimum": 1,
            "maximum": 4094,
            "description": "Associated VLAN ID"
          },
          "description": {
            "type": "string",
            "description": "Prefix description"
          },
          "status": {
            "type": "string",
            "enum": ["active", "reserved", "deprecated"],
            "description": "Prefix status"
          }
        }
      }
    },
    "tags": {
      "type": "array",
      "description": "List of tags from NetBox for organizing resources (shared across all sites)",
      "items": {
        "type": "object",
        "required": ["name", "slug"],
        "properties": {
          "name": {
            "type": "string",
            "minLength": 1,
            "description": "Tag name"
          },
          "slug": {
            "type": "string",
            "minLength": 1,
            "pattern": "^[a-z0-9-]+$",
            "description": "Tag slug identifier (lowercase, alphanumeric, hyphens only)"
          },
          "description": {
            "type": "string",
            "description": "Tag description"
          },
          "color": {
            "type": "string",
            "pattern": "^[0-9a-fA-F]{6}$",
            "description": "Tag color as 6-character hex code (without # prefix)",
            "example": "2196f3"
          }
        }
      }
    }
  }
}
```

### Example: Valid Artifact

**File**: `artifacts/tfvars/site-pennington.tfvars.json`

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

**Validation**: ✅ PASS
- Contains all required fields (`site_name`, `site_slug`)
- All fields match expected types
- VLAN IDs are in valid range (1-4094)
- CIDR notation is valid
- Keys are sorted alphabetically
- 2-space indentation with trailing newline

## Artifact Path Convention

**Requirement**: All Terraform input artifacts MUST follow the established path convention.

### Directory Structure

```
artifacts/
└── tfvars/
    ├── site-pennington.tfvars.json
    └── site-countfleetcourt.tfvars.json
```

### Naming Convention

- **Pattern**: `{site_slug}.tfvars.json`
- **{site_slug}**: The exact value from the `site_slug` field (typically includes `site-` prefix)
- **Extension**: MUST be `.tfvars.json` (not `.json` or `.tfvars`)

### Examples

| Site Slug Value (`site_slug` field) | Artifact Filename |
|-------------------------------------|-------------------|
| `site-pennington` | `site-pennington.tfvars.json` |
| `site-countfleetcourt` | `site-countfleetcourt.tfvars.json` |
| `site-production` | `site-production.tfvars.json` |

**Note**: The `site_slug` field value is used as-is for the filename. In this repository, site slugs follow the convention `site-{location}` by convention, but the filename pattern itself is simply `{site_slug}.tfvars.json`.

## Validation Requirements

**Requirement**: Terraform plan jobs MUST validate artifacts against this contract and FAIL if the contract is violated, even if attestation exists.

### Validation Hierarchy

Validation occurs in the following order (all must pass):

1. **File Existence Check** - Artifact file must exist at expected path
2. **JSON Syntax Validation** - File must be valid JSON
3. **Schema Validation** - File must conform to JSON Schema (required fields, types, constraints)
4. **Attestation Verification** - File must have valid SLSA provenance attestation
5. **Terraform Variable Validation** - Terraform must accept the variables (via `terraform validate`)

**Important**: Attestation is necessary but NOT sufficient. An attested artifact that violates the schema MUST be rejected.

### Validation Implementation

Terraform plan workflows implement validation through:

#### 1. Attestation Gate (Security)

```yaml
- name: Verify artifact attestations
  uses: ./.github/actions/verify-attestation
  with:
    artifact-path: 'artifacts/tfvars/site-${{ matrix.site }}.tfvars.json'
    environment: 'prod'
```

This step verifies that:
- Artifact has a valid SLSA provenance attestation
- Artifact was generated by the trusted render workflow
- Artifact has not been modified since attestation

**Failure Behavior**: Workflow fails immediately if attestation is missing or invalid.

See [docs/phase4/attestation-gate.md](attestation-gate.md) for details.

#### 2. Terraform Validate (Schema)

```yaml
- name: Terraform Validate
  working-directory: terraform
  run: terraform validate
```

This step verifies that:
- Terraform configuration is syntactically valid
- All required variables are defined in `terraform/variables.tf`
- Variable types match expected types

**Failure Behavior**: Workflow fails if variable definitions don't match.

#### 3. Terraform Plan (Contract Enforcement)

```yaml
- name: Terraform Plan
  working-directory: terraform
  run: |
    terraform plan -var-file="../artifacts/tfvars/site-${{ matrix.site }}.tfvars.json"
```

This step verifies that:
- tfvars file contains all required fields
- Field values are compatible with Terraform variable types
- No unexpected fields that would cause plan failures

**Failure Behavior**: Workflow fails if required fields are missing or types are incompatible.

### Error Examples

#### Missing Required Field

**Invalid Artifact**: Missing `site_slug`

```json
{
  "site_name": "site-pennington",
  "vlans": []
}
```

**Expected Error**:
```
Error: No value for required variable

  on variables.tf line 37:
  37: variable "site_slug" {

The module variable "site_slug" is not set, and has no default value.
```

**Result**: ❌ Terraform plan MUST fail

#### Invalid Field Type

**Invalid Artifact**: `vlan_id` is string instead of number

```json
{
  "site_name": "site-pennington",
  "site_slug": "site-pennington",
  "vlans": [
    {
      "vlan_id": "10",
      "name": "Home LAN"
    }
  ]
}
```

**Expected Error**:
```
Error: Invalid value for input variable

  on variables.tf line 49:
  49: variable "vlans" {

The given value is not suitable for var.vlans: element 0: attribute "vlan_id":
number required.
```

**Result**: ❌ Terraform plan MUST fail

#### Invalid CIDR Format

**Invalid Artifact**: CIDR is not valid notation

```json
{
  "site_name": "site-pennington",
  "site_slug": "site-pennington",
  "prefixes": [
    {
      "cidr": "192.168.10.0"
    }
  ]
}
```

**Expected Error**: May not fail at plan stage but will fail during validation or apply when CIDR is parsed.

**Result**: ⚠️ Consider adding CIDR validation in future versions

## Contract Enforcement in Workflows

### Render Artifacts Workflow

**File**: `.github/workflows/render-artifacts.yaml`

**Responsibility**: Generate artifacts that conform to this contract

**Enforcement**:
- `render_tfvars.py` script generates artifacts in the specified format
- Deterministic JSON output with sorted keys
- One file per site with correct naming convention
- All required fields populated from NetBox export

**Output Attestation**: After generation, artifacts are attested with SLSA provenance

```yaml
- name: Attest Terraform tfvars Artifacts
  uses: actions/attest-build-provenance@v1
  with:
    subject-path: 'artifacts/tfvars/*.json'
```

### Terraform Plan Workflow

**File**: `.github/workflows/terraform-plan.yaml`

**Responsibility**: Consume artifacts and enforce contract validation

**Enforcement Steps**:

1. **Download Artifacts** - Retrieve attested artifacts from render workflow
2. **Verify Attestations** - Ensure artifacts have valid SLSA provenance
3. **Terraform Init** - Initialize provider and modules
4. **Terraform Validate** - Validate configuration and variable schema
5. **Terraform Plan** - Generate plan using artifact (fails if contract violated)

**Contract Failure Behavior**: Workflow fails with clear error message indicating which validation step failed.

## Stability Guarantees for Plan Jobs

**Requirement**: All fields, format, and paths referenced in Terraform plan jobs MUST remain stable.

### Stable References

These references are guaranteed to remain unchanged:

| Reference | Type | Guarantee |
|-----------|------|-----------|
| `artifacts/tfvars/site-{slug}.tfvars.json` | Path | File path format is stable |
| `site_name` | Variable | Variable name and type (string) are stable |
| `site_slug` | Variable | Variable name and type (string) are stable |
| `vlans[]` | Variable | Variable name and array structure are stable |
| `prefixes[]` | Variable | Variable name and array structure are stable |
| `tags[]` | Variable | Variable name and array structure are stable |

### Non-Breaking Changes

These changes are allowed without breaking the contract:

- ✅ Adding new optional fields to the root object
- ✅ Adding new optional fields to nested objects (VLAN, prefix, tag)
- ✅ Adding new object types to arrays (if backward compatible)
- ✅ Increasing validation strictness (with proper notice)

### Breaking Changes

These changes would break the contract and require a MAJOR version bump:

- ❌ Renaming required fields (`site_name` → `name`)
- ❌ Changing required field types (`site_slug: string` → `site_slug: number`)
- ❌ Removing required fields
- ❌ Changing path format (`site-{slug}.tfvars.json` → `{slug}.json`)
- ❌ Changing file format (JSON → YAML)

## Migration and Upgrade Path

When contract changes are necessary:

### For MINOR Version Updates (Non-Breaking)

Example: Adding optional field `site_region`

1. **Announce**: Document new field in contract
2. **Deploy**: Update render pipeline to include new field
3. **Test**: Verify Terraform accepts both old and new format
4. **Use**: New field available immediately for those who need it

**Impact**: No migration required. Existing artifacts continue to work.

### For MAJOR Version Updates (Breaking)

Example: Renaming `site_name` to `name`

1. **Announce**: 30-day notice of upcoming change
2. **Deprecate**: Mark old field as deprecated in documentation
3. **Support Both**: Render pipeline generates both old and new fields
4. **Migrate**: Update Terraform variables to accept both fields
5. **Test**: Verify all workflows work with new format
6. **Switch**: Update render pipeline to only generate new field
7. **Cleanup**: Remove old field support from Terraform

**Impact**: Requires coordinated update of render pipeline and Terraform configuration.

## Compliance Checklist

Use this checklist to verify artifacts comply with the contract:

### Artifact Generation

- [ ] One artifact file per site
- [ ] File format is JSON (`.tfvars.json` extension)
- [ ] File path follows convention: `artifacts/tfvars/site-{slug}.tfvars.json`
- [ ] JSON is valid (parseable by standard JSON parsers)
- [ ] JSON formatting is deterministic (sorted keys, 2-space indent, trailing newline)
- [ ] Contains required field: `site_name`
- [ ] Contains required field: `site_slug`
- [ ] All VLAN objects have required fields (`vlan_id`, `name`)
- [ ] All prefix objects have required fields (`cidr`)
- [ ] All tag objects have required fields (`name`, `slug`)
- [ ] All field types match schema (strings are strings, numbers are numbers, etc.)
- [ ] VLAN IDs are in range 1-4094
- [ ] CIDR notation is valid (pattern: `x.x.x.x/y`)
- [ ] Artifact has SLSA provenance attestation

### Terraform Integration

- [ ] Terraform variables defined in `terraform/variables.tf` match contract
- [ ] Required variables do not have default values (force explicit input)
- [ ] Optional variables have appropriate defaults
- [ ] Plan workflow verifies attestations before use
- [ ] Plan workflow fails if required fields are missing
- [ ] Plan workflow fails if attestation is invalid
- [ ] Plan workflow uses correct artifact path pattern

## Troubleshooting

### Artifact Not Found

**Error**: `No such file: artifacts/tfvars/site-production.tfvars.json`

**Possible Causes**:
- Site slug mismatch (file generated with different slug)
- Artifact not downloaded before plan
- Render workflow did not complete successfully

**Resolution**:
1. Verify render workflow completed: `gh run list --workflow render-artifacts.yaml`
2. Check artifact was uploaded: `gh run view <run-id> --log`
3. Verify site slug matches exactly (case-sensitive)

### Required Variable Not Set

**Error**: `No value for required variable: site_name`

**Possible Causes**:
- Artifact missing `site_name` field
- Artifact format is incorrect
- Wrong artifact file used for this site

**Resolution**:
1. Download and inspect artifact: `cat artifacts/tfvars/site-{slug}.tfvars.json`
2. Verify artifact contains `site_name` field
3. Verify JSON is valid: `jq . artifacts/tfvars/site-{slug}.tfvars.json`
4. Re-run render workflow if artifact is malformed

### Attestation Verification Failed

**Error**: `❌ Attestation verification failed for artifacts/tfvars/site-production.tfvars.json`

**Possible Causes**:
- Artifact was not attested during generation
- Artifact was modified after attestation
- Attestation from untrusted source

**Resolution**:
1. **DO NOT USE** this artifact - it may be compromised
2. Re-run render workflow to generate new attested artifact
3. Investigate why attestation failed (check render workflow logs)
4. Verify attestation manually: `gh attestation verify <file> --owner <owner> --repo <repo>`

See [docs/phase4/attestation-gate.md](attestation-gate.md) for more details.

### Type Mismatch

**Error**: `Invalid value for input variable: number required, got string`

**Possible Causes**:
- Field has wrong type in artifact (e.g., `"10"` instead of `10`)
- Schema changed but artifact generation not updated

**Resolution**:
1. Inspect artifact and verify field types match schema
2. Update render pipeline if types are incorrect
3. Re-run render workflow to generate corrected artifact

## References

### Related Documentation

- **Attestation Gate**: [docs/phase4/attestation-gate.md](attestation-gate.md) - Artifact verification process
- **Trust Boundary**: [docs/phase3/terraform-boundary.md](../phase3/terraform-boundary.md) - Trust model and security
- **NetBox Mapping**: [docs/netbox-tfvars-mapping.md](../netbox-tfvars-mapping.md) - Field mapping from NetBox
- **Render Pipeline**: [docs/render-pipeline.md](../render-pipeline.md) - Artifact generation process
- **Attestation**: [docs/phase3/attestation.md](../phase3/attestation.md) - SLSA provenance details

### Implementation Files

- **Contract Schema**: `docs/phase4/terraform-input-contract.md` (this document)
- **Terraform Variables**: `terraform/variables.tf` - Variable definitions
- **Render Script**: `netbox-client/scripts/render_tfvars.py` - Artifact generation
- **Attestation Gate**: `.github/actions/verify-attestation/action.yml` - Verification action
- **Render Workflow**: `.github/workflows/render-artifacts.yaml` - Artifact generation workflow
- **Plan Workflow**: `.github/workflows/terraform-plan.yaml` - Terraform plan workflow

### External Standards

- **JSON Specification**: [RFC 8259](https://tools.ietf.org/html/rfc8259)
- **JSON Schema**: [JSON Schema Draft 7](https://json-schema.org/draft-07/schema)
- **SLSA Provenance**: [SLSA Provenance v1.0](https://slsa.dev/provenance/v1)
- **Semantic Versioning**: [SemVer 2.0.0](https://semver.org/)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-19 | Initial stable contract definition |

## Contact and Support

For questions about this contract:
- Review existing documentation in `docs/`
- Check workflow implementations in `.github/workflows/`
- Open an issue for clarifications or proposed changes

**Contract Owner**: Infrastructure Team

**Review Schedule**: Quarterly (or as needed for breaking changes)
