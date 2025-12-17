#!/usr/bin/env python3
"""NetBox Minimal Intent CRUD Example.

This script demonstrates basic CRUD (Create, Read, Update, Delete) operations
for the minimal NetBox intent data model, including:
- Sites (physical locations)
- VLANs (virtual LANs)
- Prefixes (IP address ranges)
- Tags (metadata for organizing resources)

This is a simplified example for learning purposes. For production use,
see the more robust seed_netbox.py script.

Usage:
    # Set environment variables
    export NETBOX_URL="http://localhost:8000/api/"
    export NETBOX_API_TOKEN="0123456789abcdef0123456789abcdef01234567"

    # Run the script
    python netbox-client/scripts/post_minimal_intent.py

    # Or with explicit data file
    python netbox-client/scripts/post_minimal_intent.py \
        netbox-client/examples/intent-minimal-schema.json

Environment Variables:
    NETBOX_URL: NetBox API endpoint URL
        (default: http://localhost:8000/api/)
    NETBOX_API_TOKEN: NetBox API authentication token (required)
"""

import argparse
import json
import sys

import requests

# Try to import from nb_config, but allow token validation to be deferred
try:
    # Add the scripts directory to the path for imports
    import os
    from pathlib import Path

    SCRIPT_DIR = Path(__file__).parent
    sys.path.insert(0, str(SCRIPT_DIR))

    # Import configuration - this will fail if TOKEN is not set
    # We catch this and provide a more user-friendly message
    from nb_config import NETBOX_URL, TOKEN
except AssertionError:
    # nb_config raises AssertionError if TOKEN is not set
    print("Error: NETBOX_API_TOKEN environment variable is required")
    print("Example: export NETBOX_API_TOKEN='your-token-here'")
    sys.exit(1)
except ImportError:
    # Fallback if nb_config is not available
    NETBOX_URL = os.getenv("NETBOX_URL", "http://localhost:8000/api/")
    TOKEN = os.getenv("NETBOX_API_TOKEN")
    if not TOKEN:
        print("Error: NETBOX_API_TOKEN environment variable is required")
        print("Example: export NETBOX_API_TOKEN='your-token-here'")
        sys.exit(1)

# API headers for authentication
HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json",
}


def create_site(site_data):
    """Create a site in NetBox.

    Args:
        site_data: Dictionary with site configuration (name, slug, description)

    Returns:
        Created site object or existing site if already present
    """
    # Check if site already exists
    response = requests.get(
        f"{NETBOX_URL}dcim/sites/",
        headers=HEADERS,
        params={"slug": site_data["slug"]},
    )
    response.raise_for_status()

    results = response.json()
    if results["count"] > 0:
        site = results["results"][0]
        print(f"✅ Site '{site_data['name']}' already exists (ID: {site['id']})")
        return site

    # Create new site
    response = requests.post(
        f"{NETBOX_URL}dcim/sites/",
        json=site_data,
        headers=HEADERS,
    )
    response.raise_for_status()
    site = response.json()
    print(f"✅ Created site '{site_data['name']}' (ID: {site['id']})")
    return site


def create_tag(tag_data):
    """Create a tag in NetBox.

    Args:
        tag_data: Dictionary with tag configuration (name, slug, description, color)

    Returns:
        Created tag object or existing tag if already present
    """
    # Check if tag already exists
    response = requests.get(
        f"{NETBOX_URL}extras/tags/",
        headers=HEADERS,
        params={"slug": tag_data["slug"]},
    )
    response.raise_for_status()

    results = response.json()
    if results["count"] > 0:
        tag = results["results"][0]
        print(f"✅ Tag '{tag_data['name']}' already exists (ID: {tag['id']})")
        return tag

    # Create new tag
    response = requests.post(
        f"{NETBOX_URL}extras/tags/",
        json=tag_data,
        headers=HEADERS,
    )
    response.raise_for_status()
    tag = response.json()
    print(f"✅ Created tag '{tag_data['name']}' (ID: {tag['id']})")
    return tag


