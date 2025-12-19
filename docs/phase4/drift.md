# Drift Semantics Documentation (Phase 4 Scope)

## Overview

This document defines what constitutes "drift" across different boundaries in the infrastructure pipeline, how drift is detected, and what enforcement actions are taken for each type of drift. Understanding drift semantics is critical for maintaining infrastructure consistency and ensuring safe, predictable deployments.

**Phase 4 Scope**: This document focuses on drift detection and handling for NetBox ↔ Artifact and Artifact ↔ Terraform plan boundaries. Terraform plan ↔ UniFi state drift is explicitly out of scope for Phase 4.

**Status**: Stable as of Phase 4

**Last Updated**: 2025-12-19

## What is Drift?

**Drift** is any divergence between an expected state (source of truth) and an actual state (rendered artifact or deployed infrastructure). Drift can occur due to:

- Manual changes to infrastructure outside the pipeline
- Timing differences between artifact generation and consumption
- Failed or incomplete deployments
- External modifications to the source of truth
- Concurrent modifications by multiple actors

## Drift Boundaries

The infrastructure pipeline has three primary boundaries where drift can be detected:

```
┌──────────┐      Boundary 1       ┌──────────┐      Boundary 2       ┌──────────────┐
│          │  ─────────────────▶   │          │  ─────────────────▶   │              │
│  NetBox  │   (Illegal Drift)     │ Artifact │   (Expected Drift)    │  Terraform   │
│ (Intent) │   Abort/Restart       │ (tfvars) │   Human/Agent Review  │     Plan     │
│          │                        │          │                        │              │
└──────────┘                        └──────────┘                        └──────────────┘
                                                                               │
                                                                               │ Boundary 3
                                                                               │ (Out of Scope)
                                                                               ▼
                                                                        ┌──────────────┐
                                                                        │              │
                                                                        │  UniFi       │
                                                                        │  State       │
                                                                        │              │
                                                                        └──────────────┘
```

### Boundary 1: NetBox ↔ Artifact (Illegal Drift)

**Status**: ❌ **Illegal** - Must be prevented or corrected

**Description**: Drift between NetBox (source of truth) and generated artifacts (tfvars, UniFi configs) during the artifact generation process.

**Detection Window**: During render pipeline execution (`.github/workflows/render-artifacts.yaml`)

**Enforcement**: **Abort pipeline or require restart**

#### What Causes This Drift?

1. **Concurrent NetBox Modifications**: NetBox data changes while the render pipeline is reading it
2. **API Instability**: NetBox API returns inconsistent results between consecutive calls
3. **Race Conditions**: Multiple exports occurring simultaneously reading different states
4. **Transaction Inconsistencies**: Reading data across non-atomic API calls

#### Example Scenarios

**Scenario 1: Concurrent Modification During Export**

```
Time    Event
────────────────────────────────────────────────────────────────
T0      Pipeline starts, exports sites.json (includes site-A)
T1      Human operator creates site-B in NetBox
T2      Pipeline exports vlans.json (includes VLANs for site-A and site-B)
T3      Pipeline exports prefixes.json (includes prefixes for site-A and site-B)
T4      Pipeline renders site-A.tfvars.json (missing VLAN/prefix associations)
```

**Result**: Artifact is inconsistent - some resources reference site-B data but site-B itself is missing from sites.json.

**Enforcement**: ❌ **Abort** - The artifact is internally inconsistent and must not be used.

**Scenario 2: VLAN Deletion During Rendering**

```
Time    Event
────────────────────────────────────────────────────────────────
T0      Pipeline exports vlans.json (VLAN 100 exists)
T1      Human operator deletes VLAN 100 in NetBox
T2      Pipeline exports prefixes.json (references to VLAN 100 are gone)
T3      Pipeline renders tfvars (VLAN 100 present, no associated prefixes)
```

**Result**: Artifact contains orphaned VLAN with no network prefixes.

**Enforcement**: ⚠️ **Warning** - May be acceptable if the VLAN is being decommissioned, but should trigger validation.

#### Why This Drift is Illegal

NetBox ↔ Artifact drift violates the fundamental assumption that **artifacts are atomic snapshots** of NetBox intent at a specific point in time. Allowing this drift would mean:

