#!/bin/bash
# Test script for attestation verification gate action
set -e

echo "🧪 Testing Attestation Verification Gate Action"
echo "================================================"
echo ""

# Test 1: Validate action.yml structure
echo "Test 1: Validating action.yml structure..."
python3 -c "
import yaml
import sys

with open('.github/actions/verify-attestation/action.yml') as f:
    action = yaml.safe_load(f)

# Check required fields
assert 'name' in action, 'Missing name field'
assert 'description' in action, 'Missing description field'
assert 'inputs' in action, 'Missing inputs field'
assert 'outputs' in action, 'Missing outputs field'
assert 'runs' in action, 'Missing runs field'

# Check required inputs
assert 'artifact-path' in action['inputs'], 'Missing artifact-path input'
assert action['inputs']['artifact-path']['required'] is True, 'artifact-path should be required'

# Check environment input has correct default
assert action['inputs']['environment']['default'] == 'prod', 'environment default should be prod'

# Check outputs
assert 'verified-count' in action['outputs'], 'Missing verified-count output'
assert 'failed-count' in action['outputs'], 'Missing failed-count output'
assert 'bypassed' in action['outputs'], 'Missing bypassed output'

# Check runs configuration
assert action['runs']['using'] == 'composite', 'Should be a composite action'
assert 'steps' in action['runs'], 'Missing steps in runs'

print('✅ action.yml structure is valid')
"

# Test 2: Check that terraform-plan.yaml uses the action
echo ""
echo "Test 2: Checking terraform-plan.yaml integration..."
grep -q "uses: ./.github/actions/verify-attestation" .github/workflows/terraform-plan.yaml && \
    echo "✅ terraform-plan.yaml uses the verify-attestation action"

# Test 3: Validate documentation exists
echo ""
echo "Test 3: Checking documentation..."
test -f "docs/phase4/attestation-gate.md" && \
    echo "✅ Main documentation exists (attestation-gate.md)"
test -f ".github/actions/verify-attestation/README.md" && \
    echo "✅ Action README exists"

# Test 4: Check documentation contains key sections
echo ""
echo "Test 4: Checking documentation content..."
grep -q "## Purpose" docs/phase4/attestation-gate.md && \
    echo "✅ Documentation has Purpose section"
grep -q "## Usage" docs/phase4/attestation-gate.md && \
    echo "✅ Documentation has Usage section"
grep -q "Production Mode" docs/phase4/attestation-gate.md && \
    echo "✅ Documentation describes production mode"
grep -q "Development Mode" docs/phase4/attestation-gate.md && \
    echo "✅ Documentation describes development mode"

# Test 5: Verify shell script syntax in action
echo ""
echo "Test 5: Validating shell script syntax in action steps..."
# Extract shell scripts from action.yml and validate them
python3 << 'PYEOF'
import yaml
import subprocess
import tempfile

with open('.github/actions/verify-attestation/action.yml') as f:
    action = yaml.safe_load(f)

for i, step in enumerate(action['runs']['steps']):
    if 'run' in step and step.get('shell') == 'bash':
        script = step['run']
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            # Add shebang for shellcheck
            f.write('#!/bin/bash\n')
            # Replace GitHub Actions expressions with dummy values for syntax check
            script = script.replace('${{ inputs.', '${INPUT_')
            script = script.replace('${{ steps.', '${STEPS_')
            script = script.replace('${{ github.', '${GITHUB_')
            script = script.replace(' }}', '}')
            f.write(script)
            temp_path = f.name

        # Basic bash syntax check
        result = subprocess.run(['bash', '-n', temp_path], capture_output=True)
        if result.returncode != 0:
            print(f'❌ Syntax error in step {i}: {step.get("name", "unnamed")}')
            print(result.stderr.decode())
            exit(1)

print('✅ All shell scripts have valid syntax')
PYEOF

echo ""
echo "================================================"
echo "✅ All tests passed!"
echo ""
echo "The attestation verification gate action is ready to use."
