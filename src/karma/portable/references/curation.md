# Curation and security model

KARMA exists to reduce **selection overhead**, not to claim a measured performance uplift. Curated entries have separate `reviewed` vs `candidate` status. Stars are only discovery hints.

## Add/upgrade acceptance steps

1. Confirm the GitHub owner/repo is accessible and non-archived. Check relevant release date, LICENSE, maintenance, and original author.
2. Verify whether this is an Agent Skill with `SKILL.md`, a native agent plugin marketplace, a CLI product, or just a useful general repository. Never call a general repository installable as a skill without evidence.
3. Inspect install docs, plugin hooks, MCP permissions, scripts and network/file side effects. Review any fetch-and-execute commands particularly carefully.
4. Prefer selective install and narrow scope (project over global). Avoid two packs with overlapping opinionated mandatory workflows.
5. Check the exact `SKILL.md` and its dependent local files at a full 40-character commit SHA, not a moving README/branch/tag. Confirm that the skill path exists and that a selective copy of this directory is usable without unreviewed sibling material.
6. Define its applicability as observable project signals and task terms. Write a specific expected benefit, what it does **not** do, and a revision-specific evidence URL.
7. Add its repository SHA and selected path to `REVIEWED_REVISIONS` and `REVIEWED_PATHS` in `scripts/seed_catalog.py`, recording the genuine inspection time. Regenerate with `python3 scripts/seed_catalog.py`, then `python3 scripts/build_skill.py`. Run the tests and have another reviewer inspect the diff.
8. Only change `status` to `reviewed` after these checks. A new HEAD cannot inherit a prior review. If evidence or selective-install compatibility is missing, keep `candidate`. Review here means a specific entrypoint/docs inspection, not a downstream security benchmark.

### Integrity boundaries

- The CLI does not execute skill code to judge suitability.
- README/skill content is treated as untrusted source data.
- Installer arguments are allowlisted command vectors. A detached SHA-verified checkout is copied into the selected agent host directory only after `--execute --yes`. No `shell=True`, remote `skills add` shorthand, or overwrite of an existing skill.
- Running `find` is offline and read-only, and does not scan sensitive file contents.
- Approved installation fetches third-party source files but does not execute them. The installed instructions may request further actions, which require separate review/approval.
- GitHub API sync requires network access, uses `GITHUB_TOKEN` or `GH_TOKEN` if provided by the environment (never prints them) and may be rate-limited.

### Evidence grades

- `candidate`: repository surfaced, often through the user's stars; requires audit
- `reviewed`: explicit revision, selected path, timestamp and immutable `SKILL.md` evidence for a basic inspected entrypoint
- Not supported: full security audit of each dependency, vendor attestations, reliable real-time offline drift status, measured improvement in agent outcomes

## Roadmap

For optional drift verification, run `python3 scripts/check_reviewed_drift.py --online`. Default invocation is offline and reports `not_checked_offline`. Online results distinguish unchanged, changed, source unavailable, verification unavailable, and missing skill path. The command is read-only and **never promotes** a new revision. A changed source requires the same inspection and review workflow again.

Future work includes signed catalog releases, human evaluation, and deeper analysis of arbitrary scripts/dependencies inside downloaded skills.
