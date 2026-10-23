# Google Antigravity Agent Adapter

## Activation Contract

- **Target Path**: `.agent/skills/ui-master` or `~/.gemini/antigravity/agents/ui-master.md`
- **Identity**: `@ui-master`
- **Subagents**: `@ui-master-critic`, `@ui-master-motion`, `@ui-master-a11y`, `@ui-master-crx`, `@ui-master-researcher`

## Execution Rules

1. When receiving UI/UX/CRX tasks, invoke the deterministic engine via CLI or MCP:
   ```bash
   uim audit ./src --json
   uim contrast "#0f172a" "#38bdf8" --json
   ```
2. Check `uim rig list` or use `ui-master-rig` stdio MCP server for WCAG calculations.
3. Record multi-agent traces in `/Users/mamdouhaboammar/.gemini/antigravity/traces/` using `ui_multi_agent_trace`.
4. Halt immediately if the circuit breaker trips (`failure_streak >= 2`).
