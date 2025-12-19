# Attestation Verification Gate Documentation

## Overview

The attestation verification gate is a reusable composite action that enforces cryptographic verification of artifact attestations before they can be consumed by downstream workflows. This gate implements a fail-closed security model for production environments while allowing explicit bypass for development and testing.

**Location**: `.github/actions/verify-attestation`

**Type**: Composite Action

## Purpose

The attestation gate serves as a critical security control in the infrastructure supply chain:

- **Enforce Trust Boundary**: Ensures only attested artifacts are consumed by Terraform and other infrastructure tools
- **Fail-Closed by Default**: Production environments require valid attestations - no exceptions
- **Explicit Dev Override**: Development and test environments can bypass verification with an explicit flag
- **Cryptographic Verification**: Uses GitHub's attestation API to verify SLSA provenance
- **Audit Trail**: Logs all verification attempts with clear pass/fail indicators

## Usage

### Basic Usage (Production - Fail Closed)

```yaml
- name: Verify artifact attestations
  uses: ./.github/actions/verify-attestation
  with:
    artifact-path: 'artifacts/tfvars/*.json'
```

This is the recommended usage for production workflows. The action will:
- Verify all files matching the glob pattern
- Fail the workflow if any artifact lacks valid attestation
- Fail the workflow if any artifact has been modified since attestation

### Development Usage (With Explicit Bypass)

```yaml
- name: Verify artifact attestations (dev mode)
  uses: ./.github/actions/verify-attestation
  with:
    artifact-path: 'artifacts/tfvars/*.json'
    environment: 'dev'
    allow-bypass: 'true'
```

This usage is **ONLY** appropriate for development and testing workflows. The action will:
- Skip verification entirely when bypass is enabled
- Log a warning that verification was bypassed
- Continue workflow execution without checking attestations

**IMPORTANT**: Bypass is ignored in production environments. Setting `environment: 'prod'` with `allow-bypass: 'true'` will still enforce verification.

### Advanced Usage (Custom Repository)

```yaml
- name: Verify artifact attestations
  uses: ./.github/actions/verify-attestation
  with:
    artifact-path: 'artifacts/tfvars/*.json'
    repo-owner: 'custom-org'
    repo-name: 'custom-repo'
```

This is useful when verifying artifacts that were generated in a different repository.

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `artifact-path` | Yes | - | Path to artifact file(s) to verify. Supports glob patterns like `artifacts/*.json` or `artifacts/tfvars/*.json`. |
| `environment` | No | `prod` | Environment mode. Must be either `prod` (fail-closed) or `dev` (allow bypass). |
| `allow-bypass` | No | `false` | Explicitly allow bypass of attestation verification. Only effective when `environment: 'dev'`. |
| `repo-owner` | No | Current repo owner | Repository owner for attestation verification. |
| `repo-name` | No | Current repo name | Repository name for attestation verification. |

## Outputs

| Output | Description |
|--------|-------------|
| `verified-count` | Number of artifacts successfully verified |
| `failed-count` | Number of artifacts that failed verification |
| `bypassed` | Whether verification was bypassed (`true`/`false`) |

## Behavior

### Production Mode (Default)

When `environment: 'prod'` (the default):

1. **Mandatory Verification**: All artifacts MUST have valid attestations
2. **No Bypass**: The `allow-bypass` flag is ignored
3. **Fail Closed**: Any verification failure stops the workflow
4. **Exit Codes**:
   - `0` - All artifacts verified successfully
   - `1` - One or more artifacts failed verification OR no artifacts found

### Development Mode

When `environment: 'dev'` AND `allow-bypass: 'true'`:

1. **Verification Skipped**: No attestation checks are performed
2. **Warning Logged**: Clear indication that bypass was used
3. **Success**: Always exits with code `0`
4. **Audit Trail**: Bypass is logged in outputs (`bypassed: true`)

When `environment: 'dev'` AND `allow-bypass: 'false'`:

1. **Same as Production**: Full verification is performed
2. **Fail Closed**: Any verification failure stops the workflow

## Verification Process

The action performs the following steps for each artifact:

1. **File Discovery**: Expands glob pattern to find all matching files
2. **Existence Check**: Verifies files exist at specified paths
3. **Digest Calculation**: Computes SHA256 digest for logging
4. **Attestation Verification**: Uses `gh attestation verify` to check:
   - Attestation exists for the artifact
   - Attestation is cryptographically valid
   - Attestation is from the correct repository
   - Artifact matches the attested digest (no tampering)
5. **Result Logging**: Records pass/fail for each artifact

## Error Scenarios

### No Files Found

**Error**: No files matching the artifact-path pattern

**Cause**:
- Incorrect glob pattern
- Artifacts not downloaded before verification
- Expected artifacts were not generated

**Resolution**:
- Verify the artifact-path pattern is correct
- Ensure artifact download step runs before verification
- Check that artifact generation completed successfully

### Attestation Not Found

**Error**: No valid attestation found for artifact

**Cause**:
- Artifact was not attested during generation
- Attestation workflow did not have required permissions
- Artifact is from an untrusted source

**Resolution**:
- Verify the artifact generation workflow includes attestation step
- Check that workflow has `id-token: write` and `attestations: write` permissions
- Ensure artifacts are from the expected repository

### Attestation Verification Failed

**Error**: Artifact has been modified after attestation

**Cause**:
- Artifact was tampered with after generation
- Artifact digest does not match attested digest

**Resolution**:
- DO NOT USE this artifact - it may be compromised
- Re-run the artifact generation workflow to create new attested artifacts
- Investigate how the artifact was modified

### Attestation From Untrusted Source

**Error**: Attestation is not from expected repository/workflow

**Cause**:
- Artifact originated from different repository
- Attestation was generated by unauthorized workflow

