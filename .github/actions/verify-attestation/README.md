# Verify Attestation Action

A composite GitHub Action that verifies artifact attestations with fail-closed behavior in production environments.

## Quick Start

```yaml
- name: Verify artifact attestations
  uses: ./.github/actions/verify-attestation
  with:
    artifact-path: 'artifacts/tfvars/*.json'
```

## Documentation

See [docs/phase4/attestation-gate.md](../../../docs/phase4/attestation-gate.md) for complete documentation including:

- Usage examples
- Input/output reference
- Error scenarios and troubleshooting
- Security considerations
- Integration patterns

## Basic Examples

### Production (Fail Closed - Default)

```yaml
- uses: ./.github/actions/verify-attestation
  with:
    artifact-path: 'artifacts/tfvars/*.json'
    environment: 'prod'  # Optional, this is the default
```

### Development (With Bypass)

```yaml
- uses: ./.github/actions/verify-attestation
  with:
    artifact-path: 'artifacts/tfvars/*.json'
    environment: 'dev'
    allow-bypass: 'true'
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `artifact-path` | Yes | - | Path or glob pattern to artifacts |
| `environment` | No | `prod` | `prod` (fail-closed) or `dev` (allow bypass) |
| `allow-bypass` | No | `false` | Allow bypass (only in dev mode) |

## Outputs

| Output | Description |
|--------|-------------|
| `verified-count` | Number of artifacts verified |
| `failed-count` | Number of artifacts that failed |
| `bypassed` | Whether verification was bypassed |

## Features

- ✅ **Fail-closed by default** - Production always requires valid attestations
- ✅ **Explicit dev bypass** - Development can skip verification with clear audit trail
- ✅ **Glob pattern support** - Verify multiple files with patterns like `*.json`
- ✅ **Detailed logging** - Clear error messages for debugging
- ✅ **SLSA provenance** - Verifies cryptographic integrity using GitHub attestations
