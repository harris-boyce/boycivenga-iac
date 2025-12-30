#!/usr/bin/env python3
"""Apply network configuration via UniFi API directly.

Reads Terraform tfvars format, applies via UniFi API, saves state.
This script provides an alternative to Terraform when the provider has issues.
"""

import argparse
import hashlib
import ipaddress
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


def calculate_dhcp_range(
    cidr: str, start_offset: int = 6, end_offset: int = 254
) -> tuple[str, str]:
    """Calculate DHCP start/stop from CIDR.

    UniFi reserves .1-.5 for system use:
    - .1 = Gateway
    - .2-.5 = Reserved for controller, DNS, etc.

    Default range: .6 to .254 (or last usable IP if subnet is smaller)

    Args:
        cidr: Network CIDR (e.g., "10.100.0.0/24")
        start_offset: IP offset for DHCP start (default: 6)
        end_offset: IP offset for DHCP end (default: 254)

    Returns:
        Tuple of (dhcp_start, dhcp_stop)

    Raises:
        ValueError: If CIDR is invalid or subnet too small
    """
    try:
        network = ipaddress.IPv4Network(cidr, strict=False)
    except (ValueError, ipaddress.AddressValueError) as e:
        raise ValueError(f"Invalid CIDR format '{cidr}': {e}") from e

    # Validate subnet is large enough for DHCP
    # Need at least network + gateway + 1 reserved + 2 DHCP IPs + broadcast = 5 minimum
    usable_ips = network.num_addresses - 2  # Exclude network and broadcast
    if usable_ips < start_offset + 2:
        raise ValueError(
            f"Subnet {cidr} too small for DHCP range "
            f"(only {usable_ips} usable IPs, need at least {start_offset + 2})"
        )

    # Calculate start and end IPs
    start_ip = network.network_address + start_offset
    # Use minimum of end_offset and last usable IP
    # (usable_ips already excludes broadcast)
    max_offset = min(end_offset, usable_ips)
    end_ip = network.network_address + max_offset

    return (str(start_ip), str(end_ip))


def cidr_to_gateway(cidr: str) -> str:
    """Convert network CIDR to gateway IP with mask.

    UniFi API requires gateway IP format (e.g., "10.100.0.1/24")
    not network address format (e.g., "10.100.0.0/24").

    Args:
        cidr: Network CIDR (e.g., "10.100.0.0/24")

    Returns:
        Gateway IP with mask (e.g., "10.100.0.1/24")

    Raises:
        ValueError: If CIDR is invalid
    """
    try:
        network = ipaddress.IPv4Network(cidr, strict=False)
    except (ValueError, ipaddress.AddressValueError) as e:
        raise ValueError(f"Invalid CIDR format '{cidr}': {e}") from e

    # Gateway is always .1 (first usable IP)
    gateway = network.network_address + 1
    return f"{gateway}/{network.prefixlen}"


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
    client: UniFiClient,
    desired_networks: List[Dict[str, Any]],
    site: str = "default",
    fail_fast: bool = False,
) -> Dict[str, Any]:
    """Apply network configurations to UniFi controller.

    Args:
        client: Authenticated UniFi client
        desired_networks: List of network configurations to apply
        site: Site name (default: "default")
        fail_fast: If True, abort on first failure. If False, collect all failures.

    Returns:
        Dictionary with results: created, updated, unchanged, failures,
        and current_state

    Note:
        When fail_fast=False, partial state is still saved for successful
        operations. This allows recovery from partial failures.
    """
    created = []
    updated = []
    unchanged = []
    failures = []

    # PERFORMANCE: Fetch all networks once and cache for lookups
    # Avoids repeated API calls in find_network_by_name()
    print("Fetching existing networks from controller...")
    all_networks = client.get_networks(site)
    network_cache = {net["name"]: net for net in all_networks}
    print(f"  Found {len(all_networks)} existing network(s)")

    for network_config in desired_networks:
        name = network_config["name"]
        print(f"Processing network: {name}")

        try:
            # Check cache instead of making repeated API calls
            existing = network_cache.get(name)

            if existing:
                # Update existing network
                network_id = existing["_id"]
                updated_config = {**existing, **network_config}
                result = client.update_network(network_id, updated_config, site)
                updated.append(result)
                vlan_id = network_config.get("vlan")
                print(f"  ✓ Updated: {name} (VLAN {vlan_id})")
                # Update cache with new result
                network_cache[name] = result
            else:
                # Create new network
                result = client.create_or_update_network(network_config, site)
                created.append(result)
                print(f"  ✓ Created: {name} (VLAN {network_config.get('vlan')})")
                # Add to cache
                network_cache[name] = result

        except Exception as e:
            error_msg = str(e)
            print(f"  ✗ Error processing {name}: {error_msg}")
            failures.append(
                {
                    "network": name,
                    "vlan_id": network_config.get("vlan"),
                    "error": error_msg,
                    "config": network_config,
                }
            )

            if fail_fast:
                raise

    return {
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "failures": failures,
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
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Abort on first failure (default: continue and collect all failures)",
    )

    args = parser.parse_args()

    # Determine state file path
    if args.state_file:
        state_file = args.state_file
    else:
        repo_root = Path(__file__).parent.parent
        state_file = repo_root / "state" / f"{args.site}-networks.json"

    # Production safety check: Insecure TLS must never be enabled in CI/CD
    if os.getenv("GITHUB_ACTIONS") == "true":
        allow_insecure = os.getenv("TF_VAR_unifi_allow_insecure", "").lower()
        if allow_insecure == "true":
            print("❌ SECURITY ERROR: Insecure TLS is not allowed in GitHub Actions")
            print("   Set TF_VAR_unifi_allow_insecure=false in production")
            print("   Insecure TLS is only permitted for local development")
            return 1

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
        result = apply_networks(client, desired_networks, args.site, args.fail_fast)

        print("\nSummary:")
        print(f"  Created: {len(result['created'])}")
        print(f"  Updated: {len(result['updated'])}")
        print(f"  Unchanged: {len(result['unchanged'])}")

        # Report failures if any
        if result["failures"]:
            print(f"  Failed: {len(result['failures'])}")
            print("\nFailed networks:")
            for failure in result["failures"]:
                net_name = failure["network"]
                vlan_id = failure["vlan_id"]
                error = failure["error"]
                print(f"  ✗ {net_name} (VLAN {vlan_id}): {error}")

        # Save state even if some failed (partial state for recovery)
        # Only save successful networks
        save_state(result, state_file, tfvars_checksum, args.site)

        if result["failures"]:
            print("\n⚠️  Apply completed with failures")
            print("   Partial state saved for successful networks")
            print("   Review errors above and re-run to retry failed networks")
            return 1
        else:
            print("\n✓ Apply completed successfully")
            return 0

    except Exception as e:
        print(f"\n✗ Apply failed: {e}")
        return 1

    finally:
        client.logout()


if __name__ == "__main__":
    sys.exit(main())
