# Terraform Plan Approval Workflow

## Overview

The Terraform plan workflow is approval-gated to ensure that infrastructure changes are reviewed and explicitly authorized before execution. This document describes how to request and approve Terraform plan execution.

## Key Principles

1. **PR Approval Required**: Terraform plan ONLY runs after a PR is approved
2. **Explicit Artifact Reference**: PR must specify which render artifacts run to use
3. **Full Traceability**: PR number, approver, and artifact source are recorded
4. **No Push Triggers**: Branch pushes do NOT trigger Terraform plan

## Workflow Steps

### Step 1: Identify Render Artifacts Run

First, identify the render artifacts workflow run that generated the configurations you want to plan:

1. Navigate to Actions → Render Artifacts workflow
2. Find the successful workflow run you want to use
3. Note the run ID from the URL: `https://github.com/owner/repo/actions/runs/<RUN_ID>`
4. Verify the artifacts were attested (look for attestation steps in the run)

### Step 2: Create Pull Request

Create a PR that references the render artifacts run:

**Option A: Use the PR Template**

1. Go to Pull Requests → New Pull Request
2. Select "Terraform Plan Request" template (if available)
3. Fill in the render run ID or URL
4. Describe the expected infrastructure changes

**Option B: Manual PR Creation**

Create a PR with the following format in the description:

```markdown
## Terraform Plan Request

Render Run: 1234567890

Or include the full URL:
https://github.com/harris-boyce/boycivenga-iac/actions/runs/1234567890

### Expected Changes
- VLAN updates for pennington site
- New subnet configuration
```

**Important**: The workflow will extract the render run ID using these patterns:
- `Render Run: <id>`
- `render_run_id: <id>`
- URL containing `actions/runs/<id>`

### Step 3: Review Process

The PR should be reviewed by a repository maintainer who will verify:

1. ✅ Render artifacts run completed successfully
2. ✅ Attested artifacts are available
3. ✅ Changes align with infrastructure intent in NetBox
4. ✅ Proper security controls are in place
5. ✅ No unauthorized modifications

### Step 4: Approval Triggers Plan

When a maintainer approves the PR:

1. **Automatic Trigger**: The `pull_request_review` event fires
2. **Workflow Validation**: Checks that review state is "approved"
3. **Metadata Extraction**: Extracts PR number, approver, and render run ID
4. **Artifact Download**: Downloads artifacts from the specified run
5. **Attestation Verification**: Verifies SLSA provenance (mandatory)
6. **Plan Execution**: Runs Terraform plan for specified sites
7. **Traceability Recording**: Records PR, approver, and artifact source

### Step 5: Review Plan Results

After the workflow completes:

1. View the workflow run in GitHub Actions
2. Review the plan output and structured diff
3. Check the workflow summary for:
   - Approval details (PR number, approver)
   - Artifact source (render run ID)
   - Plan results (resources to be created/modified/deleted)
4. Download plan artifacts if needed for further review

## Examples

### Example 1: Plan for All Sites

```markdown
## Terraform Plan Request

This PR requests Terraform plan execution for all sites based on the latest
NetBox export and render.

**Render Run:** https://github.com/harris-boyce/boycivenga-iac/actions/runs/1234567890

### Expected Changes
- Update VLAN configurations across all sites
- Add new management subnets
```

### Example 2: Plan for Specific Site

```markdown
## Terraform Plan Request

This PR requests Terraform plan execution for the pennington site only.

**Render Run ID:** 1234567890

### Expected Changes
- Add VLAN 200 "Guest" to pennington site
- Update DHCP range for existing VLANs
```

## Manual Dispatch (Testing Only)

For testing and development, the workflow can be manually triggered:

1. Go to Actions → Terraform Plan
2. Click "Run workflow"
3. Fill in required inputs:
   - `render_run_id`: The workflow run ID to use
   - `pr_number` (optional): For traceability
   - `site` (optional): Specific site to plan

**Note**: Manual dispatch should only be used for:
- Testing workflow changes
- Emergency situations (with proper documentation)
- Development/staging environments

## Security Guarantees

The approval-gated workflow provides:

| Guarantee | Implementation |
|-----------|----------------|
| **No unauthorized execution** | Only approved PRs trigger workflow |
| **Artifact traceability** | Render run ID explicitly referenced |
| **Full audit trail** | PR, approver, and timestamps recorded |
| **Attestation enforcement** | All artifacts verified before use |
| **No push bypass** | Branch pushes cannot trigger plans |
| **Access control** | GitHub PR approval permissions required |

## Troubleshooting

### Issue: "Could not find render run ID in PR description"

**Solution**: Ensure your PR description contains one of these formats:
- `Render Run: 1234567890`
- `render_run_id: 1234567890`
- Link with `actions/runs/1234567890`

### Issue: "Workflow did not trigger after approval"

**Solution**: Check that:
1. The PR review state is "approved" (not "commented" or "changes requested")
2. The workflow file is on the base branch
3. GitHub Actions has permissions to run workflows

### Issue: "Failed to download artifacts"

**Solution**: Verify:
1. The render run ID is correct
2. The render workflow completed successfully
3. Artifacts have not expired (30-day retention)
4. The workflow has `actions: read` permission

### Issue: "Attestation verification failed"

**Solution**: This indicates:
1. Artifacts are not attested (render workflow issue)
2. Artifacts have been modified (security violation)
3. Attestation signature is invalid

**Action**: Do NOT bypass verification. Investigate the root cause and regenerate artifacts.

## Best Practices

1. **Always reference specific render runs** - Don't use "latest" or ambiguous references
2. **Review artifacts before approval** - Download and inspect tfvars files
3. **Document expected changes** - Help reviewers understand the plan
4. **Verify attestations** - Ensure artifacts come from trusted source
5. **Keep PRs focused** - One render run per PR for clear traceability
6. **Archive plan results** - Download plan artifacts for records

## Related Documentation

- [docs/phase4/security.md](security.md) - Complete security boundaries
- [docs/phase3/terraform-boundary.md](../phase3/terraform-boundary.md) - Trust boundary contract
- [docs/phase4/attestation-gate.md](attestation-gate.md) - Attestation verification
- [docs/render-pipeline.md](../render-pipeline.md) - Render artifacts workflow
- [README.md](../../README.md) - Repository overview

## Questions?

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for contributor guidelines and support.
