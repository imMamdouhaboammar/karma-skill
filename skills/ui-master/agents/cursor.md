# Cursor Agent Adapter

## Activation Contract

- **Target Path**: `.cursor/skills/ui-master` or `.cursor/rules/ui-master.mdc`
- **Globs**: `**/*.{tsx,jsx,vue,svelte,css,html}`

## Execution Rules

1. Automatically invoke UI-Master constraints whenever touching UI components, CSS styling, or design tokens.
2. Invariant Checklist:
   - Use `h-dvh` instead of `h-screen`.
   - Never animate `width`, `height`, `margin`, or `padding`; use only `transform` and `opacity`.
   - Always ensure interactive elements pass WCAG 2.2 contrast (`uim contrast <fg> <bg>`).
   - Add `aria-label` to icon-only buttons.
   - Enforce `text-balance` on headers and `tabular-nums` on tabular data.
