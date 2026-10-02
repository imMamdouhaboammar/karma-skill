# OpenAI Codex Agent Adapter

## Activation Contract

- **Target Path**: `.agents/skills/find-karma` or global `~/.codex/skills/find-karma`
- **Plugin Manifest**: `.codex-plugin/plugin.json`
- **Trigger**: When the user asks for `FIND KARMA ☯`, `find karma`, or requests skill recommendations for the project.

## Execution Rules

1. Resolve the active repository path.
2. Execute the bundled portable tool in read-only mode:
   ```bash
   python3 "${SKILL_DIR:-.agents/skills/find-karma}/scripts/karma.py" find --project "$PWD" --goal "<USER_GOAL>" --agent codex --json
   ```
3. Parse the structured JSON output and present 2-5 recommendations with:
   - Name and purpose
   - Exact matching evidence
   - Preview of install command: `npx --yes skills add <repo> -a codex -y`
4. **Safety Invariant**: Never invoke shell execution of third-party skills without explicit approval.
