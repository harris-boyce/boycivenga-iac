# OPA Policies for Terraform Plan Evaluation

This directory contains Open Policy Agent (OPA) policies for evaluating Terraform plans before apply operations.

## Policy Files

- **terraform_plan.rego**: Main policy for evaluating Terraform plans
- **common.rego**: Reusable helper functions and rules

## Policy Evaluation

Policies are automatically evaluated in the `terraform-plan.yaml` GitHub Actions workflow.

### Input Format

Policies expect a JSON input document with the following structure:

```json
{
  "plan": {
    "format_version": "1.2",
    "terraform_version": "1.9.0",
    "resource_changes": [
      {
        "address": "unifi_network.management",
        "change": {
          "actions": ["create"],
          "before": null,
          "after": { ... }
        }
      }
    ]
  },
  "metadata": {
    "artifact": {
      "path": "site-pennington.tfvars.json",
      "site": "pennington"
    },
    "provenance": {
      "render_run_id": "1234567890",
      "attestation_verified": true,
      "pr_number": "42",
      "approver": "username",
      "approved_at": "2024-01-15T10:30:00Z"
    },
    "deletion_approved": false
  }
}
```

### Policy Decisions

The main decision rule is `data.terraform.plan.allow`:

- **true**: Plan is approved and can proceed
- **false**: Plan is denied and workflow fails

### Testing Policies Locally

You can test policies locally using OPA CLI:

```bash
# Install OPA
curl -L -o opa https://github.com/open-policy-agent/opa/releases/download/v0.60.0/opa_linux_amd64
chmod +x opa

# Create a test input file
cat > test-input.json << 'EOF'
{
  "plan": {
    "resource_changes": [
      {
        "address": "unifi_network.test",
        "type": "unifi_network",
        "change": {
          "actions": ["create"]
        }
      }
    ]
  },
  "metadata": {
    "artifact": {
      "path": "test.tfvars.json",
      "site": "test"
    },
    "provenance": {
      "render_run_id": "123",
      "attestation_verified": true,
      "pr_number": "1",
      "approver": "testuser"
    }
  }
}
EOF

# Evaluate the policy
./opa eval --bundle .github/policies/ --input test-input.json 'data.terraform.plan.allow'

# Get denial reasons (if any)
./opa eval --bundle .github/policies/ --input test-input.json 'data.terraform.plan.deny'

# Get detailed violations
./opa eval --bundle .github/policies/ --input test-input.json 'data.terraform.plan.violations'

# Get summary
./opa eval --bundle .github/policies/ --input test-input.json 'data.terraform.plan.summary'
```

## Policy Rules

### Main Policy (terraform_plan.rego)

The main policy enforces the following rules:

1. **Attestation Required**: Artifact must have verified attestation
2. **No Unapproved Deletions**: Destructive changes require explicit approval
3. **Valid Provenance**: Provenance information must be complete
4. **PR Approval**: PR number and approver must be present
5. **Non-Empty Plan**: Plan must contain at least one resource change

### Common Helpers (common.rego)

The common module provides:

- Resource type validation
- Change action classification
- String and array utilities
- Attestation validation helpers

## Extending Policies

To add new policy rules:

1. **Add a new deny rule** in `terraform_plan.rego`:
   ```rego
   deny contains msg if {
       some_condition_not_met
       msg := "Your denial message here"
   }
   ```

2. **Add helper rules** as needed:
   ```rego
   some_condition_not_met if {
       # Your condition logic
   }
   ```

3. **Add violations** for detailed reporting:
   ```rego
   violations contains violation if {
       some_condition_not_met
       violation := {
           "type": "your_violation_type",
           "severity": "high",
           "message": "Detailed message",
           "resource": "affected_resource"
       }
   }
   ```

4. **Test your changes** locally before committing

## Policy Development Best Practices

1. **Keep policies simple**: Each rule should check one thing
2. **Use descriptive names**: Rule names should explain what they check
3. **Add comments**: Explain complex logic
4. **Test thoroughly**: Test both pass and fail cases
5. **Use common helpers**: Reuse functions from common.rego
6. **Document violations**: Provide clear messages for failures

## References

- [OPA Documentation](https://www.openpolicyagent.org/docs/latest/)
- [Rego Language Reference](https://www.openpolicyagent.org/docs/latest/policy-reference/)
- [Policy Engine Documentation](../../docs/phase5/policy-engine.md)
