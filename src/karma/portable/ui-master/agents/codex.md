# OpenAI Codex Agent Adapter

## Activation Contract

- **Target Path**: `.agents/skills/ui-master`
- **Specification**: Codex Skill & Subagent Protocol

## Execution Rules

1. Inspect UI files with zero obviousness commentary. Enforce the Direct Payload Invariant.
2. Run automated validation before proposing frontend diffs:
   ```bash
   uim audit ./src --json
   ```
3. Calculate precise contrast ratios before changing CSS color tokens:
   ```bash
   uim contrast "<fg>" "<bg>" --json
   ```
4. Adhere strictly to WCAG 2.2 AAA/AA requirements and avoid modifying `letter-spacing` or introducing arbitrary `z-*` values.
