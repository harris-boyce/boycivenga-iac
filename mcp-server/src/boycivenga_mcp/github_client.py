#!/usr/bin/env python3
"""GitHub API client using gh CLI subprocess calls.

This module provides a wrapper around the GitHub CLI for workflow operations.
It uses subprocess calls to 'gh' rather than PyGithub to leverage the existing
gh installation and avoid additional dependencies.
"""

import json
import os
import subprocess
import time
from typing import Any, Dict, Optional


class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""

    pass


class GitHubClient:
    """GitHub API client using gh CLI.

    This client wraps the GitHub CLI to provide programmatic access to
    workflow operations. It assumes 'gh' is installed and authenticated.
    """

    def __init__(self, repo: Optional[str] = None, token: Optional[str] = None):
        """Initialize GitHub client.

        Args:
            repo: Repository in format "owner/name". If None, uses GITHUB_REPO env var.
            token: GitHub personal access token. If None, uses GITHUB_TOKEN env var.
                   Note: gh CLI may use its own auth if this is not set.

        Raises:
            GitHubClientError: If repo is not provided and GITHUB_REPO is not set.
        """
        self.repo = repo or os.getenv("GITHUB_REPO")
        if not self.repo:
            raise GitHubClientError(
                "Repository must be provided or set via "
                "GITHUB_REPO environment variable"
            )

        self.token = token or os.getenv("GITHUB_TOKEN")

        # Validate gh CLI is available
        try:
            subprocess.run(
                ["gh", "--version"], capture_output=True, check=True, text=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise GitHubClientError(f"GitHub CLI (gh) is not available: {e}")

    def _run_gh_command(self, args: list[str]) -> str:
        """Run a gh CLI command and return stdout.

        Args:
            args: Command arguments (gh will be prepended)

        Returns:
            Command stdout as string

        Raises:
            GitHubClientError: If command fails
        """
        env = os.environ.copy()
        if self.token:
            env["GITHUB_TOKEN"] = self.token

        try:
            result = subprocess.run(
                ["gh"] + args, capture_output=True, check=True, text=True, env=env
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            raise GitHubClientError(f"gh command failed: {error_msg}")

    def get_workflow_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get the status of a workflow run.

        Args:
            run_id: Workflow run ID

        Returns:
            Dictionary with run information including:
            - conclusion: Final result (success, failure, cancelled, etc.)
            - status: Current status (queued, in_progress, completed)
            - workflowName: Name of the workflow
            - createdAt: ISO timestamp when run was created
            - updatedAt: ISO timestamp when run was last updated
            - url: URL to view the run

        Raises:
            GitHubClientError: If run doesn't exist or command fails
        """
        output = self._run_gh_command(
            [
                "run",
                "view",
                run_id,
                "--repo",
                self.repo,
                "--json",
                "conclusion,status,workflowName,createdAt,updatedAt,url",
            ]
        )

        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            raise GitHubClientError(f"Failed to parse gh output: {e}")

    def trigger_workflow(
        self,
        workflow_file: str,
        ref: str = "main",
        inputs: Optional[Dict[str, str]] = None,
    ) -> str:
        """Trigger a workflow dispatch event.

        Args:
            workflow_file: Workflow filename (e.g., "render-artifacts.yaml")
            ref: Git ref to run workflow on (default: "main")
            inputs: Workflow inputs as key-value pairs

        Returns:
            The triggered workflow run ID

        Raises:
            GitHubClientError: If workflow trigger fails

        Note:
            This method triggers the workflow and polls for up to 10 seconds
            to identify the newly created run. Uses before/after comparison
            to handle race conditions when multiple workflows might be triggered
            concurrently. The actual workflow execution is asynchronous.
        """
        # Get the current latest run ID before triggering (to detect new run)
        try:
            before_output = self._run_gh_command(
                [
                    "run",
                    "list",
                    "--repo",
                    self.repo,
                    "--workflow",
                    workflow_file,
                    "--limit",
                    "1",
                    "--json",
                    "databaseId",
                ]
            )
            before_runs = json.loads(before_output)
            before_id = before_runs[0]["databaseId"] if before_runs else 0
        except (json.JSONDecodeError, KeyError, IndexError):
            # No existing runs, start from 0
            before_id = 0

        # Build trigger command
        cmd = ["workflow", "run", workflow_file, "--repo", self.repo, "--ref", ref]

        # Add inputs if provided
        if inputs:
            for key, value in inputs.items():
                cmd.extend(["--field", f"{key}={value}"])

        # Trigger workflow (this doesn't return run ID directly)
        self._run_gh_command(cmd)

        # Poll for new run (max 10 attempts, 1 second apart)
        for attempt in range(10):
            time.sleep(1)

            try:
                after_output = self._run_gh_command(
                    [
                        "run",
                        "list",
                        "--repo",
                        self.repo,
                        "--workflow",
                        workflow_file,
                        "--limit",
                        "5",
                        "--json",
                        "databaseId,createdAt",
                    ]
                )
                after_runs = json.loads(after_output)

                # Find the first run with ID greater than before_id
                for run in after_runs:
                    if run["databaseId"] > before_id:
                        return str(run["databaseId"])

            except (json.JSONDecodeError, KeyError) as e:
                # Continue polling on transient errors
                if attempt == 9:  # Last attempt
                    raise GitHubClientError(f"Failed to parse run list: {e}")
                continue

        # If we get here, we didn't find the new run within timeout
        raise GitHubClientError(
            f"Workflow triggered but run ID not found within 10 seconds. "
            f"Check workflow runs manually for {workflow_file}."
        )
