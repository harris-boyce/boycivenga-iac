"""Pytest configuration and fixtures for integration tests.

Provides shared fixtures for UniFi client, Terraform runner, and test data management.
"""

import os
import uuid

import pytest

from .helpers.terraform_runner import TerraformRunner
from .helpers.unifi_client import UniFiClient


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "fast: mark test as fast (< 10s)")
    config.addinivalue_line("markers", "terraform: mark test as Terraform-specific")
    config.addinivalue_line("markers", "mcp: mark test as MCP workflow test")


def pytest_collection_modifyitems(config, items):
    """Skip tests if integration testing is not enabled."""
    if os.getenv("UNIFI_INTEGRATION_TESTS_ENABLED") != "true":
        skip_marker = pytest.mark.skip(
            reason=(
                "Integration tests disabled "
                "(UNIFI_INTEGRATION_TESTS_ENABLED != true)"
            )
        )
        for item in items:
            item.add_marker(skip_marker)


@pytest.fixture(scope="session")
def unifi_url():
    """Get UniFi controller URL from environment."""
    return os.getenv("UNIFI_TEST_CONTROLLER_URL", "https://localhost:8443")


@pytest.fixture(scope="session")
def unifi_credentials():
    """Get UniFi controller credentials from environment."""
    return {
        "username": os.getenv("TF_VAR_unifi_username", "admin"),
        "password": os.getenv(
            "TF_VAR_unifi_password", "unifi-integration-test-password"
        ),
    }


@pytest.fixture(scope="session")
def unifi_client(unifi_url, unifi_credentials):
    """Create authenticated UniFi client for the test session.

    This fixture is session-scoped to avoid repeated logins.
    The client remains logged in for the duration of the test session.
    """
    client = UniFiClient(
        url=unifi_url,
        username=unifi_credentials["username"],
        password=unifi_credentials["password"],
    )

    client.login()
    yield client
    client.logout()


@pytest.fixture(scope="session", autouse=True)
def clean_unifi_controller(unifi_client):
    """Ensure UniFi controller is clean before running tests.

    This fixture runs automatically at the start of the test session
    to remove any leftover test resources from previous runs.
    """
    # Cleanup any test networks from previous runs
    deleted = unifi_client.cleanup_test_networks()
    if deleted > 0:
        print(f"\n  Cleaned up {deleted} leftover test network(s) from previous runs")


@pytest.fixture
def test_network_name():
    """Generate unique network name for test isolation."""
    return f"test-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def terraform_runner():
    """Create Terraform runner in temporary directory.

    Automatically cleans up the temporary directory and destroys
    any created resources after the test completes.
    """
    with TerraformRunner() as runner:
        yield runner


@pytest.fixture
def terraform_vars():
    """Get Terraform variables from environment.

    Returns dictionary of variables compatible with write_tfvars().
    Note: UniFi provider credentials (username, password, api_url, allow_insecure)
    are read from TF_VAR_* environment variables and should not be included here.
    """
    return {
        # Minimal site configuration for testing
        "site_name": "Test Site",
        "site_slug": "test",
        "site_description": "Integration test site",
        "vlans": [],
        "prefixes": [],
        "tags": [],
    }


@pytest.fixture
def github_token():
    """Get GitHub token from environment (for MCP tests).

    Skips MCP tests if token is not available.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        pytest.skip("GITHUB_TOKEN not set, skipping MCP workflow test")
    return token
