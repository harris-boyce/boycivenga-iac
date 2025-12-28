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


def extract_site_from_vlan(vlan_data: Dict[str, Any]) -> Optional[str]:
    """Extract site slug from VLAN data.

    Handles both NetBox API format (nested object) and minimal schema (string).

    Args:
        vlan_data: VLAN dictionary from NetBox export

    Returns:
        Site slug string, or None if site cannot be determined
    """
    vlan_site = vlan_data.get("site")
    if isinstance(vlan_site, dict):
        return vlan_site.get("slug", vlan_site.get("name"))
    elif isinstance(vlan_site, str):
        return vlan_site
    return None


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
    """Extract VLAN VID from prefix's VLAN association.

    Returns VLAN VID (the actual VLAN tag like 10, 20, 30) which is used
    in Terraform tfvars output. VIDs can be reused across sites.

    Handles both:
    - Nested VLAN object: {"id": 180, "vid": 10, "name": "LAN"}
      (NetBox API format - extracts 'vid' field)
    - Simple integer: 10 (minimal schema format)

    Args:
        prefix_data: Prefix dictionary from NetBox export

    Returns:
        VLAN VID as integer, or None if not associated
    """
    vlan = prefix_data.get("vlan")

    if vlan is None:
        return None
    elif isinstance(vlan, dict):
        # NetBox API format: extract VID from nested object
        vlan_vid = vlan.get("vid")
        if vlan_vid is None:
            vlan_vid = vlan.get("vlan_id")
        return vlan_vid
    elif isinstance(vlan, int):
        # Minimal schema format: integer is the VID
        return vlan
    else:
        return None


def build_vlan_site_mapping(
    all_vlans: List[Dict[str, Any]],
) -> Dict[tuple[str, int], str]:
    """Build a mapping of (site_slug, VLAN VID) to site slug.

    This mapping is used to determine which site a prefix belongs to
    based on its VLAN association, since NetBox API prefix objects
    do not include a direct 'site' field.

    Uses composite keys (site_slug, vid) which naturally handles the common
    case where multiple sites use the same VLAN VIDs (e.g., both sites having
    VLAN 10 for their LAN). This is a valid network design since VLANs are
    layer-2 constructs isolated per site.

    Args:
        all_vlans: List of all VLANs from NetBox export

    Returns:
        Dictionary mapping (site_slug, vid) tuple to site slug
        Example: {("pennington", 10): "pennington",
                  ("countfleetcourt", 10): "countfleetcourt"}

    Note:
        - Handles both NetBox API format (nested site object) and
          minimal schema format (simple site string)
        - VLANs without site associations or VIDs are skipped
        - Same VID can exist at multiple sites (this is normal and valid)
    """
    mapping = {}

    for vlan in all_vlans:
        # Extract site slug
        site_slug = extract_site_from_vlan(vlan)
        if not site_slug:
            continue

        # Extract VLAN VID
        try:
            vlan_vid = extract_vlan_id(vlan)
        except ValueError:
            # Skip VLANs with null/missing VID
            continue

        # Use composite key (site_slug, vid) to allow same VID at different sites
        mapping[(site_slug, vlan_vid)] = site_slug

    return mapping


def build_vlan_id_to_site_mapping(
    all_vlans: List[Dict[str, Any]],
) -> Dict[int, str]:
    """Build a mapping of VLAN internal ID to site slug.

    This mapping is used to determine site from sparse VLAN references
    in prefix objects, which only include the internal VLAN ID but not
    the full site information.

    Args:
        all_vlans: List of all VLANs from NetBox export (full objects)

    Returns:
        Dictionary mapping internal VLAN ID to site slug
        Example: {180: "pennington", 187: "countfleetcourt"}

    Note:
        - Only VLANs with both internal ID and site are included
        - Used alongside composite key mapping for complete functionality
    """
    mapping = {}

    for vlan in all_vlans:
        # Extract internal ID
        vlan_id = vlan.get("id")
        if vlan_id is None:
            continue

        # Extract site slug
        site_slug = extract_site_from_vlan(vlan)
        if site_slug:
            mapping[vlan_id] = site_slug

    return mapping


def extract_prefix_site(
    prefix: Dict[str, Any],
    vlan_site_mapping: Dict[tuple[str, int], str],
    vlan_id_to_site: Dict[int, str],
) -> Optional[str]:
    """Extract the site slug for a prefix.

    Tries multiple methods in order:
    1. Direct 'site' field (minimal schema compatibility)
    2a. VLAN association lookup using nested VLAN's site (NetBox API with full VLAN)
    2b. VLAN internal ID lookup (NetBox API with sparse VLAN reference)

    Args:
        prefix: Prefix dictionary from NetBox export
        vlan_site_mapping: (site_slug, vid) → site slug mapping
            (for composite key lookups)
        vlan_id_to_site: internal_vlan_id → site slug mapping
            (for sparse VLAN lookups)

    Returns:
        Site slug string, or None if site cannot be determined
    """
    # Method 1: Check for direct site field (minimal schema format)
    prefix_site = prefix.get("site")
    if prefix_site:
        if isinstance(prefix_site, dict):
            return prefix_site.get("slug", prefix_site.get("name"))
        elif isinstance(prefix_site, str):
            return prefix_site

    # Method 2: Look up via VLAN association (NetBox API format)
    vlan = prefix.get("vlan")
    if vlan and isinstance(vlan, dict):
        # Method 2a: Try to get site from full VLAN object (if available)
        vlan_site_slug = extract_site_from_vlan({"site": vlan.get("site")})
        vlan_vid = vlan.get("vid")
        if vlan_vid is None:
            vlan_vid = vlan.get("vlan_id")

        if vlan_site_slug and vlan_vid is not None:
            # Look up using composite key (full VLAN object case)
            return vlan_site_mapping.get((vlan_site_slug, vlan_vid))

        # Method 2b: Fall back to internal ID lookup (sparse VLAN reference)
        vlan_internal_id = vlan.get("id")
        if vlan_internal_id is not None:
            site_from_id = vlan_id_to_site.get(vlan_internal_id)
            if site_from_id:
                return site_from_id

    # No site could be determined
    return None


