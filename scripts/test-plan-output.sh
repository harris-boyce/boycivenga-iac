#!/bin/bash
# Test script for validating Terraform plan output structure
set -e

echo "🧪 Testing Terraform Plan Output Structure"
echo "=========================================="
echo ""

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass() {
    echo "✅ $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
    echo "❌ $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

# Test 1: Validate documentation exists
echo "Test 1: Checking documentation..."
if [ -f "docs/phase4/plan-output.md" ]; then
    pass "Documentation exists (plan-output.md)"
else
    fail "Documentation missing (plan-output.md)"
fi

# Test 2: Check documentation contains required sections
echo ""
echo "Test 2: Checking documentation content..."
for section in "## Overview" "## Output Artifacts" "## Deterministic Ordering" "## Parsing Guidelines" "## Integration with CI/CD" "## Validation"; do
    if grep -q "$section" docs/phase4/plan-output.md; then
        pass "Documentation has '$section' section"
    else
        fail "Documentation missing '$section' section"
    fi
done

# Test 3: Validate terraform-plan.yaml generates JSON output
echo ""
echo "Test 3: Checking workflow generates JSON output..."
if grep -q "terraform show -json" .github/workflows/terraform-plan.yaml; then
    pass "Workflow generates JSON plan output"
else
    fail "Workflow missing JSON plan generation"
fi

# Test 4: Check workflow uploads plan artifacts
echo ""
echo "Test 4: Checking workflow uploads plan artifacts..."
if grep -A10 "Upload Terraform Plans" .github/workflows/terraform-plan.yaml | grep -q "\.json"; then
    pass "Workflow uploads JSON plan artifacts"
else
    fail "Workflow missing JSON plan upload"
fi

if grep -A10 "Upload Terraform Plans" .github/workflows/terraform-plan.yaml | grep -q "\.binary"; then
    pass "Workflow uploads binary plan artifacts"
else
    fail "Workflow missing binary plan upload"
fi

# Test 5: Check Python diff generator exists
echo ""
echo "Test 5: Checking diff generator script..."
if [ -f "scripts/generate-plan-diff.py" ]; then
    pass "Diff generator script exists"

    # Validate Python syntax
    if python3 -m py_compile scripts/generate-plan-diff.py 2>/dev/null; then
        pass "Diff generator script has valid syntax"
    else
        fail "Diff generator script has syntax errors"
    fi
else
    fail "Diff generator script missing"
fi

# Test 6: Test diff generator with sample data
echo ""
echo "Test 6: Testing diff generator with sample data..."
python3 << 'PYEOF'
import json
import tempfile
import subprocess
import os

# Create sample plan
sample_plan = {
    "format_version": "1.2",
    "terraform_version": "1.0.0",
    "resource_changes": [
        {
            "address": "unifi_network.vlan_guest",
            "change": {"actions": ["create"]}
        },
        {
            "address": "unifi_network.vlan_management",
            "change": {"actions": ["create"]}
        },
        {
            "address": "unifi_network.default",
            "change": {"actions": ["update"]}
        }
    ]
}

# Write to temp file
temp_file = None
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(sample_plan, f)
    temp_file = f.name

try:
    # Run diff generator
    result = subprocess.run(
        ['python3', 'scripts/generate-plan-diff.py', temp_file, 'test-site'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        output = result.stdout
        # Verify output contains expected sections
        assert '# Terraform Plan Diff Summary' in output
        assert '## Change Summary' in output
        assert '## Machine-Readable Summary' in output
        assert 'test-site' in output
        print("✅ Diff generator produces valid output")
    else:
        print(f"❌ Diff generator failed: {result.stderr}")
        exit(1)
finally:
    if temp_file and os.path.exists(temp_file):
        os.unlink(temp_file)
PYEOF

if [ $? -eq 0 ]; then
    pass "Diff generator test passed"
else
    fail "Diff generator test failed"
fi

# Test 7: Verify workflow uses diff generator
echo ""
echo "Test 7: Checking workflow uses diff generator..."
if grep -q "generate-plan-diff.py" .github/workflows/terraform-plan.yaml; then
    pass "Workflow uses diff generator script"
else
    fail "Workflow missing diff generator integration"
fi

# Test 8: Check CI includes plan output test
echo ""
echo "Test 8: Checking CI integration..."
if grep -q "test-plan-output.sh" .github/workflows/ci.yaml; then
    pass "CI includes plan output validation"
else
    fail "CI missing plan output test"
fi

# Final summary
echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="
echo "Passed: $TESTS_PASSED"
if [ $TESTS_FAILED -gt 0 ]; then
    echo "Failed: $TESTS_FAILED"
    echo ""
    echo "❌ Some tests failed. Please review the output above."
    exit 1
else
    echo "Failed: 0"
    echo ""
    echo "✅ All tests passed!"
fi
