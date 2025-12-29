# Testing Guide

## Running Tests

All tests follow the simple function-based pattern used in the netbox-client module.

### Run All Tests

```bash
# GitHub client tests
python /workspaces/boycivenga-iac/mcp-server/tests/test_github_client.py

# Tool tests
python /workspaces/boycivenga-iac/mcp-server/tests/test_tools/test_get_status.py
python /workspaces/boycivenga-iac/mcp-server/tests/test_tools/test_trigger_render.py
python /workspaces/boycivenga-iac/mcp-server/tests/test_tools/test_trigger_plan.py
python /workspaces/boycivenga-iac/mcp-server/tests/test_tools/test_trigger_apply.py
```

### Run All Tests (Quick Script)

```bash
cd /workspaces/boycivenga-iac/mcp-server
for test in tests/test_*.py tests/test_tools/test_*.py; do
  python "$test" || exit 1
done
echo "✅ All tests passed!"
```

## Manual Testing with Real API

### Setup

```bash
export GITHUB_TOKEN="ghp_..."
export GITHUB_REPO="harris-boyce/boycivenga-iac"
```

### Test get_workflow_status

```bash
python -c "
from src.boycivenga_mcp.github_client import GitHubClient
c = GitHubClient()
print(c.get_workflow_run_status('20562567130'))
"
```

### Test trigger_render

```bash
python -c "
from src.boycivenga_mcp.github_client import GitHubClient
from src.boycivenga_mcp.tools.trigger_render import trigger_render
c = GitHubClient()
print(trigger_render(c))
"
```

### Test trigger_plan

```bash
python -c "
from src.boycivenga_mcp.github_client import GitHubClient
from src.boycivenga_mcp.tools.trigger_plan import trigger_plan
c = GitHubClient()
print(trigger_plan('20562567130', site='pennington', github_client=c))
"
```

### Test trigger_apply (CAREFUL - modifies infrastructure)

```bash
# Only run if you have a valid plan run!
python -c "
from src.boycivenga_mcp.github_client import GitHubClient
from src.boycivenga_mcp.tools.trigger_apply import trigger_apply
c = GitHubClient()
print(trigger_apply('PLAN_RUN_ID', 'pennington', 'PR_NUM', c))
"
```

## Testing with Claude Desktop

### 1. Configure Claude Desktop

Edit config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "boycivenga-iac": {
      "command": "python",
      "args": ["/workspaces/boycivenga-iac/mcp-server/src/boycivenga_mcp/server.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_...",
        "GITHUB_REPO": "harris-boyce/boycivenga-iac"
      }
    }
  }
}
```

### 2. Restart Claude Desktop

### 3. Test Each Tool

#### Test get_workflow_status

```
Claude, can you check the status of workflow run 20562567130?
```

Expected: Returns workflow status with conclusion, timestamps, URL

#### Test trigger_render

```
Claude, please trigger the render artifacts pipeline
```

Expected: Returns run ID and URL of triggered workflow

#### Test trigger_plan

```
Claude, please run terraform plan for site pennington using render run 20562567130
```

Expected: Returns run ID of plan workflow with correct inputs

#### Test trigger_apply

```
Claude, please apply the plan from run [PLAN_RUN_ID] for site pennington with PR 42
```

Expected: Returns run ID of apply workflow with validation

### 4. Test Error Handling

#### Invalid run ID

```
Claude, check status of workflow run 999999999
```

Expected: Error message about run not found

#### Invalid parameters

```
Claude, trigger plan with render run "not-a-number"
```

Expected: Error message about invalid input format

## Test Coverage

The test suite covers:
- ✅ GitHub client initialization (with/without env vars)
- ✅ gh CLI command execution (success/failure)
- ✅ Workflow status retrieval (success/error/invalid JSON)
- ✅ Workflow triggering (basic/with inputs)
- ✅ All tool success paths
- ✅ All tool error paths
- ✅ Input validation for all parameters
- ✅ Injection attack prevention
