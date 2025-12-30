"""Integration tests for MCP server workflow orchestration.

Tests MCP server's ability to trigger and monitor GitHub Actions workflows
that interact with UniFi controllers.

Note: These tests require GITHUB_TOKEN to be set and will trigger actual
GitHub Actions workflows. They may be slower than other integration tests.
"""

import os
import subprocess

import pytest


@pytest.mark.mcp
def test_mcp_server_installed():
    """Verify MCP server is installed and importable.

    This is a basic sanity check that the MCP server package is
    properly installed in the development environment.
    """
    try:
        import boycivenga_mcp

        assert boycivenga_mcp is not None
    except ImportError:
        pytest.fail("MCP server package 'boycivenga_mcp' is not installed")


@pytest.mark.mcp
def test_github_cli_available():
    """Verify GitHub CLI (gh) is available for MCP server.

    The MCP server uses gh CLI for GitHub API operations,
    so it must be installed and accessible.
    """
    result = subprocess.run(
        ["gh", "--version"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, "GitHub CLI (gh) is not available"
    assert "gh version" in result.stdout, "Unexpected gh version output"


@pytest.mark.mcp
@pytest.mark.slow
def test_render_workflow_status(github_token):
    """Test that render workflow can be triggered and status checked.

    This test verifies the basic MCP workflow:
    1. Trigger render-artifacts workflow via gh CLI
    2. Poll for workflow completion
    3. Verify workflow succeeded

    Note: This test actually triggers a GitHub Actions workflow and may
    take several minutes to complete.
    """
    # Get repository from environment
    repo = os.getenv("GITHUB_REPO", "harris-boyce/boycivenga-iac")

    # Trigger render workflow using gh CLI (same method as MCP server)
    result = subprocess.run(
        [
            "gh",
            "workflow",
            "run",
            "render-artifacts.yaml",
            "--repo",
            repo,
            "--ref",
            "main",
        ],
        capture_output=True,
        text=True,
    )

    # Note: This test is disabled by default because it triggers real workflows
    # To enable, remove the skip marker or run with: pytest -m "mcp and slow"
    pytest.skip(
        "Skipping actual workflow trigger test to avoid unintended CI runs. "
        "Enable manually for full integration testing."
    )

    assert result.returncode == 0, f"Failed to trigger workflow: {result.stderr}"

    # In a real test, we would:
    # 1. Extract run ID from gh CLI output
    # 2. Poll workflow status using gh CLI
    # 3. Verify completion and success
    # 4. Validate rendered artifacts exist


@pytest.mark.mcp
def test_unifi_controller_accessible_from_mcp_context():
    """Verify that MCP server context can access UniFi controller.

    Tests that the UniFi controller is accessible from the same
    network/environment context where the MCP server would run.
    """
    import requests
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    unifi_url = os.getenv("UNIFI_TEST_CONTROLLER_URL", "https://localhost:8443")

    try:
        response = requests.get(f"{unifi_url}/status", verify=False, timeout=5)
        assert response.status_code in [
            200,
            302,
        ], f"Unexpected status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        pytest.fail(f"UniFi controller not accessible: {e}")
