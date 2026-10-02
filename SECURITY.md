# Security Policy

## Core Invariants

KARMA ☯ is designed with a defense-in-depth, offline-first security architecture:

1. **Offline by Default**:
   `find`, `show`, `catalog`, `validate`, and `doctor` operate completely offline using stdlib Python. No external network requests, telemetry, background daemons, or remote analytics.

2. **Dry-Run & User Approval First**:
   KARMA is a skill *recommender*, not an automatic installer. The `install` command prints a dry-run preview by default. External installer processes (`npx skills add ...`) are strictly prevented from executing unless the user explicitly passes both `--execute` and `--yes`.

3. **Untrusted Data Boundaries**:
   Data fetched during `sync-stars` or retrieved from GitHub/READMEs is treated as untrusted data, never as executable instructions or agent directives. Star counts and third-party README claims are never accepted as proof of security or safety.

4. **Zero Secret/Credential Ingestion**:
   Project fingerprinting inspects filenames and manifest dependencies only. It never reads `.env` files, credentials, private keys, authentication tokens, or source code contents into memory or catalog.

5. **Symlink and Path Traversal Protection**:
   KARMA rejects directory symlink traversal during project fingerprinting and refuses to write through symlinked agent target directories during `init-agent`.

6. **Shell Injection Defense**:
   All CLI arguments and external command executions are strictly array-passed and quoted with `shlex.quote`. Unvalidated string interpolation in subshells is strictly prohibited.

## Reporting a Vulnerability

If you discover a potential security vulnerability in KARMA, please report it privately:

- **Author**: Mamdouh Aboammar
- **GitHub**: [imMamdouhaboammar](https://github.com/imMamdouhaboammar)

Please include a reproduction script and impact description. We appreciate your efforts to keep open-source and agentic computing secure.