def create_vlan(vlan_data, site_id):
    """Create a VLAN in NetBox.

    Args:
        vlan_data: Dictionary with VLAN configuration
        site_id: NetBox site ID to associate the VLAN with

    Returns:
        Created VLAN object or existing VLAN if already present
    """
    # Prepare VLAN payload
    vlan_payload = {
        "vid": vlan_data["vlan_id"],
        "name": vlan_data["name"],
        "status": vlan_data.get("status", "active"),
        "site": site_id,
    }

    if "description" in vlan_data:
        vlan_payload["description"] = vlan_data["description"]

    # Check if VLAN already exists for this site
    response = requests.get(
        f"{NETBOX_URL}ipam/vlans/",
        headers=HEADERS,
        params={"vid": vlan_data["vlan_id"], "site_id": site_id},
    )
    response.raise_for_status()

    results = response.json()
    if results["count"] > 0:
        vlan = results["results"][0]
        print(
            f"✅ VLAN {vlan_data['vlan_id']} '{vlan_data['name']}' "
            f"already exists (ID: {vlan['id']})"
        )
        return vlan

    # Create new VLAN
    response = requests.post(
        f"{NETBOX_URL}ipam/vlans/",
        json=vlan_payload,
        headers=HEADERS,
    )
    response.raise_for_status()
    vlan = response.json()
    print(
        f"✅ Created VLAN {vlan_data['vlan_id']} '{vlan_data['name']}' "
        f"(ID: {vlan['id']})"
    )
    return vlan


def create_prefix(prefix_data, site_id, vlan_id=None):
    """Create an IP prefix in NetBox.

    Args:
        prefix_data: Dictionary with prefix configuration
        site_id: NetBox site ID to associate the prefix with
        vlan_id: Optional VLAN ID to associate with the prefix

    Returns:
        Created prefix object or existing prefix if already present
    """
    # Prepare prefix payload
    prefix_payload = {
        "prefix": prefix_data["prefix"],
        "status": prefix_data.get("status", "active"),
        "site": site_id,
    }

    if "description" in prefix_data:
        prefix_payload["description"] = prefix_data["description"]

    if vlan_id:
        prefix_payload["vlan"] = vlan_id

    # Check if prefix already exists
    response = requests.get(
        f"{NETBOX_URL}ipam/prefixes/",
        headers=HEADERS,
        params={"prefix": prefix_data["prefix"]},
    )
    response.raise_for_status()

    results = response.json()
    if results["count"] > 0:
        prefix = results["results"][0]
        print(f"✅ Prefix {prefix_data['prefix']} already exists (ID: {prefix['id']})")
        return prefix

    # Create new prefix
    response = requests.post(
        f"{NETBOX_URL}ipam/prefixes/",
        json=prefix_payload,
        headers=HEADERS,
    )
    response.raise_for_status()
    prefix = response.json()
    print(f"✅ Created prefix {prefix_data['prefix']} (ID: {prefix['id']})")
    return prefix


def read_example():
    """Demonstrate READ operations - fetch and display existing resources."""
    print("\n" + "=" * 60)
    print("READ Example: Fetching existing sites")
    print("=" * 60)

    response = requests.get(f"{NETBOX_URL}dcim/sites/", headers=HEADERS)
    response.raise_for_status()

    sites = response.json()["results"]
    print(f"Found {len(sites)} site(s):")
    for site in sites[:5]:  # Show first 5 sites
        print(f"  - {site['name']} (slug: {site['slug']})")


def update_example(site_slug):
    """Demonstrate UPDATE operations - modify an existing resource.

    Args:
        site_slug: Slug of the site to update
    """
    print("\n" + "=" * 60)
    print(f"UPDATE Example: Updating site '{site_slug}'")
    print("=" * 60)

    # Get the site
    response = requests.get(
        f"{NETBOX_URL}dcim/sites/",
        headers=HEADERS,
        params={"slug": site_slug},
    )
    response.raise_for_status()

    results = response.json()
    if results["count"] == 0:
        print(f"Site '{site_slug}' not found, skipping update example")
        return

    site = results["results"][0]
    site_id = site["id"]

    # Update the site description
    updated_description = f"{site.get('description', '')} (Updated via API)"
    update_payload = {
        "description": updated_description,
    }

    response = requests.patch(
        f"{NETBOX_URL}dcim/sites/{site_id}/",
        json=update_payload,
        headers=HEADERS,
    )
    response.raise_for_status()

    updated_site = response.json()
    print(f"✅ Updated site '{site_slug}':")
    print(f"   New description: {updated_site['description']}")


