#!/usr/bin/env python3
"""Copy the tested standalone CLI and catalog into the portable SKILL package."""
from pathlib import Path
import shutil
root = Path(__file__).resolve().parents[1]
files = [
    (root / 'src/karma/runtime.py', root / 'skills/find-karma/scripts/karma.py'),
    (root / 'catalog/curated.json', root / 'src/karma/catalog.json'),
    (root / 'catalog/curated.json', root / 'skills/find-karma/assets/catalog.json'),
]
# Pip installations contain a fully portable copy, too.
portable = root / 'src' / 'karma' / 'portable'
portable.mkdir(parents=True, exist_ok=True)
for a,b in files:
    b.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(a, b)
    print(f'packaged {b.relative_to(root)}')

shutil.copytree(root / 'skills' / 'find-karma', portable, dirs_exist_ok=True)
print('packaged Python wheel portable skill')
