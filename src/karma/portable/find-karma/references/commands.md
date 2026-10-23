# CLI reference

All commands require Python 3.10+ only, with no third-party libraries.
Run `./bin/karma <command>` inside the source checkout, or `python3 <skill-path>/scripts/karma.py <command>` after copying the portable skill.

- `find [--project DIRECTORY] [--goal TEXT] [--agent codex|claude-code|cursor|gemini|opencode|antigravity] [--limit 1..30] [--json]`: read-only offline suggestions
- `catalog [--all] [--kind skill|plugin|tool] [--json]`: list reviewed, or pending review too
- `show ID [--agent NAME] [--json]`: source and benefits for one record
- `install ID --agent NAME`: print exact command, **do not run it**
- `install ID --agent NAME --execute --yes`: explicit opt-in to execute the `npx skills add` installer. No shell interpolation is used. Not supported for native plugin marketplaces/manual tools
- `init-agent [--project ROOT] [--agent NAME] [--dry-run] [--force]`: copy this portable skill into an agent-specific workspace path
- `sync-stars [--user USER] [--project ROOT] [--max-pages N] [--output PATH] [--json]`: GitHub REST fetch of public starred repos, writes only UNREVIEWED candidates to JSON; never edits the curated list
- `doctor [--json]`: environment and package check
- `validate [--json]`: verify bundled catalog schema and install source safety

The `find` command reads filenames and bounded `package.json` metadata. It does not send source files to a model or external service.

### Examples

```sh
./bin/karma find --project ./webapp --goal 'React and Next.js UI quality' --agent claude-code
./bin/karma find --goal 'rust security audit' --agent codex --json
./bin/karma install matt-tdd --agent codex
./bin/karma init-agent --agent cursor --project /path/to/project
```

No external skill installation is performed during tests.
