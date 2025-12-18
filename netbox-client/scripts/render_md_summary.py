#!/usr/bin/env python3
"""Render human-readable Markdown network summaries from NetBox intent export data.

This script converts NetBox intent-export JSON files into Markdown summary
documents, one per site. Each summary includes site information, prefixes,
VLANs, tags, and a high-level topology diagram using Mermaid.

The script reads NetBox data exported by export_intent.py (or compatible format)
and generates site-specific Markdown files that can be used for documentation,
review, or operational reference.

Usage:
    # Generate summaries from NetBox export directory
    python netbox-client/scripts/render_md_summary.py \
        --input-dir artifacts/intent-export

    # Generate from a single consolidated intent file
    python netbox-client/scripts/render_md_summary.py \
        --input-file netbox-client/examples/intent-minimal-schema.json

    # Specify custom output directory
    python netbox-client/scripts/render_md_summary.py \
        --input-dir artifacts/intent-export --output-dir /tmp/summaries

Output:
    Generates files in artifacts/summary/:
    - site-pennington.md
    - site-countfleetcourt.md
    - etc.

Each summary includes:
    - Site name and description
    - Network prefixes with VLAN associations
    - VLAN configurations
    - Applied tags
    - Mermaid topology diagram

Environment Variables:
    None required. This script operates on local files.

Features:
    - Human-readable Markdown format
    - Mermaid diagrams for visual topology
    - Site isolation: Each site gets its own summary file
    - Comprehensive network documentation
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


def extract_site_slug(site_data: Dict[str, Any]) -> str:
    """Extract site slug from site data.

    Tries 'slug' first, falls back to 'name' if slug is missing.

    Args:
        site_data: Site dictionary from NetBox export

    Returns:
        Site slug string
    """
    return site_data.get("slug", site_data.get("name", "unknown"))


def generate_mermaid_topology(
    site: Dict[str, Any],
    prefixes: List[Dict[str, Any]],
    vlans: List[Dict[str, Any]],
) -> str:
    """Generate a Mermaid diagram showing network topology.

    Creates a simple network diagram showing the site, VLANs, and prefixes.

    Args:
        site: Site data from NetBox
        prefixes: List of prefixes for this site
        vlans: List of VLANs for this site

    Returns:
        Mermaid diagram as a string
    """
    site_name = site.get("name", "Site")
    site_slug = extract_site_slug(site)

    # Start mermaid diagram
    lines = [
        "```mermaid",
        "graph TD",
        f"    Site[\"{site_name}\"]",
    ]

    # Create VLAN nodes
    vlan_map = {vlan.get("vlan_id"): vlan for vlan in vlans}

    if vlans:
        for vlan in vlans:
            vlan_id = vlan.get("vlan_id", "?")
            vlan_name = vlan.get("name", f"VLAN {vlan_id}")
            vlan_node_id = f"VLAN{vlan_id}"
            lines.append(f"    {vlan_node_id}[\"VLAN {vlan_id}: {vlan_name}\"]")
            lines.append(f"    Site --> {vlan_node_id}")

    # Add prefix nodes connected to their VLANs
    if prefixes:
        for i, prefix in enumerate(prefixes):
            prefix_cidr = prefix.get("prefix", "unknown")
            prefix_desc = prefix.get("description", "")
            vlan_id = prefix.get("vlan")

            # Create sanitized node ID
            prefix_node_id = f"Prefix{i}"

            # Build label
            if prefix_desc:
                prefix_label = f"{prefix_cidr}<br/>{prefix_desc}"
            else:
                prefix_label = prefix_cidr

            lines.append(f"    {prefix_node_id}[\"{prefix_label}\"]")

            # Connect to VLAN if associated
            if vlan_id and vlan_id in vlan_map:
                vlan_node_id = f"VLAN{vlan_id}"
                lines.append(f"    {vlan_node_id} --> {prefix_node_id}")
            else:
                # Connect directly to site if no VLAN
                lines.append(f"    Site --> {prefix_node_id}")

    # Close mermaid block
    lines.append("```")

    return "\n".join(lines)


def render_site_markdown(
    site: Dict[str, Any],
    prefixes: List[Dict[str, Any]],
    vlans: List[Dict[str, Any]],
    tags: List[Dict[str, Any]],
) -> str:
    """Render Markdown summary for a single site.

    Args:
        site: Site data from NetBox
        prefixes: List of prefixes for this site
        vlans: List of VLANs for this site
        tags: List of all tags

    Returns:
        Markdown document as a string
    """
    site_name = site.get("name", "Unknown Site")
    site_slug = extract_site_slug(site)
    site_desc = site.get("description", "")

    lines = [
        f"# Network Summary: {site_name}",
        "",
    ]

    # Site information
    lines.extend([
        "## Site Information",
        "",
        f"**Name:** {site_name}",
        f"**Slug:** {site_slug}",
    ])

    if site_desc:
        lines.append(f"**Description:** {site_desc}")

    lines.append("")

    # Topology diagram
    lines.extend([
        "## Network Topology",
        "",
        generate_mermaid_topology(site, prefixes, vlans),
        "",
    ])

    # Prefixes section
    lines.extend([
        "## IP Prefixes",
        "",
    ])

    if prefixes:
        lines.extend([
            "| Prefix | VLAN ID | Description | Status |",
            "|--------|---------|-------------|--------|",
        ])
        for prefix in prefixes:
            prefix_cidr = prefix.get("prefix", "N/A")
            vlan_id = prefix.get("vlan", "N/A")
            if vlan_id == "N/A" or vlan_id is None:
                vlan_id = "—"
            description = prefix.get("description", "")
            status = prefix.get("status", "active")
            lines.append(f"| {prefix_cidr} | {vlan_id} | {description} | {status} |")
    else:
        lines.append("*No prefixes configured*")

    lines.append("")

    # VLANs section
    lines.extend([
        "## VLANs",
        "",
    ])

    if vlans:
        lines.extend([
            "| VLAN ID | Name | Description | Status |",
            "|---------|------|-------------|--------|",
        ])
        for vlan in vlans:
            vlan_id = vlan.get("vlan_id", "N/A")
            name = vlan.get("name", "")
            description = vlan.get("description", "")
            status = vlan.get("status", "active")
            lines.append(f"| {vlan_id} | {name} | {description} | {status} |")
    else:
        lines.append("*No VLANs configured*")

    lines.append("")

    # Tags section
    lines.extend([
        "## Tags",
        "",
    ])

    if tags:
        lines.extend([
            "| Name | Slug | Description | Color |",
            "|------|------|-------------|-------|",
        ])
        for tag in tags:
            name = tag.get("name", "")
            slug = tag.get("slug", "")
            description = tag.get("description", "")
            color = tag.get("color", "")
            color_display = f"🎨 `{color}`" if color else ""
            lines.append(f"| {name} | {slug} | {description} | {color_display} |")
    else:
        lines.append("*No tags configured*")

    lines.extend([
        "",
        "---",
        "",
        f"*Generated from NetBox intent data for {site_name}*",
        "",
    ])

    return "\n".join(lines)


def write_markdown_file(content: str, output_path: Path) -> None:
    """Write Markdown content to a file.

    Args:
        content: Markdown content string
        output_path: Path to write the Markdown file
    """
    try:
        with open(output_path, "w") as f:
            f.write(content)
        print(f"✅ Generated: {output_path}")
    except Exception as e:
        print(f"❌ Error writing {output_path}: {e}")
        raise


def main():
    """Main function to handle command-line arguments and render Markdown summaries."""
    parser = argparse.ArgumentParser(
        description="Render Markdown network summaries from NetBox intent export data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from NetBox export directory
  python render_md_summary.py --input-dir artifacts/intent-export

  # Generate from consolidated intent file
  python render_md_summary.py --input-file netbox-client/examples/intent-minimal-schema.json

  # Specify custom output directory
  python render_md_summary.py --input-dir artifacts/intent-export --output-dir /tmp/summaries

Output Content:
  Each Markdown file includes:
  - Site information (name, slug, description)
  - Network topology diagram (Mermaid)
  - IP prefixes table
  - VLANs table
  - Tags table

Output Files:
  artifacts/summary/site-{slug}.md (one per site)
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
        default=Path("artifacts/summary"),
        help="Output directory for Markdown files (default: artifacts/summary)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("NetBox to Markdown Summary Converter")
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

    # Generate Markdown summary for each site
    print("🔨 Generating Markdown summaries...")
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

        # Render Markdown for this site
        markdown_content = render_site_markdown(
            site, site_prefixes, site_vlans, all_tags
        )

        # Write to file
        # If slug already starts with "site-", don't add it again
        if site_slug.startswith("site-"):
            output_file = args.output_dir / f"{site_slug}.md"
        else:
            output_file = args.output_dir / f"site-{site_slug}.md"
        write_markdown_file(markdown_content, output_file)
        generated_files.append(output_file)
        print()

    # Summary
    print("=" * 70)
    print("Generation Complete")
    print("=" * 70)
    print(f"✅ Generated {len(generated_files)} Markdown summary file(s)")
    print(f"   Output location: {args.output_dir.resolve()}")
    print()
    print("Files created:")
    for file_path in generated_files:
        print(f"  - {file_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
