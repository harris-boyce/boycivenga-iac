"""Integration tests for UniFi API apply and plan scripts.

Tests the direct API integration that replaces Terraform for network creation.
"""

import json
import subprocess

import pytest


@pytest.fixture
def test_tfvars(tmp_path):
    """Create a test tfvars file."""
    tfvars = {
        "site_name": "Test Site",
        "site_slug": "test",
        "site_description": "Integration test site",
        "vlans": [
            {
                "vlan_id": 200,
                "name": "test-api-200",
                "description": "Test network via API",
                "status": "active",
            }
        ],
        "prefixes": [
            {
                "cidr": "10.200.0.0/24",
                "vlan_id": 200,
                "description": "Test prefix",
                "status": "active",
            }
        ],
        "tags": [],
    }

    tfvars_file = tmp_path / "test.tfvars.json"
    with open(tfvars_file, "w") as f:
        json.dump(tfvars, f, indent=2)

    return tfvars_file


@pytest.fixture
def cleanup_test_networks(unifi_client):
    """Clean up test networks before and after tests."""
    # Clean up before test
    unifi_client.cleanup_test_networks()
    yield
    # Clean up after test
    unifi_client.cleanup_test_networks()


def test_apply_creates_network(
    test_tfvars, unifi_client, tmp_path, cleanup_test_networks
):
    """Test that apply script creates networks correctly."""
    state_file = tmp_path / "state.json"

    # Run apply script
    result = subprocess.run(
        [
            "python",
            "scripts/apply_via_unifi.py",
            "--tfvars",
            str(test_tfvars),
            "--state-file",
            str(state_file),
        ],
        capture_output=True,
        text=True,
    )

    # Check script succeeded
    assert result.returncode == 0, f"Apply failed: {result.stderr}"
    assert "Apply completed successfully" in result.stdout

    # Verify network was created in UniFi
    networks = unifi_client.get_networks()
    test_network = next((n for n in networks if n.get("name") == "test-api-200"), None)

    assert test_network is not None, "Network was not created"
    assert test_network.get("vlan") == 200
    assert test_network.get("ip_subnet") == "10.200.0.1/24"
    assert test_network.get("dhcpd_enabled") is True
    assert test_network.get("dhcpd_start") == "10.200.0.6"
    assert test_network.get("dhcpd_stop") == "10.200.0.254"

    # Verify state file was created
    assert state_file.exists(), "State file was not created"

    with open(state_file) as f:
        state = json.load(f)

    assert state["format_version"] == "1.0"
    assert len(state["networks"]) == 1
    assert state["networks"][0]["name"] == "test-api-200"
    assert state["networks"][0]["vlan_id"] == 200


def test_apply_is_idempotent(
    test_tfvars, unifi_client, tmp_path, cleanup_test_networks
):
    """Test that applying twice doesn't duplicate resources."""
    state_file = tmp_path / "state.json"

    # Apply first time
    result1 = subprocess.run(
        [
            "python",
            "scripts/apply_via_unifi.py",
            "--tfvars",
            str(test_tfvars),
            "--state-file",
            str(state_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result1.returncode == 0, f"First apply failed: {result1.stderr}"

    # Apply second time
    result2 = subprocess.run(
        [
            "python",
            "scripts/apply_via_unifi.py",
            "--tfvars",
            str(test_tfvars),
            "--state-file",
            str(state_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0, f"Second apply failed: {result2.stderr}"

    # Verify only one network exists
    networks = unifi_client.get_networks()
    test_networks = [n for n in networks if n.get("name") == "test-api-200"]

    assert (
        len(test_networks) == 1
    ), "Idempotency check failed - duplicate network created"


def test_plan_detects_changes(
    test_tfvars, unifi_client, tmp_path, cleanup_test_networks
):
    """Test that plan script detects changes when network doesn't exist."""
    state_file = tmp_path / "state.json"

    # Run plan script (network doesn't exist yet)
    result = subprocess.run(
        [
            "python",
            "scripts/plan_unifi.py",
            "--tfvars",
            str(test_tfvars),
            "--state-file",
            str(state_file),
        ],
        capture_output=True,
        text=True,
    )

    # Plan should exit with code 2 (changes detected)
    assert result.returncode == 2, f"Plan should detect changes: {result.stderr}"
    assert "to create" in result.stdout
    assert "test-api-200" in result.stdout


def test_plan_no_changes_after_apply(
    test_tfvars, unifi_client, tmp_path, cleanup_test_networks
):
    """Test that plan shows no changes after successful apply."""
    state_file = tmp_path / "state.json"

    # Apply first
    apply_result = subprocess.run(
        [
            "python",
            "scripts/apply_via_unifi.py",
            "--tfvars",
            str(test_tfvars),
            "--state-file",
            str(state_file),
        ],
        capture_output=True,
        text=True,
    )
    assert apply_result.returncode == 0, f"Apply failed: {apply_result.stderr}"

    # Run plan
    plan_result = subprocess.run(
        [
            "python",
            "scripts/plan_unifi.py",
            "--tfvars",
            str(test_tfvars),
            "--state-file",
            str(state_file),
        ],
        capture_output=True,
        text=True,
    )

    # Plan should exit with code 0 (no changes)
    assert plan_result.returncode == 0, f"Plan failed: {plan_result.stderr}"
    assert "No changes needed" in plan_result.stdout


def test_plan_detects_drift(test_tfvars, unifi_client, tmp_path, cleanup_test_networks):
    """Test that plan detects manual changes (drift)."""
    state_file = tmp_path / "state.json"

    # Apply network
    apply_result = subprocess.run(
        [
            "python",
            "scripts/apply_via_unifi.py",
            "--tfvars",
            str(test_tfvars),
            "--state-file",
            str(state_file),
        ],
        capture_output=True,
        text=True,
    )
    assert apply_result.returncode == 0, f"Apply failed: {apply_result.stderr}"

    # Manually modify the network in UniFi
    network = unifi_client.find_network_by_name("test-api-200")
    assert network is not None, "Network not found for drift test"

    modified_config = {
        **network,
        "dhcpd_start": "10.200.0.10",  # Change DHCP range
    }
    unifi_client.update_network(network["_id"], modified_config)

    # Run plan - should detect drift
    plan_result = subprocess.run(
        [
            "python",
            "scripts/plan_unifi.py",
            "--tfvars",
            str(test_tfvars),
            "--state-file",
            str(state_file),
        ],
        capture_output=True,
        text=True,
    )

    # Plan should show drift warning and update needed
    assert "DRIFT DETECTED" in plan_result.stdout or "to update" in plan_result.stdout
    assert "dhcpd_start" in plan_result.stdout


def test_dry_run_mode(test_tfvars, unifi_client, tmp_path, cleanup_test_networks):
    """Test that dry-run mode doesn't create resources."""
    state_file = tmp_path / "state.json"

    # Run apply in dry-run mode
    result = subprocess.run(
        [
            "python",
            "scripts/apply_via_unifi.py",
            "--tfvars",
            str(test_tfvars),
            "--state-file",
            str(state_file),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Dry-run failed: {result.stderr}"
    assert "DRY RUN" in result.stdout or "Would apply" in result.stdout

    # Verify network was NOT created
    networks = unifi_client.get_networks()
    test_network = next((n for n in networks if n.get("name") == "test-api-200"), None)

    assert test_network is None, "Network should not be created in dry-run mode"

    # Verify state file was NOT created
    assert not state_file.exists(), "State file should not be created in dry-run mode"
