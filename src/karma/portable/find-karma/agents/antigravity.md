# Google Antigravity Agent Adapter

## Activation Contract

- **Target Path**: `.agent/skills/find-karma` or global `~/.gemini/config/skills/find-karma`
- **Trigger**: When the user requests `FIND KARMA ☯`, `find karma`, or asks for optimal agent skills for the project.

## Execution Rules

1. Inspect workspace metadata via read-mostly deterministic scan.
2. Run karma runtime:
   ```bash
   python3 "${SKILL_DIR:-.agent/skills/find-karma}/scripts/karma.py" find --project "$PWD" --goal "<USER_GOAL>" --agent antigravity --json
   ```
3. Deliver curated, verified skills with rationale, expected benefits, and source repositories.
4. Keep the human in the loop: no automatic installation without explicit approval.
