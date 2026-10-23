# Example: TDD & Testing Discovery

## Scenario
A team lead asks:
> "FIND KARMA: what testing and TDD skills fit our repository?"

## Execution Trace

```bash
python3 "$SKILL_DIR/scripts/karma.py" find \
  --project . \
  --goal "TDD and unit test coverage" \
  --agent codex \
  --json
```

## Expected Response Format

```markdown
### ☯ Recommended Testing Skills

1. **matt-tdd** (`mattpocock/skills`)
   - **Lane**: testing
   - **Why now**: Explicit user request for Test-Driven Development (TDD) discipline and red-green-refactor workflows.
   - **Source**: https://github.com/mattpocock/skills
   - **Installation Preview**: `npx --yes skills add mattpocock/skills --skill tdd -a codex -y`

2. **evals-skills** (`ai-evals-course/evals-skills`)
   - **Lane**: evals
   - **Why now**: Evaluation suites and behavioral verification.
   - **Source**: https://github.com/ai-evals-course/evals-skills
   - **Installation Preview**: `npx --yes skills add ai-evals-course/evals-skills -a codex -y`
```