def filter_resources_by_site(
    resources: List[Dict[str, Any]],
    site_slug: str,
    site_name: str,
    resource_type: str,
    vlan_site_mapping: Optional[Dict[tuple[str, int], str]] = None,
    vlan_id_to_site: Optional[Dict[int, str]] = None,
) -> List[Dict[str, Any]]:
    """Filter resources (prefixes or VLANs) by site.

    Handles both NetBox API format (nested objects) and minimal schema format
    (simple strings). For prefixes, uses VLAN association to determine site.

    Args:
        resources: List of resource dictionaries
        site_slug: Site slug to filter by
        site_name: Site name to filter by (fallback)
        resource_type: Type of resource ("prefix" or "vlan")
        vlan_site_mapping: (site_slug, vid) → site slug mapping
            (for composite key lookups)
        vlan_id_to_site: internal_vlan_id → site slug mapping
            (for sparse VLAN lookups)

    Returns:
        Filtered list of resources belonging to the specified site
    """
    filtered = []
    unmatched = []

    for resource in resources:
        resource_site_slug = None

        if resource_type == "prefix":
            # Use VLAN-based matching for prefixes
            if vlan_site_mapping is None or vlan_id_to_site is None:
                raise ValueError(
                    "vlan_site_mapping and vlan_id_to_site required "
                    "for prefix filtering"
                )
            resource_site_slug = extract_prefix_site(
                resource, vlan_site_mapping, vlan_id_to_site
            )
        else:
            # Direct site field for VLANs
            resource_site = resource.get("site")
            if isinstance(resource_site, dict):
                resource_site_slug = resource_site.get(
                    "slug", resource_site.get("name")
                )
            else:
                resource_site_slug = resource_site

        # Match against site slug or name
        if resource_site_slug == site_slug or resource_site_slug == site_name:
            filtered.append(resource)
        elif resource_site_slug is None:
            unmatched.append(resource)

    # Log unmatched resources for debugging
    if unmatched:
        print(f"  ⚠️  {len(unmatched)} {resource_type}(s) without site association:")
        for res in unmatched[:3]:  # Show first 3
            if resource_type == "prefix":
                vlan_id = extract_vlan_association(res)
                print(
                    f"     - {res.get('prefix', 'unknown')}: "
                    f"VLAN={vlan_id}, "
                    f'desc="{res.get("description", "")[:40]}"'
                )
            else:
                try:
                    vlan_id_val = extract_vlan_id(res)
                    print(
                        f"     - VLAN {vlan_id_val}: " f"{res.get('name', 'unnamed')}"
                    )
                except ValueError:
                    print(f"     - VLAN ?: {res.get('name', 'unnamed')}")
        if len(unmatched) > 3:
            print(f"     ... and {len(unmatched) - 3} more")

    return filtered


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

    # Build VLAN → Site mapping for prefix-to-site matching
    print("🔗 Building VLAN → Site mapping...")
    vlan_site_mapping = build_vlan_site_mapping(all_vlans)
    vlan_id_to_site = build_vlan_id_to_site_mapping(all_vlans)
    print(f"   Composite key mapping: {len(vlan_site_mapping)} entries")
    print(f"   Internal ID mapping: {len(vlan_id_to_site)} VLANs")
    print()

    # Generate tfvars file for each site
    print("🔨 Generating tfvars files...")
    print()

    generated_files = []
    for site in sites:
        site_slug = extract_site_slug(site)
        site_name = site.get("name", site_slug)

        print(f"Processing site: {site_name} ({site_slug})")

        # Filter prefixes and VLANs for this site using VLAN-based matching
        site_prefixes = filter_resources_by_site(
            all_prefixes,
            site_slug,
            site_name,
            "prefix",
            vlan_site_mapping,
            vlan_id_to_site,
        )

        site_vlans = filter_resources_by_site(all_vlans, site_slug, site_name, "vlan")

        # Filter VLANs to only include those with corresponding prefixes
        # This ensures Terraform contract compliance: each VLAN must have a network
        prefix_vlan_ids = {
            extract_vlan_association(p)
            for p in site_prefixes
            if extract_vlan_association(p) is not None
        }
        site_vlans_with_prefixes = [
            v for v in site_vlans if extract_vlan_id(v) in prefix_vlan_ids
        ]

        if len(site_vlans_with_prefixes) < len(site_vlans):
            skipped = len(site_vlans) - len(site_vlans_with_prefixes)
            print(
                f"  ⚠️  Skipping {skipped} VLAN(s) without prefix assignments "
                f"(Terraform requires each VLAN to have a network)"
            )

        print(f"  - {len(site_prefixes)} prefix(es)")
        print(f"  - {len(site_vlans_with_prefixes)} VLAN(s)")
        print(f"  - {len(all_tags)} tag(s) (shared)")

        # Render tfvars for this site
        tfvars = render_site_tfvars(
            site, site_prefixes, site_vlans_with_prefixes, all_tags
        )

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
