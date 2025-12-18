#!/usr/bin/env python3
"""Tests for render_md_summary.py script.

This test suite validates the NetBox to Markdown summary conversion logic
to ensure correct output format and content.
"""

import sys
import tempfile
from pathlib import Path

# Add scripts directory to path for imports
# This allows importing render_md_summary module for testing without
# requiring a package structure. Both files are in the scripts directory.
sys.path.insert(0, str(Path(__file__).parent))

import render_md_summary  # noqa: E402


def test_extract_site_slug():
    """Test site slug extraction logic."""
    # Test with slug field present
    site_with_slug = {"name": "site-pennington", "slug": "site-pennington"}
    assert render_md_summary.extract_site_slug(site_with_slug) == "site-pennington"

    # Test with only name field
    site_without_slug = {"name": "site-pennington"}
    assert (
        render_md_summary.extract_site_slug(site_without_slug) == "site-pennington"
    )

    # Test with empty dict
    empty_site = {}
    assert render_md_summary.extract_site_slug(empty_site) == "unknown"

    print("✅ test_extract_site_slug passed")


def test_generate_mermaid_topology():
    """Test Mermaid topology diagram generation."""
    site = {
        "name": "site-pennington",
        "slug": "site-pennington",
        "description": "Test site",
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

    result = render_md_summary.generate_mermaid_topology(site, prefixes, vlans)

    # Validate structure
    assert "```mermaid" in result
    assert "graph TD" in result
    assert "site-pennington" in result
    assert "VLAN10" in result
    assert "192.168.10.0/24" in result
    assert "```" in result.split("\n")[-1]

    print("✅ test_generate_mermaid_topology passed")


def test_render_site_markdown():
    """Test Markdown rendering for a single site."""
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

    result = render_md_summary.render_site_markdown(site, prefixes, vlans, tags)

    # Validate structure
    assert "# Network Summary: site-pennington" in result
    assert "## Site Information" in result
    assert "## Network Topology" in result
    assert "## IP Prefixes" in result
    assert "## VLANs" in result
    assert "## Tags" in result

    # Validate content
    assert "site-pennington" in result
    assert "Primary residence" in result
    assert "192.168.10.0/24" in result
    assert "VLAN 10" in result or "| 10 |" in result
    assert "home-network" in result
    assert "```mermaid" in result

    print("✅ test_render_site_markdown passed")


def test_render_site_markdown_empty_resources():
    """Test Markdown rendering with empty prefixes, VLANs, and tags."""
    site = {
        "name": "test-site",
        "slug": "test-site",
        "description": "Test site with no resources",
    }

    prefixes = []
    vlans = []
    tags = []

    result = render_md_summary.render_site_markdown(site, prefixes, vlans, tags)

    # Validate structure still exists
    assert "# Network Summary: test-site" in result
    assert "## IP Prefixes" in result
    assert "## VLANs" in result
    assert "## Tags" in result

    # Validate empty state messages
    assert "*No prefixes configured*" in result
    assert "*No VLANs configured*" in result
    assert "*No tags configured*" in result

    print("✅ test_render_site_markdown_empty_resources passed")


def test_render_site_markdown_prefix_without_vlan():
    """Test rendering a prefix that is not associated with a VLAN."""
    site = {
        "name": "test-site",
        "slug": "test-site",
        "description": "Test site",
    }

    prefixes = [
        {
            "prefix": "10.0.0.0/8",
            "vlan": None,  # No VLAN association
            "description": "Untagged prefix",
            "status": "active",
        }
    ]

    vlans = []
    tags = []

    result = render_md_summary.render_site_markdown(site, prefixes, vlans, tags)

    # Validate prefix is shown with no VLAN
    assert "10.0.0.0/8" in result
    assert "Untagged prefix" in result
    # Check that the VLAN column shows a placeholder
    lines = result.split("\n")
    # Find the table line (starts with |), not the mermaid diagram line
    prefix_lines = [line for line in lines if "10.0.0.0/8" in line and line.startswith("|")]
    assert len(prefix_lines) > 0, "Expected to find prefix in table"
    prefix_line = prefix_lines[0]
    # Should have — or similar for empty VLAN
    assert "—" in prefix_line or "N/A" in prefix_line

    print("✅ test_render_site_markdown_prefix_without_vlan passed")


def test_write_and_read_markdown_file():
    """Test writing Markdown content to a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        output_file = tmpdir_path / "test-site.md"

        content = "# Test Site\n\nThis is a test."

        # Write file
        render_md_summary.write_markdown_file(content, output_file)

        # Verify file exists
        assert output_file.exists()

        # Verify content
        with open(output_file, "r") as f:
            read_content = f.read()
        assert read_content == content

    print("✅ test_write_and_read_markdown_file passed")


def run_all_tests():
    """Run all test functions."""
    print("=" * 70)
    print("Running render_md_summary.py tests")
    print("=" * 70)
    print()

    test_functions = [
        test_extract_site_slug,
        test_generate_mermaid_topology,
        test_render_site_markdown,
        test_render_site_markdown_empty_resources,
        test_render_site_markdown_prefix_without_vlan,
        test_write_and_read_markdown_file,
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
            print(f"❌ {test_func.__name__} raised an exception: {e}")
            failed += 1

    print()
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
