# VS Code (Roo Code / Cline / Copilot) Adapter

## Activation Contract

- **Target Path**: `.vscode/skills/ui-master`
- **MCP Configuration**: Configure `.vscode/mcp.json` with `ui-master-rig` stdio server.

## Configuration (.vscode/mcp.json)

```json
{
  "mcpServers": {
    "ui-master-rig": {
      "command": "uim",
      "args": ["mcp"]
    },
    "ui-skills": {
      "url": "https://www.ui-skills.com/mcp"
    }
  }
}
```

## Execution Rules

1. Use `ui_contrast` tool via MCP before suggesting color adjustments.
2. Use `ui_anti_slop_lint` tool via MCP to verify component files.
3. Use `ui_crx_audit` when editing Chrome Extensions.
