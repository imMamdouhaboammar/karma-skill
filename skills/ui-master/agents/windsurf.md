# Windsurf (Cascade) Agent Adapter

## Activation Contract

- **Target Path**: `.windsurf/skills/ui-master` or `.windsurfrules`

## Cascade Execution Directives

1. When writing React/Vue/Svelte components, never use `h-screen`. Always use `h-dvh`.
2. Animate exclusively compositor properties (`transform`, `opacity`) using `motion/react` or CSS transitions under 200ms with `ease-out`.
3. Check contrast compliance with `uim contrast <fg> <bg>` before locking design tokens.
4. If writing Chrome Extension popups, always encapsulate in Closed Shadow DOM.
