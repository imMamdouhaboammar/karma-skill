#!/usr/bin/env python3
"""Offline fallback bridge for UI-Master tools when Rust binary is not yet compiled."""
from __future__ import annotations
import argparse
import json
import math
import re
import sys
from pathlib import Path

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
        files = [target]
    elif target.is_dir():
        files = list(target.rglob('*'))
    else:
        return {"error": f"Path not found: {path_str}"}

    for f in files:
        if not f.is_file() or f.suffix not in ('.tsx', '.jsx', '.html', '.css', '.vue', '.svelte'):
            continue
        files_scanned += 1
        try:
            content = f.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for line_no, line in enumerate(content.splitlines(), 1):
            if 'h-screen' in line:
                violations.append({
                    "file": str(f),
                    "line": line_no,
                    "rule": "viewport-vh-mobile-jump",
                    "severity": "BLOCK",
                    "message": "Use h-dvh instead of h-screen to prevent mobile viewport jumping.",
                    "snippet": line.strip()[:80]
                })
    return {
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
    a_parser.add_argument("--json", action="store_true")

    args = p.parse_args()
    if args.cmd == "contrast":
        res = contrast_ratio(args.fg, args.bg)
        print(json.dumps(res, indent=2))
    elif args.cmd == "audit":
        res = audit_path(args.path)
        print(json.dumps(res, indent=2))
    else:
        p.print_help()

if __name__ == "__main__":
    main()
