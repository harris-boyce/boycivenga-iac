# MCP Server for boycivenga-iac Workflow Orchestration

## Overview

Model Context Protocol server enabling Claude Desktop to orchestrate GitHub Actions workflows for infrastructure-as-code operations.

## Installation

### 1. Install Python Dependencies

```bash
cd mcp-server
pip install -e .
```

### 2. Configure GitHub Authentication

Create a GitHub Personal Access Token with permissions:
- `repo` (full repository access)
- `workflow` (trigger workflows)

Export as environment variable:
```bash
export GITHUB_TOKEN="ghp_..."
```

### 3. Configure Claude Desktop

Edit Claude Desktop configuration:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the MCP server:
```json
{
  "mcpServers": {
    "boycivenga-iac": {
      "command": "python",
      "args": [
        "/workspaces/boycivenga-iac/mcp-server/src/boycivenga_mcp/server.py"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_...",
        "GITHUB_REPO": "harris-boyce/boycivenga-iac"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

Restart Claude Desktop to load the MCP server.

## Available Tools

### 1. `get_workflow_status`

**Description**: Get the status of a GitHub Actions workflow run.

**Parameters**:
- `run_id` (string, required): Workflow run ID

**Returns**: JSON with conclusion, status, workflow name, timestamps

**Example**:
```
Claude, can you check the status of workflow run 20562567130?
```

### 2. `trigger_render`

**Description**: Trigger the render-artifacts workflow.

**Parameters**: None

**Returns**: Run ID and URL of triggered workflow

**Example**:
```
Claude, please trigger the render artifacts pipeline
```

### 3. `trigger_plan`

**Description**: Trigger terraform-plan workflow for a site.

**Parameters**:
- `render_run_id` (string, required): Render artifacts run ID to use
- `site` (string, optional): Site to plan (empty = all sites)
- `pr_number` (string, optional): PR number for traceability

**Returns**: Run ID and URL of triggered workflow

**Example**:
```
Claude, please run terraform plan for site pennington using render run 12345
```

### 4. `trigger_apply`

**Description**: Trigger terraform-apply workflow.

**Parameters**:
- `plan_run_id` (string, required): Plan workflow run ID
- `site` (string, required): Site to apply
- `pr_number` (string, required): PR number for traceability

**Returns**: Run ID and URL of triggered workflow

**Example**:
```
Claude, please apply the plan from run 67890 for site pennington with PR 42
```

## Testing

Run tests:
```bash
python tests/test_github_client.py
python tests/test_tools/test_get_status.py
```

## Architecture

```
mcp-server/
├── src/boycivenga_mcp/
│   ├── server.py           # FastMCP server with tool registration
│   ├── github_client.py    # GitHub API wrapper using gh CLI
│   └── tools/              # Individual tool implementations
└── tests/                  # Test suite
```

## Security Considerations

1. **Token Security**: GitHub token grants full workflow access. Store securely.
2. **Read-Only First**: Test with get_workflow_status before using trigger operations.
3. **Fail-Closed**: All operations fail safely if auth/validation fails.
4. **No State**: Server is stateless; all context comes from GitHub.
