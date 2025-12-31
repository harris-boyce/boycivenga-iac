#!/usr/bin/env python3
"""Preview changes before applying (equivalent to terraform plan).

Compares desired state from tfvars against:
1. Recorded state (state file from last apply)
2. Actual state (current UniFi controller state)

Detects:
- Networks to create (in tfvars but not in controller)
- Networks to update (exist but differ from tfvars)
- Networks to delete (in controller but not in tfvars)
- Drift (controller differs from recorded state)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add tests/integration to path for imports  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent.parent / "tests" / "integration"))

from helpers.unifi_client import UniFiClient  # noqa: E402

# Import functions from apply script  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent))
from apply_via_unifi import build_desired_state, load_tfvars  # noqa: E402


def load_state_file(state_file: Path) -> Optional[Dict[str, Any]]:
    """Load state file if it exists.

    Args:
        state_file: Path to state file

    Returns:
        State dictionary or None if file doesn't exist
    """
    if not state_file.exists():
        return None

    with open(state_file, "r") as f:
        return json.load(f)


def normalize_network_for_comparison(network: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize network config for comparison.

    UniFi API returns many fields we don't care about. Extract only the
    fields we manage via tfvars for accurate comparison.

    Args:
        network: Network dictionary from UniFi API or state file

    Returns:
        Normalized dictionary with only managed fields
    """
    return {
        "name": network.get("name"),
        "vlan": network.get("vlan") or network.get("vlan_id"),
        "ip_subnet": network.get("ip_subnet") or network.get("subnet"),
        "dhcpd_enabled": network.get("dhcpd_enabled", True),
        "dhcpd_start": network.get("dhcpd_start"),
        "dhcpd_stop": network.get("dhcpd_stop"),
    }


def networks_differ(net1: Dict[str, Any], net2: Dict[str, Any]) -> bool:
    """Compare two networks to see if they differ.

    Args:
        net1: First network (normalized)
        net2: Second network (normalized)

    Returns:
        True if networks differ in any managed field
    """
    # Compare only the fields we manage
    fields_to_compare = [
        "vlan",
        "ip_subnet",
        "dhcpd_enabled",
        "dhcpd_start",
        "dhcpd_stop",
    ]

    for field in fields_to_compare:
        if net1.get(field) != net2.get(field):
            return True

    return False