- ❌ Artifacts cannot be trusted as accurate representations of intent
- ❌ Attestations prove provenance but not correctness
- ❌ Downstream consumers cannot make safe decisions based on inconsistent data
- ❌ Rollback to previous artifacts becomes unreliable

#### Enforcement Actions

| Drift Severity | Action | Rationale |
|----------------|--------|-----------|
| **Inconsistent internal references** | ❌ **Abort pipeline immediately** | Data integrity violation; artifacts are corrupt |
| **Missing required fields** | ❌ **Abort pipeline immediately** | Schema violation; Terraform will fail |
| **Concurrent NetBox modification** | ⚠️ **Manual investigation required** | Detection possible but not automated; requires re-run |
| **Unexpected state during render** | ⚠️ **Warn and continue, but flag for review** | May be intentional (e.g., in-progress changes) |
| **API timeout or error** | 🔄 **Retry with exponential backoff** | Transient error; NetBox may recover |

#### Detection Mechanisms

**Phase 4 Implementations**:

1. **Schema Validation**: Validate that all required fields are present and correctly typed
2. **Referential Integrity Checks**: Ensure all foreign key references (VLAN IDs, site IDs) resolve correctly
3. **Consistency Checks**: Verify that NetBox export snapshots are internally consistent
4. **Timestamp Correlation**: Record export start/end times to detect potential race windows

**Example Validation (Pseudocode)**:

```python
# In render_tfvars.py
def validate_artifact_consistency(sites, vlans, prefixes):
    """Validate internal consistency of NetBox exports."""

    # Check that all VLAN references in prefixes exist in vlans
    vlan_ids = {vlan['id'] for vlan in vlans}
    for prefix in prefixes:
        if prefix.get('vlan') and prefix['vlan']['id'] not in vlan_ids:
            raise ConsistencyError(
                f"Prefix {prefix['cidr']} references non-existent VLAN {prefix['vlan']['id']}"
            )

    # Check that all site references are valid
    site_ids = {site['id'] for site in sites}
    for vlan in vlans:
        if vlan.get('site') and vlan['site']['id'] not in site_ids:
            raise ConsistencyError(
                f"VLAN {vlan['name']} references non-existent site {vlan['site']['id']}"
            )

    return True
```

#### Mitigation Strategies

**Current Phase 4 Mitigations**:

1. **Read-Only API Token**: Render pipeline cannot modify NetBox, reducing risk of self-inflicted drift
2. **Sequential Export**: Export resources in dependency order (sites → VLANs → prefixes)
3. **Fast Execution**: Minimize time window where drift can occur
4. **Atomic Snapshot Semantics**: Treat each pipeline run as a point-in-time snapshot

**Future Enhancements**:

1. **NetBox Transactions**: Use NetBox API transactions (if available) to ensure atomic reads
2. **Change Detection**: Query NetBox change logs before/after export to detect concurrent modifications
3. **Pessimistic Locking**: Request NetBox read locks during critical export windows
4. **Export Versioning**: Include NetBox version/change-id in artifacts for drift detection

#### Non-Goals for Phase 4

Phase 4 **does not** address:

- ❌ **NetBox Data Validation**: Ensuring data in NetBox is semantically correct (e.g., non-overlapping IP ranges)
- ❌ **NetBox Access Control**: Preventing unauthorized NetBox modifications
- ❌ **Change Approval Workflow**: Requiring approval for NetBox changes before export
- ❌ **Real-Time Drift Detection**: Detecting drift outside of pipeline execution
- ❌ **Automatic Drift Remediation**: Automatically correcting inconsistent NetBox data

### Boundary 2: Artifact ↔ Terraform Plan (Expected Drift)

**Status**: ✅ **Expected** - Normal part of the workflow

**Description**: Drift between attested artifacts (tfvars) and Terraform plan output. This represents the **intended changes** that Terraform will apply to achieve the desired state defined in NetBox.

**Detection Window**: During Terraform plan operation

**Enforcement**: **Human or agent review required before apply**

#### Why This Drift is Expected

Artifact ↔ Terraform plan drift is **the entire point** of infrastructure-as-code. The drift represents:

