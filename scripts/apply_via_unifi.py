#!/usr/bin/env python3
"""Apply network configuration via UniFi API directly.

Reads Terraform tfvars format, applies via UniFi API, saves state.
This script provides an alternative to Terraform when the provider has issues.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add tests/integration to path for imports  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent.parent / "tests" / "integration"))

from helpers.unifi_client import UniFiClient  # noqa: E402


def load_tfvars(tfvars_path: Path) -> Dict[str, Any]:
    """Load Terraform variables from JSON file.

    Args:
        tfvars_path: Path to tfvars.json file

    Returns:
        Dictionary of Terraform variables
    """
    if not tfvars_path.exists():
        raise FileNotFoundError(f"Tfvars file not found: {tfvars_path}")

    with open(tfvars_path, "r") as f:
        return json.load(f)


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file.

    Args:
        file_path: Path to file

    Returns:
        Hex digest of SHA256 hash
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


def calculate_dhcp_range(cidr: str) -> tuple[str, str]:
    """Calculate DHCP start/stop from CIDR.

    Args:
        cidr: Network CIDR (e.g., "10.100.0.0/24")

    Returns:
        Tuple of (dhcp_start, dhcp_stop)
    """
    # Simple implementation: .6 to .254
    # Example: 10.100.0.0/24 -> 10.100.0.6 to 10.100.0.254
    network = cidr.split("/")[0]
    octets = network.split(".")
    base = ".".join(octets[:3])

    return (f"{base}.6", f"{base}.254")


def cidr_to_gateway(cidr: str) -> str:
    """Convert network CIDR to gateway IP with mask.

    Args:
        cidr: Network CIDR (e.g., "10.100.0.0/24")

    Returns:
        Gateway IP with mask (e.g., "10.100.0.1/24")
    """
    network, mask = cidr.split("/")
    octets = network.split(".")
    # Use .1 as gateway
    octets[-1] = "1"
    gateway = ".".join(octets)
    return f"{gateway}/{mask}"


def build_network_config(
    vlan: Dict[str, Any], prefix: Dict[str, Any]
) -> Dict[str, Any]:
    """Build UniFi network configuration from VLAN and prefix.

    Args:
        vlan: VLAN configuration from tfvars
        prefix: Network prefix configuration from tfvars

    Returns:
        UniFi API network configuration dictionary
    """
    dhcp_start, dhcp_stop = calculate_dhcp_range(prefix["cidr"])

    # Build network config in UniFi API format
    # Note: UniFi expects ip_subnet to be gateway IP, not network address
    config = {
        "name": vlan["name"],
        "purpose": "corporate",
        "networkgroup": "LAN",
        "vlan_enabled": True,
        "vlan": vlan["vlan_id"],
        "ip_subnet": cidr_to_gateway(prefix["cidr"]),  # Convert to gateway IP
        "dhcpd_enabled": True,
        "dhcpd_start": dhcp_start,
        "dhcpd_stop": dhcp_stop,
    }

    return config


def build_desired_state(tfvars: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Transform tfvars into UniFi API network configurations.

    Args:
        tfvars: Terraform variables dictionary

    Returns:
        List of UniFi network configurations
    """
    networks = []

    # Create a mapping of vlan_id -> prefix for quick lookup
    prefix_map = {p["vlan_id"]: p for p in tfvars.get("prefixes", [])}

    for vlan in tfvars.get("vlans", []):
        vlan_id = vlan["vlan_id"]

        # Find corresponding prefix
        if vlan_id not in prefix_map:
            vlan_name = vlan["name"]
            print(
                f"WARNING: No prefix found for VLAN {vlan_id} "
                f"({vlan_name}), skipping"
            )
            continue

        prefix = prefix_map[vlan_id]
        network_config = build_network_config(vlan, prefix)
        networks.append(network_config)

    return networks


