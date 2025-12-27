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
# This allows importing render_tfvars module for testing without
# requiring a package structure. This is acceptable for simple test scripts
# in the same directory as the module being tested.
sys.path.insert(0, str(Path(__file__).parent))

import render_tfvars  # noqa: E402


def test_extract_status_value():
    """Test status value extraction from NetBox format."""
    # Test with NetBox API object format
    status_obj = {"label": "Reserved", "value": "reserved"}
    assert render_tfvars.extract_status_value(status_obj) == "reserved"

    # Test with plain string format
    assert render_tfvars.extract_status_value("active") == "active"

    # Test with None
    assert render_tfvars.extract_status_value(None) == "active"

    # Test with deprecated status
    status_deprecated = {"label": "Deprecated", "value": "deprecated"}
    assert render_tfvars.extract_status_value(status_deprecated) == "deprecated"

    print("✅ test_extract_status_value passed")


def test_extract_vlan_id():
    """Test VLAN ID extraction with validation."""
    # Test with 'vid' field (NetBox API)
    vlan_with_vid = {"vid": 10, "name": "Test VLAN", "site": "test-site"}
    assert render_tfvars.extract_vlan_id(vlan_with_vid) == 10

    # Test with 'vlan_id' field (minimal schema)
    vlan_with_id = {"vlan_id": 20, "name": "Test VLAN", "site": "test-site"}
    assert render_tfvars.extract_vlan_id(vlan_with_id) == 20

    # Test with VLAN ID 0 (edge case, should work)
    vlan_with_zero = {"vid": 0, "name": "Default VLAN", "site": "test-site"}
    assert render_tfvars.extract_vlan_id(vlan_with_zero) == 0

    # Test with null vlan_id (should raise ValueError)
    vlan_null_id = {"vlan_id": None, "name": "Test VLAN", "site": "test-site"}
    try:
        render_tfvars.extract_vlan_id(vlan_null_id)
        assert False, "Should have raised ValueError for null vlan_id"
    except ValueError as e:
        assert "no VLAN ID assigned" in str(e)

    # Test with missing vlan_id (should raise ValueError)
    vlan_missing_id = {"name": "Test VLAN", "site": "test-site"}
    try:
        render_tfvars.extract_vlan_id(vlan_missing_id)
        assert False, "Should have raised ValueError for missing vlan_id"
    except ValueError as e:
        assert "no VLAN ID assigned" in str(e)

    print("✅ test_extract_vlan_id passed")


def test_extract_vlan_association():
    """Test VLAN association extraction from prefix data."""
    # Test with simple integer VLAN ID
    prefix_simple = {"prefix": "10.0.0.0/24", "vlan": 10}
    assert render_tfvars.extract_vlan_association(prefix_simple) == 10

    # Test with VLAN ID 0 (edge case)
    prefix_zero = {"prefix": "10.0.0.0/24", "vlan": 0}
    assert render_tfvars.extract_vlan_association(prefix_zero) == 0

    # Test with nested VLAN object (vid field)
    prefix_nested_vid = {
        "prefix": "10.0.0.0/24",
        "vlan": {"vid": 20, "name": "Test VLAN"},
    }
    assert render_tfvars.extract_vlan_association(prefix_nested_vid) == 20

    # Test with nested VLAN object (vlan_id field)
    prefix_nested_id = {
        "prefix": "10.0.0.0/24",
        "vlan": {"vlan_id": 30, "name": "Test VLAN"},
    }
    assert render_tfvars.extract_vlan_association(prefix_nested_id) == 30

    # Test with nested VLAN object with vid=0 (edge case)
    prefix_nested_zero = {
        "prefix": "10.0.0.0/24",
        "vlan": {"vid": 0, "name": "Default VLAN"},
    }
    assert render_tfvars.extract_vlan_association(prefix_nested_zero) == 0

    # Test with no VLAN association
    prefix_no_vlan = {"prefix": "10.0.0.0/24"}
    assert render_tfvars.extract_vlan_association(prefix_no_vlan) is None

    # Test with null VLAN
    prefix_null_vlan = {"prefix": "10.0.0.0/24", "vlan": None}
    assert render_tfvars.extract_vlan_association(prefix_null_vlan) is None

    print("✅ test_extract_vlan_association passed")


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


