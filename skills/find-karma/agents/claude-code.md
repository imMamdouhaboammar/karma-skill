# Claude Code Agent Adapter

## Activation Contract

- **Target Path**: `.claude/skills/find-karma` or global `~/.claude/skills/find-karma`
- **Trigger**: When the user asks for `FIND KARMA ☯`, `find karma`, or requests skill recommendations for the project.

## Execution Rules

1. Resolve the active project root `$PWD`.
2. Execute the bundled portable tool in read-only mode:
   ```bash
   python3 "${SKILL_DIR:-.claude/skills/find-karma}/scripts/karma.py" find --project "$PWD" --goal "<USER_GOAL>" --agent claude-code --json
   ```
3. Format the top 2-5 recommendations with:
   - Skill name & lane
   - **Why now** (concrete repository signals matching the goal)
   - Verified source repository
   - Installation instructions (Claude plugin or `npx skills add`)
4. **Safety Invariant**: Do NOT execute installation or marketplace commands automatically. Claude Code must prompt the user for approval.