def apply_networks(
    client: UniFiClient, desired_networks: List[Dict[str, Any]], site: str = "default"
) -> Dict[str, Any]:
    """Apply network configurations to UniFi controller.

    Args:
        client: Authenticated UniFi client
        desired_networks: List of network configurations to apply
        site: Site name (default: "default")

    Returns:
        Dictionary with results: created, updated, unchanged counts and network details
    """
    created = []
    updated = []
    unchanged = []

    for network_config in desired_networks:
        name = network_config["name"]
        print(f"Processing network: {name}")

        try:
            # Use idempotent create_or_update
            result = client.create_or_update_network(network_config, site)

            # Determine if it was created or updated by checking if it existed before
            existing = client.find_network_by_name(name, site)
            if existing and existing.get("_id") == result.get("_id"):
                # Check if anything actually changed
                # For simplicity, consider create_or_update as update if existed
                updated.append(result)
                vlan_id = network_config.get("vlan")
                print(f"  ✓ Updated: {name} (VLAN {vlan_id})")
            else:
                created.append(result)
                print(f"  ✓ Created: {name} (VLAN {network_config.get('vlan')})")

        except Exception as e:
            print(f"  ✗ Error processing {name}: {e}")
            raise

    return {
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "current_state": created + updated + unchanged,
    }


def save_state(
    state_data: Dict[str, Any], state_file: Path, tfvars_checksum: str, site: str
) -> None:
    """Save state to JSON file.

    Args:
        state_data: State data from apply_networks
        state_file: Path to state file
        tfvars_checksum: Checksum of tfvars file
        site: Site name
    """
    state = {
        "format_version": "1.0",
        "applied_at": datetime.utcnow().isoformat() + "Z",
        "applied_by": os.getenv("GITHUB_ACTOR", os.getenv("USER", "unknown")),
        "site": site,
        "tfvars_checksum": tfvars_checksum,
        "networks": [
            {
                "id": net.get("_id"),
                "name": net.get("name"),
                "vlan_id": net.get("vlan"),
                "subnet": net.get("ip_subnet"),
                "created_at": datetime.utcnow().isoformat() + "Z",
                "source": "netbox",
            }
            for net in state_data["current_state"]
        ],
    }

    # Ensure parent directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)

    # Write state file
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    print(f"\n✓ State saved to: {state_file}")


def main():
    """Main entry point for apply script."""
    parser = argparse.ArgumentParser(
        description="Apply network configuration via UniFi API"
    )
    parser.add_argument(
        "--tfvars",
        type=Path,
        required=True,
        help="Path to Terraform tfvars.json file",
    )
    parser.add_argument(
        "--site",
        type=str,
        default="default",
        help="UniFi site name (default: default)",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        help="Path to state file (default: state/{site}-networks.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying",
    )

    args = parser.parse_args()

    # Determine state file path
    if args.state_file:
        state_file = args.state_file
    else:
        repo_root = Path(__file__).parent.parent
        state_file = repo_root / "state" / f"{args.site}-networks.json"

    # Load tfvars
    print(f"Loading tfvars from: {args.tfvars}")
    tfvars = load_tfvars(args.tfvars)
    tfvars_checksum = calculate_file_checksum(args.tfvars)

    # Build desired state
    print(f"\nBuilding desired state for site: {args.site}")
    desired_networks = build_desired_state(tfvars)
    print(f"  Found {len(desired_networks)} network(s) to apply")

    if args.dry_run:
        print("\nDRY RUN - Would apply:")
        for net in desired_networks:
            print(f"  - {net['name']} (VLAN {net['vlan']}): {net['ip_subnet']}")
        print("\nNo changes applied (dry-run mode)")
        return 0

    # Connect to UniFi
    print("\nConnecting to UniFi controller...")
    client = UniFiClient()
    client.login()
    print("  ✓ Authenticated")

    # Apply networks
    net_count = len(desired_networks)
    print(f"\nApplying {net_count} network(s)...")
    try:
        result = apply_networks(client, desired_networks, args.site)

        print("\nSummary:")
        print(f"  Created: {len(result['created'])}")
        print(f"  Updated: {len(result['updated'])}")
        print(f"  Unchanged: {len(result['unchanged'])}")

        # Save state
        save_state(result, state_file, tfvars_checksum, args.site)

        print("\n✓ Apply completed successfully")
        return 0

    except Exception as e:
        print(f"\n✗ Apply failed: {e}")
        return 1

    finally:
        client.logout()


if __name__ == "__main__":
    sys.exit(main())
