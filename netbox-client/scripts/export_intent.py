#!/usr/bin/env python3
"""NetBox Intent Export Script.

This script exports NetBox "intent" data (sites, prefixes, VLANs, tags)
to JSON and YAML files. It queries the NetBox API and creates structured
output files for backup, documentation, or migration purposes.

The script exports the following NetBox objects:
- Sites (DCIM): Physical locations and data centers
- Prefixes (IPAM): IP address ranges and subnets
- VLANs (IPAM): Virtual LAN configurations
- Tags (Extras): Metadata tags for organizing resources

Usage:
    # Export all intent data with default output directory
    python netbox-client/scripts/export_intent.py

    # Export to a custom directory
    python netbox-client/scripts/export_intent.py --output-dir /path/to/output

    # Export only specific resource types
    python netbox-client/scripts/export_intent.py --sites --vlans

Environment Variables:
    NETBOX_URL: NetBox API endpoint URL
        (default: http://localhost:8000/api/)
    NETBOX_API_TOKEN: NetBox API authentication token (required)

API Endpoints Used:
    - GET /api/dcim/sites/ - List all sites
    - GET /api/ipam/prefixes/ - List all IP prefixes
    - GET /api/ipam/vlans/ - List all VLANs
    - GET /api/extras/tags/ - List all tags

Output Files:
    The script generates the following files in the output directory:
    - sites.json, sites.yaml - Site configurations
    - prefixes.json, prefixes.yaml - IP prefix allocations
    - vlans.json, vlans.yaml - VLAN configurations
    - tags.json, tags.yaml - Tag definitions
"""

import argparse
import json
import sys
from pathlib import Path

import requests
import yaml

# Add the scripts directory to the path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# Try to import from nb_config, but provide user-friendly error if token is missing
try:
    from nb_config import NETBOX_URL, TOKEN  # noqa: E402
except AssertionError:
    # nb_config raises AssertionError if TOKEN is not set
    print("Error: NETBOX_API_TOKEN environment variable is required")
    print("Example: export NETBOX_API_TOKEN='your-token-here'")
    sys.exit(1)
except ImportError:
    # Fallback if nb_config is not available
    import os

    NETBOX_URL = os.getenv("NETBOX_URL", "http://localhost:8000/api/")
    TOKEN = os.getenv("NETBOX_API_TOKEN")
    if not TOKEN:
        print("Error: NETBOX_API_TOKEN environment variable is required")
        print("Example: export NETBOX_API_TOKEN='your-token-here'")
        sys.exit(1)

# API headers for authentication
HEADERS = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}


def fetch_sites():
    """Fetch all sites from NetBox with pagination support.

    API Endpoint: GET /api/dcim/sites/

    Returns:
        List of site objects with their configuration data
    """
    print("📍 Fetching sites from NetBox...")
    all_sites = []
    url = f"{NETBOX_URL}dcim/sites/"

    try:
        while url:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            all_sites.extend(results)
            url = data.get("next")  # Get next page URL or None

        print(f"   Found {len(all_sites)} site(s)")
        return all_sites
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching sites: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None  # Return None to indicate error vs empty list


def fetch_prefixes():
    """Fetch all IP prefixes from NetBox with pagination support.

    API Endpoint: GET /api/ipam/prefixes/

    Returns:
        List of prefix objects with their configuration data
    """
    print("🌐 Fetching prefixes from NetBox...")
    all_prefixes = []
    url = f"{NETBOX_URL}ipam/prefixes/"

    try:
        while url:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            all_prefixes.extend(results)
            url = data.get("next")  # Get next page URL or None

        print(f"   Found {len(all_prefixes)} prefix(es)")
        return all_prefixes
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching prefixes: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None  # Return None to indicate error vs empty list


def fetch_vlans():
    """Fetch all VLANs from NetBox with pagination support.

    API Endpoint: GET /api/ipam/vlans/

    Returns:
        List of VLAN objects with their configuration data
    """
    print("📡 Fetching VLANs from NetBox...")
    all_vlans = []
    url = f"{NETBOX_URL}ipam/vlans/"

    try:
        while url:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            all_vlans.extend(results)
            url = data.get("next")  # Get next page URL or None

        print(f"   Found {len(all_vlans)} VLAN(s)")
        return all_vlans
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching VLANs: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None  # Return None to indicate error vs empty list


def fetch_tags():
    """Fetch all tags from NetBox with pagination support.

    API Endpoint: GET /api/extras/tags/

    Returns:
        List of tag objects with their configuration data
    """
    print("🏷️  Fetching tags from NetBox...")
    all_tags = []
    url = f"{NETBOX_URL}extras/tags/"

    try:
        while url:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            all_tags.extend(results)
            url = data.get("next")  # Get next page URL or None

        print(f"   Found {len(all_tags)} tag(s)")
        return all_tags
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching tags: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None  # Return None to indicate error vs empty list