- ✅ **Intended Infrastructure Changes**: New VLANs, networks, or configuration updates
- ✅ **Declarative State Management**: Terraform calculates the delta between desired state (artifact) and current state (infrastructure)
- ✅ **Safe Review Mechanism**: Human or automated agent reviews changes before applying

This drift is **not an error** - it's the **desired workflow**.

#### Example Scenarios

**Scenario 1: Adding a New VLAN**

```
NetBox Intent (New):
- Site: Pennington
- VLAN 50: "Guest Network"
- Prefix: 192.168.50.0/24

Artifact (Rendered):
{
  "vlans": [
    {"vlan_id": 10, "name": "Management"},
    {"vlan_id": 50, "name": "Guest Network"}  // NEW
  ]
}

Terraform Plan (Drift Detected):
+ unifi_network.guest_network
    network = "192.168.50.0/24"
    name    = "Guest Network"
    vlan_id = 50
```

**Enforcement**: ✅ **Review and approve** - This is an expected change representing NetBox intent.

**Scenario 2: Modifying VLAN Name**

```
NetBox Intent (Updated):
- VLAN 10: "Management LAN" (was "Management")

Artifact (Rendered):
{
  "vlans": [
    {"vlan_id": 10, "name": "Management LAN"}  // UPDATED
  ]
}

Terraform Plan (Drift Detected):
~ unifi_network.management
    name = "Management" -> "Management LAN"
```

**Enforcement**: ✅ **Review and approve** - This is an expected change.

**Scenario 3: Deleting a VLAN**

```
NetBox Intent (Removed):
- VLAN 99 deleted

Artifact (Rendered):
{
  "vlans": [
    {"vlan_id": 10, "name": "Management"}
    // VLAN 99 removed
  ]
}

Terraform Plan (Drift Detected):
- unifi_network.old_vlan
```

**Enforcement**: ⚠️ **Review carefully** - Deletions require extra scrutiny to avoid accidental data loss.

#### Detection Mechanisms

**Phase 4 Implementation**:

1. **Terraform Plan Output**: Standard `terraform plan` output shows all detected drift
2. **JSON Plan Export**: Machine-readable plan via `terraform show -json tfplan`
3. **Structured Diff**: Generated markdown summary via `scripts/generate-plan-diff.py`
4. **GitHub Actions Summary**: Plan output displayed in workflow step summary

**Example Detection**:

```bash
# Generate Terraform plan
terraform plan \
  -var-file="artifacts/tfvars/site-pennington.tfvars.json" \
  -out=tfplan-pennington.binary

# Convert to machine-readable JSON
terraform show -json tfplan-pennington.binary > tfplan-pennington.json

# Extract change summary
jq -r '.resource_changes[] | "\(.change.actions | join(",")): \(.address)"' \
  tfplan-pennington.json
```

**Expected Output**:

```
create: unifi_network.guest_network
update: unifi_network.management
delete: unifi_network.old_vlan
no-op: unifi_network.lan
```

#### Review Requirements

All Artifact ↔ Terraform plan drift requires review before `terraform apply`. Review can be performed by:

1. **Human Operator**: Manual review of Terraform plan output
2. **Automated Agent**: Policy-based review using plan analysis tools
3. **Hybrid**: Automated pre-screening with human approval for high-risk changes

**Review Checklist**:

- [ ] All changes are intentional and match NetBox intent
- [ ] No unexpected deletions or modifications
- [ ] Resource dependencies are correctly handled
- [ ] Changes do not violate security or compliance policies
- [ ] Rollback plan exists for high-risk changes
- [ ] Change window is appropriate (e.g., maintenance window for deletions)

#### Enforcement Actions

| Change Type | Review Level | Approval Required |
|-------------|--------------|-------------------|
| **Create new resources** | ✅ Standard review | Human or agent |
| **Update existing resources** | ✅ Standard review | Human or agent |
| **Modify non-destructive attributes** | ✅ Standard review | Human or agent |
| **Delete resources** | ⚠️ **Enhanced review** | Human approval required |
| **Replace resources (delete + create)** | ⚠️ **Enhanced review** | Human approval required |
| **High-impact changes** (production VLANs, etc.) | 🔴 **Strict review** | Senior engineer approval |

