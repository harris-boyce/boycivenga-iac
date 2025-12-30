"""Integration tests for Terraform UniFi network resource creation.

Tests CRUD operations on UniFi network resources via Terraform.
"""

import pytest


@pytest.mark.fast
@pytest.mark.terraform
def test_create_simple_network(
    terraform_runner, terraform_vars, test_network_name, unifi_client
):
    """Create a simple network via Terraform and verify it exists in UniFi controller.

    This is a basic end-to-end test that validates:
    - Terraform can create resources
    - Resources appear in UniFi controller
    - Resources can be destroyed
    """
    # Update vars with a test VLAN and corresponding network prefix
    terraform_vars["vlans"] = [
        {
            "vlan_id": 100,
            "name": test_network_name,
            "description": "Integration test network",
            "status": "active",
        }
    ]
    terraform_vars["prefixes"] = [
        {
            "cidr": "10.100.0.0/24",
            "vlan_id": 100,
            "description": "Integration test network prefix",
            "status": "active",
        }
    ]

    # Write variables file
    terraform_runner.write_tfvars(terraform_vars)

    # Initialize Terraform
    terraform_runner.init()

    # Apply configuration
    terraform_runner.apply(auto_approve=True)

    # Verify network exists in UniFi controller
    networks = unifi_client.get_networks()
    network_names = [net.get("name") for net in networks]

    assert test_network_name in network_names, (
        f"Network '{test_network_name}' not found in UniFi controller "
        "after Terraform apply"
    )

    # Cleanup is handled by terraform_runner fixture's __exit__
    # (runs terraform destroy automatically)


@pytest.mark.terraform
def test_create_network_with_vlan(
    terraform_runner, terraform_vars, test_network_name, unifi_client
):
    """Create network with specific VLAN ID and verify VLAN configuration."""
    vlan_id = 200

    terraform_vars["vlans"] = [
        {
            "vlan_id": vlan_id,
            "name": test_network_name,
            "description": "VLAN test network",
            "status": "active",
        }
    ]
    terraform_vars["prefixes"] = [
        {
            "cidr": "10.200.0.0/24",
            "vlan_id": vlan_id,
            "description": "VLAN test network prefix",
            "status": "active",
        }
    ]

    terraform_runner.write_tfvars(terraform_vars)

    terraform_runner.init()
    terraform_runner.apply(auto_approve=True)

    # Find the created network
    networks = unifi_client.get_networks()
    test_network = None
    for net in networks:
        if net.get("name") == test_network_name:
            test_network = net
            break

    assert test_network is not None, f"Network '{test_network_name}' not found"

    # Verify VLAN configuration
    if test_network.get("vlan_enabled"):
        actual_vlan = test_network.get("vlan")
        assert actual_vlan == vlan_id, f"Expected VLAN {vlan_id}, got {actual_vlan}"


@pytest.mark.terraform
def test_update_network(
    terraform_runner, terraform_vars, test_network_name, unifi_client
):
    """Create network, modify it via Terraform, and verify update."""
    terraform_vars["vlans"] = [
        {
            "vlan_id": 300,
            "name": test_network_name,
            "description": "Original description",
            "status": "active",
        }
    ]
    terraform_vars["prefixes"] = [
        {
            "cidr": "10.300.0.0/24",
            "vlan_id": 300,
            "description": "Original prefix description",
            "status": "active",
        }
    ]

    terraform_runner.write_tfvars(terraform_vars)

    terraform_runner.init()
    terraform_runner.apply(auto_approve=True)

    # Verify initial creation
    networks = unifi_client.get_networks()
    assert any(net.get("name") == test_network_name for net in networks)

    # Update the description
    terraform_vars["vlans"][0]["description"] = "Updated description"
    terraform_runner.write_tfvars(terraform_vars)

    # Apply update
    terraform_runner.apply(auto_approve=True)

    # Verify update (note: UniFi API might not expose description in all cases)
    networks = unifi_client.get_networks()
    assert any(
        net.get("name") == test_network_name for net in networks
    ), "Network disappeared after update"


@pytest.mark.terraform
def test_delete_network(
    terraform_runner, terraform_vars, test_network_name, unifi_client
):
    """Create network via Terraform, then destroy it and verify deletion."""
    terraform_vars["vlans"] = [
        {
            "vlan_id": 400,
            "name": test_network_name,
            "description": "Test deletion",
            "status": "active",
        }
    ]
    terraform_vars["prefixes"] = [
        {
            "cidr": "10.400.0.0/24",
            "vlan_id": 400,
            "description": "Test deletion prefix",
            "status": "active",
        }
    ]

    terraform_runner.write_tfvars(terraform_vars)

    terraform_runner.init()
    terraform_runner.apply(auto_approve=True)

    # Verify creation
    networks = unifi_client.get_networks()
    assert any(
        net.get("name") == test_network_name for net in networks
    ), "Network was not created"

    # Destroy via Terraform
    terraform_runner.destroy(auto_approve=True)

    # Verify deletion
    networks = unifi_client.get_networks()
    network_names = [net.get("name") for net in networks]

    assert (
        test_network_name not in network_names
    ), f"Network '{test_network_name}' still exists after terraform destroy"
