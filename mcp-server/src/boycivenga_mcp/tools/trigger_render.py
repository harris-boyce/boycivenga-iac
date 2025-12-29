#!/usr/bin/env python3
"""Tool: trigger_render - Trigger render-artifacts workflow."""

from typing import Any, Dict

from ..github_client import GitHubClient, GitHubClientError


def trigger_render(github_client: GitHubClient) -> Dict[str, Any]:
    """Trigger the render-artifacts workflow.

    This workflow:
    - Exports data from NetBox API
    - Renders Terraform tfvars files
    - Renders UniFi configuration files
    - Uploads attested artifacts
    - Creates documentation PR

    The workflow runs on the main branch and requires no inputs.

    Args:
        github_client: Initialized GitHubClient instance

    Returns:
        Dictionary containing:
        - success (bool): Whether the operation succeeded
        - data (dict): Run information if successful (run_id, url)
        - error (str): Error message if failed

    Example successful response:
        {
            "success": True,
            "data": {
                "run_id": "20562567130",
                "url": "https://github.com/harris-boyce/boycivenga-iac/actions/runs/20562567130",
                "workflow": "render-artifacts.yaml"
            }
        }
    """
    try:
        run_id = github_client.trigger_workflow(workflow_file="render-artifacts.yaml", ref="main")

        # Construct URL for convenience
        repo = github_client.repo
        url = f"https://github.com/{repo}/actions/runs/{run_id}"

        return {
            "success": True,
            "data": {"run_id": run_id, "url": url, "workflow": "render-artifacts.yaml"},
        }
    except GitHubClientError as e:
        return {"success": False, "error": str(e)}
