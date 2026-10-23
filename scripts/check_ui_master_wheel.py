"""Fail if a built wheel omits the portable UI-Master audit entrypoints."""

from pathlib import Path
import sys
from zipfile import ZipFile


REQUIRED = {
    "karma/portable/ui-master/SKILL.md",
    "karma/portable/ui-master/scripts/uim",
    "karma/portable/ui-master/scripts/bridge.py",
    "karma/portable/ui-master/mcp/mcp.json",
    "karma/portable/ui-master/mcp/tools/ui_anti_slop_lint.json",
    "karma/portable/ui-master/agents/codex.md",
    "karma/portable/ui-master/subagents/ui-master-a11y.md",
    "karma/portable/ui-master/assets/ui-skills-catalog.json",
}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check_ui_master_wheel.py <wheel-file>", file=sys.stderr)
        return 2
    wheel = Path(sys.argv[1])
    with ZipFile(wheel) as archive:
        missing = sorted(REQUIRED - set(archive.namelist()))
    if missing:
        print("Portable UI-Master files missing from wheel:\n" + "\n".join(missing), file=sys.stderr)
        return 1
    print(f"Portable UI-Master wheel contents verified: {wheel.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
