#!/usr/bin/env python3
"""Tests for trigger_render.py tool"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from boycivenga_mcp.github_client import GitHubClientError  # noqa: E402
from boycivenga_mcp.tools.trigger_render import trigger_render  # noqa: E402


def test_trigger_render_success():
    """Test successful render workflow trigger."""
    mock_client = MagicMock()
    mock_client.trigger_workflow.return_value = "20562567130"
    mock_client.repo = "harris-boyce/boycivenga-iac"

    result = trigger_render(mock_client)

    assert result["success"] is True
    assert result["data"]["run_id"] == "20562567130"
    assert "actions/runs/20562567130" in result["data"]["url"]
    assert result["data"]["workflow"] == "render-artifacts.yaml"

    # Verify client was called correctly
    mock_client.trigger_workflow.assert_called_once_with(
        workflow_file="render-artifacts.yaml", ref="main"
    )
    print("✅ test_trigger_render_success passed")


def test_trigger_render_error():
    """Test error handling in render workflow trigger."""
    mock_client = MagicMock()
    mock_client.trigger_workflow.side_effect = GitHubClientError(
        "Workflow trigger failed"
    )

    result = trigger_render(mock_client)

    assert result["success"] is False
    assert "error" in result
    assert "Workflow trigger failed" in result["error"]
    print("✅ test_trigger_render_error passed")


def test_trigger_render_url_construction():
    """Test that URL is correctly constructed from repo and run_id."""
    mock_client = MagicMock()
    mock_client.trigger_workflow.return_value = "12345"
    mock_client.repo = "owner/repo"

    result = trigger_render(mock_client)

    expected_url = "https://github.com/owner/repo/actions/runs/12345"
    assert result["data"]["url"] == expected_url
    print("✅ test_trigger_render_url_construction passed")


def run_all_tests():
    """Run all test functions."""
    print("=" * 70)
    print("Running trigger_render.py tests")
    print("=" * 70)
    print()

    test_functions = [
        test_trigger_render_success,
        test_trigger_render_error,
        test_trigger_render_url_construction,
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
