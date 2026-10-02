# Example: React UI Discovery

## Scenario
A developer working in a React & TypeScript repository asks:
> "FIND KARMA ☯: How can I polish my frontend UI and component accessibility?"

## Execution Trace

```bash
python3 "$SKILL_DIR/scripts/karma.py" find \
  --project examples/react-app \
  --goal "frontend UI polish and accessibility" \
  --agent codex \
  --json
```

## Expected Response Format

```markdown
### ☯ Recommended Skills for React UI Polish

1. **ui-skills** (`ibelick/ui-skills`)
   - **Lane**: frontend-quality
   - **Why now**: Detected React 19 + TypeScript dependencies in `package.json` with matching goal for UI component quality.
   - **Source**: https://github.com/ibelick/ui-skills
   - **Installation Preview**: `npx --yes skills add ibelick/ui-skills -a codex -y`

Would you like me to install any of these skills? Please specify the ones you approve.
```
