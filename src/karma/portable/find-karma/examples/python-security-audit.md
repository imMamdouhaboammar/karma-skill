# Example: Python Security Audit

## Scenario
A backend engineer working on a Python FastAPI project asks:
> "FIND KARMA: recommend security and audit skills"

## Execution Trace

```bash
python3 "$SKILL_DIR/scripts/karma.py" find \
  --project examples/python-api \
  --goal "security audit and secret scanning" \
  --agent claude-code \
  --json
```

## Expected Response Format

```markdown
### ☯ Security Discovery Guardrail

Only show entries actually returned as `reviewed` by the live catalog. The earlier `trailofbits-security` and `dokion` manual-install records have no revision-verified installation route and are now **candidates**, not installable recommendations. Never synthesize a mutable installation command to fill a security shortlist. If no purpose-matched reviewed security entry exists, say so and recommend a new revision-specific review.
```
