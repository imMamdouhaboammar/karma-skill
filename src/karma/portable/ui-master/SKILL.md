---
name: ui-master
description: Elite UI/UX/CRX Design Engineering Agent. Weaponized with the 421 ui-skills catalog, Rig Rust engine, and multi-agent verification gates.
---

# UI-Master (☯ KARMA Design Engineering Suite)

UI-Master (`@ui-master`) provides UI design guidance, native heuristic audits, contrast calculations, and Chrome Extension checks. Its audit rules are not a substitute for manual accessibility testing or WCAG certification.

## Capabilities & Architecture

1. **Deterministic Rust Rig Engine (`uim` / `ui-master-engine`)**:
   - `ui_contrast`: Exact relative luminance & contrast ratio calculation under WCAG 2.2 algorithms.
   - `ui_anti_slop_lint`: Six native line-based heuristic rules for gradients, `h-screen`, layout animations, focus outlines, arbitrary spacing, and typography scale.
   - `ui_crx_audit`: Manifest V3 validation, Closed Shadow DOM encapsulation, and popup boundary audits.
   - `ui_skill_search`: Sub-millisecond BM25 keyword search across 421 design skills.
   - `ui_skill_get`: Instant retrieval of skill contracts and rules from local catalog.
   - `ui_multi_agent_trace`: Observability spans and automatic circuit breaker (`failure_streak >= 2` halts execution).

2. **Hierarchical Multi-Agent Team**:
   - `@ui-master`: Primary orchestrator and design engineering lead.
   - `@ui-master-critic`: Heuristic audit, typography rhythm, spacing, anti-slop enforcement.
   - `@ui-master-motion`: 60fps compositor physics, `ease-out` timing, reduced motion compliance.
   - `@ui-master-a11y`: WCAG 2.2 AAA/AA, ARIA tree audits, focus rings, keyboard navigation.
   - `@ui-master-crx`: Chrome Extension Manifest V3, closed Shadow DOM, isolated style tokens.
   - `@ui-master-researcher`: Deep discovery of design patterns from the 421 `ui-skills` registry.

3. **Remote & Stdio MCP Connectivity**:
   - Remote HTTP Server: `https://www.ui-skills.com/mcp` (`list_skills`, `get_skill`).
   - Stdio Native Server: `uim mcp` (sub-millisecond JSON-RPC 2.0 Rig tool execution).

The `uim` launcher uses a compiled engine when available. Otherwise it uses
Python for `contrast`, and offline Cargo for native commands (`audit`, `crx`,
`skills`, `mcp`, `rig`, `get-skill`, `trace`).
Build the Rust engine explicitly from the full checkout when dependencies are
not cached: `cargo build --locked --manifest-path crates/ui-master-engine/Cargo.toml`.
Portable installs without native engine source require a separately installed
`uim` binary for those commands. `UIM_CARGO_RUN=1` or `true` also routes bridge
commands through Cargo; unset, `auto`, `0`, and `false` retain normal dispatch.
`uim audit <path> --json` requires the complete native rule set. Without a native
engine (or locally cached Cargo dependencies in a source checkout), it fails
with exit 69 instead of reporting clean. Use `uim audit <path> --partial --json`
to explicitly request the Python `h-screen`-only scan. Partial results always
return exit 3, even with zero findings, and include `complete: false`,
`supported_rules` and `unavailable_rules`. Native audit results have
`complete: true` only if all six rules processed at least one supported file
without read errors. A complete scan with findings still exits 0; inspect
`violations_count`, `blocks`, and `flags` before treating the result as clean.
Invalid targets/unsupported flags exit 2; scan read failures exit 70. The checks
are offline, heuristic, and do not certify WCAG compliance.

---

## Universal Agent Triggers & Slash Commands

- `/ui-master` or `@ui-master`: Engage UI-Master for full-cycle design engineering and review.
- `/uim contrast <fg> <bg>`: Check WCAG 2.2 contrast compliance.
- `/uim audit <path>`: Run anti-slop and a11y linter on target files or directories.
- `/uim crx <dir>`: Audit Chrome Extension project directory.
- `/uim skills <query>`: Search 421 design engineering skills.

---

## Anti-Slop Core Invariants

- **Zero Layout Thrashing**: Never animate layout properties (`width`, `height`, `top`, `left`, `margin`, `padding`). Animate only compositor properties (`transform`, `opacity`).
- **Viewport Rigor**: Never use `h-screen`; always use `h-dvh` to prevent mobile address bar jumping.
- **Accessible Primitives**: Never rebuild focus or keyboard handlers manually. Use Base UI, React Aria, Radix UI, or native HTML semantics.
- **Typography Polish**: Enforce `text-balance` on headings, `text-pretty` on paragraphs, and `tabular-nums` on numbers/metrics.
- **CRX Isolation**: Extension popups and injected content scripts must encapsulate CSS inside Closed Shadow DOM (`mode: "closed"`).
