#!/usr/bin/env python3
"""Offline fallback bridge for UI-Master tools when Rust binary is not yet compiled."""
from __future__ import annotations
import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

SUPPORTED_RULES = ["layout/viewport-hscreen"]
UNAVAILABLE_RULES = [
    "anti-slop/purple-gradient", "motion/layout-thrashing", "a11y/focus-outline",
    "layout/arbitrary-spacing", "typography/excess-scale",
]
UI_EXTENSIONS = {'.tsx', '.jsx', '.html', '.css', '.vue', '.svelte'}
IGNORED_DIRECTORIES = {'node_modules', 'target', 'dist'}


class InvalidAuditTarget(ValueError):
    pass


def partial_metadata() -> dict:
    return {
        "engine": "python", "complete": False, "partial": True,
        "supported_rules": SUPPORTED_RULES, "unavailable_rules": UNAVAILABLE_RULES,
    }


def failed_metadata() -> dict:
    """No rules completed over the requested target when scanning fails."""
    return {
        "engine": "python", "complete": False, "partial": False,
        "supported_rules": [], "unavailable_rules": SUPPORTED_RULES + UNAVAILABLE_RULES,
    }

def parse_color(c: str) -> tuple[int, int, int]:
    c = c.strip().lower()
    if c.startswith('#'):
        c = c[1:]
        if len(c) == 3:
            c = ''.join([ch * 2 for ch in c])
        if len(c) == 6:
            return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    m = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', c)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return 0, 0, 0

def rel_luminance(r: int, g: int, b: int) -> float:
    def norm(val: int) -> float:
        s = val / 255.0
        return s / 12.92 if s <= 0.04045 else math.pow((s + 0.055) / 1.055, 2.4)
    return 0.2126 * norm(r) + 0.7152 * norm(g) + 0.0722 * norm(b)

def contrast_ratio(fg: str, bg: str) -> dict:
    fr, fg_g, fb = parse_color(fg)
    br, bg_g, bb = parse_color(bg)
    l1 = rel_luminance(fr, fg_g, fb)
    l2 = rel_luminance(br, bg_g, bb)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    ratio = (lighter + 0.05) / (darker + 0.05)
    return {
        "fg": {"hex": fg, "r": fr, "g": fg_g, "b": fb},
        "bg": {"hex": bg, "r": br, "g": bg_g, "b": bb},
        "ratio": round(ratio, 2),
        "formatted_ratio": f"{ratio:.2f}:1",
        "passes_aa_normal": ratio >= 4.5,
        "passes_aa_large": ratio >= 3.0,
        "passes_aaa_normal": ratio >= 7.0,
        "passes_aaa_large": ratio >= 4.5,
        "passes_ui_component": ratio >= 3.0,
        "recommendation": "Compliant" if ratio >= 4.5 else "Contrast too low. Use darker foreground or lighter background."
    }

def audit_path(path_str: str) -> dict:
    target = Path(path_str)
    violations = []
    files_scanned = 0
    if target.is_file():
        files = [target] if target.suffix in UI_EXTENSIONS else []
    elif target.is_dir():
        files = []
        def fail_walk(error: OSError) -> None:
            raise error
        for root, dirs, names in os.walk(target, onerror=fail_walk, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d not in IGNORED_DIRECTORIES)
            files.extend(Path(root) / name for name in sorted(names)
                         if not name.startswith('.') and Path(name).suffix in UI_EXTENSIONS)
    else:
        raise InvalidAuditTarget(f"Path not found or not a readable target: {path_str}")

    if not files:
        raise InvalidAuditTarget(f"No supported UI files found: {path_str}")

    for f in files:
        content = f.read_text(encoding='utf-8')
        files_scanned += 1
        for line_no, line in enumerate(content.splitlines(), 1):
            if 'h-screen' in line and 'h-dvh' not in line:
                violations.append({
                    "file": str(f),
                    "line": line_no,
                    "rule": "layout/viewport-hscreen",
                    "severity": "FLAG",
                    "message": "Viewport unit 'h-screen' causes mobile address bar jumping and scroll bugs.",
                    "snippet": line.strip(),
                    "fix": "Use 'h-dvh' (dynamic viewport height) or 'min-h-dvh' instead of 'h-screen'.",
                })
    return {**partial_metadata(),
        "files_scanned": files_scanned,
        "violations_count": len(violations),
        "blocks": len([v for v in violations if v["severity"] == "BLOCK"]),
        "flags": len([v for v in violations if v["severity"] != "BLOCK"]),
        "violations": violations
    }

def main():
    p = argparse.ArgumentParser(description="UI-Master Bridge")
    sub = p.add_subparsers(dest="cmd")
    
    c_parser = sub.add_parser("contrast")
    c_parser.add_argument("fg")
    c_parser.add_argument("bg")
    c_parser.add_argument("--json", action="store_true")
    
    a_parser = sub.add_parser("audit")
    a_parser.add_argument("path")
    a_parser.add_argument("--partial", action="store_true", help="Run only the h-screen rule (not verification)")
    a_parser.add_argument("--json", action="store_true")

    args = p.parse_args()
    if args.cmd == "contrast":
        res = contrast_ratio(args.fg, args.bg)
        print(json.dumps(res, indent=2))
    elif args.cmd == "audit":
        if not args.partial:
            error = "Comprehensive audit requires the native Rust engine; use uim audit <path> or explicitly request --partial."
            print(f"uim: {error}", file=sys.stderr)
            if args.json:
                print(json.dumps({**failed_metadata(), "error": error}, indent=2))
            return 69
        try:
            res = audit_path(args.path)
        except InvalidAuditTarget as exc:
            print(f"uim: {exc}", file=sys.stderr)
            if args.json:
                print(json.dumps({**failed_metadata(), "error": str(exc)}, indent=2))
            return 2
        except (OSError, UnicodeError) as exc:
            print(f"uim: audit could not read all files: {exc}", file=sys.stderr)
            if args.json:
                print(json.dumps({**failed_metadata(), "error": f"Audit read failed: {exc}"}, indent=2))
            return 70
        print("uim: PARTIAL audit only; no comprehensive verification was performed.", file=sys.stderr)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"PARTIAL AUDIT (NOT VERIFIED): {res['files_scanned']} files, {res['violations_count']} findings")
            for v in res['violations']:
                print(f"{v['severity']} {v['rule']} {v['file']}:{v['line']} - {v['message']}")
        return 3
    else:
        p.print_help()

if __name__ == "__main__":
    sys.exit(main())
