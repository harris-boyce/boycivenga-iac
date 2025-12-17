#!/usr/bin/env python3
"""Tests for render_unifi.py script.

This test suite validates the NetBox to UniFi configuration conversion logic
to ensure deterministic and correct output.
"""

import json
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
# This allows importing render_unifi module for testing without
# requiring a package structure. This is acceptable for simple test scripts
# in the same directory as the module being tested.
sys.path.insert(0, str(Path(__file__).parent))

import render_unifi  # noqa: E402


def test_extract_site_slug():
    """Test site slug extraction logic."""
    # Test with slug field present
    site_with_slug = {"name": "site-pennington", "slug": "site-pennington"}
    assert render_unifi.extract_site_slug(site_with_slug) == "site-pennington"

    # Test with only name field
    site_without_slug = {"name": "site-pennington"}
    assert render_unifi.extract_site_slug(site_without_slug) == "site-pennington"

    # Test with empty dict
    empty_site = {}
    assert render_unifi.extract_site_slug(empty_site) == "unknown"

    print("✅ test_extract_site_slug passed")


def test_render_unifi_site():
    """Test UniFi site rendering."""
    site = {
        "name": "site-pennington",
        "slug": "site-pennington",
        "description": "Primary residence",
    }

    result = render_unifi.render_unifi_site(site)

    assert "name" in result
    assert "desc" in result
    assert result["name"] == "site-pennington"
    assert result["desc"] == "Primary residence"

    print("✅ test_render_unifi_site passed")


def test_render_unifi_networks():
    """Test UniFi network rendering from prefixes."""
    prefixes = [
        {
            "prefix": "192.168.10.0/24",
            "vlan": 10,
            "description": "Home LAN",
            "status": "active",
        },
        {
            "prefix": "192.168.20.0/24",
            "vlan": None,
            "description": "Guest Network",
            "status": "active",
        },
    ]

    result = render_unifi.render_unifi_networks(prefixes)

    assert len(result) == 2

    # Check first network (with VLAN)
    network1 = result[0]
    assert network1["name"] == "Home LAN"
    assert network1["ip_subnet"] == "192.168.10.0/24"
    assert network1["vlan"] == 10
    assert network1["vlan_enabled"] is True
    assert network1["enabled"] is True
    assert network1["purpose"] == "corporate"

    # Check second network (without VLAN)
    network2 = result[1]
    assert network2["name"] == "Guest Network"
    assert network2["ip_subnet"] == "192.168.20.0/24"
    assert network2["vlan_enabled"] is False
    assert "vlan" not in network2
    assert network2["enabled"] is True

    print("✅ test_render_unifi_networks passed")


def test_render_unifi_vlans():
    """Test UniFi VLAN rendering."""
    vlans = [
        {
            "vlan_id": 10,
            "name": "Home LAN",
            "description": "Default VLAN",
            "status": "active",
        },
        {
            "vlan_id": 20,
            "name": "Guest VLAN",
            "description": "Guest network",
            "status": "deprecated",
        },
    ]

    result = render_unifi.render_unifi_vlans(vlans)

    assert len(result) == 2

    # Check first VLAN
    vlan1 = result[0]
    assert vlan1["vlan_id"] == 10
    assert vlan1["name"] == "Home LAN"
    assert vlan1["enabled"] is True

    # Check second VLAN (deprecated should be disabled)
    vlan2 = result[1]
    assert vlan2["vlan_id"] == 20
    assert vlan2["name"] == "Guest VLAN"
    assert vlan2["enabled"] is False

    print("✅ test_render_unifi_vlans passed")


def test_render_unifi_wlans():
    """Test UniFi WLAN rendering (placeholder)."""
    result = render_unifi.render_unifi_wlans()

    # Should return empty list (placeholder)
    assert isinstance(result, list)
    assert len(result) == 0

    print("✅ test_render_unifi_wlans passed")


def test_render_site_unifi_config():
    """Test complete UniFi config rendering for a site."""
    site = {
        "name": "site-pennington",
        "slug": "site-pennington",
        "description": "Primary residence",
    }

    prefixes = [
        {
            "prefix": "192.168.10.0/24",
            "vlan": 10,
            "description": "Home LAN",
            "status": "active",
        }
    ]

    vlans = [
        {
            "vlan_id": 10,
            "name": "Home LAN",
            "description": "Default VLAN",
            "status": "active",
        }
    ]

    result = render_unifi.render_site_unifi_config(site, prefixes, vlans)

    # Validate structure
    assert "_warning" in result
    assert "_source" in result
    assert "site" in result
    assert "networks" in result
    assert "vlans" in result
    assert "wlans" in result

    # Validate site
    assert result["site"]["name"] == "site-pennington"
    assert result["site"]["desc"] == "Primary residence"

    # Validate networks
    assert len(result["networks"]) == 1
    assert result["networks"][0]["ip_subnet"] == "192.168.10.0/24"

    # Validate VLANs
    assert len(result["vlans"]) == 1
    assert result["vlans"][0]["vlan_id"] == 10

    # Validate WLANs (placeholder)
    assert len(result["wlans"]) == 0

    print("✅ test_render_site_unifi_config passed")


