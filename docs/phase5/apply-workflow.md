# Terraform Apply Workflow (CI-Only)

## Overview

The Terraform Apply workflow is a **CI-only** workflow that enforces strict security boundaries and policy gates before applying infrastructure changes. This workflow implements a fail-closed model where any security violation or missing approval blocks execution.

**Workflow File**: `.github/workflows/terraform-apply.yaml`

**Key Principle**: Apply operations are ONLY permitted in GitHub Actions after successful policy evaluation. Manual or local execution is impossible.

## Table of Contents

- [Security Boundaries](#security-boundaries)
- [Workflow Architecture](#workflow-architecture)
- [Triggering Apply](#triggering-apply)
- [Pre-Apply Verification](#pre-apply-verification)
- [Apply Execution](#apply-execution)
- [Fail-Closed Behavior](#fail-closed-behavior)
- [Traceability](#traceability)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Explicit Non-Goals](#explicit-non-goals)

---

## Security Boundaries

The Terraform Apply workflow enforces multiple security boundaries:

### 1. CI-Only Execution Boundary

**Enforcement**: The workflow ONLY runs in GitHub Actions.

| Allowed | Prohibited |
|---------|------------|
| ✅ GitHub Actions workflow_dispatch | ❌ Local terraform apply |
| ✅ CI environment with audit trail | ❌ Manual execution outside CI |
| ✅ Controlled GitHub Actions environment | ❌ Alternative CI/CD systems |

**Why**: CI-only execution ensures:
- Complete audit trail of all infrastructure changes
- Consistent security controls applied to all applies
- No opportunity for unauthorized local modifications
- Integration with GitHub's security and compliance features

### 2. Policy Gate Boundary

**Enforcement**: Apply ONLY runs after successful policy evaluation in the plan workflow.

The workflow requires:
- ✅ Valid plan workflow run ID
- ✅ Plan workflow completed successfully
- ✅ Policy evaluation passed in plan workflow
- ✅ Policy re-evaluation passes in apply workflow

**Why**: Policy gates ensure:
- All changes reviewed against organizational policies
- Destructive changes require explicit approval
- Attestation requirements enforced
- No bypass of security checks

### 3. Attestation Re-Verification Boundary

**Enforcement**: All artifacts MUST be re-verified before apply.

The workflow re-verifies:
- ✅ tfvars artifact attestations (using verify-attestation action)
- ✅ Plan file integrity (checksum verification)
- ✅ Plan and artifact consistency

**Why**: Re-verification ensures:
- Artifacts have not been tampered with between plan and apply
- Plan files match the approved plan
- Complete chain of custody maintained
- Trust boundary contract upheld

### 4. Fail-Closed Boundary

**Enforcement**: Any security violation causes immediate workflow failure.

The workflow fails on:
- ❌ Missing or invalid plan run ID
- ❌ Plan workflow not completed successfully
- ❌ Failed attestation verification
- ❌ Failed policy evaluation
- ❌ Missing plan artifacts
- ❌ Plan file integrity check failure

**Why**: Fail-closed behavior ensures:
- No silent security failures
- Explicit investigation required for failures
- No accidental bypasses
- Security-first approach

---

## Workflow Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Terraform Apply Workflow                  │
│                        (CI-Only)                             │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Job 1: Validate Inputs                                       │
│  ✓ Validate plan_run_id (numeric, exists)                   │
│  ✓ Validate site name (alphanumeric)                        │
│  ✓ Validate pr_number (numeric)                             │
│  ✓ Verify plan workflow completed successfully              │
│  ✓ Verify workflow is terraform-plan                        │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Job 2: Terraform Apply                                       │
│                                                              │
│  Step 1: Download Plan Artifacts                            │
│   ✓ Download terraform-tfvars from plan run                 │
│   ✓ Download terraform-plan-{site} from plan run            │
│                                                              │
│  Step 2: Re-verify Attestations (MANDATORY)                 │
│   ✓ Re-verify tfvars attestation with verify-attestation    │
│   ✓ Verify plan file integrity (checksums)                  │
│                                                              │
│  Step 3: Re-evaluate Policy (MANDATORY)                     │
│   ✓ Install OPA (same version as plan workflow)             │
│   ✓ Re-evaluate policy against plan JSON                    │
│   ✓ Fail if policy no longer passes                         │
│                                                              │
│  Step 4: Apply Terraform Plan                               │
│   ✓ Initialize Terraform                                    │
│   ✓ Apply binary plan file                                  │
│   ✓ Record apply metadata                                   │
│                                                              │
│  Step 5: Record Metadata                                    │
│   ✓ Record apply run ID                                     │
│   ✓ Record plan run ID reference                            │
│   ✓ Record checksums and verification status                │
│   ✓ Upload metadata artifact (90-day retention)             │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Job 3: Apply Summary                                         │
│  ✓ Generate comprehensive summary                           │
│  ✓ Document security verification results                   │
│  ✓ Provide traceability links                               │
└─────────────────────────────────────────────────────────────┘
```

### Jobs

#### 1. validate-inputs

**Purpose**: Validate all workflow inputs before proceeding.

**Validations**:
- Plan run ID is numeric and valid
- Site name is alphanumeric (prevents injection attacks)
- PR number is numeric
- Plan workflow exists and completed successfully
- Plan workflow is the correct workflow (terraform-plan)

**Outputs**: Validated inputs for use in subsequent jobs

#### 2. terraform-apply

**Purpose**: Execute the terraform apply with full security verification.

**Environment**: Uses GitHub environment `production-{site}` for additional protection layer

**Steps**:
1. Download artifacts from plan run
2. Re-verify attestations
3. Re-evaluate policy
4. Apply terraform plan
5. Record metadata

**Key Security Features**:
- Uses `.github/actions/verify-attestation` for mandatory attestation verification
- Re-runs OPA policy evaluation to catch any tampering
- Verifies plan file integrity with checksums
- Records complete audit trail

#### 3. apply-summary

**Purpose**: Generate comprehensive summary and documentation.

**Always Runs**: Even if apply fails, summary provides debugging information

---

## Triggering Apply

### Prerequisites

Before triggering apply, you must have:

1. ✅ **Successful terraform-plan workflow run**
   - Workflow must have completed successfully
   - Policy evaluation must have passed
   - Plan artifacts must be available

2. ✅ **Approved PR**
   - PR must be approved by authorized reviewer
   - PR must reference the render artifacts run

3. ✅ **Valid plan artifacts**
   - Binary plan file (`tfplan-{site}.binary`)
   - JSON plan file (`tfplan-{site}.json`)
   - Attested tfvars file (`site-{site}.tfvars.json`)

### Trigger Method

**ONLY Method**: Manual workflow dispatch via GitHub Actions UI

**Required Inputs**:
- `plan_run_id`: The terraform-plan workflow run ID (must be successful)
- `site`: The site to apply (must have a plan artifact in the run)
- `pr_number`: The PR number for traceability

### Steps to Trigger

1. **Navigate to Actions**
   - Go to GitHub repository → Actions tab
   - Select "Terraform Apply (CI-Only)" workflow

2. **Click "Run workflow"**
   - Click the "Run workflow" dropdown button

3. **Fill in Required Inputs**
   ```
   plan_run_id: 1234567890
   site: pennington
   pr_number: 42
   ```

4. **Review and Confirm**
   - Double-check the plan run ID
   - Verify the site name matches available plans
   - Confirm the PR number is correct

5. **Click "Run workflow"**
   - Workflow will start immediately
   - Input validation runs first
   - Apply proceeds only if all validations pass

### Finding Plan Run ID

To find the plan run ID:

1. Go to Actions → Terraform Plan workflow
2. Find the successful run for your PR
3. Copy the run ID from the URL: `https://github.com/owner/repo/actions/runs/<RUN_ID>`
4. Verify the run shows "Policy evaluation PASSED"

---

## Pre-Apply Verification

The workflow performs comprehensive verification before applying changes:

### Input Validation

```bash
✓ plan_run_id is numeric
✓ site is alphanumeric (prevents injection)
✓ pr_number is numeric
✓ Plan workflow exists
✓ Plan workflow completed successfully
✓ Plan workflow is "Terraform Plan"
```

### Artifact Verification

```bash
✓ terraform-tfvars artifact downloaded
✓ terraform-plan-{site} artifact downloaded
✓ Binary plan file exists
✓ JSON plan file exists
✓ File checksums calculated
```

### Attestation Re-Verification

```bash
✓ tfvars attestation verified with verify-attestation action
✓ Attestation is from trusted workflow
✓ Artifact has not been modified
✓ Complete provenance chain validated
```

**Implementation**: Uses `.github/actions/verify-attestation` in production mode
- Cannot be bypassed
- Fails workflow on verification failure
- See [docs/phase4/attestation-gate.md](../phase4/attestation-gate.md) for details

### Policy Re-Evaluation

```bash
✓ OPA installed (same version as plan workflow)
✓ Policy bundle loaded from .github/policies/
✓ Policy input document created
✓ Policy evaluation executed
✓ Policy still passes (no tampering detected)
```

**Why Re-Evaluate?**
- Detects any tampering with plan files
- Ensures policy rules haven't changed between plan and apply
- Provides defense-in-depth security
- Maintains fail-closed behavior

---

## Apply Execution

### Terraform Initialization

The workflow initializes Terraform with:
- Same provider configuration as plan workflow
- Same backend configuration
- Ensures consistent state

### Apply Operation

```bash
terraform apply -auto-approve <plan-file>
```

**Why `-auto-approve` is Safe**:
- Applying a **specific binary plan file**
- Plan has already been reviewed and approved
- Plan passed policy evaluation
- Artifacts verified and re-verified
- Complete audit trail exists

**NOT Using**: Interactive approval or creating a new plan

### Provider Configuration

**Current**: Stub credentials for demonstration

**Production**: Configure real credentials using:
- GitHub Actions secrets
- OIDC authentication with cloud provider
- Secure credential management

Example for production:
```yaml
- name: Configure Terraform provider (production)
  run: |
    echo "TF_VAR_unifi_username=${{ secrets.UNIFI_USERNAME }}" >> $GITHUB_ENV
    echo "TF_VAR_unifi_password=${{ secrets.UNIFI_PASSWORD }}" >> $GITHUB_ENV
    echo "TF_VAR_unifi_api_url=${{ secrets.UNIFI_API_URL }}" >> $GITHUB_ENV
```

---

## Fail-Closed Behavior

The workflow implements strict fail-closed behavior:

### Failure Conditions

| Condition | Result | Recovery |
|-----------|--------|----------|
| Invalid plan run ID | ❌ Immediate failure | Provide valid plan run ID |
| Plan workflow not successful | ❌ Immediate failure | Run successful plan workflow |
| Wrong workflow type | ❌ Immediate failure | Use terraform-plan workflow |
| Attestation verification failed | ❌ Immediate failure | Investigate artifact tampering |
| Policy re-evaluation failed | ❌ Immediate failure | Investigate plan changes |
| Missing artifacts | ❌ Immediate failure | Verify plan workflow completion |
| Plan integrity check failed | ❌ Immediate failure | Investigate plan tampering |
| Terraform apply failed | ❌ Failure (configurable) | Investigate terraform errors |

### No Bypass Mechanisms

**Intentionally NOT Supported**:
- ❌ Emergency override flag
- ❌ Dev mode bypass
- ❌ Skip attestation verification
- ❌ Skip policy evaluation
- ❌ Force apply flag

**Why**: Security and compliance requirements mandate that ALL applies:
- Follow the same process
- Have complete audit trail
- Pass all security checks
- Cannot be bypassed

**Emergency Situations**: If an emergency truly requires bypass:
1. Document the emergency situation
2. Create an incident report
3. Follow organization's emergency change process
4. Consider creating a separate emergency workflow with appropriate controls

---

## Traceability

The workflow maintains complete traceability:

### Apply Metadata

Recorded for every apply:

```json
{
  "apply_run_id": "9876543210",
  "plan_run_id": "1234567890",
  "site": "pennington",
  "pr_number": "42",
  "applied_by": "username",
  "applied_at": "2024-01-15T12:00:00Z",
  "binary_checksum": "abc123...",
  "json_checksum": "def456...",
  "attestation_verified": true,
  "policy_result": "pass",
  "apply_status": "success"
}
```

**Retention**: 90 days (configurable)

### Audit Trail

Complete chain from intent to deployment:

```
NetBox Intent
    ↓
Render Artifacts Workflow (attested)
    ↓
Pull Request (with render run reference)
    ↓
PR Approval
    ↓
Terraform Plan Workflow (policy evaluation)
    ↓
Plan Artifacts (with checksums)
    ↓
Terraform Apply Workflow (re-verification)
    ↓
Applied Infrastructure Changes
```

### GitHub Integration

Traceability links provided in workflow summary:
- Link to PR
- Link to plan workflow run
- Link to apply workflow run
- Link to render artifacts workflow run
- Actor who triggered apply
- Timestamps for all operations

---

## Usage Examples

### Example 1: Apply Single Site

After successful plan workflow run 1234567890 for PR #42:

1. **Navigate to Actions → Terraform Apply (CI-Only)**

2. **Click "Run workflow"**

3. **Enter inputs**:
   ```
   plan_run_id: 1234567890
   site: pennington
   pr_number: 42
   ```

4. **Click "Run workflow"**

5. **Monitor execution**:
   - Input validation: ~10 seconds
   - Artifact download: ~30 seconds
   - Attestation verification: ~20 seconds
   - Policy re-evaluation: ~15 seconds
   - Terraform apply: varies by plan size

6. **Review results**:
   - Check workflow summary for status
   - Review apply metadata artifact
   - Verify infrastructure changes

### Example 2: Apply Multiple Sites

To apply to multiple sites from the same plan run:

**Important**: Run applies **sequentially**, not in parallel, to avoid:
- State locking conflicts
- Race conditions
- Unclear audit trail

For each site:
1. Trigger apply workflow with site-specific inputs
2. Wait for completion
3. Review results before proceeding to next site

Example sequence:
```
Apply pennington (plan_run_id: 1234567890, site: pennington, pr_number: 42)
  ↓ [wait for completion]
Apply countfleetcourt (plan_run_id: 1234567890, site: countfleetcourt, pr_number: 42)
  ↓ [wait for completion]
```

### Example 3: Verifying Apply Success

After apply completes:

1. **Check workflow summary**
   - Verify "Apply Status: success"
   - Review security verification section

2. **Download apply metadata**
   - Go to workflow run artifacts
   - Download `terraform-apply-metadata-{site}`
   - Review JSON for complete details

3. **Verify infrastructure**
   - Check actual infrastructure (e.g., UniFi controller)
   - Verify changes match plan
   - Confirm no unexpected changes

4. **Update documentation**
   - Link apply run in deployment log
   - Update change management records
   - Close related tickets/issues

---

## Troubleshooting

### Issue: "Plan workflow not completed successfully"

**Cause**: The referenced plan workflow did not complete with status "success"

**Resolution**:
1. Check the plan workflow run status
2. If failed, investigate and fix the issue
3. Run a new plan workflow
4. Use the new plan run ID for apply

### Issue: "Failed to download artifacts"

**Cause**: Artifacts not available from plan workflow

**Possible Causes**:
- Plan workflow did not complete successfully
- Artifacts expired (30-day retention by default)
- Site name mismatch
- Wrong plan run ID

**Resolution**:
1. Verify plan run ID is correct
2. Check artifact retention period
3. Verify site name matches plan artifacts
4. Run new plan workflow if artifacts expired

### Issue: "Attestation verification failed"

**Cause**: Artifact attestation could not be verified

**Possible Causes**:
- Artifact not attested (render workflow issue)
- Artifact modified after attestation (security violation)
- Attestation signature invalid

**Resolution**:
1. **DO NOT BYPASS** - This is a security boundary
2. Investigate why attestation failed
3. Regenerate artifacts from render workflow
4. Run new plan workflow
5. Use new plan run ID for apply

### Issue: "Policy re-evaluation failed"

**Cause**: Plan no longer passes policy evaluation

**Possible Causes**:
- Plan file tampered with
- Policy rules changed between plan and apply
- Metadata inconsistency

**Resolution**:
1. **DO NOT PROCEED** - This indicates potential tampering
2. Compare plan checksums with original
3. Review policy changes (if any)
4. Regenerate plan if necessary
5. Investigate security incident if tampering suspected

### Issue: "Terraform apply failed"

**Cause**: Terraform apply operation failed

**In Stub Mode**: Expected - no real credentials configured

**In Production**:
1. Check terraform error message
2. Verify provider credentials
3. Check provider connectivity
4. Review terraform state
5. Investigate infrastructure issues

**Resolution**:
1. Fix underlying issue
2. Do NOT re-run apply with same plan if:
   - Infrastructure partially applied
   - State is inconsistent
3. Run new plan workflow to assess current state
4. Use new plan for corrective apply

### Issue: "Wrong workflow type"

**Cause**: Provided run ID is not from terraform-plan workflow

**Resolution**:
1. Verify you're using the correct workflow run ID
2. Use run ID from "Terraform Plan" workflow, not other workflows
3. Check workflow name in Actions UI

---

## Explicit Non-Goals

The following are **intentionally NOT supported** in this workflow:

### 1. Emergency Override

**Not Supported**: Emergency bypass flag or override mechanism

**Reasoning**:
- Security boundaries must always be enforced
- No emergency is urgent enough to skip security checks
- Bypasses create security vulnerabilities
- Complete audit trail is mandatory

**Alternative**: If true emergencies require faster processes:
- Create separate emergency change workflow with appropriate controls
- Document emergency procedures
- Require post-emergency review

### 2. Dev Mode Bypass

**Not Supported**: Development mode that skips verification

**Reasoning**:
- All environments should follow same security process
- Dev/staging should test production workflows
- Bypasses in dev lead to production bypasses
- Consistent processes reduce errors

**Alternative**: Use test/staging environments with:
- Same workflow
- Same security controls
- Lower-impact infrastructure

### 3. Multi-Environment Apply

**Not Supported**: Single workflow handling multiple environments (dev/staging/prod)

**Reasoning**:
- Each environment should have dedicated workflow
- Environment-specific controls and approval processes
- Reduces risk of applying to wrong environment
- Clearer separation of concerns

**Alternative**: Create separate workflows:
- `terraform-apply-dev.yaml`
- `terraform-apply-staging.yaml`
- `terraform-apply-prod.yaml`

Each with environment-appropriate controls.

### 4. Local Execution

**Not Supported**: Running this workflow locally or outside GitHub Actions

**Reasoning**:
- CI-only execution is a core security boundary
- Local execution bypasses audit trail
- GitHub Actions provides secure execution environment
- Consistent environment for all applies

**Alternative**: None - this is a strict requirement

### 5. Manual Artifact Creation

**Not Supported**: Using manually created or modified artifacts

**Reasoning**:
- All artifacts must come from render pipeline
- Attestation verification enforces this
- Manual artifacts bypass authority boundary
- Cannot be trusted

**Alternative**: Always use artifacts from render and plan workflows

---

## Integration Points

### With Terraform Plan Workflow

The apply workflow depends on outputs from plan workflow:

**Required Artifacts from Plan**:
- `terraform-tfvars` bundle (attested)
- `terraform-plan-{site}` bundle per site:
  - Binary plan file
  - JSON plan file
  - Structured diff (optional, for reference)

**Required Status**: Plan workflow must complete with status "success"

**Policy Requirement**: Plan must pass policy evaluation

### With Policy Engine

The apply workflow re-evaluates policies:

**Policy Bundle**: `.github/policies/`

**Policy Rules**:
- Attestation verification
- PR approval present
- Valid provenance
- Destructive change approval (if applicable)

**OPA Version**: Must match plan workflow version (0.60.0)

**See**: [docs/phase5/policy-engine.md](policy-engine.md) for policy details

### With Attestation Gate

The apply workflow uses the attestation gate action:

**Action**: `.github/actions/verify-attestation`

**Mode**: Production (fail-closed)

**Cannot Be Bypassed**: No allow-bypass flag in apply workflow

**See**: [docs/phase4/attestation-gate.md](../phase4/attestation-gate.md) for gate details

### With GitHub Environments

The apply workflow uses GitHub environments for additional protection:

**Environment**: `production-{site}` (e.g., `production-pennington`)

**Benefits**:
- Additional approval layer (if configured)
- Environment-specific secrets
- Deployment tracking
- Environment protection rules

**Configuration**: Define in repository settings → Environments

---

## Best Practices

### 1. Verify Before Apply

Always verify before triggering apply:
- ✅ Review plan output in plan workflow summary
- ✅ Check policy evaluation passed
- ✅ Verify attestations succeeded
- ✅ Confirm expected changes match plan
- ✅ Check PR is approved
- ✅ Review structured diff

### 2. Sequential Applies

When applying to multiple sites:
- ✅ Apply to one site at a time
- ✅ Verify each apply before proceeding
- ✅ Monitor for issues
- ❌ Don't trigger multiple applies simultaneously

### 3. Record Keeping

Maintain complete records:
- ✅ Download apply metadata artifacts
- ✅ Link apply runs in change management
- ✅ Document any issues encountered
- ✅ Update infrastructure documentation
- ✅ Close related tickets

### 4. Failure Investigation

When apply fails:
- ✅ Review complete error output
- ✅ Check terraform state
- ✅ Verify infrastructure state
- ✅ Document findings
- ❌ Don't retry without understanding failure

### 5. Security Vigilance

Stay vigilant for security issues:
- ✅ Investigate any attestation failures
- ✅ Report policy evaluation failures
- ✅ Monitor for unusual patterns
- ✅ Review audit logs regularly
- ❌ Never bypass security checks

---

## Related Documentation

- [docs/phase5/policy-engine.md](policy-engine.md) - Policy engine documentation
- [docs/phase5/policy-input-contract.md](policy-input-contract.md) - Policy input format
- [docs/phase4/terraform-plan-approval-workflow.md](../phase4/terraform-plan-approval-workflow.md) - Plan approval process
- [docs/phase4/attestation-gate.md](../phase4/attestation-gate.md) - Attestation verification
- [docs/phase4/security.md](../phase4/security.md) - Complete security boundaries
- [docs/phase3/terraform-boundary.md](../phase3/terraform-boundary.md) - Trust boundary contract
- [README.md](../../README.md) - Repository overview

---

## Questions and Support

For questions or issues:

1. Check this documentation thoroughly
2. Review related documentation links above
3. Check workflow run logs for detailed error messages
4. Review troubleshooting section
5. See [CONTRIBUTING.md](../../CONTRIBUTING.md) for support channels

**Remember**: This workflow enforces security boundaries. If something is blocked, there's a security reason. Understand the reason before attempting to bypass any checks.
