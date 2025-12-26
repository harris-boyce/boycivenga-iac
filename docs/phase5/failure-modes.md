# Failure Modes & Tech Debt

## Overview

This document captures the known limitations, failure modes, emergency recovery gaps, and technical debt related to the policy, approval, and apply workflows in this infrastructure-as-code repository. The purpose is to surface risks that are not hidden, enabling informed decision-making and preparing for future emergency workflows.

**Status**: Active Documentation

**Last Updated**: Phase 5

**Document Version**: 1.0.0

**Explicit Non-Goals**: This document does NOT include implementation of break-glass workflows or automated recovery mechanisms. Those are intentionally deferred to future phases.

## Table of Contents

- [Emergency Override Gaps](#emergency-override-gaps)
- [Manual Recovery Situations](#manual-recovery-situations)
- [Known Limitations](#known-limitations)
- [Policy Engine Risks](#policy-engine-risks)
- [Attestation & Provenance Risks](#attestation--provenance-risks)
- [Apply Workflow Risks](#apply-workflow-risks)
- [Technical Debt](#technical-debt)
- [Mitigation Strategies](#mitigation-strategies)
- [Future Work](#future-work)

---

## Emergency Override Gaps

This section documents situations where emergency override mechanisms do NOT exist, creating potential operational challenges during incidents.

### 1. No Break-Glass Workflow

**Gap**: No emergency workflow exists to bypass policy evaluation, attestation verification, or approval gates during critical outages.

**Impact**: During a critical infrastructure outage requiring immediate remediation, the standard workflow enforces:
- PR approval gate (requires reviewer availability)
- Policy evaluation (must pass OPA rules)
- Attestation verification (requires artifacts from render pipeline)
- Human approval for destructive changes (requires reviewer action)

**Risk Level**: **HIGH** - Critical incidents may require infrastructure changes faster than standard approval workflows permit.

**Example Scenario**:
```
Time: 2:00 AM Saturday
Situation: Critical routing misconfiguration causing complete network outage
Problem:
  - Standard workflow requires PR approval from maintainer
  - Maintainer is asleep and unreachable
  - Changes require going through full render → plan → approve → apply cycle
  - Estimated time to recovery: 2-4 hours
  - Business impact: All services down
```

**Current Workaround**: NONE - System enforces all gates with no bypass mechanism.

**Documentation Reference**:
- [docs/phase5/apply-workflow.md](apply-workflow.md#explicit-non-goals) explicitly states emergency overrides are NOT supported
- [docs/phase5/policy-engine.md](policy-engine.md#explicit-non-goals) confirms no emergency bypass

---

### 2. No Policy Override Mechanism

**Gap**: Policy evaluation failures cannot be overridden, even with explicit operator acknowledgment.

**Impact**: If OPA policy rules produce false positives or become overly restrictive, there is no mechanism to override the policy decision with human judgment.

**Risk Level**: **MEDIUM** - Policy false positives could block legitimate changes.

**Example Scenario**:
```
Situation: Policy rule incorrectly flags a safe configuration change as destructive
Problem:
  - Policy evaluation fails with "Destructive changes detected"
  - The change is actually safe (false positive in policy logic)
  - No override flag or manual approval can bypass the policy failure
  - Must fix policy code and re-run entire workflow
  - Time to deploy: Hours or days
```

**Current Workaround**: Must modify `.github/policies/terraform_plan.rego` to fix policy logic, commit, and re-run workflow.

**Documentation Reference**: [docs/phase5/policy-engine.md](policy-engine.md#explicit-non-goals)

---

### 3. No Attestation Bypass

**Gap**: Failed attestation verification cannot be bypassed, even when artifact integrity is verified through other means.

**Impact**: If attestation infrastructure fails (e.g., GitHub attestation service outage), infrastructure deployments are completely blocked.

**Risk Level**: **MEDIUM** - Dependent on GitHub's attestation service availability.

**Example Scenario**:
```
Situation: GitHub attestation service experiencing outage
Problem:
  - Render pipeline cannot attest artifacts
  - Plan workflow cannot verify attestations
  - All infrastructure deployments blocked
  - No bypass mechanism exists
  - Must wait for GitHub service recovery
```

**Current Workaround**: NONE - Attestation verification is mandatory in production mode.

**Documentation Reference**:
- [docs/phase4/attestation-gate.md](../phase4/attestation-gate.md)
- [docs/phase5/apply-workflow.md](apply-workflow.md#attestation-re-verification-boundary)

---

### 4. No Manual Artifact Creation

**Gap**: Cannot manually create or modify artifacts to work around render pipeline failures.

**Impact**: If NetBox is unavailable or the render pipeline is broken, cannot generate Terraform configurations manually.

**Risk Level**: **MEDIUM** - Dependent on NetBox availability and render pipeline health.

**Example Scenario**:
```
Situation: NetBox database corruption or API outage
Problem:
  - Cannot export data from NetBox
  - Render pipeline cannot generate artifacts
  - Cannot manually create tfvars files (violates authority boundary)
  - All infrastructure changes blocked until NetBox restored
```

**Current Workaround**: NONE - Manual artifacts violate the authority boundary (NetBox is sole source of truth).

**Documentation Reference**: [docs/phase4/security.md](../phase4/security.md#authority-boundaries)

---

### 5. No Local Execution Option

**Gap**: Terraform cannot be run locally, even for troubleshooting or emergency recovery.

**Impact**: During GitHub Actions outages or CI/CD issues, cannot deploy infrastructure changes using local Terraform execution.

**Risk Level**: **MEDIUM** - Dependent on GitHub Actions availability.

**Example Scenario**:
```
Situation: GitHub Actions experiencing extended outage
Problem:
  - Cannot run workflows
  - No local execution permitted (violates execution boundary)
  - Infrastructure changes completely blocked
  - Must wait for GitHub service recovery
```

**Current Workaround**: NONE - Local execution is explicitly prohibited.

**Documentation Reference**: [docs/phase4/security.md](../phase4/security.md#execution-boundaries)

---

## Manual Recovery Situations

This section describes situations that require manual intervention outside the automated workflows.

### 1. State File Corruption

**Situation**: Terraform state file becomes corrupted or inconsistent.

**Manual Steps Required**:
1. Access the Terraform backend (location depends on backend configuration)
2. Create backup of current state file
3. Manually inspect and repair state JSON
4. Test with `terraform state list` and `terraform plan`
5. Restore corrected state to backend
6. Re-run plan workflow to verify consistency

**Tools Required**:
- Direct access to Terraform backend (S3, local file, etc.)
- JSON editing tools
- Terraform CLI (must be run locally, violating execution boundary)

**Risk**: State corruption could cause terraform to believe resources don't exist, leading to attempted duplicate creation or deletion.

**Documentation Gap**: No documented procedure for state file recovery.

---

### 2. Partial Apply Failure

**Situation**: Terraform apply fails midway through execution, leaving infrastructure in an inconsistent state.

**Manual Steps Required**:
1. Access workflow logs to identify which resources were applied
2. Manually verify infrastructure state
3. Compare actual state with Terraform state file
4. May need to manually import or remove resources from state:
   ```bash
   # These commands violate execution boundary (local execution prohibited)
   terraform state rm 'resource.name'
   terraform import 'resource.name' 'resource-id'
   ```
5. Run new plan workflow to assess current state
6. Decide whether to proceed or roll back manually

**Risk**: Infrastructure and state divergence can cause subsequent plans to be incorrect.

**Documentation Gap**: No documented procedure for recovering from partial apply failures.

---

### 3. Approval Metadata Corruption

**Situation**: Approval metadata artifacts are missing, corrupted, or contain incorrect data.

**Manual Steps Required**:
1. Download plan artifacts from workflow run
2. Inspect `tfplan-{site}-approval.json` file
3. Identify corruption or missing data
4. Cannot manually fix (artifact attestation would fail)
5. Must re-run plan workflow to regenerate metadata

**Risk**: Incorrect approval metadata could route apply to wrong environment (protected vs. unprotected).

**Documentation Gap**: No validation or verification of approval metadata integrity.

---

### 4. Policy Logic Errors

**Situation**: Policy rules contain bugs that block legitimate changes or allow dangerous changes.

**Manual Steps Required**:
1. Identify policy issue by reviewing OPA evaluation output
2. Download policy input JSON from workflow artifacts
3. Test policy locally with `opa eval`:
   ```bash
   opa eval --bundle .github/policies/ --input test-input.json 'data.terraform.plan.allow'
   ```
4. Fix policy logic in `.github/policies/terraform_plan.rego`
5. Commit policy changes
6. Re-run plan workflow with fixed policy

**Risk**: Policy bugs could block all infrastructure changes or allow dangerous changes to proceed.

**Documentation Gap**: No policy testing framework or automated validation.

---

### 5. Artifact Expiration

**Situation**: Plan artifacts expire (default 30-day retention) before apply is executed.

**Manual Steps Required**:
1. Verify artifacts are no longer available in workflow run
2. Check if infrastructure state has changed since plan was created
3. Must run completely new render → plan cycle
4. Cannot reuse expired plan

**Risk**: Long delays between plan and apply could result in stale plans that don't reflect current state.

**Documentation Gap**: No alerting or notification when artifacts are approaching expiration.

---

### 6. GitHub Environment Misconfiguration

**Situation**: GitHub Environment protection rules are misconfigured (wrong reviewers, missing environment, etc.).

**Manual Steps Required**:
1. Go to repository Settings → Environments
2. Verify environment exists: `production-{site}-protected`
3. Check required reviewers are configured
4. Add/remove reviewers as needed
5. Verify deployment branch rules (if any)
6. Test by triggering apply workflow

**Risk**: Misconfigured environments could:
- Block all applies (no authorized reviewers)
- Allow unauthorized applies (no protection rules)
- Route to wrong environment

**Documentation Gap**: No automated validation of environment configuration.

---

## Known Limitations

This section documents inherent limitations in the current implementation.

### 1. Single Approval Model

**Limitation**: All destructive changes use the same approval model regardless of impact or risk level.

**Example**: Deleting a single test VLAN requires the same approval as deleting production core networking.

**Impact**: No graduated approval based on change risk or scope.

**Mitigation**: Policy could be enhanced to require different approval environments based on resource types or labels.

**Status**: Intentional design decision for simplicity.

---

### 2. No Rollback Mechanism

**Limitation**: No automated rollback if apply succeeds but causes operational issues.

**Impact**: Must manually create corrective changes through full render → plan → apply cycle.

**Example**:
```
1. Apply changes VLAN configuration
2. Change is syntactically correct but causes network issues
3. Terraform reports success (no errors)
4. Must manually revert in NetBox and go through full cycle to restore
```

**Mitigation**: Maintain backups and test changes in staging environments.

**Status**: Out of scope for current phase.

---

### 3. No Multi-Region Support

**Limitation**: Workflows assume single region/environment deployment.

**Impact**: Cannot easily manage infrastructure across multiple isolated environments (dev/staging/prod).

**Mitigation**: Would require separate repositories or workspace management.

**Status**: Intentional design decision documented in [docs/phase5/apply-workflow.md](apply-workflow.md#explicit-non-goals).

---

### 4. No Drift Correction Automation

**Limitation**: Drift detection exists but no automated correction workflow.

**Impact**: Detected drift must be manually evaluated and corrected through standard approval flow.

**Reference**: See [docs/phase4/drift.md](../phase4/drift.md) for drift detection details.

**Status**: Intentional - drift correction should be reviewed and approved.

---

### 5. Sequential Site Application

**Limitation**: Must apply changes to sites sequentially, not in parallel.

**Impact**: Applying to multiple sites takes longer (no parallelization).

**Example**: Applying to 5 sites serially could take 25 minutes vs. 5 minutes in parallel.

**Rationale**: Prevents state locking conflicts and maintains clear audit trail.

**Status**: Intentional design decision documented in [docs/phase5/apply-workflow.md](apply-workflow.md#example-2-apply-multiple-sites).

---

### 6. Plan Artifacts Size Limits

**Limitation**: GitHub Actions artifacts have size limits (may vary by plan size).

**Impact**: Very large Terraform plans may exceed artifact size limits, causing upload failures.

**Mitigation**: Keep infrastructure modular and deploy incrementally.

**Status**: No current implementation to split or compress large plans.

---

### 7. No Granular RBAC

**Limitation**: GitHub repository permissions are coarse-grained (read/write/admin).

**Impact**: Cannot grant permissions like "can approve but cannot trigger apply" or "can view plans but cannot approve".

**Mitigation**: Use GitHub Environment protection rules for additional approval gates.

**Status**: Limited by GitHub's permission model.

---

## Policy Engine Risks

This section documents risks specific to the OPA policy engine.

### 1. Policy Logic Complexity

**Risk**: As policies grow more complex, they become harder to reason about and may contain bugs.

**Impact**: Policy bugs could:
- Block legitimate changes (false positives)
- Allow dangerous changes (false negatives)
- Create confusing error messages

**Current State**: Policies are relatively simple (check for deletions, verify attestations).

**Mitigation**:
- Keep policies simple and well-documented
- Add policy testing framework (future work)
- Regular policy reviews

---

### 2. Policy Drift

**Risk**: Policy rules may become outdated as infrastructure patterns evolve.

**Impact**: Policies may block new patterns that are actually safe.

**Example**: Policy assumes certain resource types, but new UniFi provider adds new resource types not in policy.

**Mitigation**: Regular policy reviews and updates as infrastructure patterns change.

**Status**: No automated policy versioning or deprecation warnings.

---

### 3. OPA Version Pinning

**Risk**: Workflow pins specific OPA version (0.60.0). Newer versions may have bug fixes or security patches.

**Impact**: Could miss important security updates or bug fixes.

**Mitigation**: Regularly review and update pinned OPA version.

**Status**: Manual process - no automated dependency scanning for OPA version.

---

### 4. No Policy Testing Framework

**Risk**: Policy changes are not automatically tested before deployment.

**Impact**: Broken policies could block all infrastructure deployments.

**Mitigation**: Test policies locally before committing (manual process).

**Status**: No automated test suite for policies.

**Future Work**: Implement policy testing in CI (see [Technical Debt](#technical-debt)).

---

### 5. Policy Input Schema Changes

**Risk**: Changes to Terraform JSON format or workflow metadata could break policies.

**Impact**: Policies may fail to evaluate correctly if input structure changes.

**Example**: A Terraform upgrade changes the plan JSON format, causing policy rules to stop working.

**Mitigation**: Pin Terraform version and test policy changes thoroughly.

**Status**: No schema validation for policy inputs.

---

## Attestation & Provenance Risks

This section documents risks related to artifact attestation and SLSA provenance.

### 1. Attestation Service Dependency

**Risk**: Completely dependent on GitHub's artifact attestation service.

**Impact**: If GitHub attestation service is unavailable or broken, all deployments are blocked.

**Likelihood**: Low (GitHub service is generally reliable).

**Mitigation**: NONE - No fallback or bypass mechanism.

**Status**: Accepted risk - attestation is mandatory security control.

---

### 2. No Attestation Expiration

**Risk**: Attestations don't expire - old attested artifacts could be used indefinitely (within artifact retention period).

**Impact**: Stale artifacts could be used for apply operations.

**Mitigation**: Policy could check artifact/attestation timestamp freshness.

**Status**: Artifacts expire via GitHub retention policy (30 days default), but no explicit freshness checks.

---

### 3. Limited Attestation Validation

**Risk**: Attestation verification checks signature and builder identity, but limited validation of attestation content.

**Impact**: Attestation could be valid but artifact contents could still be problematic.

**Example**: Render pipeline could be compromised to generate malicious artifacts with valid attestations.

**Mitigation**: Multiple security layers (PR approval, policy evaluation, human review).

**Status**: Attestation verifies provenance, not artifact contents.

---

### 4. Attestation Key Compromise

**Risk**: If GitHub's attestation signing keys are compromised, attestations could be forged.

**Impact**: Could deploy malicious infrastructure configurations.

**Likelihood**: Very low (GitHub manages keys securely).

**Mitigation**: None at our level - dependent on GitHub's key management.

**Status**: Accepted risk - trust GitHub's attestation infrastructure.

---

## Apply Workflow Risks

This section documents risks specific to the terraform-apply workflow.

### 1. No Apply Timeout

**Risk**: Apply operations have no configured timeout - could run indefinitely.

**Impact**: A hung apply could block subsequent applies or consume runner resources.

**Mitigation**: GitHub Actions has default timeouts (6 hours for self-hosted runners, varies for GitHub-hosted).

**Status**: No explicit timeout configuration in workflow.

---

### 2. No Progress Monitoring

**Risk**: Long-running applies have no progress updates or heartbeat mechanism.

**Impact**: Difficult to distinguish between slow apply and hung apply.

**Mitigation**: Review workflow logs for terraform output.

**Status**: No structured progress reporting during apply.

---

### 3. Apply Metadata Retention

**Risk**: Apply metadata artifacts have 90-day retention by default.

**Impact**: Historical apply information is lost after retention period.

**Mitigation**: Export/archive important apply metadata before expiration.

**Status**: No automated archival of apply history.

---

### 4. No Apply Cancellation

**Risk**: Once apply starts, cannot safely cancel it.

**Impact**: If wrong plan is applied, must let it complete before correcting.

**Mitigation**: Verify plan thoroughly before triggering apply.

**Status**: Workflow cancellation could leave infrastructure in inconsistent state.

---

### 5. Stub Credentials in Current Implementation

**Risk**: Current implementation uses stub credentials for demonstration.

**Impact**: Terraform apply will fail in actual use until real credentials are configured.

**Documentation**: [docs/phase5/apply-workflow.md](apply-workflow.md#provider-configuration) documents this limitation.

**Status**: Expected - production credentials must be configured before real use.

---

### 6. No Apply Confirmation

**Risk**: Apply workflow uses `terraform apply -auto-approve` without additional confirmation.

**Impact**: Once apply starts, changes are automatically applied to infrastructure.

**Mitigation**: Multiple upstream gates (PR approval, policy evaluation, plan review, optional human approval).

**Status**: Intentional design - plan has already been reviewed and approved.

---

## Technical Debt

This section tracks known technical debt and deferred improvements.

### 1. No Policy Testing Framework

**Debt**: OPA policies have no automated test suite.

**Impact**: Policy changes could break deployments without detection until runtime.

**Work Required**:
- Create test fixtures with sample plan JSON
- Write test cases for each policy rule
- Integrate into CI pipeline
- Document testing approach

**Priority**: HIGH - Policy bugs can block all deployments.

**Effort**: Medium (2-3 days)

---

### 2. No Environment Configuration Validation

**Debt**: No automated validation that GitHub Environments are correctly configured.

**Impact**: Misconfigured environments could block or allow unintended approvals.

**Work Required**:
- Create validation script to check environment configuration
- Verify required reviewers are set
- Check environment naming conventions
- Run validation in CI

**Priority**: MEDIUM - Manual configuration is error-prone.

**Effort**: Small (1 day)

---

### 3. No Approval Metadata Validation

**Debt**: Approval metadata files are not validated for schema correctness.

**Impact**: Corrupted or incorrect approval metadata could route apply to wrong environment.

**Work Required**:
- Define JSON schema for approval metadata
- Add validation step in workflow
- Fail workflow if metadata is invalid

**Priority**: MEDIUM - Incorrect routing could bypass approval gates.

**Effort**: Small (1 day)

---

### 4. No Artifact Freshness Checks

**Debt**: No validation that artifacts are recent (not stale).

**Impact**: Old artifacts could be used for apply, not reflecting current infrastructure state.

**Work Required**:
- Add timestamp comparison in policy
- Define acceptable freshness window (e.g., 7 days)
- Fail policy evaluation if artifacts too old

**Priority**: LOW - Artifact retention handles extreme staleness.

**Effort**: Small (1 day)

---

### 5. No Workflow Run Dependency Tracking

**Debt**: No structured tracking of workflow run dependencies (render → plan → apply chain).

**Impact**: Difficult to trace complete workflow lineage for audit purposes.

**Work Required**:
- Create metadata format for run dependencies
- Store dependency information in artifacts
- Build tooling to visualize dependency chain

**Priority**: LOW - Manual tracking is possible through workflow summaries.

**Effort**: Medium (2-3 days)

---

### 6. No Alerting or Monitoring

**Debt**: No alerting when workflows fail or require attention.

**Impact**: Must manually check GitHub Actions for workflow status.

**Work Required**:
- Integrate with notification system (Slack, email, etc.)
- Alert on workflow failures
- Alert on pending environment approvals
- Alert on approaching artifact expiration

**Priority**: MEDIUM - Improves operational visibility.

**Effort**: Medium (2-3 days)

---

### 7. No Plan Diff Comparison

**Debt**: Cannot easily compare plans across workflow runs.

**Impact**: Difficult to understand how plans change over time or between runs.

**Work Required**:
- Store structured plan diffs
- Build tooling to compare plans
- Visualize plan evolution

**Priority**: LOW - Nice to have for analysis.

**Effort**: Medium (2-3 days)

---

### 8. Hard-coded Environment Names

**Debt**: Environment names are constructed using string concatenation in workflow.

**Impact**: Changes to naming convention require workflow updates.

**Work Required**:
- Move environment naming to configuration
- Support custom naming patterns
- Validate environment names

**Priority**: LOW - Current approach works adequately.

**Effort**: Small (1 day)

---

### 9. No Automated State Backup

**Debt**: Terraform state is not automatically backed up before apply.

**Impact**: State corruption or apply failure could lose state history.

**Work Required**:
- Implement pre-apply state backup
- Store backup in artifacts or separate storage
- Document restoration procedure

**Priority**: MEDIUM - State loss is difficult to recover from.

**Effort**: Small (1 day)

---

### 10. No Cost Estimation

**Debt**: No cost estimation or budget validation in plan workflow.

**Impact**: Could deploy expensive infrastructure without cost awareness.

**Work Required**:
- Integrate cost estimation tool (e.g., Infracost)
- Add cost checks to policy evaluation
- Alert on high-cost plans

**Priority**: LOW - Not applicable to on-premises UniFi infrastructure.

**Effort**: Medium (could be significant depending on provider)

---

## Mitigation Strategies

This section provides general strategies for working within the current limitations.

### 1. Emergency Response Planning

**Strategy**: Create documented emergency response procedures that work within the security boundaries.

**Actions**:
- Document escalation paths for getting urgent PR approvals
- Maintain contact information for multiple authorized reviewers across time zones
- Create expedited review process for critical changes
- Practice emergency scenarios regularly
- Consider separate "emergency" environments with different protection rules (future work)

---

### 2. Staging Environment

**Strategy**: Use staging/test environment to validate changes before production.

**Actions**:
- Create separate staging infrastructure
- Deploy all changes to staging first
- Validate functionality in staging
- Use identical workflows for staging and production
- Reduce risk of production apply failures

---

### 3. Regular Policy Reviews

**Strategy**: Schedule regular reviews of policy rules to catch drift and errors.

**Actions**:
- Monthly policy review meetings
- Document policy decisions and rationale
- Test policies with real-world scenarios
- Update policies as infrastructure patterns evolve

---

### 4. Comprehensive Testing

**Strategy**: Thoroughly test changes before deploying to production.

**Actions**:
- Test NetBox changes in NetBox test instance
- Review rendered artifacts before creating PR
- Carefully review plan output before approving
- Use structured diff for detailed change review
- Validate changes in staging environment

---

### 5. Documentation and Training

**Strategy**: Maintain comprehensive documentation and train team members.

**Actions**:
- Keep documentation up to date
- Document all manual recovery procedures (as they are developed)
- Train multiple team members on workflows
- Cross-train for coverage during absences
- Regular knowledge sharing sessions

---

### 6. Monitoring and Alerting

**Strategy**: Implement monitoring for workflow health and status (future work).

**Actions**:
- Set up workflow failure notifications
- Monitor artifact expiration
- Track approval wait times
- Alert on stale PRs or pending applies
- Dashboard for workflow status

---

## Future Work

This section outlines potential future improvements to address limitations.

### 1. Break-Glass Workflow (HIGH PRIORITY)

**Description**: Create emergency workflow with appropriate controls but reduced gates.

**Requirements**:
- Requires explicit incident declaration
- Logs all actions with enhanced auditing
- Requires post-incident review and documentation
- Limited to emergency recovery scenarios only
- Cannot be used for routine changes

**Considerations**:
- How to prevent abuse of break-glass mechanism
- What level of verification can be safely skipped
- How to ensure complete audit trail
- Post-incident review process

**Effort**: Large (5-7 days)

---

### 2. Policy Testing Framework (HIGH PRIORITY)

**Description**: Automated testing for OPA policies.

**Requirements**:
- Test fixtures with sample inputs
- Test cases for each policy rule
- CI integration
- Coverage reporting

**Effort**: Medium (2-3 days)

---

### 3. Rollback Automation (MEDIUM PRIORITY)

**Description**: Automated rollback of failed or problematic applies.

**Requirements**:
- Track previous successful state
- Automated rollback trigger
- Verification that rollback is safe
- Audit trail for rollbacks

**Considerations**:
- May not be possible for all resource types
- Could cause issues if infrastructure has dependencies
- Needs careful design to avoid cascading failures

**Effort**: Large (7-10 days)

---

### 4. Enhanced Monitoring (MEDIUM PRIORITY)

**Description**: Comprehensive monitoring and alerting for workflows.

**Requirements**:
- Workflow status notifications
- Artifact expiration warnings
- Pending approval alerts
- Failure alerting with context

**Effort**: Medium (3-4 days)

---

### 5. State Backup Automation (MEDIUM PRIORITY)

**Description**: Automatic Terraform state backup before applies.

**Requirements**:
- Pre-apply state snapshot
- Secure storage of backups
- Documented restoration procedure
- Retention policy for backups

**Effort**: Small (1-2 days)

---

### 6. Multi-Environment Support (LOW PRIORITY)

**Description**: Support for dev/staging/prod environments with different policies.

**Requirements**:
- Environment-specific policy rules
- Separate workflow files or workspace management
- Environment-specific credentials
- Clear separation and naming conventions

**Effort**: Large (10-15 days)

---

### 7. Plan Diff Analysis (LOW PRIORITY)

**Description**: Tools to compare and analyze plan changes over time.

**Requirements**:
- Structured diff storage
- Comparison tooling
- Visualization
- Historical trending

**Effort**: Medium (3-5 days)

---

## Summary

This document captures the current state of failure modes, emergency gaps, and technical debt in the policy, approval, and apply workflows. Key takeaways:

### Critical Gaps

1. **No emergency override mechanism** - Critical incidents must follow standard approval flow
2. **No break-glass workflow** - No expedited path for emergency changes
3. **No local execution option** - Completely dependent on GitHub Actions availability
4. **No policy override** - False positives in policy block legitimate changes
5. **No attestation bypass** - Dependent on GitHub attestation service availability

### Manual Recovery Required For

1. State file corruption
2. Partial apply failures
3. Approval metadata corruption
4. Policy logic errors
5. Artifact expiration
6. Environment misconfiguration

### High Priority Technical Debt

1. Policy testing framework
2. Environment configuration validation
3. State backup automation
4. Approval metadata validation

### Risk Acceptance

The current design intentionally prioritizes security and audit trail completeness over operational flexibility. The documented limitations are known tradeoffs for maintaining strong security boundaries. Future phases may address some limitations through carefully designed emergency workflows that preserve audit trail while providing faster response paths.

---

**Document Status**: Complete and ready for review

**Next Steps**:
1. Review this document with team
2. Prioritize future work items
3. Create issues for high-priority technical debt
4. Schedule regular updates to capture new limitations as they're discovered
5. Update as emergency procedures are developed and tested
