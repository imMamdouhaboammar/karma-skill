# OpenCode Agent Adapter

## Activation Contract

- **Target Path**: `.opencode/skills/find-karma` or global `~/.opencode/skills/find-karma`
- **Trigger**: When the user requests `FIND KARMA ☯`, `find karma`, or asks for project skill discovery in OpenCode.

## Execution Rules

1. Execute the discovery engine:
   ```bash
   python3 "${SKILL_DIR:-.opencode/skills/find-karma}/scripts/karma.py" find --project "$PWD" --goal "<USER_GOAL>" --agent opencode --json
   ```
2. Present 2-5 recommendations with:
   - Reason for match
   - Source repository
   - Installation preview command (`npx --yes skills add <repo> -a opencode -y`)
3. Await explicit confirmation before installing.
