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
   - **Reviewed**: `55363c305097d4c84487bd5f323d29b3f067bf72`, `skills/ui-skills-root`
   - **Installation Preview**: `karma install ui-skills --agent codex` (dry run)

Would you like me to install any of these skills? Please specify the ones you approve.
```
