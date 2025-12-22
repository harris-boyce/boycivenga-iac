#!/bin/bash
# Test script for OPA policy engine integration
set -e

echo "🧪 Testing OPA Policy Engine Integration"
echo "========================================="
echo ""

# Test 1: Validate policy files exist
echo "Test 1: Checking policy files exist..."
test -f .github/policies/terraform_plan.rego && echo "  ✅ terraform_plan.rego exists"
test -f .github/policies/common.rego && echo "  ✅ common.rego exists"
test -f .github/policies/README.md && echo "  ✅ README.md exists"

# Test 2: Check that terraform-plan.yaml integrates policy evaluation
echo ""
echo "Test 2: Checking terraform-plan.yaml integration..."
grep -q "Evaluate Policy with OPA" .github/workflows/terraform-plan.yaml && \
    echo "  ✅ terraform-plan.yaml includes policy evaluation step"
grep -q "OPA_VERSION=" .github/workflows/terraform-plan.yaml && \
    echo "  ✅ OPA version is pinned for deterministic execution"

# Test 3: Validate documentation exists
echo ""
echo "Test 3: Checking documentation..."
test -f docs/phase5/policy-engine.md && \
    echo "  ✅ Policy engine documentation exists (docs/phase5/policy-engine.md)"

# Test 4: Install OPA and validate policy syntax
echo ""
echo "Test 4: Validating Rego policy syntax..."
OPA_VERSION="0.60.0"
OPA_BIN="/tmp/opa-test"

if [ ! -f "$OPA_BIN" ]; then
    echo "  📦 Downloading OPA ${OPA_VERSION}..."
    curl -sL -o "$OPA_BIN" "https://github.com/open-policy-agent/opa/releases/download/v${OPA_VERSION}/opa_linux_amd64_static"
    chmod +x "$OPA_BIN"
fi

echo "  ✅ OPA version: $($OPA_BIN version | head -1)"

# Check policy syntax
echo "  🔍 Checking terraform_plan.rego syntax..."
"$OPA_BIN" check .github/policies/terraform_plan.rego && \
    echo "  ✅ terraform_plan.rego syntax is valid"

echo "  🔍 Checking common.rego syntax..."
"$OPA_BIN" check .github/policies/common.rego && \
    echo "  ✅ common.rego syntax is valid"

# Test 5: Test policy with sample inputs
echo ""
echo "Test 5: Testing policy evaluation with sample inputs..."

# Create test input - PASS scenario (attested artifact, no deletions)
cat > /tmp/policy-test-pass.json << 'EOF'
{
  "plan": {
    "format_version": "1.2",
    "terraform_version": "1.9.0",
    "resource_changes": [
      {
        "address": "unifi_network.test",
        "type": "unifi_network",
        "change": {
          "actions": ["create"],
          "before": null,
          "after": {
            "name": "Test Network"
          }
        }
      }
    ]
  },
  "metadata": {
    "artifact": {
      "path": "site-test.tfvars.json",
      "site": "test"
    },
    "provenance": {
      "render_run_id": "123456",
      "attestation_verified": true,
      "pr_number": "1",
      "approver": "testuser"
    },
    "deletion_approved": false
  }
}
EOF

echo "  🔍 Testing PASS scenario (attested artifact, create only)..."
if "$OPA_BIN" eval \
    --bundle .github/policies/ \
    --input /tmp/policy-test-pass.json \
    --format pretty \
    'data.terraform.plan.allow' | grep -q "true"; then
    echo "  ✅ Policy correctly allows compliant plan"
else
    echo "  ❌ Policy incorrectly denied compliant plan"
    exit 1
fi

# Create test input - FAIL scenario (unattested artifact)
cat > /tmp/policy-test-fail-attestation.json << 'EOF'
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
      "path": "site-test.tfvars.json",
      "site": "test"
    },
    "provenance": {
      "render_run_id": "123456",
      "attestation_verified": false,
      "pr_number": "1",
      "approver": "testuser"
    }
  }
}
EOF

echo "  🔍 Testing FAIL scenario (unattested artifact)..."
if "$OPA_BIN" eval \
    --bundle .github/policies/ \
    --input /tmp/policy-test-fail-attestation.json \
    --format pretty \
    'data.terraform.plan.allow' | grep -q "false"; then
    echo "  ✅ Policy correctly denies unattested artifact"
else
    echo "  ❌ Policy incorrectly allowed unattested artifact"
    exit 1
fi

# Create test input - FAIL scenario (unapproved deletion)
cat > /tmp/policy-test-fail-deletion.json << 'EOF'
{
  "plan": {
    "resource_changes": [
      {
        "address": "unifi_network.test",
        "type": "unifi_network",
        "change": {
          "actions": ["delete"]
        }
      }
    ]
  },
  "metadata": {
    "artifact": {
      "path": "site-test.tfvars.json",
      "site": "test"
    },
    "provenance": {
      "render_run_id": "123456",
      "attestation_verified": true,
      "pr_number": "1",
      "approver": "testuser"
    },
    "deletion_approved": false
  }
}
EOF

echo "  🔍 Testing FAIL scenario (unapproved deletion)..."
if "$OPA_BIN" eval \
    --bundle .github/policies/ \
    --input /tmp/policy-test-fail-deletion.json \
    --format pretty \
    'data.terraform.plan.allow' | grep -q "false"; then
    echo "  ✅ Policy correctly denies unapproved deletion"
else
    echo "  ❌ Policy incorrectly allowed unapproved deletion"
    exit 1
fi

# Test 6: Verify policy outputs summary information
echo ""
echo "Test 6: Testing policy summary output..."
SUMMARY=$("$OPA_BIN" eval \
    --bundle .github/policies/ \
    --input /tmp/policy-test-pass.json \
    --format pretty \
    'data.terraform.plan.summary')

echo "$SUMMARY" | grep -q "allowed" && echo "  ✅ Summary includes 'allowed' field"
echo "$SUMMARY" | grep -q "total_resources" && echo "  ✅ Summary includes 'total_resources' field"
echo "$SUMMARY" | grep -q "violations" && echo "  ✅ Summary includes 'violations' field"

# Cleanup
rm -f /tmp/policy-test-*.json

echo ""
echo "========================================="
echo "✅ All policy engine tests passed!"
echo "========================================="