def test_render_site_tfvars_with_netbox_status_objects():
    """Test tfvars rendering with NetBox API status objects."""
    site = {
        "name": "Count Fleet Court",
        "slug": "count-fleet-court",
        "description": "Secondary family residence",
    }

    prefixes = [
        {
            "prefix": "10.2.10.0/24",
            "vlan": {"vid": 10, "name": "CFC_Home_General"},
            "description": "Home/General VLAN subnet",
            "status": {"label": "Reserved", "value": "reserved"},
        }
    ]

    vlans = [
        {
            "vid": 10,
            "name": "CFC_Home_General",
            "description": "Family devices",
            "status": {"label": "Reserved", "value": "reserved"},
        }
    ]

    tags = []

    result = render_tfvars.render_site_tfvars(site, prefixes, vlans, tags)

    # Validate status extraction
    assert result["prefixes"][0]["status"] == "reserved"
    assert result["vlans"][0]["status"] == "reserved"

    # Validate VLAN ID extraction from nested object
    assert result["prefixes"][0]["vlan_id"] == 10
    assert result["vlans"][0]["vlan_id"] == 10

    print("✅ test_render_site_tfvars_with_netbox_status_objects passed")


def test_render_site_tfvars_with_null_vlan_id():
    """Test that null VLAN ID raises clear error."""
    site = {"name": "test-site", "slug": "test-site"}
    prefixes = []
    vlans = [
        {
            "vlan_id": None,
            "name": "Test VLAN",
            "description": "Test",
            "status": "active",
        }
    ]
    tags = []

    try:
        render_tfvars.render_site_tfvars(site, prefixes, vlans, tags)
        assert False, "Should have raised ValueError for null vlan_id"
    except ValueError as e:
        error_msg = str(e)
        assert "no VLAN ID assigned" in error_msg
        assert "test-site" in error_msg

    print("✅ test_render_site_tfvars_with_null_vlan_id passed")


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


def test_build_vlan_site_mapping():
    """Test VLAN to site mapping construction."""
    vlans = [
        {"vid": 10, "site": {"slug": "site-a", "name": "Site A"}},
        {"vid": 20, "site": {"slug": "site-b", "name": "Site B"}},
        {"vid": 30, "site": "site-a"},  # Minimal schema format
        {"vid": 40, "site": None},  # No site
    ]

    mapping = render_tfvars.build_vlan_site_mapping(vlans)

    assert mapping[10] == "site-a"
    assert mapping[20] == "site-b"
    assert mapping[30] == "site-a"
    assert 40 not in mapping  # VLAN without site excluded

    print("✅ test_build_vlan_site_mapping passed")


def test_build_vlan_site_mapping_with_collisions():
    """Test VLAN mapping handles ID collisions."""
    vlans = [
        {"vid": 10, "site": {"slug": "site-a"}},
        {"vid": 10, "site": {"slug": "site-b"}},  # Same VLAN ID
    ]

    # Should log warning but not crash
    mapping = render_tfvars.build_vlan_site_mapping(vlans)

    # One of them should be in the mapping (last one wins)
    assert 10 in mapping
    assert mapping[10] in ["site-a", "site-b"]

    print("✅ test_build_vlan_site_mapping_with_collisions passed")


def test_extract_prefix_site_via_vlan():
    """Test prefix site extraction via VLAN association."""
    prefix = {
        "prefix": "10.1.10.0/24",
        "vlan": {"vid": 10, "name": "LAN"},
    }
    vlan_mapping = {10: "pennington", 20: "other-site"}

    site = render_tfvars.extract_prefix_site(prefix, vlan_mapping)
    assert site == "pennington"

    print("✅ test_extract_prefix_site_via_vlan passed")


