#!/usr/bin/env python3
"""Render Terraform tfvars files from NetBox intent export data.

This script converts NetBox intent-export JSON files into Terraform variable
(tfvars) files, one per site. The output is deterministic and suitable for
version control and automated workflows.

The script reads NetBox data exported by export_intent.py (or compatible format)
and generates site-specific tfvars files that can be used with Terraform
infrastructure deployments.

Usage:
    # Generate tfvars from NetBox export directory
    python netbox-client/scripts/render_tfvars.py \
        --input-dir artifacts/intent-export

    # Generate from a single consolidated intent file
    python netbox-client/scripts/render_tfvars.py \
        --input-file netbox-client/examples/intent-minimal-schema.json

    # Specify custom output directory
    python netbox-client/scripts/render_tfvars.py \
        --input-dir artifacts/intent-export --output-dir /tmp/tfvars

Output:
    Generates files in artifacts/tfvars/:
    - site-pennington.tfvars.json
    - site-countfleetcourt.tfvars.json
    - etc.

NetBox Field Mapping to Terraform Variables:
    Sites:
        NetBox field → Terraform variable
        - name → site_name
        - slug → site_slug
        - description → site_description

    Prefixes (grouped by site):
        NetBox field → Terraform variable
        - prefix → prefixes[].cidr
        - vlan (int or nested object) → prefixes[].vlan_id
        - description → prefixes[].description
        - status (string or object.value) → prefixes[].status

    VLANs (grouped by site):
        NetBox field → Terraform variable
        - vlan_id or vid → vlans[].vlan_id (REQUIRED, must not be null)
        - name → vlans[].name
        - description → vlans[].description
        - status (string or object.value) → vlans[].status

    Tags (included in all site files):
        NetBox field → Terraform variable
        - name → tags[].name
        - slug → tags[].slug
        - description → tags[].description
        - color → tags[].color

NetBox API Compatibility:
    This script handles both minimal schema format (simple values) and
    NetBox API format (nested objects):

    - Status fields: Extracts 'value' from {"label": "Reserved", "value": "reserved"}
    - VLAN IDs: Handles both 'vid' and 'vlan_id' field names
    - VLAN associations: Handles both integers and nested VLAN objects

Validation:
    The script enforces Terraform Input Contract requirements:
    - VLAN IDs must not be null (raises ValueError with clear message)
    - Status values are extracted from objects if necessary
    - All output conforms to schema in docs/phase4/terraform-input-contract.md

Environment Variables:
    None required. This script operates on local files.

Features:
    - Deterministic output: Same input always produces same output
    - Sorted keys: JSON keys are sorted for consistency
    - Site isolation: Each site gets its own tfvars file
    - Validation: Verifies required fields are present and valid
    - Clear error messages: Indicates which site/VLAN has issues
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


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
        input_dir: Directory containing sites.json, prefixes.json, vlans.json, tags.json
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


def extract_status_value(status: Any) -> str:
    """Extract status value from NetBox status field.

    NetBox API returns status as an object with 'label' and 'value' fields.
    This function extracts just the 'value' string for Terraform compatibility.

    Args:
        status: Status field from NetBox (can be string or dict)

    Returns:
        Status string value (e.g., "active", "reserved", "deprecated")
    """
    if status is None:
        return "active"
    elif isinstance(status, dict):
        # NetBox API format: {"label": "Reserved", "value": "reserved"}
        return status.get("value", "active")
    elif isinstance(status, str):
        # Already a string (from minimal schema or simplified export)
        return status
    else:
        # Fallback for unexpected types
        return "active"


def extract_site_slug(site_data: Dict[str, Any]) -> str:
    """Extract site slug from site data.

    Tries 'slug' first, falls back to 'name' if slug is missing.

    Args:
        site_data: Site dictionary from NetBox export

    Returns:
        Site slug string
    """
    return site_data.get("slug", site_data.get("name", "unknown"))


def extract_vlan_id(vlan_data: Dict[str, Any]) -> int:
    """Extract VLAN ID from NetBox VLAN data.

    NetBox may use 'vid' or 'vlan_id' field for VLAN ID.
    This function tries both field names.

    Args:
        vlan_data: VLAN dictionary from NetBox export

    Returns:
        VLAN ID as integer

    Raises:
        ValueError: If VLAN ID is null or missing
    """
    # Try both possible field names with explicit None checking
    vlan_id = vlan_data.get("vid")
    if vlan_id is None:
        vlan_id = vlan_data.get("vlan_id")

    if vlan_id is None:
        # Extract site info for better error message
        site = vlan_data.get("site", "unknown")
        if isinstance(site, dict):
            site = site.get("slug", site.get("name", "unknown"))

        raise ValueError(
            f"VLAN '{vlan_data.get('name', 'unnamed')}' "
            f"(site: {site}) has no VLAN ID assigned. "
            f"Please assign VLAN ID in NetBox before rendering."
        )

    return int(vlan_id)


def extract_vlan_association(prefix_data: Dict[str, Any]) -> Optional[int]:
    """Extract VLAN ID from prefix's VLAN association.

    Handles both simple VLAN ID (integer) and nested VLAN object.

    Args:
        prefix_data: Prefix dictionary from NetBox export

    Returns:
        VLAN ID as integer, or None if not associated
    """
    vlan = prefix_data.get("vlan")

    if vlan is None:
        return None
    elif isinstance(vlan, dict):
        # Nested VLAN object: {"vid": 10, "name": "LAN", ...}
        # Try 'vid' first, then 'vlan_id', with explicit None checking
        vlan_id = vlan.get("vid")
        if vlan_id is None:
            vlan_id = vlan.get("vlan_id")
        return vlan_id
    elif isinstance(vlan, int):
        # Simple VLAN ID (from minimal schema)
        return vlan
    else:
        return None


def render_site_tfvars(
    site: Dict[str, Any],
    prefixes: List[Dict[str, Any]],
    vlans: List[Dict[str, Any]],
    tags: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Render Terraform variables for a single site.

    Args:
        site: Site data from NetBox
        prefixes: List of prefixes for this site
        vlans: List of VLANs for this site
        tags: List of all tags (included in every site)

    Returns:
        Dictionary of Terraform variables ready for JSON serialization
    """
    # Map site fields
    tfvars = {
        "site_name": site.get("name", ""),
        "site_slug": extract_site_slug(site),
        "site_description": site.get("description", ""),
    }

    # Map prefixes
    tfvars["prefixes"] = [
        {
            "cidr": prefix.get("prefix", ""),
            "vlan_id": extract_vlan_association(prefix),
            "description": prefix.get("description", ""),
            "status": extract_status_value(prefix.get("status")),
        }
        for prefix in prefixes
    ]

    # Map VLANs with validation
    tfvars_vlans = []
    for vlan in vlans:
        try:
            vlan_id = extract_vlan_id(vlan)
            tfvars_vlans.append(
                {
                    "vlan_id": vlan_id,
                    "name": vlan.get("name", ""),
                    "description": vlan.get("description", ""),
                    "status": extract_status_value(vlan.get("status")),
                }
            )
        except ValueError as e:
            # Re-raise with context about which site is being processed
            site_name = site.get("name", "unknown")
            raise ValueError(f"Error processing site '{site_name}': {e}") from e

    tfvars["vlans"] = tfvars_vlans

    # Map tags (same for all sites)
    tfvars["tags"] = [
        {
            "name": tag.get("name", ""),
            "slug": tag.get("slug", tag.get("name", "")),
            "description": tag.get("description", ""),
            "color": tag.get("color", ""),
        }
        for tag in tags
    ]

    return tfvars


