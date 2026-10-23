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
   - **Reviewed**: `5beb35b040e3de97e54fa9e386d7e42d15c295c2`, `skills/engineering/tdd`
   - **Installation Preview**: `karma install matt-tdd --agent codex` (dry run)

The previous `eval-skills` record remains a candidate because its old docs inspection did not establish an exact reviewed commit and skill path. It must not appear as a trusted install recommendation.
```
