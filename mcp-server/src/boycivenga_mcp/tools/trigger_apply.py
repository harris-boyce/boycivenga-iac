#!/usr/bin/env python3
"""Tool: trigger_apply - Trigger terraform-apply workflow."""

from typing import Any, Dict

from ..github_client import GitHubClient, GitHubClientError


def trigger_apply(
    plan_run_id: str, site: str, pr_number: str, github_client: GitHubClient
) -> Dict[str, Any]:
    """Trigger the terraform-apply workflow.

    This workflow:
    - Validates inputs (plan run ID, site, PR number)
    - Downloads plan artifacts from specified plan run
    - Re-verifies SLSA attestations for artifacts
    - Re-evaluates plan against OPA policies
    - Applies the approved Terraform plan
    - Records complete audit trail

    IMPORTANT: This is a destructive operation that modifies infrastructure.
    The workflow enforces strict validation and re-verification before apply.

    Args:
        plan_run_id: Terraform plan workflow run ID (must have passed policy)
        site: Site to apply (required, must match plan artifact)
        pr_number: PR number for traceability (required)
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
                "run_id": "20562700000",
                "url": "https://github.com/harris-boyce/boycivenga-iac/actions/runs/20562700000",
                "workflow": "terraform-apply.yaml",
                "inputs": {
                    "plan_run_id": "20562600000",
                    "site": "pennington",
                    "pr_number": "42"
                }
            }
        }

    Validation:
        - All parameters are REQUIRED
        - plan_run_id must be numeric
        - site must be alphanumeric (with hyphens/underscores)
        - pr_number must be numeric

    Security:
        - Plan run must have completed successfully
        - Attestations are re-verified before apply
        - Policy is re-evaluated before apply
        - Full audit trail is recorded
    """
    # Input validation - all parameters required
    if not plan_run_id:
        return {"success": False, "error": "plan_run_id is required"}

    if not plan_run_id.isdigit():
        return {"success": False, "error": "plan_run_id must be a numeric workflow run ID"}

    if not site:
        return {"success": False, "error": "site is required"}

    if not site.replace("-", "").replace("_", "").isalnum():
        return {
            "success": False,
            "error": "site must contain only alphanumeric characters, hyphens, and underscores",
        }

    if not pr_number:
        return {"success": False, "error": "pr_number is required"}

    if not pr_number.isdigit():
        return {"success": False, "error": "pr_number must be numeric"}

    try:
        # Build workflow inputs - all required
        inputs = {"plan_run_id": plan_run_id, "site": site, "pr_number": pr_number}

        # Trigger workflow
        run_id = github_client.trigger_workflow(
            workflow_file="terraform-apply.yaml", ref="main", inputs=inputs
        )

        # Construct URL
        url = f"https://github.com/{github_client.repo}/actions/runs/{run_id}"

        return {
            "success": True,
            "data": {
                "run_id": run_id,
                "url": url,
                "workflow": "terraform-apply.yaml",
                "inputs": inputs,
            },
        }
    except GitHubClientError as e:
        return {"success": False, "error": str(e)}
