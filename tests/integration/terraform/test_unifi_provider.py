"""Integration tests for Terraform UniFi provider connectivity.

Tests basic provider configuration and authentication.
"""

import pytest


@pytest.mark.fast
@pytest.mark.terraform
def test_provider_connectivity(unifi_client):
    """Verify UniFi controller is accessible and responsive.

    This is a fast sanity check that the UniFi controller is running
    and reachable before attempting Terraform operations.
    """
    # Test connectivity by fetching sites
    sites = unifi_client.get_sites()

    # Should have at least the default site
    assert len(sites) > 0, "No sites found in UniFi controller"

    # Verify default site exists
    site_names = [site.get("name") for site in sites]
    assert "default" in site_names, "Default site not found"


@pytest.mark.fast
@pytest.mark.terraform
def test_provider_authentication(terraform_runner, terraform_vars):
    """Verify Terraform provider can authenticate to UniFi controller.

    Tests that the Terraform UniFi provider is correctly configured
    with credentials and can initialize successfully.
    """
    # Initialize Terraform (downloads provider)
    terraform_runner.init()
    assert terraform_runner.initialized, "Terraform init failed"

    # Validate configuration
    is_valid = terraform_runner.validate()
    assert is_valid, "Terraform configuration is not valid"


@pytest.mark.terraform
def test_provider_configuration_from_env(terraform_runner):
    """Verify Terraform provider reads configuration from environment variables.

    Ensures that TF_VAR_* environment variables are properly set and
    accessible to Terraform configuration.
    """
    import os

    # Verify environment variables are set
    assert os.getenv("TF_VAR_unifi_username"), "TF_VAR_unifi_username not set"
    assert os.getenv("TF_VAR_unifi_password"), "TF_VAR_unifi_password not set"
    assert os.getenv("TF_VAR_unifi_api_url"), "TF_VAR_unifi_api_url not set"
    assert os.getenv(
        "TF_VAR_unifi_allow_insecure"
    ), "TF_VAR_unifi_allow_insecure not set"

    # Initialize and validate
    terraform_runner.init()
    is_valid = terraform_runner.validate()

    assert is_valid, "Terraform provider configuration is invalid"
