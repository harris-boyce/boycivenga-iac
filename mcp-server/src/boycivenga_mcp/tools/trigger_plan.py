#!/usr/bin/env python3
"""Tool: trigger_plan - Trigger terraform-plan workflow."""

from typing import Any, Dict, Optional

from ..github_client import GitHubClient, GitHubClientError


def trigger_plan(
    render_run_id: str,
    site: Optional[str] = None,
    pr_number: Optional[str] = None,
    github_client: GitHubClient = None,
) -> Dict[str, Any]:
    """Trigger the terraform-plan workflow.

    This workflow:
    - Downloads attested artifacts from specified render run
    - Verifies SLSA provenance attestations
    - Runs Terraform plan for site(s)
    - Evaluates plans against OPA policies
    - Uploads plan artifacts for apply workflow

    Args:
        render_run_id: Render artifacts workflow run ID to use
        site: Site to plan (optional; if empty, plans all sites)
        pr_number: PR number for traceability (optional)
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
                "run_id": "20562600000",
                "url": (
                    "https://github.com/harris-boyce/boycivenga-iac"
                    "/actions/runs/20562600000"
                ),
                "workflow": "terraform-plan.yaml",
                "inputs": {
                    "render_run_id": "20562567130",
                    "site": "pennington",
                    "pr_number": "42"
                }
            }
        }

    Validation:
        - render_run_id must be numeric
        - site must be alphanumeric (if provided)
        - pr_number must be numeric (if provided)
    """
    # Input validation
    if not render_run_id or not render_run_id.isdigit():
        return {
            "success": False,
            "error": "render_run_id must be a numeric workflow run ID",
        }

    if site and not site.replace("-", "").replace("_", "").isalnum():
        return {
            "success": False,
            "error": (
                "site must contain only alphanumeric characters, "
                "hyphens, and underscores"
            ),
        }

    if pr_number and not pr_number.isdigit():
        return {"success": False, "error": "pr_number must be numeric"}

    try:
        # Build workflow inputs
        inputs = {"render_run_id": render_run_id}

        if pr_number:
            inputs["pr_number"] = pr_number

        if site:
            inputs["site"] = site

        # Trigger workflow
        run_id = github_client.trigger_workflow(
            workflow_file="terraform-plan.yaml", ref="main", inputs=inputs
        )

        # Construct URL
        url = f"https://github.com/{github_client.repo}/actions/runs/{run_id}"

        return {
            "success": True,
            "data": {
                "run_id": run_id,
                "url": url,
                "workflow": "terraform-plan.yaml",
                "inputs": inputs,
            },
        }
    except GitHubClientError as e:
        return {"success": False, "error": str(e)}
