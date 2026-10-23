# UI-Master audit coverage contract (Issue #5)

**Decision:** Require the native Rust engine for comprehensive `uim audit`. Keep
Python's one-rule fallback only behind explicit `--partial`, returning exit `3`.

## Reasoning and alternatives

Python previously scanned only `h-screen` yet returned the same success-shaped
count object and exit `0` as Rust. Duplicating all Rust heuristics in Python
would create two rule engines that can drift whenever native checks change.
We selected one comprehensive engine and a clearly labeled limited fallback.
No network fetch, runtime dependency install, or new mandatory Python package
is added. `contrast` retains its original Python fallback.

## Executable rule inventory

`crates/ui-master-engine/src/audit.rs` is the source of truth. Every rule is
line-oriented and heuristic; there is no full JSX/CSS AST or WCAG conformance
analysis. Rules run for `.tsx`, `.jsx`, `.html`, `.css`, `.vue`, `.svelte`.

| Rule | Severity | Detection and exception |
| --- | --- | --- |
| `anti-slop/purple-gradient` | BLOCK | Same line `from-purple-` and `to-pink-`/`to-fuchsia-`, or `bg-gradient-to-r` plus `purple` |
| `layout/viewport-hscreen` | FLAG | Contains `h-screen` but not `h-dvh` on that line |
| `motion/layout-thrashing` | BLOCK | Animation/transition marker and `width`/`height`/`margin`/`padding` on same line |
| `a11y/focus-outline` | BLOCK | Contains `outline-none` without `focus-visible:` on that line |
| `layout/arbitrary-spacing` | FLAG | Whitespace-delimited `p-[...]`, `m-[...]` or `gap-[...]` token ending in `px]` and parsed as a non-4px multiple (native parser limitation applies to some `gap` forms) |
| `typography/excess-scale` | BLOCK | More than four distinct recognized `text-*` sizes within one file; finding line is 1 |

Violation fields are `file` (string), `line` (one-based integer), `rule`
(string), `severity` (`BLOCK`/`FLAG`), `message` (string), `snippet` (string),
and `fix` (string). The native `fix` values are embedded in `audit.rs` and
covered by rule fixtures. Findings order follows sorted file paths, then
per-line rule order; typography is evaluated after the file's lines.

## State and exit codes

| State | JSON | Exit |
| --- | --- | --- |
| Native scanned one or more supported files, no findings | `engine: rust`, `complete: true`, `partial: false`, counters all zero | `0` |
| Native scanned successfully with findings | Same completeness; nonzero findings counts | `0` (legacy behavior retained) |
| Python one-rule scan, zero or more findings | `engine: python`, `complete: false`, `partial: true`, supported/unavailable rules | `3` |
| Invalid target, no supported UI files, unsupported option | JSON error with `complete: false` when `--json` is valid | `2` |
| Native runtime unavailable | stderr diagnostic, no success payload | `69` |
| File/directory read failure | JSON error with `complete: false` when requested | `70` |

Errors represent *no completed audit*: `partial: false`, an empty
`supported_rules` array where returned by Python, and an `error` string. This
avoids listing rules as executed when the scan was never completed.

`files_scanned` counts supported UI files **successfully read**; `0` with
`complete: true` is never produced by this contract. `violations_count` is the
number of findings, with `blocks` and `flags` partitioning it. When reading
fails, the scan aborts and does not emit success-shaped counters. JSON output
is on stdout, diagnostics on stderr; native human output states `COMPLETE`,
Python human output states `PARTIAL (NOT VERIFIED)`.

`supported_rules` identifies executed rule IDs. For the native engine this is
all six rules and `unavailable_rules` is empty; for the Python fallback it is
only `layout/viewport-hscreen` and the remaining five IDs are unavailable.
`complete: true` means those six heuristics executed over all discovered UI
files successfully, **not** that a visual design passed every quality check.

## Engine selection and compatibility

The launcher preserves the established selection of an independent `uim` on
PATH and local release/debug engines, but **strict audits probe** each candidate
with the native `audit-contract --json` command before trusting it. A verified
candidate advertises `comprehensive-v1` and all six rule IDs; older binaries
are skipped. The same probe applies to `~/.bun/bin/uim` and
`~/.bun/bin/ui-master-engine`. Without a verified compiled engine, a strict
audit attempts `cargo run --offline --locked` from the source checkout. In a
portable install without native source, users must provide an independent
compiled engine. `--partial` is intercepted before engine discovery and
selects the Python bridge deliberately. The bridge rejects direct unqualified
`audit` calls. `UIM_CARGO_RUN` remains validated as before; `contrast` honors
its historical setting. Existing `0`-on-findings semantics for completed
native scans are unchanged. Rust's extra metadata is additive in CLI, Rig,
and MCP JSON results. Unknown flags fail rather than silently changing scope.

Python 3.10 is supported. The Node/Bun adapter routes all audit commands through
the shell launcher to avoid stale-binary bypass, preserves subprocess exit codes,
and maps child signal termination to nonzero status. Source and portable skills
share the generated bridge/launcher. To migrate automation, inspect
`complete`, `violations_count`, and exit code; do not interpret exit `0` alone
as no findings. Rollback of this contract would reopen Issue #5, so keep the
regression gate when adapting callers.

## Future rules and remaining limitations

Adding a native rule requires updating `AUDIT_RULES`, its fixture coverage,
the Python unavailable list, and this inventory. The shared fixture corpus is
under `tests/fixtures/ui_audit/`. Native directory-symlink cycles and trace
durability are separately tracked by Issue #14. The native arbitrary-spacing
token parser is intentionally not redesigned here. No heuristic audit offers
a WCAG certification or proof that every UI defect was detected.