def compute_diff(
    desired: List[Dict[str, Any]],
    recorded: List[Dict[str, Any]],
    actual: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute three-way diff between desired, recorded, and actual state.

    Args:
        desired: Networks from tfvars (what we want)
        recorded: Networks from state file (what we applied last time)
        actual: Networks from UniFi controller (what exists now)

    Returns:
        Dictionary with to_create, to_update, to_delete, drift lists
    """
    # Build name-based lookups for fast access
    desired_by_name = {net["name"]: net for net in desired}
    recorded_by_name = {net.get("name"): net for net in recorded}
    actual_by_name = {net.get("name"): net for net in actual}

    to_create = []
    to_update = []
    to_delete = []
    drift = []

    # Check what needs to be created or updated
    for name, desired_net in desired_by_name.items():
        actual_net = actual_by_name.get(name)

        if not actual_net:
            # Network doesn't exist - needs to be created
            to_create.append(desired_net)
        else:
            # Network exists - check if it needs updating
            desired_norm = normalize_network_for_comparison(desired_net)
            actual_norm = normalize_network_for_comparison(actual_net)

            if networks_differ(desired_norm, actual_norm):
                to_update.append(
                    {
                        "name": name,
                        "current": actual_norm,
                        "desired": desired_norm,
                    }
                )

            # Check for drift (actual differs from recorded)
            recorded_net = recorded_by_name.get(name)
            if recorded_net:
                recorded_norm = normalize_network_for_comparison(recorded_net)
                if networks_differ(actual_norm, recorded_norm):
                    drift.append(
                        {
                            "name": name,
                            "recorded": recorded_norm,
                            "actual": actual_norm,
                        }
                    )

    # Check what needs to be deleted (exists but not desired)
    for name, actual_net in actual_by_name.items():
        if name not in desired_by_name:
            # Skip non-test networks to avoid accidental deletion
            if not name.startswith("test-"):
                continue
            to_delete.append(actual_net)

    is_clean = not (to_create or to_update or to_delete)

    return {
        "to_create": to_create,
        "to_update": to_update,
        "to_delete": to_delete,
        "drift": drift,
        "is_clean": is_clean,
    }


def print_diff_summary(diff: Dict[str, Any]) -> None:
    """Print human-readable diff summary.

    Args:
        diff: Diff dictionary from compute_diff()
    """
    print("\n" + "=" * 70)
    print("PLAN SUMMARY")
    print("=" * 70)

    if diff["is_clean"]:
        print("\n✓ No changes needed - infrastructure matches desired state")
        return

    # Print networks to create
    if diff["to_create"]:
        print(f"\n[+] Networks to CREATE: {len(diff['to_create'])}")
        for net in diff["to_create"]:
            print(f"    + {net['name']}")
            print(f"      VLAN: {net.get('vlan')}")
            print(f"      Subnet: {net.get('ip_subnet')}")

    # Print networks to update
    if diff["to_update"]:
        print(f"\n[~] Networks to UPDATE: {len(diff['to_update'])}")
        for net in diff["to_update"]:
            print(f"    ~ {net['name']}")
            current = net["current"]
            desired = net["desired"]

            # Show what's changing
            for field in [
                "vlan",
                "ip_subnet",
                "dhcpd_enabled",
                "dhcpd_start",
                "dhcpd_stop",
            ]:
                if current.get(field) != desired.get(field):
                    print(f"      {field}: {current.get(field)} → {desired.get(field)}")

    # Print networks to delete
    if diff["to_delete"]:
        print(f"\n[-] Networks to DELETE: {len(diff['to_delete'])}")
        for net in diff["to_delete"]:
            print(f"    - {net.get('name')}")
            print(f"      VLAN: {net.get('vlan')}")
            print(f"      Subnet: {net.get('ip_subnet')}")

    # Print drift warnings
    if diff["drift"]:
        drift_count = len(diff["drift"])
        print(
            f"\n[!] DRIFT DETECTED: {drift_count} network(s) "
            f"modified outside of this tool"
        )
        for net in diff["drift"]:
            print(f"    ! {net['name']}")
            recorded = net["recorded"]
            actual = net["actual"]

            for field in [
                "vlan",
                "ip_subnet",
                "dhcpd_enabled",
                "dhcpd_start",
                "dhcpd_stop",
            ]:
                if recorded.get(field) != actual.get(field):
                    rec_val = recorded.get(field)
                    act_val = actual.get(field)
                    print(
                        f"      {field}: {rec_val} (recorded) vs " f"{act_val} (actual)"
                    )

    print("\n" + "=" * 70)
    create_count = len(diff["to_create"])
    update_count = len(diff["to_update"])
    delete_count = len(diff["to_delete"])
    print(
        f"Plan: {create_count} to create, {update_count} to update, "
        f"{delete_count} to delete"
    )
    print("=" * 70 + "\n")


def main():
    """Main entry point for plan script."""
    parser = argparse.ArgumentParser(
        description="Preview network configuration changes (like terraform plan)"
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
        "--ignore-drift",
        action="store_true",
        help="Don't report drift (manual changes)",
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
        # Check both UNIFI_ALLOW_INSECURE and TF_VAR_unifi_allow_insecure
        # for backward compatibility
        allow_insecure = (
            os.getenv("UNIFI_ALLOW_INSECURE")
            or os.getenv("TF_VAR_unifi_allow_insecure")
            or ""
        ).lower()
        if allow_insecure == "true":
            print("❌ SECURITY ERROR: Insecure TLS is not allowed in GitHub Actions")
            print("   Set UNIFI_ALLOW_INSECURE=false in production")
            print("   Insecure TLS is only permitted for local development")
            return 1

    # Load desired state from tfvars
    print(f"Loading desired state from: {args.tfvars}")
    tfvars = load_tfvars(args.tfvars)
    desired = build_desired_state(tfvars)
    print(f"  Found {len(desired)} desired network(s)")

    # Load recorded state from state file (optional - for drift detection)
    print(f"\nLoading recorded state from: {state_file}")
    state_data = load_state_file(state_file)
    if state_data:
        recorded = state_data.get("networks", [])
        print(f"  Found {len(recorded)} recorded network(s)")
        print(f"  Last applied: {state_data.get('applied_at')}")
        print(f"  Applied by: {state_data.get('applied_by')}")
    else:
        recorded = []
        print(
            "  No state file found - comparing desired (NetBox) vs actual (UniFi) only"
        )

    # Load actual state from UniFi controller
    print(f"\nQuerying UniFi controller for site: {args.site}")
    client = UniFiClient()
    client.login()
    try:
        all_networks = client.get_networks(args.site)
        # Filter to only test networks or networks we manage
        actual = [
            net
            for net in all_networks
            if net.get("name", "").startswith("test-")
            or any(d["name"] == net.get("name") for d in desired)
        ]
        print(f"  Found {len(actual)} managed network(s)")
    finally:
        client.logout()

    # Compute diff
    print("\nComputing diff...")
    diff = compute_diff(desired, recorded, actual)

    # Optionally suppress drift reporting
    if args.ignore_drift:
        diff["drift"] = []

    # Print summary
    print_diff_summary(diff)

    # Exit with appropriate code
    # 0 = no changes needed
    # 2 = changes detected (Terraform convention)
    if diff["is_clean"]:
        return 0
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())