**Resolution**:
- Verify `repo-owner` and `repo-name` inputs are correct
- Do not use artifacts from untrusted sources

## Integration Examples

### Terraform Plan Workflow

```yaml
jobs:
  terraform-plan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Download artifacts
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh run download ${{ inputs.render_run_id }} --name terraform-tfvars --dir artifacts/tfvars

      - name: Verify artifact attestations
        uses: ./.github/actions/verify-attestation
        with:
          artifact-path: 'artifacts/tfvars/*.json'
          environment: 'prod'

      - name: Terraform Plan
        working-directory: terraform
        run: |
          terraform plan -var-file="../artifacts/tfvars/site-production.tfvars.json"
```

### Development Workflow

```yaml
jobs:
  test-plan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Generate test artifacts (local)
        run: |
          mkdir -p artifacts/tfvars
          echo '{}' > artifacts/tfvars/test.tfvars.json

      - name: Verify artifact attestations (dev bypass)
        uses: ./.github/actions/verify-attestation
        with:
          artifact-path: 'artifacts/tfvars/*.json'
          environment: 'dev'
          allow-bypass: 'true'

      - name: Test Terraform Plan
        working-directory: terraform
        run: |
          terraform plan -var-file="../artifacts/tfvars/test.tfvars.json"
```

## Security Considerations

### Trust Boundary Contract

The attestation gate implements the trust boundary contract defined in [docs/phase3/terraform-boundary.md](../phase3/terraform-boundary.md):

**Terraform MUST only consume attested artifacts.**

This gate enforces that contract by:
- Failing closed in production (no bypass allowed)
- Requiring valid attestations before artifacts can be used
- Verifying cryptographic integrity of artifacts
- Providing audit trail of all verification attempts

### Production vs Development

| Aspect | Production | Development |
|--------|-----------|-------------|
| Attestation Required | ✅ Always | ⚠️ Optional with explicit bypass |
| Bypass Allowed | ❌ Never | ✅ With `allow-bypass: 'true'` |
| Failure Behavior | 🛑 Stop workflow | 🛑 Stop workflow (unless bypassed) |
| Use Case | All production deployments | Local testing, development, CI experiments |

### When to Use Bypass

Bypass should **ONLY** be used for:

✅ **Appropriate Uses**:
- Local development testing with mock artifacts
- CI pipeline development and debugging
- Unit testing of workflows that consume artifacts
- Experiments with new artifact formats

❌ **NEVER Use Bypass For**:
- Production deployments
- Staging environments that mirror production
- Any workflow that applies infrastructure changes
- Workflows that affect customer-facing systems

### Audit and Compliance

The attestation gate provides audit trails through:

1. **GitHub Actions Logs**: Every verification attempt is logged with artifact paths, digests, and results
2. **Step Outputs**: `verified-count`, `failed-count`, and `bypassed` outputs can be used for reporting
3. **GitHub Summary**: Verification results are visible in workflow summaries
4. **Exit Codes**: Failures are clearly indicated with non-zero exit codes

To review attestation verification history:
```bash
# List all workflow runs that used attestation verification
gh run list --workflow terraform-plan.yaml

# View logs for specific run
gh run view <run-id> --log
```

## Troubleshooting

### Action fails with "No files found"

**Problem**: The glob pattern doesn't match any files

**Solution**:
1. Check the artifact download step completed successfully
2. Verify the path uses the correct relative path from workflow root
3. Test the glob pattern: `ls -la artifacts/tfvars/*.json`

### Action fails with "Invalid environment"

**Problem**: Environment input is not 'prod' or 'dev'

**Solution**: Set `environment: 'prod'` or `environment: 'dev'` in the action inputs

### Verification passes but should fail

**Problem**: Expecting artifacts to be verified but bypass is enabled

**Solution**: Check that either:
- `environment: 'prod'` is set (bypass is ignored), OR
- `allow-bypass: 'false'` is set (default)

### Need to check attestation manually

To manually verify an artifact outside the action:

```bash
# Download artifact
gh run download <run-id> --name terraform-tfvars --dir artifacts

# Verify attestation
gh attestation verify artifacts/tfvars/site-production.tfvars.json \
  --owner harris-boyce \
  --repo boycivenga-iac
```

## References

- **Implementation**: `.github/actions/verify-attestation/action.yml`
- **Trust Boundary**: [docs/phase3/terraform-boundary.md](../phase3/terraform-boundary.md)
- **Attestation**: [docs/phase3/attestation.md](../phase3/attestation.md)
- **SLSA Provenance**: https://slsa.dev/provenance/
- **GitHub Attestations**: https://docs.github.com/en/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds

## Maintenance

### Updating the Action

When modifying the attestation gate:

1. Update `.github/actions/verify-attestation/action.yml`
2. Update this documentation (`docs/phase4/attestation-gate.md`)
3. Test changes in a dev workflow first
4. Update all workflows that use the action if inputs changed
5. Document breaking changes in PR description

### Version Management

The action is used with a relative path (`./.github/actions/verify-attestation`), so it always uses the version from the current branch/commit. This means:

- ✅ Changes take effect immediately when merged
- ✅ No version pinning needed
- ⚠️ Test thoroughly before merging changes
- ⚠️ Breaking changes affect all workflows immediately

## Future Enhancements

Potential improvements for future phases:

- **Policy-as-Code**: Support for custom verification policies (e.g., require specific workflow)
- **Multiple Repositories**: Verify artifacts from multiple source repositories
- **Attestation Cache**: Cache verification results to speed up repeated verifications
- **Custom Verification Logic**: Support for additional verification steps beyond SLSA provenance
- **Detailed Reports**: Generate JSON/HTML reports of verification results
- **Slack/Teams Notifications**: Alert on verification failures
