# Integration Tests

This directory contains integration tests for the UniFi Network Application infrastructure managed by Terraform and the MCP server workflow orchestration.

## Overview

Integration tests validate end-to-end functionality by interacting with a real UniFi controller running as a sidecar container in the devcontainer environment.

### What is Tested

- **Terraform UniFi Provider**: Connectivity, authentication, and resource CRUD operations
- **MCP Server**: Workflow orchestration and GitHub Actions integration
- **End-to-End Flows**: NetBox → Terraform → UniFi controller verification

## Prerequisites

Integration tests require the UniFi Network Application sidecar to be running. This is automatically configured in the devcontainer environment.

### Environment Setup

1. Use the devcontainer with docker-compose.yml (automatic in VS Code/Codespaces)
2. Ensure `UNIFI_INTEGRATION_TESTS_ENABLED=true` (auto-set in docker-compose)
3. Wait for UniFi controller to initialize (~2-3 minutes on first start)

## Running Tests

### Run All Integration Tests

```bash
./scripts/run-integration-tests.sh
```

### Run Fast Tests Only

Fast tests complete in < 30 seconds and are suitable for pre-commit hooks:

```bash
./scripts/run-integration-tests.sh --fast
```

### Run Specific Test File

```bash
pytest tests/integration/terraform/test_unifi_provider.py -v
```

### Run Tests with Specific Marker

```bash
# Only fast tests
pytest tests/integration/ -m "fast" -v

# Only Terraform tests
pytest tests/integration/ -m "terraform" -v

# Only MCP tests
pytest tests/integration/ -m "mcp" -v
```

## Test Organization

```
tests/integration/
├── README.md                    # This file
├── conftest.py                  # Pytest configuration and fixtures
├── helpers/
│   ├── unifi_client.py          # UniFi API client wrapper
│   └── terraform_runner.py      # Terraform execution wrapper
├── terraform/
│   ├── test_unifi_provider.py   # Provider connectivity tests
│   └── test_network_creation.py # Network resource CRUD tests
└── mcp/
    └── test_workflow_integration.py # MCP workflow tests
```

## Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.fast`: Quick tests (< 10s each) suitable for pre-commit
- `@pytest.mark.terraform`: Terraform-specific integration tests
- `@pytest.mark.mcp`: MCP server workflow tests

## Writing New Tests

### Using Fixtures

Integration tests use pytest fixtures for common setup:

```python
import pytest

@pytest.mark.fast
@pytest.mark.terraform
def test_my_feature(unifi_client, terraform_runner, test_network_name):
    """Test description."""
    # unifi_client: Authenticated UniFi API client
    # terraform_runner: Terraform execution wrapper with auto-cleanup
    # test_network_name: Unique network name for test isolation

    # Your test code here
    pass
```

### Test Data Management

- **Unique Names**: Use `test_network_name` fixture for unique resource names
- **Automatic Cleanup**: `terraform_runner` destroys resources in __exit__
- **Manual Cleanup**: `unifi_client.cleanup_test_networks()` removes orphaned test resources

### Example Test

```python
@pytest.mark.fast
@pytest.mark.terraform
def test_create_network(terraform_runner, terraform_vars, test_network_name, unifi_client):
    """Create network via Terraform and verify in UniFi controller."""
    # Configure test VLAN
    terraform_vars["vlans"] = [{
        "vlan_id": 100,
        "name": test_network_name,
        "description": "Test network",
        "status": "active",
    }]

    # Write variables and apply
    var_file = terraform_runner.write_tfvars(terraform_vars)
    terraform_runner.init()
    terraform_runner.apply(auto_approve=True)

    # Verify in UniFi
    networks = unifi_client.get_networks()
    network_names = [net.get("name") for net in networks]
    assert test_network_name in network_names

    # Cleanup happens automatically via fixture
```

## Debugging Test Failures

### View Container Logs

```bash
# UniFi controller logs
docker logs unifi-test-controller

# MongoDB logs
docker logs unifi-mongodb
```

### Access UniFi Web Interface

1. In VS Code, open the Ports panel
2. Forward port 8443
3. Open https://localhost:8443 in browser
4. Login: admin / unifi-integration-test-password

### Check Test Environment

```bash
# Verify environment variables
env | grep UNIFI
env | grep TF_VAR

# Test UniFi controller accessibility
curl -k https://localhost:8443/status

# Run single test with verbose output
pytest tests/integration/terraform/test_unifi_provider.py::test_provider_connectivity -vv -s
```

### Common Issues

**UniFi controller not ready:**
- Wait 2-3 minutes for first initialization
- Check health: `docker inspect unifi-test-controller | grep Health`
- Restart: Rebuild devcontainer

**Terraform provider errors:**
- Verify environment variables are set
- Check `terraform validate` output
- Ensure `allow_insecure=true` for self-signed certificates

**Orphaned test resources:**
- Run cleanup: `python -c "from helpers.unifi_client import UniFiClient; UniFiClient().cleanup_test_networks()"`
- Or destroy manually via UniFi web interface

## CI/CD Integration

Integration tests can run in GitHub Actions using service containers (see Phase 7 implementation).

For now, run integration tests locally or via workflow_dispatch triggers.

## Performance

Expected test durations:

- **Fast tests**: 20-30 seconds total
- **Full suite**: 1-2 minutes total
- **MCP workflow tests**: 3-5 minutes (trigger actual GitHub Actions)

## Additional Resources

- [Terraform UniFi Provider Docs](https://registry.terraform.io/providers/paultyng/unifi/latest/docs)
- [UniFi API Documentation](https://ubntwiki.com/products/software/unifi-controller/api)
- [Pytest Documentation](https://docs.pytest.org/)
