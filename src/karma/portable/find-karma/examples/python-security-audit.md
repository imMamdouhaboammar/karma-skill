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
### ☯ Recommended Security Skills

1. **trailofbits-security** (`trailofbits/skills`)
   - **Lane**: security
   - **Why now**: Detected Python codebase requiring security review and vulnerability auditing.
   - **Source**: https://github.com/trailofbits/skills
   - **Installation Preview**: `/plugin marketplace add trailofbits/skills; /plugin menu; select only required plugin.`

2. **dokion** (`imMamdouhaboammar/dokion`)
   - **Lane**: supply-chain
   - **Why now**: Codebase verification and supply-chain integrity checks.
   - **Source**: https://github.com/imMamdouhaboammar/dokion
   - **Installation Preview**: `npx --yes skills add imMamdouhaboammar/dokion -a claude-code -y`

Would you like to proceed with installing any of these?
```
