#!/usr/bin/env python3
"""Tests for trigger_apply.py tool"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from boycivenga_mcp.github_client import GitHubClientError
from boycivenga_mcp.tools.trigger_apply import trigger_apply


def test_trigger_apply_success():
    """Test successful apply trigger with all required inputs."""
    mock_client = MagicMock()
    mock_client.trigger_workflow.return_value = "20562700000"
    mock_client.repo = "harris-boyce/boycivenga-iac"

    result = trigger_apply(
        plan_run_id="20562600000", site="pennington", pr_number="42", github_client=mock_client
    )

    assert result["success"] is True
    assert result["data"]["run_id"] == "20562700000"
    assert result["data"]["inputs"]["plan_run_id"] == "20562600000"
    assert result["data"]["inputs"]["site"] == "pennington"
    assert result["data"]["inputs"]["pr_number"] == "42"

    # Verify all inputs were passed
    call_args = mock_client.trigger_workflow.call_args
    inputs = call_args[1]["inputs"]
    assert inputs["plan_run_id"] == "20562600000"
    assert inputs["site"] == "pennington"
    assert inputs["pr_number"] == "42"

    print("✅ test_trigger_apply_success passed")


def test_trigger_apply_missing_plan_run_id():
    """Test validation when plan_run_id is missing."""
    mock_client = MagicMock()

    result = trigger_apply(
        plan_run_id="", site="pennington", pr_number="42", github_client=mock_client
    )

    assert result["success"] is False
    assert "plan_run_id is required" in result["error"]

    print("✅ test_trigger_apply_missing_plan_run_id passed")


def test_trigger_apply_invalid_plan_run_id():
    """Test validation of plan_run_id format."""
    mock_client = MagicMock()

    result = trigger_apply(
        plan_run_id="not-a-number", site="pennington", pr_number="42", github_client=mock_client
    )

    assert result["success"] is False
    assert "numeric" in result["error"]

    print("✅ test_trigger_apply_invalid_plan_run_id passed")


def test_trigger_apply_missing_site():
    """Test validation when site is missing."""
    mock_client = MagicMock()

    result = trigger_apply(plan_run_id="12345", site="", pr_number="42", github_client=mock_client)

    assert result["success"] is False
    assert "site is required" in result["error"]

    print("✅ test_trigger_apply_missing_site passed")


def test_trigger_apply_invalid_site():
    """Test validation of site format."""
    mock_client = MagicMock()

    result = trigger_apply(
        plan_run_id="12345",
        site="site;DROP TABLE users--",
        pr_number="42",
        github_client=mock_client,
    )

    assert result["success"] is False
    assert "alphanumeric" in result["error"]

    print("✅ test_trigger_apply_invalid_site passed")


def test_trigger_apply_missing_pr_number():
    """Test validation when pr_number is missing."""
    mock_client = MagicMock()

    result = trigger_apply(
        plan_run_id="12345", site="pennington", pr_number="", github_client=mock_client
    )

    assert result["success"] is False
    assert "pr_number is required" in result["error"]

    print("✅ test_trigger_apply_missing_pr_number passed")


def test_trigger_apply_invalid_pr_number():
    """Test validation of pr_number format."""
    mock_client = MagicMock()

    result = trigger_apply(
        plan_run_id="12345", site="pennington", pr_number="not-a-number", github_client=mock_client
    )

    assert result["success"] is False
    assert "numeric" in result["error"]

    print("✅ test_trigger_apply_invalid_pr_number passed")


def test_trigger_apply_valid_site_with_hyphens():
    """Test that sites with hyphens are accepted."""
    mock_client = MagicMock()
    mock_client.trigger_workflow.return_value = "20562700001"
    mock_client.repo = "harris-boyce/boycivenga-iac"

    result = trigger_apply(
        plan_run_id="12345", site="count-fleet-court", pr_number="42", github_client=mock_client
    )

    assert result["success"] is True
    assert result["data"]["inputs"]["site"] == "count-fleet-court"

    print("✅ test_trigger_apply_valid_site_with_hyphens passed")


def test_trigger_apply_error():
    """Test error handling in apply workflow trigger."""
    mock_client = MagicMock()
    mock_client.trigger_workflow.side_effect = GitHubClientError("Workflow trigger failed")

    result = trigger_apply(
        plan_run_id="12345", site="pennington", pr_number="42", github_client=mock_client
    )

    assert result["success"] is False
    assert "Workflow trigger failed" in result["error"]

    print("✅ test_trigger_apply_error passed")


def run_all_tests():
    """Run all test functions."""
    print("=" * 70)
    print("Running trigger_apply.py tests")
    print("=" * 70)
    print()

    test_functions = [
        test_trigger_apply_success,
        test_trigger_apply_missing_plan_run_id,
        test_trigger_apply_invalid_plan_run_id,
        test_trigger_apply_missing_site,
        test_trigger_apply_invalid_site,
        test_trigger_apply_missing_pr_number,
        test_trigger_apply_invalid_pr_number,
        test_trigger_apply_valid_site_with_hyphens,
        test_trigger_apply_error,
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
