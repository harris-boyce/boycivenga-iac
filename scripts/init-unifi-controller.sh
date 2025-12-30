#!/bin/bash
# Initialize UniFi Network Application controller for integration testing
#
# This script sets up a fresh UniFi controller with an admin account
# and default site for testing. It's idempotent and safe to run multiple times.
#
# Usage:
#   ./scripts/init-unifi-controller.sh

set -e

UNIFI_URL="${UNIFI_TEST_CONTROLLER_URL:-https://localhost:8443}"
ADMIN_USER="${TF_VAR_unifi_username:-admin}"
ADMIN_PASS="${TF_VAR_unifi_password:-unifi-integration-test-password}"

echo "🔧 Initializing UniFi controller at $UNIFI_URL..."

# Check if controller is accessible
if ! curl -k -f -s "$UNIFI_URL/status" >/dev/null 2>&1; then
    echo "❌ UniFi controller is not accessible at $UNIFI_URL"
    echo "Run wait-for-unifi.sh first to ensure controller is ready"
    exit 1
fi

# Check if already initialized by trying to access the API
# If we can successfully call an authenticated endpoint, controller is initialized
if curl -k -s -X POST "$UNIFI_URL/api/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASS\"}" \
    -c /tmp/unifi-cookies.txt \
    | grep -q "ok"; then

    echo "✅ UniFi controller already initialized"
    echo "   Admin user: $ADMIN_USER"
    echo "   API URL: $UNIFI_URL"
    rm -f /tmp/unifi-cookies.txt
    exit 0
fi

echo "📋 UniFi controller not initialized, setting up..."

# The UniFi Network Application from linuxserver.io uses a web-based setup wizard
# For automated testing, we need to complete the initial setup programmatically

# Step 1: Complete initial setup wizard
echo "  Setting up admin account..."

# The initial setup typically requires:
# 1. Accept EULA
# 2. Create admin account
# 3. Configure site

# Note: The exact API endpoints for initial setup may vary by UniFi version
# For linuxserver.io image, the setup is often auto-completed or simplified

# Try to create admin user via setup endpoint
SETUP_RESPONSE=$(curl -k -s -X POST "$UNIFI_URL/api/cmd/sitemgr" \
    -H "Content-Type: application/json" \
    -d "{
        \"cmd\": \"add-default-admin\",
        \"name\": \"$ADMIN_USER\",
        \"email\": \"admin@localhost.local\",
        \"x_password\": \"$ADMIN_PASS\"
    }" 2>&1 || true)

# Verify we can now login
if curl -k -s -X POST "$UNIFI_URL/api/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASS\"}" \
    -c /tmp/unifi-cookies.txt \
    | grep -q "ok"; then

    echo "✅ UniFi controller initialized successfully!"
    echo ""
    echo "Controller details:"
    echo "  URL: $UNIFI_URL"
    echo "  Username: $ADMIN_USER"
    echo "  Password: $ADMIN_PASS"
    echo ""
    echo "Access web interface:"
    echo "  1. Forward port 8443 in VS Code"
    echo "  2. Open https://localhost:8443"
    echo "  3. Login with credentials above"

    rm -f /tmp/unifi-cookies.txt
    exit 0
else
    echo "⚠️  Automatic initialization may not be complete"
    echo ""
    echo "The UniFi controller may require manual setup via web interface:"
    echo "  1. Forward port 8443 in VS Code"
    echo "  2. Open https://localhost:8443"
    echo "  3. Complete setup wizard with:"
    echo "     - Username: $ADMIN_USER"
    echo "     - Password: $ADMIN_PASS"
    echo ""
    echo "After manual setup, integration tests will work automatically."

    rm -f /tmp/unifi-cookies.txt
    exit 0
fi