def write_tfvars_file(tfvars: Dict[str, Any], output_path: Path) -> None:
    """Write tfvars data to a JSON file with deterministic formatting.

    Uses sorted keys and consistent indentation for deterministic output.

    Args:
        tfvars: Terraform variables dictionary
        output_path: Path to write the JSON file
    """
    try:
        with open(output_path, "w") as f:
            json.dump(tfvars, f, indent=2, sort_keys=True)
            f.write("\n")  # Add trailing newline
        print(f"✅ Generated: {output_path}")
    except Exception as e:
        print(f"❌ Error writing {output_path}: {e}")
        raise


def main():
    """Main function to handle command-line arguments and render tfvars files."""
    parser = argparse.ArgumentParser(
        description="Render Terraform tfvars files from NetBox intent export data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from NetBox export directory
  python render_tfvars.py --input-dir artifacts/intent-export

  # Generate from consolidated intent file
  python render_tfvars.py --input-file netbox-client/examples/intent-minimal-schema.json

  # Specify custom output directory
  python render_tfvars.py --input-dir artifacts/intent-export --output-dir /tmp/tfvars

NetBox Field Mapping:
  Sites:      name → site_name, slug → site_slug, description → site_description
  Prefixes:   prefix → cidr, vlan → vlan_id, description → description, status → status
  VLANs:      vlan_id → vlan_id, name → name, description → description, status → status
  Tags:       name → name, slug → slug, description → description, color → color

Output Files:
  artifacts/tfvars/site-{slug}.tfvars.json (one per site)
        """,
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input-dir",
        type=Path,
        help=(
            "Directory containing NetBox export files "
            "(sites.json, prefixes.json, vlans.json, tags.json)"
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
        default=Path("artifacts/tfvars"),
        help="Output directory for tfvars files (default: artifacts/tfvars)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("NetBox to Terraform tfvars Converter")
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
    all_tags = netbox_data["tags"]

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

    # Generate tfvars file for each site
    print("🔨 Generating tfvars files...")
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

        print(f"  - {len(site_prefixes)} prefix(es)")
        print(f"  - {len(site_vlans)} VLAN(s)")
        print(f"  - {len(all_tags)} tag(s) (shared)")

        # Render tfvars for this site
        tfvars = render_site_tfvars(site, site_prefixes, site_vlans, all_tags)

        # Write to file
        # If slug already starts with "site-", don't add it again
        if site_slug.startswith("site-"):
            output_file = args.output_dir / f"{site_slug}.tfvars.json"
        else:
            output_file = args.output_dir / f"site-{site_slug}.tfvars.json"
        write_tfvars_file(tfvars, output_file)
        generated_files.append(output_file)
        print()

    # Summary
    print("=" * 70)
    print("Generation Complete")
    print("=" * 70)
    print(f"✅ Generated {len(generated_files)} tfvars file(s)")
    print(f"   Output location: {args.output_dir.resolve()}")
    print()
    print("Files created:")
    for file_path in generated_files:
        print(f"  - {file_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
