#!/usr/bin/env python3
"""Render UniFi controller JSON config files from NetBox intent export data.

This script converts NetBox intent-export JSON files into UniFi-compatible
JSON payloads (site/network/vlan/wlan) for each site. The output represents
"intended" configuration and is suitable for review and version control.

⚠️  WARNING: The generated JSON represents intended state and is not ready
for direct UniFi controller ingestion without review and validation.

The script reads NetBox data exported by export_intent.py (or compatible format)
and generates site-specific UniFi configuration files.

Usage:
    # Generate UniFi configs from NetBox export directory
    python netbox-client/scripts/render_unifi.py \
        --input-dir artifacts/intent-export

    # Generate from a single consolidated intent file
    python netbox-client/scripts/render_unifi.py \
        --input-file netbox-client/examples/intent-minimal-schema.json

    # Specify custom output directory
    python netbox-client/scripts/render_unifi.py \
        --input-dir artifacts/intent-export --output-dir /tmp/unifi

Output:
    Generates files in artifacts/unifi/:
    - site-pennington.json
    - site-countfleetcourt.json
    - etc.

NetBox to UniFi Field Mapping:
    Sites → UniFi Site:
        - name → site.name
        - slug → site.desc (description)
        - description → site.desc

    Prefixes → UniFi Networks:
        - prefix → network.ip_subnet (CIDR notation)
        - vlan → network.vlan (VLAN ID, optional)
        - description → network.name
        - status → (used to determine enabled state)

    VLANs → UniFi VLANs:
        - vlan_id → vlan.vlan_id
        - name → vlan.name
        - description → (informational only)
        - status → (used to determine enabled state)

    WLANs:
        - Placeholder structure (requires additional wireless config)

Environment Variables:
    None required. This script operates on local files.

Features:
    - Deterministic output: Same input always produces same output
    - Sorted keys: JSON keys are sorted for consistency
    - Site isolation: Each site gets its own UniFi config file
    - Warning: Intended state only, not for direct controller use
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON data as a dictionary

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {file_path}: {e}")
        raise


def load_netbox_export(
    input_dir: Path = None, input_file: Path = None
) -> Dict[str, Any]:
    """Load NetBox export data from either a directory or single file.

    Args:
        input_dir: Directory containing sites.json, prefixes.json, vlans.json
        input_file: Single consolidated JSON file with all data

    Returns:
        Dictionary with keys: sites, prefixes, vlans, tags

    Raises:
        ValueError: If neither input_dir nor input_file is provided
        FileNotFoundError: If required files are not found
    """
    if input_file:
        # Load from single consolidated file
        print(f"📥 Loading NetBox data from: {input_file}")
        data = load_json_file(input_file)

        # Validate required keys
        required_keys = ["sites", "prefixes", "vlans"]
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            print(f"⚠️  Warning: Missing keys in input file: {missing_keys}")

        # Ensure all expected keys exist with defaults
        result = {
            "sites": data.get("sites", []),
            "prefixes": data.get("prefixes", []),
            "vlans": data.get("vlans", []),
            "tags": data.get("tags", []),
        }

        print(f"   Loaded {len(result['sites'])} site(s)")
        print(f"   Loaded {len(result['prefixes'])} prefix(es)")
        print(f"   Loaded {len(result['vlans'])} VLAN(s)")
        print(f"   Loaded {len(result['tags'])} tag(s)")

        return result

    elif input_dir:
        # Load from directory with separate files
        print(f"📥 Loading NetBox data from: {input_dir}")

        result = {
            "sites": [],
            "prefixes": [],
            "vlans": [],
            "tags": [],
        }

        # Load each resource type
        for resource_name in ["sites", "prefixes", "vlans", "tags"]:
            file_path = input_dir / f"{resource_name}.json"
            if file_path.exists():
                data = load_json_file(file_path)
                result[resource_name] = data
                print(f"   Loaded {len(data)} {resource_name}")
            else:
                print(f"⚠️  Warning: {file_path} not found, skipping")

        return result

    else:
        raise ValueError("Either input_dir or input_file must be provided")


def extract_site_slug(site_data: Dict[str, Any]) -> str:
    """Extract site slug from site data.

    Tries 'slug' first, falls back to 'name' if slug is missing.

    Args:
        site_data: Site dictionary from NetBox export

    Returns:
        Site slug string
    """
    return site_data.get("slug", site_data.get("name", "unknown"))


def render_unifi_site(site: Dict[str, Any]) -> Dict[str, Any]:
    """Render UniFi site configuration from NetBox site data.

    Args:
        site: Site data from NetBox

    Returns:
        UniFi site configuration dictionary
    """
    return {
        "name": site.get("name", ""),
        "desc": site.get("description", site.get("name", "")),
    }


def render_unifi_networks(prefixes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Render UniFi network configurations from NetBox prefixes.

    Args:
        prefixes: List of prefix data from NetBox

    Returns:
        List of UniFi network configuration dictionaries
    """
    networks = []
    for prefix in prefixes:
        # Extract CIDR and description
        cidr = prefix.get("prefix", "")
        description = prefix.get("description", "")
        vlan_id = prefix.get("vlan")
        status = prefix.get("status", "active")

        # Basic network config
        network = {
            "name": description if description else cidr,
            "purpose": "corporate",
            "ip_subnet": cidr,
            "enabled": status == "active",
        }

        # Add VLAN if specified
        if vlan_id is not None:
            network["vlan"] = vlan_id
            network["vlan_enabled"] = True
        else:
            network["vlan_enabled"] = False

        networks.append(network)

    return networks