#### Non-Goals for Phase 4

Phase 4 **does not** address:

- ❌ **Automatic Apply**: Terraform plans are not automatically applied in Phase 4
- ❌ **Policy-as-Code**: Advanced policy enforcement (e.g., OPA, Sentinel) is not implemented
- ❌ **Change Risk Scoring**: Automatic risk assessment of Terraform changes
- ❌ **Rollback Automation**: Automatic rollback on failed applies
- ❌ **Blast Radius Analysis**: Impact analysis for infrastructure changes
- ❌ **Deployment Orchestration**: Multi-site deployment coordination

### Boundary 3: Terraform Plan ↔ UniFi State (Future, Out of Scope)

**Status**: 🚧 **Future Phase** - Not implemented in Phase 4

**Description**: Drift between Terraform plan (intended changes) and actual UniFi controller state after apply. This would represent failures, partial deployments, or out-of-band modifications to UniFi.

**Detection Window**: After Terraform apply (if Terraform provider supports drift detection)

**Enforcement**: Not applicable to Phase 4

#### Why This is Out of Scope

Phase 4 focuses on the **pipeline up to Terraform plan**. Terraform apply operations and post-apply drift detection are deferred to future phases because:

1. **UniFi Terraform Provider Limitations**: The UniFi Terraform provider may have limited drift detection capabilities
2. **Manual Apply**: Terraform applies are performed manually in Phase 4, not through automated workflows
3. **Operational Complexity**: Real-time drift detection requires monitoring infrastructure and alerting systems
4. **Risk Management**: Phase 4 prioritizes getting the pipeline working correctly before adding post-deployment monitoring

#### Example Scenarios (Future Implementation)

**Scenario 1: Out-of-Band VLAN Modification**

```
Terraform State (Expected):
unifi_network.guest_network
  name    = "Guest Network"
  vlan_id = 50

UniFi Controller (Actual):
  name    = "Guest WiFi"  // MODIFIED via UniFi UI
  vlan_id = 50
```

**Future Detection**: `terraform plan` would detect drift and propose reverting the change.

**Scenario 2: Terraform Apply Failure**

```
Terraform Plan (Intended):
+ unifi_network.iot_network
+ unifi_network.security_cameras

Terraform Apply (Partial Failure):
✓ unifi_network.iot_network created
✗ unifi_network.security_cameras FAILED (UniFi API timeout)

UniFi State (Actual):
- iot_network exists
- security_cameras does NOT exist
```

**Future Detection**: Retry logic or manual re-apply required.

#### Future Enhancements

**Planned for Future Phases**:

1. **Automated Drift Detection**: Periodic `terraform plan` to detect out-of-band changes
2. **Drift Alerting**: Notifications when drift exceeds acceptable thresholds
3. **Drift Remediation**: Automated or semi-automated correction of detected drift
4. **Continuous Reconciliation**: Regular Terraform refreshes to maintain desired state
5. **State Locking**: Prevent concurrent Terraform operations

**Not Planned (Explicitly Non-Goals)**:

- ❌ **Real-Time UniFi Monitoring**: Continuously watching UniFi state for changes
- ❌ **UniFi Change Blocking**: Preventing manual changes to UniFi (may be needed for emergencies)
- ❌ **Bi-Directional Sync**: Importing manual UniFi changes back to NetBox (NetBox is source of truth)

## Drift Truth Table

This table summarizes all drift scenarios, their enforcement actions, and whether they are in scope for Phase 4.

