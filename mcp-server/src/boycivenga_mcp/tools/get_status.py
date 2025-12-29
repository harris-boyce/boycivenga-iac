#!/usr/bin/env python3
"""Tool: get_workflow_status - Get GitHub workflow run status."""

from typing import Any, Dict

from ..github_client import GitHubClient, GitHubClientError


def get_workflow_status(run_id: str, github_client: GitHubClient) -> Dict[str, Any]:
    """Get the status of a GitHub Actions workflow run.

    Args:
        run_id: GitHub workflow run ID
        github_client: Initialized GitHubClient instance

    Returns:
        Dictionary containing:
        - success (bool): Whether the operation succeeded
        - data (dict): Run information if successful
        - error (str): Error message if failed

    Example successful response:
        {
            "success": True,
            "data": {
                "conclusion": "success",
                "status": "completed",
                "workflowName": "Render Artifacts",
                "createdAt": "2025-12-29T01:31:55Z",
                "updatedAt": "2025-12-29T01:33:12Z",
                "url": (
                    "https://github.com/harris-boyce/boycivenga-iac"
                    "/actions/runs/20562567130"
                )
            }
        }

    Example error response:
        {
            "success": False,
            "error": "Run ID 999999 not found or you don't have access"
        }
    """
    # Validate run_id is numeric
    if not run_id or not run_id.isdigit():
        return {"success": False, "error": "run_id must be a numeric workflow run ID"}

    try:
        run_info = github_client.get_workflow_run_status(run_id)
        return {"success": True, "data": run_info}
    except GitHubClientError as e:
        return {"success": False, "error": str(e)}