def render_unifi_vlans(vlans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Render UniFi VLAN configurations from NetBox VLANs.

    Args:
        vlans: List of VLAN data from NetBox

    Returns:
        List of UniFi VLAN configuration dictionaries
    """
    unifi_vlans = []
    for vlan in vlans:
        vlan_id = vlan.get("vlan_id")
        name = vlan.get("name", "")
        status = vlan.get("status", "active")

        # Skip if no VLAN ID
        if vlan_id is None:
            continue

        unifi_vlan = {
            "vlan_id": vlan_id,
            "name": name,
            "enabled": status == "active",
        }

        unifi_vlans.append(unifi_vlan)

    return unifi_vlans


def render_unifi_wlans() -> List[Dict[str, Any]]:
    """Render placeholder UniFi WLAN configurations.

    WLANs require additional wireless configuration not available in NetBox.
    This returns a placeholder structure.

    Returns:
        Empty list (placeholder for future WLAN support)
    """
    # Placeholder for future WLAN support
    # WLAN configuration requires additional data not present in NetBox
    # (SSID, security settings, radio configuration, etc.)
    return []


def render_site_unifi_config(
    site: Dict[str, Any],
    prefixes: List[Dict[str, Any]],
    vlans: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Render complete UniFi configuration for a single site.

    Args:
        site: Site data from NetBox
        prefixes: List of prefixes for this site
        vlans: List of VLANs for this site

    Returns:
        Dictionary of UniFi configuration ready for JSON serialization
    """
    config = {
        "_warning": (
            "This configuration represents intended state and is not ready "
            "for direct UniFi controller ingestion. Review and validate before use."
        ),
        "_source": "NetBox intent export via render_unifi.py",
        "site": render_unifi_site(site),
        "networks": render_unifi_networks(prefixes),
        "vlans": render_unifi_vlans(vlans),
        "wlans": render_unifi_wlans(),
    }

    return config


def write_unifi_config_file(config: Dict[str, Any], output_path: Path) -> None:
    """Write UniFi config data to a JSON file with deterministic formatting.

    Uses sorted keys and consistent indentation for deterministic output.

    Args:
        config: UniFi configuration dictionary
        output_path: Path to write the JSON file
    """
    try:
        with open(output_path, "w") as f:
            json.dump(config, f, indent=2, sort_keys=True)
            f.write("\n")  # Add trailing newline
        print(f"✅ Generated: {output_path}")
    except Exception as e:
        print(f"❌ Error writing {output_path}: {e}")
        raise


def main():
    """Main function to handle command-line arguments and render UniFi configs."""
    parser = argparse.ArgumentParser(
        description="Render UniFi controller JSON configs from NetBox intent export",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from NetBox export directory
  python render_unifi.py --input-dir artifacts/intent-export

  # Generate from consolidated intent file
  python render_unifi.py --input-file netbox-client/examples/intent-minimal-schema.json

  # Specify custom output directory
  python render_unifi.py --input-dir artifacts/intent-export --output-dir /tmp/unifi

NetBox to UniFi Mapping:
  Sites:      name → site.name, description → site.desc
  Prefixes:   prefix → network.ip_subnet, vlan → network.vlan,
              description → network.name
  VLANs:      vlan_id → vlan.vlan_id, name → vlan.name, status → enabled
  WLANs:      Placeholder (requires additional wireless configuration)

Output Files:
  artifacts/unifi/site-{slug}.json (one per site)

⚠️  WARNING: Generated configs represent intended state only.
    Not ready for direct UniFi controller ingestion without review.
        """,
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input-dir",
        type=Path,
        help=(
            "Directory containing NetBox export files "
            "(sites.json, prefixes.json, vlans.json)"
        ),
    )
    input_group.add_argument(
        "--input-file",
        type=Path,
        help=(
            "Single consolidated NetBox export file "
            "(e.g., intent-minimal-schema.json)"
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/unifi"),
        help="Output directory for UniFi config files (default: artifacts/unifi)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("NetBox to UniFi Configuration Converter")
    print("=" * 70)
    print(f"Output directory: {args.output_dir}")
    print("=" * 70)
    print()

    # Load NetBox export data
    try:
        netbox_data = load_netbox_export(
            input_dir=args.input_dir, input_file=args.input_file
        )
    except Exception as e:
        print(f"❌ Failed to load NetBox data: {e}")
        sys.exit(1)

    sites = netbox_data["sites"]
    all_prefixes = netbox_data["prefixes"]
    all_vlans = netbox_data["vlans"]

    if not sites:
        print("⚠️  No sites found in NetBox data. Nothing to generate.")
        sys.exit(0)

    # Create output directory
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Output directory ready: {args.output_dir}")
        print()
    except Exception as e:
        print(f"❌ Error creating output directory: {e}")
        sys.exit(1)

    # Generate UniFi config file for each site
    print("🔨 Generating UniFi configuration files...")
    print()

    generated_files = []
    for site in sites:
        site_slug = extract_site_slug(site)
        site_name = site.get("name", site_slug)

        print(f"Processing site: {site_name} ({site_slug})")

        # Filter prefixes and VLANs for this site
        # NetBox export may have 'site' field (from minimal schema)
        # or nested 'site' object (from API)
        site_prefixes = []
        for prefix in all_prefixes:
            prefix_site = prefix.get("site")
            # Handle both string (minimal schema) and object (API export)
            if isinstance(prefix_site, dict):
                prefix_site_slug = prefix_site.get("slug", prefix_site.get("name"))
            else:
                prefix_site_slug = prefix_site

            if prefix_site_slug == site_slug or prefix_site_slug == site_name:
                site_prefixes.append(prefix)

        site_vlans = []
        for vlan in all_vlans:
            vlan_site = vlan.get("site")
            # Handle both string (minimal schema) and object (API export)
            if isinstance(vlan_site, dict):
                vlan_site_slug = vlan_site.get("slug", vlan_site.get("name"))
            else:
                vlan_site_slug = vlan_site

            if vlan_site_slug == site_slug or vlan_site_slug == site_name:
                site_vlans.append(vlan)

        print(f"  - {len(site_prefixes)} network(s) from prefixes")
        print(f"  - {len(site_vlans)} VLAN(s)")
        print("  - 0 WLAN(s) (placeholder)")

        # Render UniFi config for this site
        config = render_site_unifi_config(site, site_prefixes, site_vlans)

        # Write to file
        # If slug already starts with "site-", don't add it again
        if site_slug.startswith("site-"):
            output_file = args.output_dir / f"{site_slug}.json"
        else:
            output_file = args.output_dir / f"site-{site_slug}.json"
        write_unifi_config_file(config, output_file)
        generated_files.append(output_file)
        print()

    # Summary
    print("=" * 70)
    print("Generation Complete")
    print("=" * 70)
    print(f"✅ Generated {len(generated_files)} UniFi config file(s)")
    print(f"   Output location: {args.output_dir.resolve()}")
    print()
    print("⚠️  WARNING: These configurations represent intended state only.")
    print("   Review and validate before using with UniFi controller.")
    print()
    print("Files created:")
    for file_path in generated_files:
        print(f"  - {file_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