| Boundary | Drift Scenario | Severity | Enforcement Action | Phase 4 Scope |
|----------|----------------|----------|-------------------|---------------|
| **NetBox ↔ Artifact** | Inconsistent foreign key references | 🔴 Critical | ❌ Abort pipeline immediately | ✅ Yes |
| **NetBox ↔ Artifact** | Missing required fields | 🔴 Critical | ❌ Abort pipeline immediately | ✅ Yes |
| **NetBox ↔ Artifact** | Schema validation failure | 🔴 Critical | ❌ Abort pipeline immediately | ✅ Yes |
| **NetBox ↔ Artifact** | Orphaned resources (e.g., VLAN with no site) | 🟡 Warning | ⚠️ Warn and flag for review | ✅ Yes |
| **NetBox ↔ Artifact** | API timeout or transient error | 🟡 Warning | 🔄 Retry with backoff | ✅ Yes |
| **NetBox ↔ Artifact** | Concurrent NetBox modification detected | 🟠 High Risk | ⚠️ Manual investigation required | ⚠️ Partial (detection only) |
| **Artifact ↔ Terraform Plan** | New resources to create | 🟢 Normal | ✅ Review and approve | ✅ Yes |
| **Artifact ↔ Terraform Plan** | Existing resources to update | 🟢 Normal | ✅ Review and approve | ✅ Yes |
| **Artifact ↔ Terraform Plan** | Resources to delete | 🟡 Warning | ⚠️ Enhanced review required | ✅ Yes |
| **Artifact ↔ Terraform Plan** | Resources to replace | 🟡 Warning | ⚠️ Enhanced review required | ✅ Yes |
| **Artifact ↔ Terraform Plan** | High-impact changes (prod VLANs) | 🟠 High Risk | 🔴 Strict review + senior approval | ⚠️ Manual only |
| **Artifact ↔ Terraform Plan** | No changes detected | 🟢 Normal | ✅ Safe to skip apply | ✅ Yes |
| **Terraform Plan ↔ UniFi** | Out-of-band UniFi modifications | 🟡 Warning | ℹ️ Future: detect and alert | ❌ No (future phase) |
| **Terraform Plan ↔ UniFi** | Partial apply failure | 🟠 High Risk | ℹ️ Future: retry or remediate | ❌ No (future phase) |
| **Terraform Plan ↔ UniFi** | Terraform state corruption | 🔴 Critical | ℹ️ Future: state recovery procedures | ❌ No (future phase) |
| **Terraform Plan ↔ UniFi** | UniFi API unavailable during apply | 🔴 Critical | ℹ️ Future: circuit breaker + retry | ❌ No (future phase) |

### Legend

- 🔴 **Critical**: Must be prevented or immediately corrected; pipeline abortion required
- 🟠 **High Risk**: Requires enhanced review and approval; may require rollback plan
- 🟡 **Warning**: Acceptable but requires attention; flag for review
- 🟢 **Normal**: Expected behavior; standard review process
- ✅ **Yes**: Fully implemented in Phase 4
- ⚠️ **Partial**: Detection implemented but enforcement is manual
- ❌ **No**: Out of scope for Phase 4; deferred to future phases

## Operational Guidelines

### Handling Drift During Pipeline Execution

**If NetBox ↔ Artifact drift is detected:**

1. **Critical Drift (Abort):**
   ```bash
   # Pipeline automatically stops
   # Check workflow logs for error details
   gh run view <run-id> --log

   # Example error message:
   # ERROR: Consistency validation failed
   # Prefix 192.168.50.0/24 references non-existent VLAN 50
   ```

2. **Resolution Steps:**
   - Verify NetBox data is correct and consistent
   - Fix any referential integrity issues in NetBox
   - Re-run the render pipeline
   - DO NOT manually patch artifacts

**If Artifact ↔ Terraform Plan drift is detected:**

1. **Review Terraform plan output:**
   ```bash
   # Download plan artifacts
   gh run download <run-id> --name terraform-plan-pennington

   # Review plan diff
   cat tfplan-pennington-diff.md

   # Review JSON plan programmatically
   jq '.resource_changes[] | select(.change.actions != ["no-op"])' tfplan-pennington.json
   ```

2. **Approval Decision:**
   - ✅ **Approve**: Changes match NetBox intent and are safe
   - ⚠️ **Approve with caution**: Changes are correct but high-risk (require change window)
   - ❌ **Reject**: Changes are unexpected or incorrect (investigate NetBox or artifact rendering)

3. **Apply Changes:**
   ```bash
   # After approval, apply the plan
   terraform apply tfplan-pennington.binary
   ```

### Emergency Procedures

**NetBox Modified During Pipeline Run:**

1. **If suspected**:
   - Check NetBox change logs for concurrent modifications
   - Compare NetBox current state with rendered artifact
   - If discrepancies found, abort and re-run pipeline

