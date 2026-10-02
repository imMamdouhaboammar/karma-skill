# Windsurf Agent Adapter

## Activation Contract

- **Target Path**: `.windsurf/skills/find-karma` or global `~/.windsurf/skills/find-karma`
- **Trigger**: When the user requests `FIND KARMA ☯`, `find karma`, or asks for project skill discovery in Windsurf.

## Execution Rules

1. Execute the discovery engine:
   ```bash
   python3 "${SKILL_DIR:-.windsurf/skills/find-karma}/scripts/karma.py" find --project "$PWD" --goal "<USER_GOAL>" --agent windsurf --json
   ```
2. Present 2-5 recommendations with:
   - Reason for match
   - Source repository
   - Installation preview command (`npx --yes skills add <repo> -a windsurf -y`)
3. Await explicit confirmation before installing.