def export_to_json(data, file_path):
    """Export data to a JSON file.

    Args:
        data: Data structure to export (dict or list)
        file_path: Path to the output JSON file
    """
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=False)
        print(f"✅ Exported to {file_path}")
    except Exception as e:
        print(f"❌ Error writing JSON file {file_path}: {e}")


def export_to_yaml(data, file_path):
    """Export data to a YAML file.

    Args:
        data: Data structure to export (dict or list)
        file_path: Path to the output YAML file
    """
    try:
        with open(file_path, "w") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
        print(f"✅ Exported to {file_path}")
    except Exception as e:
        print(f"❌ Error writing YAML file {file_path}: {e}")


def export_resource(resource_name, data, output_dir):
    """Export a resource to both JSON and YAML formats.

    Args:
        resource_name: Name of the resource (e.g., 'sites', 'vlans')
        data: Data to export (None indicates error, empty list is valid)
        output_dir: Directory to write output files to

    Returns:
        True if export succeeded, False otherwise
    """
    if data is None:
        print(f"⚠️  Skipping export for {resource_name} due to fetch error")
        return False

    if not data:
        print(f"ℹ️  No {resource_name} found in NetBox (empty data)")
        # Still export empty list for consistency
        data = []

    json_file = output_dir / f"{resource_name}.json"
    yaml_file = output_dir / f"{resource_name}.yaml"

    export_to_json(data, json_file)
    export_to_yaml(data, yaml_file)
    return True


def main():
    """Main function to handle command-line arguments and export intent data."""
    parser = argparse.ArgumentParser(
        description="Export NetBox intent data to JSON and YAML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all intent data to default location (artifacts/intent-export/)
  python export_intent.py

  # Export to custom directory
  python export_intent.py --output-dir /tmp/netbox-export

  # Export only specific resources
  python export_intent.py --sites --vlans

API Endpoints Used:
  - GET /api/dcim/sites/ - List all sites
  - GET /api/ipam/prefixes/ - List all IP prefixes
  - GET /api/ipam/vlans/ - List all VLANs
  - GET /api/extras/tags/ - List all tags

Environment Variables:
  NETBOX_URL         NetBox API URL (default: http://localhost:8000/api/)
  NETBOX_API_TOKEN   NetBox API token (required)
        """,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/intent-export"),
        help="Output directory for exported files (default: artifacts/intent-export)",
    )

    # Options to export specific resource types
    parser.add_argument(
        "--sites",
        action="store_true",
        help="Export only sites",
    )
    parser.add_argument(
        "--prefixes",
        action="store_true",
        help="Export only prefixes",
    )
    parser.add_argument(
        "--vlans",
        action="store_true",
        help="Export only VLANs",
    )
    parser.add_argument(
        "--tags",
        action="store_true",
        help="Export only tags",
    )

    args = parser.parse_args()

    # If no specific resources are specified, export all
    export_all = not any([args.sites, args.prefixes, args.vlans, args.tags])

    print("=" * 60)
    print("NetBox Intent Export Script")
    print("=" * 60)
    print(f"NetBox URL: {NETBOX_URL}")
    print(f"Output directory: {args.output_dir}")
    print("=" * 60)

    # Create output directory if it doesn't exist
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Output directory ready: {args.output_dir}")
    except Exception as e:
        print(f"❌ Error creating output directory: {e}")
        sys.exit(1)

    print()

    # Track export success/failure
    exported_resources = []
    failed_resources = []

    # Export resources based on arguments
    if export_all or args.sites:
        sites = fetch_sites()
        if export_resource("sites", sites, args.output_dir):
            exported_resources.append("sites")
        else:
            failed_resources.append("sites")
        print()

    if export_all or args.prefixes:
        prefixes = fetch_prefixes()
        if export_resource("prefixes", prefixes, args.output_dir):
            exported_resources.append("prefixes")
        else:
            failed_resources.append("prefixes")
        print()

    if export_all or args.vlans:
        vlans = fetch_vlans()
        if export_resource("vlans", vlans, args.output_dir):
            exported_resources.append("vlans")
        else:
            failed_resources.append("vlans")
        print()

    if export_all or args.tags:
        tags = fetch_tags()
        if export_resource("tags", tags, args.output_dir):
            exported_resources.append("tags")
        else:
            failed_resources.append("tags")
        print()

    print("=" * 60)
    print("Export Complete")
    print("=" * 60)

    if exported_resources:
        print(f"✅ Successfully exported: {', '.join(exported_resources)}")

    if failed_resources:
        print(f"⚠️  Failed to export (fetch errors): {', '.join(failed_resources)}")

    if not exported_resources:
        print("❌ No data was exported")
        sys.exit(1)

    print(f"   Output location: {args.output_dir.resolve()}")
    print()

    if exported_resources:
        print("Files created:")
        for resource in exported_resources:
            json_file = args.output_dir / f"{resource}.json"
            yaml_file = args.output_dir / f"{resource}.yaml"
            if json_file.exists():
                print(f"  - {json_file}")
            if yaml_file.exists():
                print(f"  - {yaml_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
