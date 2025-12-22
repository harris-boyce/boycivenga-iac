---
name: Terraform Plan Request
about: Request Terraform plan execution for rendered artifacts
title: 'Terraform Plan: [Site Name or "All Sites"]'
labels: terraform, infrastructure
---

## Terraform Plan Request

This PR requests Terraform plan execution for the rendered artifacts from a specific render workflow run.

### Render Artifacts Source

**Render Run ID:** <!-- Replace with the workflow run ID from render-artifacts workflow -->

Or provide the full workflow run URL:
**Render Run:** <!-- https://github.com/harris-boyce/boycivenga-iac/actions/runs/XXXXXXXXXX -->

### Sites to Plan

- [ ] All sites
- [ ] Specific site: <!-- pennington / countfleetcourt -->

### Changes Overview

<!-- Describe what infrastructure changes are expected from this plan -->

### Checklist

Before requesting approval:

- [ ] I have verified the render artifacts workflow completed successfully
- [ ] I have reviewed the rendered tfvars files from the specified run
- [ ] I understand that approving this PR will trigger Terraform plan execution
- [ ] I have verified the render run ID is correct and traceable
- [ ] This PR references attested artifacts from the official render pipeline

### Approval Requirements

**Note:** Terraform plan will automatically execute when this PR is approved by a repository maintainer.

The workflow will:
1. Extract the render run ID from this PR description
2. Download the attested artifacts from the specified workflow run
3. Verify artifact attestations (SLSA provenance)
4. Execute Terraform plan for the specified sites
5. Record full traceability: PR number, approver, artifact source, plan results

### Security & Compliance

- ✅ Uses attested artifacts only
- ✅ Enforces PR approval gate
- ✅ Full audit trail maintained
- ✅ Cannot be triggered by branch push

See [docs/phase4/security.md](../../docs/phase4/security.md) for complete security documentation.