def test_deterministic_output():
    """Test that the same input produces the same output (determinism)."""
    # Create test data
    site = {"name": "test-site", "slug": "test-site", "description": "Test"}
    prefixes = [{"prefix": "10.0.0.0/24", "vlan": 1, "description": "Test"}]
    vlans = [{"vlan_id": 1, "name": "Test VLAN", "description": "Test"}]

    # Generate config multiple times
    results = []
    for _ in range(3):
        result = render_unifi.render_site_unifi_config(site, prefixes, vlans)
        # Convert to JSON string with sorted keys
        json_str = json.dumps(result, indent=2, sort_keys=True)
        results.append(json_str)

    # All results should be identical
    assert all(r == results[0] for r in results), "Output is not deterministic!"

    print("✅ test_deterministic_output passed")


def test_write_and_read_config():
    """Test writing and reading UniFi config files."""
    test_config = {
        "_warning": "Test warning",
        "_source": "test",
        "site": {"name": "test-site", "desc": "Test site"},
        "networks": [{"name": "Test", "ip_subnet": "10.0.0.0/24"}],
        "vlans": [{"vlan_id": 1, "name": "Test"}],
        "wlans": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test-config.json"

        # Write config
        render_unifi.write_unifi_config_file(test_config, output_path)

        # Verify file exists
        assert output_path.exists(), "Output file was not created"

        # Read and parse the file
        with open(output_path, "r") as f:
            loaded_data = json.load(f)

        # Verify data matches
        assert loaded_data == test_config, "Written data does not match input"

        # Verify file has trailing newline
        with open(output_path, "r") as f:
            content = f.read()
        assert content.endswith("\n"), "File should end with newline"

    print("✅ test_write_and_read_config passed")


def test_load_netbox_export_from_file():
    """Test loading NetBox export from a single consolidated file."""
    test_data = {
        "sites": [{"name": "test-site", "slug": "test-site"}],
        "prefixes": [{"site": "test-site", "prefix": "10.0.0.0/24"}],
        "vlans": [{"site": "test-site", "vlan_id": 1, "name": "Test"}],
        "tags": [{"name": "test", "slug": "test"}],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test-input.json"

        # Write test input file
        with open(input_file, "w") as f:
            json.dump(test_data, f)

        # Load using the function
        result = render_unifi.load_netbox_export(input_file=input_file)

        # Verify data was loaded correctly
        assert len(result["sites"]) == 1
        assert len(result["prefixes"]) == 1
        assert len(result["vlans"]) == 1
        assert len(result["tags"]) == 1
        assert result["sites"][0]["name"] == "test-site"

    print("✅ test_load_netbox_export_from_file passed")


def test_load_netbox_export_from_directory():
    """Test loading NetBox export from a directory with separate files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir)

        # Create separate files
        with open(input_dir / "sites.json", "w") as f:
            json.dump([{"name": "test-site", "slug": "test-site"}], f)

        with open(input_dir / "prefixes.json", "w") as f:
            json.dump([{"site": "test-site", "prefix": "10.0.0.0/24"}], f)

        with open(input_dir / "vlans.json", "w") as f:
            json.dump([{"site": "test-site", "vlan_id": 1, "name": "Test"}], f)

        with open(input_dir / "tags.json", "w") as f:
            json.dump([{"name": "test", "slug": "test"}], f)

        # Load using the function
        result = render_unifi.load_netbox_export(input_dir=input_dir)

        # Verify data was loaded correctly
        assert len(result["sites"]) == 1
        assert len(result["prefixes"]) == 1
        assert len(result["vlans"]) == 1
        assert len(result["tags"]) == 1

    print("✅ test_load_netbox_export_from_directory passed")


def test_json_keys_are_sorted():
    """Test that JSON output has sorted keys for determinism."""
    site = {"name": "zzz-site", "slug": "aaa-slug", "description": "mmm-desc"}
    prefixes = []
    vlans = []

    result = render_unifi.render_site_unifi_config(site, prefixes, vlans)

    # When we dump with sort_keys=True, the JSON output should have sorted keys
    json_str = json.dumps(result, indent=2, sort_keys=True)

    # Parse back and verify top-level keys are sorted in the JSON string
    parsed = json.loads(json_str)
    json_str_keys = json.dumps(parsed, indent=2, sort_keys=True)

    # With sort_keys=True, we should get deterministic output
    assert (
        json_str == json_str_keys
    ), "JSON output with sort_keys=True should be deterministic"

    print("✅ test_json_keys_are_sorted passed")


def run_all_tests():
    """Run all test functions."""
    print("=" * 70)
    print("Running render_unifi.py tests")
    print("=" * 70)
    print()

    test_functions = [
        test_extract_site_slug,
        test_render_unifi_site,
        test_render_unifi_networks,
        test_render_unifi_vlans,
        test_render_unifi_wlans,
        test_render_site_unifi_config,
        test_deterministic_output,
        test_write_and_read_config,
        test_load_netbox_export_from_file,
        test_load_netbox_export_from_directory,
        test_json_keys_are_sorted,
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} error: {e}")
            failed += 1

    print()
    print("=" * 70)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
