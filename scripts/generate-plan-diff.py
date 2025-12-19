#!/usr/bin/env python3
"""
Generate a structured, human-readable diff from a Terraform JSON plan.
This script creates a markdown summary suitable for both humans and automated tools.
"""

import json
import sys
from collections import defaultdict


def main():
    if len(sys.argv) < 3:
        print("Usage: generate-plan-diff.py <json_plan_file> <site_name>")
        sys.exit(1)

    json_file = sys.argv[1]
    site = sys.argv[2]

    # Read JSON plan
    with open(json_file, "r") as f:
        plan = json.load(f)

    # Extract metadata
    tf_version = plan.get("terraform_version", "unknown")
    format_version = plan.get("format_version", "unknown")

    # Count and categorize changes
    changes_by_action = defaultdict(list)
    total_changes = 0

    for resource in plan.get("resource_changes", []):
        address = resource.get("address", "unknown")
        actions = resource.get("change", {}).get("actions", [])

        # Categorize by primary action
        primary_action = actions[0] if actions else "no-op"

        # Map action to display format
        action_map = {
            "create": ("create", "+"),
            "update": ("update", "~"),
            "delete": ("delete", "-"),
            "no-op": ("no-op", ""),
            "read": ("read", "⊙"),
        }

        action_key, symbol = action_map.get(primary_action, (primary_action, "?"))

        if primary_action != "no-op":
            total_changes += 1
            changes_by_action[action_key].append((address, symbol))

    # Generate markdown summary
    print("# Terraform Plan Diff Summary")
    print(f"\n**Site**: `{site}`")
    print(f"**Terraform Version**: `{tf_version}`")
    print(f"**Format Version**: `{format_version}`")
    print("")

    # Summary counts
    print("## Change Summary")
    print("")
    if total_changes == 0:
        print("✅ **No changes.** Infrastructure is up-to-date.")
    else:
        print(f"📝 **{total_changes} resource(s)** will be modified:")
        print("")
        for action in ["create", "update", "delete"]:
            count = len(changes_by_action[action])
            if count > 0:
                action_emoji = {"create": "➕", "update": "📝", "delete": "🗑️"}
                print(
                    f"- {action_emoji.get(action, '•')} "
                    f"**{action.capitalize()}**: {count}"
                )

    # Detailed changes
    if total_changes > 0:
        print("\n## Detailed Changes")
        print("")

        # Sort actions for consistent output
        for action in ["create", "update", "delete"]:
            resources = changes_by_action[action]
            if resources:
                # Sort resources alphabetically for deterministic output
                resources.sort(key=lambda x: x[0])

                print(f"### {action.capitalize()} ({len(resources)})")
                print("")
                for address, symbol in resources:
                    print(f"- `{symbol} {address}`")
                print("")

    # Machine-readable JSON summary
    summary_json = {
        "site": site,
        "terraform_version": tf_version,
        "total_changes": total_changes,
        "changes_by_action": {
            action: len(resources) for action, resources in changes_by_action.items()
        },
        "resource_list": {
            action: sorted([addr for addr, _ in resources])
            for action, resources in changes_by_action.items()
        },
    }

    print("\n## Machine-Readable Summary")
    print("")
    print("```json")
    print(json.dumps(summary_json, indent=2, sort_keys=True))
    print("```")


if __name__ == "__main__":
    main()