2. **Prevention**:
   - Coordinate NetBox changes with pipeline schedules
   - Use NetBox maintenance windows for large changes
   - Monitor pipeline execution during critical changes

**Terraform Plan Shows Unexpected Changes:**

1. **Investigate**:
   - Review NetBox history to confirm intent
   - Check artifact attestation to verify provenance
   - Compare artifact with previous successful runs
   - Review Terraform provider version for breaking changes

2. **Resolution**:
   - If artifact is correct, approve plan
   - If artifact is incorrect, investigate render pipeline
   - If NetBox is incorrect, fix NetBox and re-render

## Automation and Tooling

### Phase 4 Tooling

**Drift Detection Tools**:

1. **NetBox Export Validation**:
   - `netbox-client/scripts/export_intent.py` (validates during export)
   - Schema validation using JSON schemas
   - Referential integrity checks

2. **Terraform Plan Analysis**:
   - `terraform plan -detailed-exitcode` (detects changes)
   - `terraform show -json` (machine-readable plan)
   - `scripts/generate-plan-diff.py` (human-readable summary)

3. **Artifact Attestation**:
   - GitHub attestation API (verifies artifact provenance)
   - `gh attestation verify` (validates attestations)
   - `.github/actions/verify-attestation` (composite action)

**Integration Example**:

```yaml
# .github/workflows/terraform-plan.yaml
- name: Verify Artifact Attestations
  uses: ./.github/actions/verify-attestation
  with:
    artifact-path: 'artifacts/tfvars/*.json'
    environment: 'prod'

- name: Terraform Plan
  id: plan
  run: |
    set +e
    terraform plan \
      -var-file="../artifacts/tfvars/site-pennington.tfvars.json" \
      -out=tfplan-pennington.binary \
      -detailed-exitcode
    PLAN_EXIT_CODE=$?
    echo "exit_code=$PLAN_EXIT_CODE" >> $GITHUB_OUTPUT
    exit $PLAN_EXIT_CODE
  continue-on-error: true

- name: Detect Drift
  run: |
    PLAN_EXIT=${{ steps.plan.outputs.exit_code }}
    if [ "$PLAN_EXIT" == "2" ]; then
      echo "✓ Drift detected - review required"
    elif [ "$PLAN_EXIT" == "0" ]; then
      echo "✓ No drift - infrastructure matches desired state"
    else
      echo "✗ Terraform plan failed"
      exit 1
    fi
```

## Related Documentation

- [attestation-gate.md](./attestation-gate.md) - Attestation verification gate implementation
- [terraform-input-contract.md](./terraform-input-contract.md) - Artifact schema and contract
- [plan-output.md](./plan-output.md) - Terraform plan output structure
- [../phase3/terraform-boundary.md](../phase3/terraform-boundary.md) - Trust boundary requirements
- [../phase3/threat-model.md](../phase3/threat-model.md) - Security model and trust boundaries
- [../render-pipeline.md](../render-pipeline.md) - Render pipeline documentation

## Summary

Phase 4 drift semantics are defined as follows:

1. **NetBox ↔ Artifact**: ❌ **Illegal drift** - Must be prevented through validation and consistency checks. Pipeline aborts on critical errors.

2. **Artifact ↔ Terraform Plan**: ✅ **Expected drift** - This is the desired workflow. All changes require human or agent review before apply.

3. **Terraform Plan ↔ UniFi State**: 🚧 **Out of scope** - Deferred to future phases. Manual intervention required for post-apply drift.

**Key Takeaways**:

- ✅ Artifacts must be atomic, consistent snapshots of NetBox intent
- ✅ Terraform drift represents intended infrastructure changes requiring review
- ✅ All drift must be explicitly reviewed and approved before apply
- ❌ NetBox data inconsistencies cause pipeline failures (by design)
- 🚧 Post-apply drift detection is a future enhancement

**Phase 4 Acceptance Criteria**:

- [x] Documented drift boundaries and semantics
- [x] Created truth table mapping drift cases to enforcement actions
- [x] Defined what is and is not considered drift for each boundary
- [x] Specified non-goals and future enhancements
- [x] Provided operational guidelines for handling drift scenarios
