#!/usr/bin/env python3
"""Tests for github_client.py"""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from boycivenga_mcp.github_client import GitHubClient, GitHubClientError


def test_client_initialization_with_repo():
    """Test client can be initialized with explicit repo."""
    client = GitHubClient(repo="owner/repo", token="fake_token")
    assert client.repo == "owner/repo"
    assert client.token == "fake_token"
    print("✅ test_client_initialization_with_repo passed")


def test_client_initialization_from_env():
    """Test client reads from environment variables."""
    with patch.dict(os.environ, {"GITHUB_REPO": "env/repo", "GITHUB_TOKEN": "env_token"}):
        client = GitHubClient()
        assert client.repo == "env/repo"
        assert client.token == "env_token"
    print("✅ test_client_initialization_from_env passed")


def test_client_initialization_without_repo_fails():
    """Test client fails if repo is not provided."""
    with patch.dict(os.environ, {}, clear=True):
        try:
            GitHubClient()
            assert False, "Should have raised GitHubClientError"
        except GitHubClientError as e:
            assert "Repository must be provided" in str(e)
    print("✅ test_client_initialization_without_repo_fails passed")


def test_gh_command_success():
    """Test successful gh command execution."""
    client = GitHubClient(repo="test/repo", token="test_token")

    mock_result = MagicMock()
    mock_result.stdout = "command output\n"

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = client._run_gh_command(["run", "list"])
        assert result == "command output"

        # Verify gh was called correctly
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "gh"
        assert call_args[0][0][1:] == ["run", "list"]

    print("✅ test_gh_command_success passed")


def test_gh_command_failure():
    """Test gh command handles errors."""
    client = GitHubClient(repo="test/repo", token="test_token")

    mock_error = subprocess.CalledProcessError(1, "gh", stderr="error message")

    with patch("subprocess.run", side_effect=mock_error):
        try:
            client._run_gh_command(["run", "list"])
            assert False, "Should have raised GitHubClientError"
        except GitHubClientError as e:
            assert "gh command failed" in str(e)

    print("✅ test_gh_command_failure passed")


def test_get_workflow_run_status_success():
    """Test successful workflow run status retrieval."""
    client = GitHubClient(repo="test/repo", token="test_token")

    mock_run_data = {
        "conclusion": "success",
        "status": "completed",
        "workflowName": "Test Workflow",
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-01T00:05:00Z",
        "url": "https://github.com/test/repo/actions/runs/123",
    }

    mock_result = MagicMock()
    mock_result.stdout = json.dumps(mock_run_data)

    with patch("subprocess.run", return_value=mock_result):
        result = client.get_workflow_run_status("123")
        assert result["conclusion"] == "success"
        assert result["workflowName"] == "Test Workflow"

    print("✅ test_get_workflow_run_status_success passed")


def test_get_workflow_run_status_invalid_json():
    """Test handling of invalid JSON response."""
    client = GitHubClient(repo="test/repo", token="test_token")

    mock_result = MagicMock()
    mock_result.stdout = "not valid json"

    with patch("subprocess.run", return_value=mock_result):
        try:
            client.get_workflow_run_status("123")
            assert False, "Should have raised GitHubClientError"
        except GitHubClientError as e:
            assert "Failed to parse" in str(e)

    print("✅ test_get_workflow_run_status_invalid_json passed")


def test_trigger_workflow_basic():
    """Test basic workflow trigger."""
    client = GitHubClient(repo="test/repo", token="test_token")

    # Mock both the trigger call and the list call
    mock_trigger = MagicMock()
    mock_trigger.stdout = ""

    mock_list = MagicMock()
    mock_list.stdout = json.dumps([{"databaseId": 456}])

    with patch("subprocess.run", side_effect=[mock_trigger, mock_list]):
        run_id = client.trigger_workflow("test-workflow.yaml")
        assert run_id == "456"

    print("✅ test_trigger_workflow_basic passed")


def test_trigger_workflow_with_inputs():
    """Test workflow trigger with inputs."""
    client = GitHubClient(repo="test/repo", token="test_token")

    mock_trigger = MagicMock()
    mock_trigger.stdout = ""

    mock_list = MagicMock()
    mock_list.stdout = json.dumps([{"databaseId": 789}])

    with patch("subprocess.run", side_effect=[mock_trigger, mock_list]) as mock_run:
        run_id = client.trigger_workflow(
            "test-workflow.yaml", inputs={"site": "pennington", "pr_number": "42"}
        )
        assert run_id == "789"

        # Verify inputs were passed correctly
        trigger_call = mock_run.call_args_list[0]
        cmd = trigger_call[0][0]
        assert "--field" in cmd
        assert "site=pennington" in cmd

    print("✅ test_trigger_workflow_with_inputs passed")


def run_all_tests():
    """Run all test functions."""
    print("=" * 70)
    print("Running github_client.py tests")
    print("=" * 70)
    print()

    test_functions = [
        test_client_initialization_with_repo,
        test_client_initialization_from_env,
        test_client_initialization_without_repo_fails,
        test_gh_command_success,
        test_gh_command_failure,
        test_get_workflow_run_status_success,
        test_get_workflow_run_status_invalid_json,
        test_trigger_workflow_basic,
        test_trigger_workflow_with_inputs,
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} error: {e}")
            failed += 1

    print()
    print("=" * 70)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
