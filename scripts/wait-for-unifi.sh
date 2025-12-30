#!/bin/bash
# Wait for UniFi Network Application controller to be ready
#
# This script polls the UniFi controller health endpoint until it responds
# successfully or a timeout is reached. Used in devcontainer postCreateCommand
# to ensure the controller is ready before running integration tests.

set -e

UNIFI_URL="${UNIFI_TEST_CONTROLLER_URL:-https://localhost:8443}"
MAX_WAIT_SECONDS=180
POLL_INTERVAL=5

echo "Waiting for UniFi controller at $UNIFI_URL..."
echo "This may take up to 2-3 minutes on first startup..."

elapsed=0
while [ $elapsed -lt $MAX_WAIT_SECONDS ]; do
    if curl -k -f -s "$UNIFI_URL/status" >/dev/null 2>&1; then
        echo "✅ UniFi controller is ready!"
        exit 0
    fi

    echo "  ⏳ Still waiting... (${elapsed}s/${MAX_WAIT_SECONDS}s)"
    sleep $POLL_INTERVAL
    elapsed=$((elapsed + POLL_INTERVAL))
done

echo "❌ Timeout waiting for UniFi controller after ${MAX_WAIT_SECONDS}s"
echo "Check container logs:"
echo "  docker logs unifi-test-controller"
echo "  docker logs unifi-mongodb"
exit 1
