# Curation and security model

KARMA exists to reduce **selection overhead**, not to claim a measured performance uplift. Curated entries have separate `reviewed` vs `candidate` status. Stars are only discovery hints.

## Add/upgrade acceptance steps

1. Confirm the GitHub owner/repo is accessible and non-archived. Check relevant release date, LICENSE, maintenance, and original author.
2. Verify whether this is an Agent Skill with `SKILL.md`, a native agent plugin marketplace, a CLI product, or just a useful general repository. Never call a general repository installable as a skill without evidence.
3. Inspect install docs, plugin hooks, MCP permissions, scripts and network/file side effects. Review any fetch-and-execute commands particularly carefully.
4. Prefer selective install and narrow scope (project over global). Avoid two packs with overlapping opinionated mandatory workflows.
5. Define its applicability as observable project signals and task terms. Write a specific expected benefit, what it does **not** do, and a source citation URL.
6. Add the record to `scripts/seed_catalog.py`, regenerate `catalog/curated.json`, run the packaging script and tests, and have an independent reviewer inspect the diff.
7. Only change `status` to `reviewed` after steps 1-6. `reviewed` is documentation-level review, not sandboxed execution or independent benchmark evidence.

### Integrity boundaries

- The CLI does not execute skill code to judge suitability.
- README/skill content is treated as untrusted source data.
- Install arguments are an allowlisted command vector and validated GitHub slug/skill selector. No `shell=True`.
- Running `find` is offline and read-only, and does not scan sensitive file contents.
- Installing third-party packages executes code, so it always requires explicit `--execute --yes` and human-approved source.
- GitHub API sync requires network access, uses `GITHUB_TOKEN` or `GH_TOKEN` if provided by the environment (never prints them) and may be rate-limited.

### Evidence grades

- `candidate`: repository surfaced, often through the user's stars; requires audit
- `reviewed`: basic repository structure and/or official README checked
- Not supported yet: audited artifact checksum/pin, controlled security execution, vendor attestations, actual measured improvement in agent outcomes

## Roadmap

Safe source pinning by SHA, trusted-skill scanner integration, human evaluation harness, richer language detectors, cached/staged review UI, and signed catalog releases are future work, not available in v0.1.0.