def delete_example_comment():
    """Document DELETE operations.

    Note: This function is for documentation only and does not perform deletions.
    DELETE operations should be used carefully in production environments.
    """
    print("\n" + "=" * 60)
    print("DELETE Example (documentation only - not executed)")
    print("=" * 60)

    example_code = """
    # To delete a site (BE CAREFUL - this is destructive!):
    site_id = 123  # Replace with actual site ID
    response = requests.delete(
        f"{NETBOX_URL}dcim/sites/{site_id}/",
        headers=HEADERS
    )
    response.raise_for_status()
    print(f"Deleted site ID {site_id}")
    """

    print("DELETE operations remove resources from NetBox.")
    print("Example code:")
    print(example_code)
    print("\n⚠️  WARNING: DELETE operations are destructive and cannot be undone!")
    print("   Use with caution in production environments.")


def main():
    """Main function to demonstrate CRUD operations."""
    parser = argparse.ArgumentParser(
        description="Demonstrate NetBox minimal intent CRUD operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "file",
        nargs="?",
        default="netbox-client/examples/intent-minimal-schema.json",
        help="Path to JSON file with intent data (default: intent-minimal-schema.json)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("NetBox Minimal Intent CRUD Example")
    print("=" * 60)
    print(f"NetBox URL: {NETBOX_URL}")
    print(f"Data file: {args.file}")
    print("=" * 60)

    # Load intent data
    try:
        with open(args.file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        sys.exit(1)

    # CREATE operations
    print("\n" + "=" * 60)
    print("CREATE Example: Creating resources from intent data")
    print("=" * 60)

    # Create tags first (they're optional but useful)
    tags = {}
    for tag_data in data.get("tags", []):
        tag = create_tag(tag_data)
        tags[tag_data["slug"]] = tag

    # Create sites
    sites = {}
    for site_data in data.get("sites", []):
        site = create_site(site_data)
        sites[site_data["slug"]] = site

    # Create VLANs (associated with sites)
    vlans = {}  # Key: (site_slug, vlan_id)
    for vlan_data in data.get("vlans", []):
        site_slug = vlan_data["site"]
        if site_slug not in sites:
            print(f"⚠️  Site '{site_slug}' not found for VLAN {vlan_data['vlan_id']}")
            continue

        site_id = sites[site_slug]["id"]
        vlan = create_vlan(vlan_data, site_id)
        vlans[(site_slug, vlan_data["vlan_id"])] = vlan

    # Create prefixes (associated with sites and optionally VLANs)
    for prefix_data in data.get("prefixes", []):
        site_slug = prefix_data["site"]
        if site_slug not in sites:
            print(
                f"⚠️  Site '{site_slug}' not found for "
                f"prefix {prefix_data['prefix']}"
            )
            continue

        site_id = sites[site_slug]["id"]
        vlan_id = None

        # Find associated VLAN if specified
        if "vlan" in prefix_data:
            vlan_key = (site_slug, prefix_data["vlan"])
            if vlan_key in vlans:
                vlan_id = vlans[vlan_key]["id"]

        create_prefix(prefix_data, site_id, vlan_id)

    # READ operations
    read_example()

    # UPDATE operations
    if data.get("sites"):
        first_site_slug = data["sites"][0]["slug"]
        update_example(first_site_slug)

    # DELETE operations (documentation only)
    delete_example_comment()

    print("\n" + "=" * 60)
    print("CRUD Examples Complete")
    print("=" * 60)
    print("✅ All operations completed successfully")
    print("\nNext steps:")
    print("  - View resources in NetBox UI: http://localhost:8000")
    print("  - Explore the NetBox API: http://localhost:8000/api/")
    print("  - Review seed_netbox.py for more robust production usage")
    print("=" * 60)


if __name__ == "__main__":
    main()
