#!/usr/bin/env python3
"""Tests for render_tfvars.py script.

This test suite validates the NetBox to Terraform tfvars conversion logic
to ensure deterministic and correct output.
"""

import json
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import render_tfvars  # noqa: E402


def test_extract_site_slug():
    """Test site slug extraction logic."""
    # Test with slug field present
    site_with_slug = {"name": "site-pennington", "slug": "site-pennington"}
    assert render_tfvars.extract_site_slug(site_with_slug) == "site-pennington"

    # Test with only name field
    site_without_slug = {"name": "site-pennington"}
    assert render_tfvars.extract_site_slug(site_without_slug) == "site-pennington"

    # Test with empty dict
    empty_site = {}
    assert render_tfvars.extract_site_slug(empty_site) == "unknown"

    print("✅ test_extract_site_slug passed")


def test_render_site_tfvars():
    """Test tfvars rendering for a single site."""
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

    tags = [
        {
            "name": "home-network",
            "slug": "home-network",
            "description": "Home network tag",
            "color": "2196f3",
        }
    ]

    result = render_tfvars.render_site_tfvars(site, prefixes, vlans, tags)

    # Validate structure
    assert "site_name" in result
    assert "site_slug" in result
    assert "site_description" in result
    assert "prefixes" in result
    assert "vlans" in result
    assert "tags" in result

    # Validate values
    assert result["site_name"] == "site-pennington"
    assert result["site_slug"] == "site-pennington"
    assert result["site_description"] == "Primary residence"
    assert len(result["prefixes"]) == 1
    assert len(result["vlans"]) == 1
    assert len(result["tags"]) == 1

    # Validate prefix mapping
    prefix = result["prefixes"][0]
    assert prefix["cidr"] == "192.168.10.0/24"
    assert prefix["vlan_id"] == 10
    assert prefix["description"] == "Home LAN"
    assert prefix["status"] == "active"

    # Validate VLAN mapping
    vlan = result["vlans"][0]
    assert vlan["vlan_id"] == 10
    assert vlan["name"] == "Home LAN"
    assert vlan["description"] == "Default VLAN"
    assert vlan["status"] == "active"

    # Validate tag mapping
    tag = result["tags"][0]
    assert tag["name"] == "home-network"
    assert tag["slug"] == "home-network"
    assert tag["description"] == "Home network tag"
    assert tag["color"] == "2196f3"

    print("✅ test_render_site_tfvars passed")


def test_deterministic_output():
    """Test that the same input produces the same output (determinism)."""
    # Create test data
    site = {"name": "test-site", "slug": "test-site", "description": "Test"}
    prefixes = [{"prefix": "10.0.0.0/24", "vlan": 1, "description": "Test"}]
    vlans = [{"vlan_id": 1, "name": "Test VLAN", "description": "Test"}]
    tags = [{"name": "test", "slug": "test", "description": "Test"}]

    # Generate tfvars multiple times
    results = []
    for _ in range(3):
        result = render_tfvars.render_site_tfvars(site, prefixes, vlans, tags)
        # Convert to JSON string with sorted keys
        json_str = json.dumps(result, indent=2, sort_keys=True)
        results.append(json_str)

    # All results should be identical
    assert all(r == results[0] for r in results), "Output is not deterministic!"

    print("✅ test_deterministic_output passed")


def test_write_and_read_tfvars():
    """Test writing and reading tfvars files."""
    test_tfvars = {
        "site_name": "test-site",
        "site_slug": "test-site",
        "site_description": "Test site",
        "prefixes": [{"cidr": "10.0.0.0/24", "vlan_id": 1, "description": "Test"}],
        "vlans": [{"vlan_id": 1, "name": "Test", "description": "Test"}],
        "tags": [{"name": "test", "slug": "test", "description": "Test"}],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.tfvars.json"

        # Write tfvars
        render_tfvars.write_tfvars_file(test_tfvars, output_path)

        # Verify file exists
        assert output_path.exists(), "Output file was not created"

        # Read and parse the file
        with open(output_path, "r") as f:
            loaded_data = json.load(f)

        # Verify data matches
        assert loaded_data == test_tfvars, "Written data does not match input"

        # Verify file has trailing newline
        with open(output_path, "r") as f:
            content = f.read()
        assert content.endswith("\n"), "File should end with newline"

    print("✅ test_write_and_read_tfvars passed")


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
        result = render_tfvars.load_netbox_export(input_file=input_file)

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
        result = render_tfvars.load_netbox_export(input_dir=input_dir)

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
    tags = []

    result = render_tfvars.render_site_tfvars(site, prefixes, vlans, tags)
    json_str = json.dumps(result, indent=2, sort_keys=True)

    # Parse back to verify key order
    lines = [line.strip() for line in json_str.split("\n") if ":" in line]
    keys = [line.split(":")[0].strip('"') for line in lines]

    # Check that keys are in sorted order
    assert keys == sorted(keys), f"Keys are not sorted: {keys}"

    print("✅ test_json_keys_are_sorted passed")


def run_all_tests():
    """Run all test functions."""
    print("=" * 70)
    print("Running render_tfvars.py tests")
    print("=" * 70)
    print()

    test_functions = [
        test_extract_site_slug,
        test_render_site_tfvars,
        test_deterministic_output,
        test_write_and_read_tfvars,
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
