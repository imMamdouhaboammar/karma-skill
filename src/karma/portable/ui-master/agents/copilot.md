# GitHub Copilot Agent Adapter

## Activation Contract

- **Target Path**: `.github/skills/ui-master` or `.github/copilot-instructions.md`

## Instructions for GitHub Copilot Workspace & CLI

1. You are paired with UI-Master, the high-discipline design engineering specialist.
2. In all UI suggestions:
   - Use accessible component primitives (`Base UI`, `React Aria`, `Radix UI`).
   - Do NOT construct custom keyboard/focus navigation logic from scratch.
   - For modal dialogs, enforce `role="dialog"`, `aria-modal="true"`, focus trap, and background scroll lock.
   - For mobile layouts, gate smooth scroll engines behind `!window.matchMedia('(pointer: coarse)').matches`.
   - Never inject AI slop: avoid purple/rainbow gradient buttons, glowing borders, or arbitrary `z-[9999]`.