def test_extract_prefix_site_direct():
    """Test prefix site extraction with direct site field."""
    prefix = {
        "prefix": "10.1.10.0/24",
        "site": "pennington",  # Minimal schema format
        "vlan": 10,
    }
    vlan_mapping = {}

    # Should use direct site field, not VLAN lookup
    site = render_tfvars.extract_prefix_site(prefix, vlan_mapping)
    assert site == "pennington"

    print("✅ test_extract_prefix_site_direct passed")


def test_extract_prefix_site_no_match():
    """Test prefix without site returns None."""
    prefix = {
        "prefix": "10.0.0.0/8",
        "vlan": None,  # No VLAN
    }
    vlan_mapping = {10: "site-a"}

    site = render_tfvars.extract_prefix_site(prefix, vlan_mapping)
    assert site is None

    print("✅ test_extract_prefix_site_no_match passed")


def test_filter_resources_by_site_prefixes():
    """Test filtering prefixes by site via VLAN mapping."""
    prefixes = [
        {"prefix": "10.1.0.0/24", "vlan": {"vid": 10}},
        {"prefix": "10.2.0.0/24", "vlan": {"vid": 20}},
        {"prefix": "10.0.0.0/8", "vlan": None},  # No VLAN
    ]
    vlan_mapping = {10: "site-a", 20: "site-b"}

    filtered = render_tfvars.filter_resources_by_site(
        prefixes, "site-a", "Site A", "prefix", vlan_mapping
    )

    assert len(filtered) == 1
    assert filtered[0]["prefix"] == "10.1.0.0/24"

    print("✅ test_filter_resources_by_site_prefixes passed")


def test_filter_resources_by_site_vlans():
    """Test filtering VLANs by site (direct site field)."""
    vlans = [
        {"vid": 10, "site": {"slug": "site-a"}},
        {"vid": 20, "site": {"slug": "site-b"}},
        {"vid": 30, "site": "site-a"},  # Minimal schema
    ]

    filtered = render_tfvars.filter_resources_by_site(vlans, "site-a", "Site A", "vlan")

    assert len(filtered) == 2
    assert filtered[0]["vid"] == 10
    assert filtered[1]["vid"] == 30

    print("✅ test_filter_resources_by_site_vlans passed")


def test_end_to_end_with_netbox_api_format():
    """Test full workflow with NetBox API format data."""
    # Create test data matching NetBox API structure
    test_data = {
        "sites": [{"name": "Pennington", "slug": "pennington"}],
        "vlans": [
            {
                "vid": 10,
                "name": "LAN",
                "site": {"slug": "pennington", "name": "Pennington"},
            }
        ],
        "prefixes": [
            {
                "prefix": "10.1.10.0/24",
                "vlan": {"vid": 10, "name": "LAN"},
                "description": "Home network",
                "status": {"value": "active"},
            }
        ],
        "tags": [],
    }

    # Write to temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "input.json"

        with open(input_file, "w") as f:
            json.dump(test_data, f)

        # Load data
        loaded_data = render_tfvars.load_netbox_export(input_file=input_file)

        # Build VLAN mapping
        vlan_mapping = render_tfvars.build_vlan_site_mapping(loaded_data["vlans"])

        # Filter prefixes for Pennington site
        site_prefixes = render_tfvars.filter_resources_by_site(
            loaded_data["prefixes"], "pennington", "Pennington", "prefix", vlan_mapping
        )

        # Verify the prefix was matched
        assert len(site_prefixes) == 1
        assert site_prefixes[0]["prefix"] == "10.1.10.0/24"

    print("✅ test_end_to_end_with_netbox_api_format passed")


