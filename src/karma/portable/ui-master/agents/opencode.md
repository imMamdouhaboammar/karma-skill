# OpenCode Agent Adapter

## Activation Contract

- **Target Path**: `.opencode/skills/ui-master`

## Execution Rules

1. Scan codebase for UI/UX anti-patterns using the `uim` binary:
   ```bash
   uim audit ./src --json
   ```
2. Retrieve relevant domain design skills:
   ```bash
   uim skills "<topic>" --limit 3 --json
   ```
3. Enforce component hierarchy, standard Tailwind shadow tokens, and single accent colors per view.
