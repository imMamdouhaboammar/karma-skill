# Security Policy

## Core Invariants

KARMA ☯ is designed with a defense-in-depth, offline-first security architecture:

1. **Offline by Default**:
   `find`, `show`, `catalog`, `validate`, and `doctor` operate completely offline using stdlib Python. No external network requests, telemetry, background daemons, or remote analytics.

2. **Dry-Run & User Approval First**:
   KARMA is a skill *recommender*, not an automatic installer. `install` is a dry run by default. Only explicit `--execute --yes` fetches the exact reviewed Git SHA and copies a verified skill directory into the current project's agent-specific location; it never invokes a moving `npx skills add` remote source. An invalid/missing reviewed revision or existing destination fails closed.

3. **Untrusted Data Boundaries**:
   Data fetched during `sync-stars` or retrieved from GitHub/READMEs is treated as untrusted data, never as executable instructions or agent directives. Star counts and third-party README claims are never accepted as proof of security or safety.

4. **Zero Secret/Credential Ingestion**:
   Project fingerprinting inspects filenames and manifest dependencies only. It never reads `.env` files, credentials, private keys, authentication tokens, or source code contents into memory or catalog.

5. **Symlink and Path Traversal Protection**:
   KARMA rejects directory symlink traversal during project fingerprinting and refuses to write through symlinked agent target directories during `init-agent`.

6. **Shell Injection Defense**:
   All CLI arguments and external command executions are strictly array-passed and quoted with `shlex.quote`. Unvalidated string interpolation in subshells is strictly prohibited.

7. **MCP Advice-Only Boundary**:
   The optional `karma-mcp` stdio server exposes only `recommend_skills` and `get_skill_guide`. Both operate against the packaged, reviewed catalog. MCP requests supply a task and optional public stack tags, not repository paths, source code or credentials. Tools never install skills, run commands, read the client's project, contact a marketplace, or enable implicit approval. Returned commands are untrusted suggestions requiring the user's explicit approval before execution.

8. **Revision Identity, Not Malware Certification**:
   Catalog schema v2 binds a reviewed entry to a full Git SHA, skill path, timestamp, and immutable evidence URL. The approved installer verifies a detached checkout at that SHA and copies only the selected directory, rejecting source or destination symlinks. This proves the selected Git content identity under normal Git hash assumptions. It does not certify third-party instructions, npm dependencies, future upstream releases, or every external resource a skill might request at runtime. Offline guides report drift as unverified; only an explicit `check_reviewed_drift.py --online` maintenance run probes upstream without promoting revisions.

## Reporting a Vulnerability

If you discover a potential security vulnerability in KARMA, please report it privately:

- **Author**: Mamdouh Aboammar
- **GitHub**: [imMamdouhaboammar](https://github.com/imMamdouhaboammar)

Please include a reproduction script and impact description. We appreciate your efforts to keep open-source and agentic computing secure.