def test_backward_compatibility_minimal_schema():
    """Test that minimal schema format still works."""
    test_data = {
        "sites": [{"name": "site-a", "slug": "site-a"}],
        "prefixes": [
            {"site": "site-a", "prefix": "10.0.0.0/24", "vlan": 10, "status": "active"}
        ],
        "vlans": [{"site": "site-a", "vlan_id": 10, "name": "LAN"}],
        "tags": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "input.json"

        with open(input_file, "w") as f:
            json.dump(test_data, f)

        # Load data
        loaded_data = render_tfvars.load_netbox_export(input_file=input_file)

        # Build VLAN mapping
        vlan_mapping = render_tfvars.build_vlan_site_mapping(loaded_data["vlans"])

        # Filter prefixes for site-a
        site_prefixes = render_tfvars.filter_resources_by_site(
            loaded_data["prefixes"], "site-a", "site-a", "prefix", vlan_mapping
        )

        # Verify the prefix was matched (using direct site field, not VLAN)
        assert len(site_prefixes) == 1
        assert site_prefixes[0]["prefix"] == "10.0.0.0/24"

    print("✅ test_backward_compatibility_minimal_schema passed")


def test_vlans_without_prefixes_filtered():
    """Test that VLANs without prefixes are filtered out."""
    test_data = {
        "sites": [{"name": "test-site", "slug": "test-site"}],
        "prefixes": [
            # Only one prefix for VLAN 10
            {
                "site": "test-site",
                "prefix": "10.0.0.0/24",
                "vlan": 10,
                "status": "active",
            }
        ],
        "vlans": [
            {"site": "test-site", "vlan_id": 10, "name": "LAN"},  # Has prefix
            {"site": "test-site", "vlan_id": 20, "name": "GUEST"},  # No prefix
            {"site": "test-site", "vlan_id": 30, "name": "MGMT"},  # No prefix
        ],
        "tags": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "input.json"

        with open(input_file, "w") as f:
            json.dump(test_data, f)

        # Load data
        loaded_data = render_tfvars.load_netbox_export(input_file=input_file)

        # Build VLAN mapping
        vlan_mapping = render_tfvars.build_vlan_site_mapping(loaded_data["vlans"])

        # Filter prefixes and VLANs
        site_prefixes = render_tfvars.filter_resources_by_site(
            loaded_data["prefixes"], "test-site", "test-site", "prefix", vlan_mapping
        )
        site_vlans = render_tfvars.filter_resources_by_site(
            loaded_data["vlans"], "test-site", "test-site", "vlan"
        )

        # Filter VLANs to only those with prefixes (simulating main() logic)
        prefix_vlan_ids = {
            render_tfvars.extract_vlan_association(p)
            for p in site_prefixes
            if render_tfvars.extract_vlan_association(p) is not None
        }
        site_vlans_with_prefixes = [
            v for v in site_vlans if render_tfvars.extract_vlan_id(v) in prefix_vlan_ids
        ]

        # Should only have 1 VLAN (the one with a prefix)
        assert len(site_vlans_with_prefixes) == 1
        assert site_vlans_with_prefixes[0]["vlan_id"] == 10

        # Verify 2 VLANs were filtered out
        assert len(site_vlans) == 3  # All VLANs for site
        assert len(site_vlans_with_prefixes) == 1  # Only those with prefixes

    print("✅ test_vlans_without_prefixes_filtered passed")


def run_all_tests():
    """Run all test functions."""
    print("=" * 70)
    print("Running render_tfvars.py tests")
    print("=" * 70)
    print()

    test_functions = [
        test_extract_status_value,
        test_extract_vlan_id,
        test_extract_vlan_association,
        test_extract_site_slug,
        test_render_site_tfvars,
        test_render_site_tfvars_with_netbox_status_objects,
        test_render_site_tfvars_with_null_vlan_id,
        test_deterministic_output,
        test_write_and_read_tfvars,
        test_load_netbox_export_from_file,
        test_load_netbox_export_from_directory,
        test_json_keys_are_sorted,
        test_build_vlan_site_mapping,
        test_build_vlan_site_mapping_with_collisions,
        test_extract_prefix_site_via_vlan,
        test_extract_prefix_site_direct,
        test_extract_prefix_site_no_match,
        test_filter_resources_by_site_prefixes,
        test_filter_resources_by_site_vlans,
        test_end_to_end_with_netbox_api_format,
        test_backward_compatibility_minimal_schema,
        test_vlans_without_prefixes_filtered,
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
