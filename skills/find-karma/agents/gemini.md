# Gemini CLI Agent Adapter

## Activation Contract

- **Target Path**: `.gemini/skills/find-karma` or global `~/.gemini/config/skills/find-karma`
- **Trigger**: When the user requests `FIND KARMA ☯`, `find karma`, or asks for project skill discovery in Gemini CLI.

## Execution Rules

1. Execute the discovery engine:
   ```bash
   python3 "${SKILL_DIR:-.gemini/skills/find-karma}/scripts/karma.py" find --project "$PWD" --goal "<USER_GOAL>" --agent gemini --json
   ```
2. Present 2-5 recommendations with:
   - Reason for match
   - Source repository
   - Installation preview command (`npx --yes skills add <repo> -a gemini -y`)
3. Await explicit confirmation before installing.
