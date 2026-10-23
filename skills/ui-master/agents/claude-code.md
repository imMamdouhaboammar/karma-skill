# Claude Code Agent Adapter

## Activation Contract

- **Target Path**: `.claude/skills/ui-master` or global `~/.claude/skills/ui-master`
- **Plugin Identifier**: `ui-master`
- **Commands**: `/ui-master`, `/uim`

## Execution Rules

1. Resolve project root `$PWD`.
2. For design review, audit, and contrast questions, run the bundled CLI:
   ```bash
   # If uim binary is installed on PATH:
   uim audit ./src --json
   uim contrast "<foreground>" "<background>" --json

   # Or via bun/node bridge:
   bun x find-karma uim audit ./src --json
   ```
3. When searching design skills, query the 421 local skills via:
   ```bash
   uim skills "<query>" --json
   ```
4. For interactive or visual critique passes, present clear, non-slop technical remedies. Never apply unrequested animations or gradients.
