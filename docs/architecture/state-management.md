# State Management Architecture

## Authority Boundaries

This document defines the authority boundaries and state management strategy for the infrastructure automation pipeline.

### Core Principle

**GitHub Actions is the secure execution pipeline, NOT a state authority.**

## Authority Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│ 1. NetBox (Source of Truth - Desired State)                 │
│    └─> Authoritative for WHAT should exist                  │
│    └─> Renders tfvars artifacts                             │
│    └─> Networks, VLANs, subnets, IP allocations             │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    (attested tfvars)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. GitHub Actions (Secure Execution Pipeline)               │
│    └─> NOT authoritative for state                          │
│    └─> Verifies attestations (SLSA provenance)              │
│    └─> Enforces policies (OPA gates)                        │
│    └─> Provides audit trail (who, what, when)               │
│    └─> Generates execution artifacts (90-day retention)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    (verified changes)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. UniFi Controller (Source of Truth - Actual State)        │
│    └─> Authoritative for WHAT currently exists              │
│    └─> Running network configuration                        │
│    └─> Operational reality                                  │
└─────────────────────────────────────────────────────────────┘
```

## State Artifacts vs State Authority

### What State Artifacts Are

State files (`state/<site>-networks.json`) are **execution receipts**, not authority:

```json
{
  "format_version": "1.0",
  "applied_at": "2025-12-30T06:14:00Z",
  "applied_by": "github-actions",
  "site": "default",
  "tfvars_checksum": "sha256:...",
  "networks": [ /* what was applied */ ]
}
```

**Purpose:**
- ✅ Audit trail: "What did we apply and when?"
- ✅ Drift detection: "Did someone manually change the controller?"
- ✅ Reconciliation metadata: "What's the gap between desired vs actual vs last-applied?"

**NOT for:**
- ❌ Source of truth (that's NetBox for desired, UniFi for actual)
- ❌ Long-term state storage (would compete with NetBox)
- ❌ Required dependency (system works without them)

### Storage Strategy

**Artifacts, not Git commits:**

```yaml
- name: Upload state file as artifact
  uses: actions/upload-artifact@v4
  with:
    name: network-state-${{ site }}
    path: state/${{ site }}-networks.json
    retention-days: 90  # Audit trail, then expire
```

**Rationale:**
1. **Security**: State not in git history (even private repos)
2. **Authority clarity**: NetBox is SSOT, not competing with git state
3. **Access control**: Artifacts use GitHub permissions
4. **Lifecycle**: Auto-expires (90 days) - not permanent
5. **Separation**: Execution metadata ≠ configuration authority

## Comparison: Traditional vs This Architecture

### Traditional Terraform

```
Terraform State (S3/Cloud)
  ├─> Source of truth for "what exists"
  ├─> Required for all operations
  ├─> Locking for concurrency
  └─> Permanent storage
```

### This Architecture

```
NetBox (Desired State SSOT)
  └─> Renders → tfvars (attested)
                  ↓
            GitHub Actions (Execution + Gates)
                  ↓
         UniFi Controller (Actual State SSOT)

State Artifacts (Optional)
  └─> Execution receipts (90-day audit trail)
```

## Drift Detection Without State

The plan script compares:

1. **Desired** (from NetBox → tfvars)
2. **Actual** (from UniFi Controller API)
3. **Recorded** (optional - from last apply artifact)

**Without state artifact:**
```
Desired vs Actual = "What needs to change?"
```

**With state artifact:**
```
Desired vs Actual = "What needs to change?"
Actual vs Recorded = "What was manually changed?" (drift alert)
```

Both modes work. State artifact adds drift visibility but isn't required.

## Security Implications

### Information Disclosure Risk: LOW

State files contain:
- Network names (same as NetBox)
- VLAN IDs (same as NetBox)
- Subnets (same as NetBox)
- UniFi resource IDs (opaque, not useful without controller access)
- Timestamps (audit metadata)

**Risk assessment:**
- 🟢 Everything is already in NetBox (authoritative source)
- 🟢 UniFi IDs are meaningless without controller credentials
- 🟢 Artifacts expire (not permanent git history)
- 🟢 Access controlled by GitHub permissions

### Defense in Depth

Even with low risk, we use artifacts not git because:
1. **Principle of least privilege**: State not needed long-term
2. **Separation of concerns**: Execution metadata ≠ configuration
3. **Audit compliance**: 90-day retention sufficient for SOC2/ISO27001
4. **Git hygiene**: Config code only, not operational data

## Implementation

### Apply Workflow

```yaml
- name: Apply changes (UniFi API)
  run: python scripts/apply_via_unifi.py --tfvars $TFVARS

- name: Upload state file as artifact
  if: success()
  uses: actions/upload-artifact@v4
  with:
    name: network-state-${{ site }}
    path: state/${{ site }}-networks.json
    retention-days: 90
```

### Plan Workflow

```python
# Load desired state (authoritative)
desired = build_desired_state(load_tfvars(tfvars_file))

# Load actual state (authoritative)
actual = unifi_client.get_networks(site)

# Load recorded state (optional audit metadata)
recorded = load_state_file(state_file) if state_file.exists() else []

# Compare
diff = compute_diff(desired, actual, recorded)
```

## Future Considerations

### If We Need Persistent State

**Option 1: GitHub Actions as Transient State Store**
- Current approach
- 90-day retention
- Best for: Portfolio, homelab, small deployments

**Option 2: External State Store (e.g., S3)**
- Separate from git
- Encrypted at rest
- Access controlled via IAM
- Best for: Production, compliance requirements

**Option 3: Eliminate State Entirely**
- Always compare NetBox (desired) vs UniFi (actual)
- No recorded state
- Best for: When drift detection not needed

### We Chose Option 1 Because

- ✅ Appropriate for portfolio/homelab use case
- ✅ Demonstrates proper separation of concerns
- ✅ Avoids overengineering (no external dependencies)
- ✅ Audit trail without git history pollution
- ✅ Clear authority boundaries (NetBox = desired, UniFi = actual)

## Key Takeaway

**GitHub Actions orchestrates the secure transformation of desired state (NetBox) into actual state (UniFi). It is NOT a state authority itself.**

State artifacts are execution receipts with limited retention, not competing sources of truth.
