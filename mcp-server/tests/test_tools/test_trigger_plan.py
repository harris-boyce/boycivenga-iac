#!/usr/bin/env python3
"""Tests for trigger_plan.py tool"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from boycivenga_mcp.github_client import GitHubClientError
from boycivenga_mcp.tools.trigger_plan import trigger_plan


def test_trigger_plan_success_minimal():
    """Test successful plan trigger with minimal inputs."""
    mock_client = MagicMock()
    mock_client.trigger_workflow.return_value = "20562600000"
    mock_client.repo = "harris-boyce/boycivenga-iac"

    result = trigger_plan("20562567130", github_client=mock_client)

    assert result["success"] is True
    assert result["data"]["run_id"] == "20562600000"
    assert result["data"]["inputs"]["render_run_id"] == "20562567130"

    # Verify only render_run_id was passed
    call_args = mock_client.trigger_workflow.call_args
    assert call_args[1]["inputs"] == {"render_run_id": "20562567130"}

    print("✅ test_trigger_plan_success_minimal passed")


def test_trigger_plan_success_with_site():
    """Test plan trigger with site parameter."""
    mock_client = MagicMock()
    mock_client.trigger_workflow.return_value = "20562600001"
    mock_client.repo = "harris-boyce/boycivenga-iac"

    result = trigger_plan("20562567130", site="pennington", github_client=mock_client)

    assert result["success"] is True
    assert result["data"]["inputs"]["site"] == "pennington"

    call_args = mock_client.trigger_workflow.call_args
    assert call_args[1]["inputs"]["site"] == "pennington"

    print("✅ test_trigger_plan_success_with_site passed")


def test_trigger_plan_success_all_inputs():
    """Test plan trigger with all optional inputs."""
    mock_client = MagicMock()
    mock_client.trigger_workflow.return_value = "20562600002"
    mock_client.repo = "harris-boyce/boycivenga-iac"

    result = trigger_plan(
        "20562567130", site="count-fleet-court", pr_number="42", github_client=mock_client
    )

    assert result["success"] is True
    assert result["data"]["inputs"]["render_run_id"] == "20562567130"
    assert result["data"]["inputs"]["site"] == "count-fleet-court"
    assert result["data"]["inputs"]["pr_number"] == "42"

    print("✅ test_trigger_plan_success_all_inputs passed")


def test_trigger_plan_invalid_render_run_id():
    """Test validation of render_run_id."""
    mock_client = MagicMock()

    # Non-numeric run ID
    result = trigger_plan("not-a-number", github_client=mock_client)
    assert result["success"] is False
    assert "numeric" in result["error"]

    # Empty run ID
    result = trigger_plan("", github_client=mock_client)
    assert result["success"] is False
    assert "numeric" in result["error"]

    print("✅ test_trigger_plan_invalid_render_run_id passed")


def test_trigger_plan_invalid_site():
    """Test validation of site parameter."""
    mock_client = MagicMock()

    # Site with invalid characters
    result = trigger_plan("12345", site="site;DROP TABLE", github_client=mock_client)
    assert result["success"] is False
    assert "alphanumeric" in result["error"]

    print("✅ test_trigger_plan_invalid_site passed")


def test_trigger_plan_invalid_pr_number():
    """Test validation of pr_number parameter."""
    mock_client = MagicMock()

    # Non-numeric PR number
    result = trigger_plan("12345", pr_number="not-a-number", github_client=mock_client)
    assert result["success"] is False
    assert "numeric" in result["error"]

    print("✅ test_trigger_plan_invalid_pr_number passed")


def test_trigger_plan_error():
    """Test error handling in plan workflow trigger."""
    mock_client = MagicMock()
    mock_client.trigger_workflow.side_effect = GitHubClientError("Workflow trigger failed")

    result = trigger_plan("12345", github_client=mock_client)

    assert result["success"] is False
    assert "Workflow trigger failed" in result["error"]

    print("✅ test_trigger_plan_error passed")


def run_all_tests():
    """Run all test functions."""
    print("=" * 70)
    print("Running trigger_plan.py tests")
    print("=" * 70)
    print()

    test_functions = [
        test_trigger_plan_success_minimal,
        test_trigger_plan_success_with_site,
        test_trigger_plan_success_all_inputs,
        test_trigger_plan_invalid_render_run_id,
        test_trigger_plan_invalid_site,
        test_trigger_plan_invalid_pr_number,
        test_trigger_plan_error,
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
