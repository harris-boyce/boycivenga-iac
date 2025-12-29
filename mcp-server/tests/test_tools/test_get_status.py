#!/usr/bin/env python3
"""Tests for get_status.py tool"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from boycivenga_mcp.github_client import GitHubClientError
from boycivenga_mcp.tools.get_status import get_workflow_status


def test_get_workflow_status_success():
    """Test successful workflow status retrieval."""
    mock_client = MagicMock()
    mock_client.get_workflow_run_status.return_value = {
        "conclusion": "success",
        "status": "completed",
        "workflowName": "Test Workflow",
    }

    result = get_workflow_status("123", mock_client)

    assert result["success"] is True
    assert "data" in result
    assert result["data"]["conclusion"] == "success"
    print("✅ test_get_workflow_status_success passed")


def test_get_workflow_status_error():
    """Test error handling in workflow status retrieval."""
    mock_client = MagicMock()
    mock_client.get_workflow_run_status.side_effect = GitHubClientError("Run not found")

    result = get_workflow_status("999", mock_client)

    assert result["success"] is False
    assert "error" in result
    assert "Run not found" in result["error"]
    print("✅ test_get_workflow_status_error passed")


def test_get_workflow_status_returns_full_data():
    """Test that all workflow data is returned."""
    mock_client = MagicMock()
    mock_run_data = {
        "conclusion": "failure",
        "status": "completed",
        "workflowName": "CI",
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-01T00:05:00Z",
        "url": "https://github.com/test/repo/actions/runs/456",
    }
    mock_client.get_workflow_run_status.return_value = mock_run_data

    result = get_workflow_status("456", mock_client)

    assert result["success"] is True
    assert result["data"] == mock_run_data
    assert result["data"]["url"] == "https://github.com/test/repo/actions/runs/456"
    print("✅ test_get_workflow_status_returns_full_data passed")


def run_all_tests():
    """Run all test functions."""
    print("=" * 70)
    print("Running get_status.py tests")
    print("=" * 70)
    print()

    test_functions = [
        test_get_workflow_status_success,
        test_get_workflow_status_error,
        test_get_workflow_status_returns_full_data,
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
