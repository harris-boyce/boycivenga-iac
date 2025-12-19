# Attestation Verification Gate - Quick Start Guide

This guide shows how to use the attestation verification gate in your workflows.

## Production Usage (Default)

For production workflows, simply use the action with the artifact path:

```yaml
- name: Verify artifact attestations
  uses: ./.github/actions/verify-attestation
  with:
    artifact-path: 'artifacts/tfvars/*.json'
```

This will:
- Verify all matching artifacts have valid attestations
- Fail the workflow if any artifact lacks valid attestation
- Fail the workflow if any artifact has been tampered with
- Log detailed verification results

## Development Usage (With Bypass)

For development/test workflows where you need to work with non-attested artifacts:

```yaml
- name: Verify artifact attestations (dev bypass)
  uses: ./.github/actions/verify-attestation
  with:
    artifact-path: 'artifacts/tfvars/*.json'
    environment: 'dev'
    allow-bypass: 'true'
```

This will:
- Skip attestation verification entirely
- Log a warning that bypass was used
- Continue workflow execution
- **Only works in dev mode - ignored in prod**

## Example: Terraform Plan Workflow

See `.github/workflows/terraform-plan.yaml` for a real-world example:

```yaml
jobs:
  terraform-plan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Download artifacts
        run: |
          gh run download $RUN_ID --name terraform-tfvars --dir artifacts/tfvars

      - name: Verify artifact attestations (REQUIRED)
        uses: ./.github/actions/verify-attestation
        with:
          artifact-path: 'artifacts/tfvars/site-${{ matrix.site }}.tfvars.json'
          environment: 'prod'

      - name: Terraform Plan
        run: |
          terraform plan -var-file="../artifacts/tfvars/site-${{ matrix.site }}.tfvars.json"
```

## Understanding the Outputs

The action provides outputs you can use in subsequent steps:

```yaml
- name: Verify attestations
  id: verify
  uses: ./.github/actions/verify-attestation
  with:
    artifact-path: 'artifacts/*.json'

- name: Check results
  run: |
    echo "Verified: ${{ steps.verify.outputs.verified-count }}"
    echo "Failed: ${{ steps.verify.outputs.failed-count }}"
    echo "Bypassed: ${{ steps.verify.outputs.bypassed }}"
```

## Troubleshooting

### "No files found matching pattern"

**Problem**: The glob pattern didn't match any files.

**Solution**:
1. Check the pattern is correct
2. Verify artifacts were downloaded before this step
3. Use `ls -la artifacts/` to debug

### "Attestation verification FAILED"

**Problem**: Artifact has no attestation or has been modified.

**Solution**:
1. Don't use this artifact - it may be compromised
2. Re-run the artifact generation workflow
3. Ensure generation workflow has proper permissions

## Full Documentation

See [docs/phase4/attestation-gate.md](attestation-gate.md) for complete documentation.
