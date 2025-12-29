#!/usr/bin/env python3
"""MCP Server for boycivenga-iac GitHub workflow orchestration.

This server provides tools for Claude Desktop to orchestrate GitHub Actions
workflows for infrastructure-as-code operations.
"""

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .github_client import GitHubClient
from .tools.get_status import get_workflow_status as get_status_impl
from .tools.trigger_apply import trigger_apply as trigger_apply_impl
from .tools.trigger_plan import trigger_plan as trigger_plan_impl
from .tools.trigger_render import trigger_render as trigger_render_impl

# Set default environment variables before initializing GitHubClient
if not os.getenv("GITHUB_REPO"):
    os.environ["GITHUB_REPO"] = "harris-boyce/boycivenga-iac"

# Initialize FastMCP server
mcp = FastMCP("boycivenga-iac")

# Initialize GitHub client (will be reused across tool calls)
github_client = GitHubClient()


@mcp.tool()
def get_workflow_status(run_id: str) -> dict[str, Any]:
    """Get the status of a GitHub Actions workflow run.

    Args:
        run_id: The GitHub workflow run ID to check

    Returns:
        Dictionary with workflow run status information
    """
    return get_status_impl(run_id, github_client)


@mcp.tool()
def trigger_render() -> dict[str, Any]:
    """Trigger the render-artifacts workflow.

    This workflow exports NetBox data, renders Terraform tfvars and UniFi configs,
    and creates attested artifacts for downstream consumption.

    Returns:
        Dictionary with triggered run information (run_id, url)
    """
    return trigger_render_impl(github_client)


@mcp.tool()
def trigger_plan(
    render_run_id: str, site: str = "", pr_number: str = ""
) -> dict[str, Any]:
    """Trigger the terraform-plan workflow.

    This workflow downloads attested artifacts from a render run, verifies
    attestations, runs Terraform plan, and evaluates OPA policies.

    Args:
        render_run_id: Render artifacts workflow run ID to use
        site: Site to plan (leave empty for all sites)
        pr_number: PR number for traceability (optional)

    Returns:
        Dictionary with triggered run information (run_id, url, inputs)
    """
    # Convert empty strings to None for optional parameters
    site_param = site if site else None
    pr_param = pr_number if pr_number else None

    return trigger_plan_impl(
        render_run_id=render_run_id,
        github_client=github_client,
        site=site_param,
        pr_number=pr_param,
    )


@mcp.tool()
def trigger_apply(plan_run_id: str, site: str, pr_number: str) -> dict[str, Any]:
    """Trigger the terraform-apply workflow.

    IMPORTANT: This is a destructive operation that modifies infrastructure.
    The workflow enforces strict validation and re-verification before apply.

    Args:
        plan_run_id: Terraform plan workflow run ID (must have passed policy)
        site: Site to apply (required)
        pr_number: PR number for traceability (required)

    Returns:
        Dictionary with triggered run information (run_id, url, inputs)
    """
    return trigger_apply_impl(
        plan_run_id=plan_run_id,
        site=site,
        pr_number=pr_number,
        github_client=github_client,
    )


def main():
    """Run the MCP server."""
    # Validate environment
    if not os.getenv("GITHUB_TOKEN"):
        print("Warning: GITHUB_TOKEN not set. Authentication may fail.")

    # Run server with stdio transport
    mcp.run()


if __name__ == "__main__":
    main()
