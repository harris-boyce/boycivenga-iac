#!/bin/bash
# Integration test runner with UniFi controller readiness checks
#
# This script orchestrates integration test execution with proper environment
# validation and UniFi controller health checking.
#
# Usage:
#   ./scripts/run-integration-tests.sh          # Run all tests
#   ./scripts/run-integration-tests.sh --fast   # Run only fast tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if UniFi integration tests are enabled
if [ "$UNIFI_INTEGRATION_TESTS_ENABLED" != "true" ]; then
    echo "⚠️  UniFi integration tests are disabled"
    echo ""
    echo "Integration tests require the UniFi Network Application sidecar."
    echo "To enable:"
    echo "  1. Ensure you're using the devcontainer with docker-compose.yml"
    echo "  2. Rebuild your devcontainer"
    echo "  3. Set UNIFI_INTEGRATION_TESTS_ENABLED=true (auto-set in docker-compose)"
    echo ""
    exit 0
fi

# Wait for UniFi controller to be ready
echo "🔍 Checking UniFi controller availability..."
"$SCRIPT_DIR/wait-for-unifi.sh" || {
    echo "❌ UniFi controller is not available"
    echo "Check container status:"
    echo "  docker ps"
    echo "  docker logs unifi-test-controller"
    exit 1
}

# Install pytest if not already installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "📦 Installing pytest..."
    pip install -q pytest requests
fi

# Determine test mode
PYTEST_ARGS=()
if [ "$1" = "--fast" ]; then
    echo "🧪 Running fast integration tests..."
    PYTEST_ARGS+=("-m" "fast")
else
    echo "🧪 Running all integration tests..."
fi

# Run integration tests
cd "$REPO_ROOT"

echo ""
echo "Test configuration:"
echo "  UniFi URL: ${UNIFI_TEST_CONTROLLER_URL:-https://localhost:8443}"
echo "  Test directory: tests/integration/"
echo ""

pytest tests/integration/ "${PYTEST_ARGS[@]}" -v --tb=short --color=yes

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All integration tests passed!"
else
    echo "❌ Some integration tests failed (exit code: $EXIT_CODE)"
    echo ""
    echo "Debugging tips:"
    echo "  - View UniFi logs: docker logs unifi-test-controller"
    echo "  - Access UniFi UI: https://localhost:8443 (forward port in VS Code)"
    echo "  - Check test output above for specific failures"
fi

exit $EXIT_CODE
