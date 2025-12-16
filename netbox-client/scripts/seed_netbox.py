#!/usr/bin/env python3
"""NetBox Seeding Script.

This script seeds NetBox with example data from YAML files.
It supports multiple sites and can be used to reset and repopulate
a local NetBox instance for testing and development.

Usage:
    # Seed a specific site
    python netbox-client/scripts/seed_netbox.py \\
        netbox-client/examples/site-pennington.yaml

    # Seed multiple sites
    python netbox-client/scripts/seed_netbox.py \\
        netbox-client/examples/*.yaml

Environment Variables:
    NETBOX_URL: NetBox API endpoint URL
        (default: http://localhost:8000/api/)
    NETBOX_API_TOKEN: NetBox API authentication token (required)
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

# Add the scripts directory to the path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from nb_config import NETBOX_URL, TOKEN  # noqa: E402

# API headers for authentication
HEADERS = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}


def seed_site(data, site_name):
    """Create a site in NetBox.

    Args:
        data: Dictionary containing site configuration
        site_name: Name of the site for logging purposes

    Returns:
        Created site object or None if error
    """
    site_config = data.get("site", {})
    if not site_config:
        print(f"⚠️  No site configuration found in {site_name}")
        return None

    # Generate slug: convert to lowercase, replace non-alphanumeric
    # with hyphens, strip leading/trailing hyphens
    default_slug = re.sub(r"[^a-z0-9]+", "-", site_config["name"].lower()).strip("-")

    site_payload = {
        "name": site_config["name"],
        "slug": site_config.get("slug", default_slug),
    }

    if "description" in site_config:
        site_payload["description"] = site_config["description"]

    try:
        # Check if site already exists
        check_url = f"{NETBOX_URL}dcim/sites/"
        params = {"slug": site_payload["slug"]}
        response = requests.get(check_url, headers=HEADERS, params=params)
        response.raise_for_status()

        if response.json()["count"] > 0:
            site = response.json()["results"][0]
            print(f"✅ Site '{site_config['name']}' already exists (ID: {site['id']})")
            return site

        # Create new site
        response = requests.post(
            f"{NETBOX_URL}dcim/sites/", json=site_payload, headers=HEADERS
        )
        response.raise_for_status()
        site = response.json()
        print(f"✅ Created site '{site_config['name']}' (ID: {site['id']})")
        return site

    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating site: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def seed_vlans(data, site_name, site_obj):
    """Create VLANs in NetBox.

    Args:
        data: Dictionary containing VLAN configuration
        site_name: Name of the site for logging purposes
        site_obj: Site object to associate VLANs with

    Returns:
        List of created VLAN objects
    """
    vlans_config = data.get("vlans", [])
    if not vlans_config:
        print(f"ℹ️  No VLANs defined in {site_name}")
        return []

    created_vlans = []
    for vlan_config in vlans_config:
        vlan_payload = {
            "vid": vlan_config["vlan_id"],
            "name": vlan_config["name"],
            "status": vlan_config.get("status", "active"),
        }

        if "description" in vlan_config:
            vlan_payload["description"] = vlan_config["description"]

        if site_obj:
            vlan_payload["site"] = site_obj["id"]

        try:
            # Check if VLAN already exists
            check_url = f"{NETBOX_URL}ipam/vlans/"
            params = {"vid": vlan_payload["vid"]}
            if site_obj:
                params["site_id"] = site_obj["id"]
            response = requests.get(check_url, headers=HEADERS, params=params)
            response.raise_for_status()

            if response.json()["count"] > 0:
                vlan = response.json()["results"][0]
                vlan_id = vlan_config["vlan_id"]
                vlan_name = vlan_config["name"]
                print(
                    f"✅ VLAN {vlan_id} ('{vlan_name}') "
                    f"already exists (ID: {vlan['id']})"
                )
                created_vlans.append(vlan)
                continue

            # Create new VLAN
            response = requests.post(
                f"{NETBOX_URL}ipam/vlans/", json=vlan_payload, headers=HEADERS
            )
            response.raise_for_status()
            vlan = response.json()
            vlan_id = vlan_config["vlan_id"]
            vlan_name = vlan_config["name"]
            print(f"✅ Created VLAN {vlan_id} ('{vlan_name}') " f"(ID: {vlan['id']})")
            created_vlans.append(vlan)

        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating VLAN {vlan_config['vlan_id']}: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"   Response: {e.response.text}")

    return created_vlans


def seed_prefixes(data, site_name, site_obj, vlans):
    """Create IP prefixes in NetBox.

    Args:
        data: Dictionary containing prefix configuration
        site_name: Name of the site for logging purposes
        site_obj: Site object to associate prefixes with
        vlans: List of VLAN objects to associate with prefixes

    Returns:
        List of created prefix objects
    """
    prefixes_config = data.get("prefixes", [])
    if not prefixes_config:
        print(f"ℹ️  No prefixes defined in {site_name}")
        return []

    # Create a mapping of VLAN IDs to VLAN objects
    vlan_map = {vlan["vid"]: vlan for vlan in vlans}

    created_prefixes = []
    for prefix_config in prefixes_config:
        prefix_payload = {
            "prefix": prefix_config["prefix"],
            "status": prefix_config.get("status", "active"),
        }

        if "description" in prefix_config:
            prefix_payload["description"] = prefix_config["description"]

        if site_obj:
            prefix_payload["site"] = site_obj["id"]

        # Associate with VLAN if specified
        if "vlan" in prefix_config and prefix_config["vlan"] in vlan_map:
            prefix_payload["vlan"] = vlan_map[prefix_config["vlan"]]["id"]

        try:
            # Check if prefix already exists
            check_url = f"{NETBOX_URL}ipam/prefixes/"
            params = {"prefix": prefix_payload["prefix"]}
            response = requests.get(check_url, headers=HEADERS, params=params)
            response.raise_for_status()

            if response.json()["count"] > 0:
                prefix = response.json()["results"][0]
                prefix_addr = prefix_config["prefix"]
                print(
                    f"✅ Prefix {prefix_addr} already exists " f"(ID: {prefix['id']})"
                )
                created_prefixes.append(prefix)
                continue

            # Create new prefix
            response = requests.post(
                f"{NETBOX_URL}ipam/prefixes/",
                json=prefix_payload,
                headers=HEADERS,
            )
            response.raise_for_status()
            prefix = response.json()
            prefix_addr = prefix_config["prefix"]
            print(f"✅ Created prefix {prefix_addr} " f"(ID: {prefix['id']})")
            created_prefixes.append(prefix)

        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating prefix {prefix_config['prefix']}: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"   Response: {e.response.text}")

    return created_prefixes


def seed_from_file(file_path):
    """Seed NetBox with data from a YAML file.

    Args:
        file_path: Path to the YAML file containing site configuration

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'=' * 60}")
    print(f"Processing: {file_path}")
    print("=" * 60)

    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        if not data:
            print(f"⚠️  Empty or invalid YAML file: {file_path}")
            return False

        # Seed in order: site -> vlans -> prefixes
        site = seed_site(data, file_path)
        if not site:
            print("⚠️  Skipping VLANs and prefixes " "due to site creation failure")
            return False

        vlans = seed_vlans(data, file_path, site)
        prefixes = seed_prefixes(data, file_path, site, vlans)

        print(f"\n✅ Successfully processed {file_path}")
        site_summary = (
            f"Site={site['name']}, " f"VLANs={len(vlans)}, " f"Prefixes={len(prefixes)}"
        )
        print(f"   Summary: {site_summary}")
        return True

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML file: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Main function to handle command-line arguments and seed NetBox."""
    parser = argparse.ArgumentParser(
        description="Seed NetBox with example data from YAML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Seed a single site
  python seed_netbox.py examples/site-pennington.yaml

  # Seed multiple sites
  python seed_netbox.py examples/site-pennington.yaml examples/site-countfleetcourt.yaml

  # Seed all sites in examples directory
  python seed_netbox.py examples/*.yaml

Environment Variables:
  NETBOX_URL         NetBox API URL (default: http://localhost:8000/api/)
  NETBOX_API_TOKEN   NetBox API token (required)
        """,
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="YAML file(s) containing site configuration",
    )

    args = parser.parse_args()

    # Sanitize URL for display (remove any potential credentials)
    parsed_url = urlparse(NETBOX_URL)
    safe_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

    print("=" * 60)
    print("NetBox Seeding Script")
    print("=" * 60)
    print(f"NetBox URL: {safe_url}")
    print(f"Files to process: {len(args.files)}")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    for file_path in args.files:
        if seed_from_file(file_path):
            success_count += 1
        else:
            fail_count += 1

    print(f"\n{'=' * 60}")
    print("Seeding Complete")
    print(f"{'=' * 60}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"{'=' * 60}")

    # Exit with error code if any files failed
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
