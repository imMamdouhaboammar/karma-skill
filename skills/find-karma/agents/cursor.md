# Cursor Agent Adapter

## Activation Contract

- **Target Path**: `.cursor/skills/find-karma` or global `~/.cursor/skills/find-karma`
- **Rule Reference**: `.cursor/rules/find-karma.mdc`
- **Trigger**: When the user asks for `FIND KARMA ☯`, `find karma`, or requests skill recommendations for the project.

## Execution Rules

1. Execute the discovery engine:
   ```bash
   python3 "${SKILL_DIR:-.cursor/skills/find-karma}/scripts/karma.py" find --project "$PWD" --goal "<USER_GOAL>" --agent cursor --json
   ```
2. Present only the strongest recommendations with why-now evidence and manual preview commands.
3. Require user consent before modifying `.cursor/rules` or running `npx skills add`.
