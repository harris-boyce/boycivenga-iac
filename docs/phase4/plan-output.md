# Terraform Plan Output Structure

## Overview

This document describes the machine-readable Terraform plan output structure used in the Boycivenga IaC pipeline. All plan outputs are designed to be:

- **Machine-parseable**: JSON format via `terraform show -json`
- **Deterministically ordered**: Consistent ordering for diffing and comparison
- **Agent-friendly**: Structured for programmatic consumption and analysis
- **Human-readable**: Includes summary views for manual review

## Output Artifacts

### 1. Binary Plan File

**File**: `tfplan-{site}.binary`

The native Terraform plan file in binary format.

- **Format**: Terraform proprietary binary format
- **Usage**: `terraform apply tfplan-{site}.binary`
- **Retention**: 30 days in GitHub Actions artifacts

### 2. JSON Plan File

**File**: `tfplan-{site}.json`

Machine-readable JSON representation generated via `terraform show -json`.

- **Format**: JSON (UTF-8 encoded)
- **Schema**: [Terraform JSON Output Format](https://developer.hashicorp.com/terraform/internals/json-format)
- **Retention**: 30 days in GitHub Actions artifacts

### 3. Structured Diff (Markdown)

**File**: `tfplan-{site}-diff.md`

Human and agent-friendly summary of plan changes.

- **Format**: Markdown with embedded JSON summary
- **Contains**: Change counts, resource lists, machine-readable JSON block
- **Retention**: 30 days in GitHub Actions artifacts

## Deterministic Ordering

All plan outputs use deterministic ordering to ensure:
1. Consistent diffs between plan runs
2. Reliable comparison for change detection
3. Stable artifact hashing

The JSON plan output from `terraform show -json` inherently maintains deterministic ordering as it reflects Terraform's internal graph structure.

## Parsing Guidelines

### For Automated Tools

```python
import json

# Parse JSON plan
with open('tfplan-site.json', 'r') as f:
    plan = json.load(f)

# Extract resource changes
for change in plan.get('resource_changes', []):
    address = change['address']
    actions = change['change']['actions']
    print(f"{actions}: {address}")
```

### For Shell Scripts

```bash
# Extract resource change summary
jq -r '.resource_changes[]? | "\(.change.actions | join(",")): \(.address)"' tfplan-site.json

# Count changes
jq '[.resource_changes[]?.change.actions[]] | group_by(.) | map({action: .[0], count: length})' tfplan-site.json
```

## Integration with CI/CD

The `terraform-plan.yaml` workflow:

1. **Generates binary plan**: `terraform plan -out=tfplan-{site}.binary`
2. **Converts to JSON**: `terraform show -json tfplan-{site}.binary`
3. **Creates diff summary**: `scripts/generate-plan-diff.py`
4. **Uploads artifacts**: Binary, JSON, and diff markdown
5. **Displays in summary**: Shows diff in GitHub Actions step summary

## Validation

The `scripts/test-plan-output.sh` script validates:

1. **Parseability**: JSON can be parsed
2. **Schema compliance**: Required fields exist
3. **Determinism**: Consistent output ordering
4. **Documentation**: Required docs exist
5. **CI integration**: Workflow properly configured

Run tests:
```bash
./scripts/test-plan-output.sh
```

## References

- [Terraform JSON Output Format](https://developer.hashicorp.com/terraform/internals/json-format)
- [terraform-plan.yaml workflow](../../.github/workflows/terraform-plan.yaml)
- [Attestation Gate](attestation-gate.md)
