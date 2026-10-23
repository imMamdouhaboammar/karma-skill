#!/usr/bin/env python3
"""Explicit, bounded Git drift inspection. No review promotion or installation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from karma import runtime


def check_repository(url: str, records: list[dict], *, allow_local: bool=False) -> list[dict]:
    """Check one repository HEAD and all curated skill paths; never edit catalog."""
    env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_TERMINAL_PROMPT='0',GIT_CONFIG_NOSYSTEM='1',
               GIT_CONFIG_GLOBAL=os.devnull,
               GIT_ALLOW_PROTOCOL='file' if allow_local else 'https')
    checked_at=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    observed=None
    try:
        if not allow_local and not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git',url):
            raise ValueError('Unexpected source')
        response=subprocess.run(['git','-c','core.hooksPath='+os.devnull,'ls-remote',url,'HEAD'],
                                capture_output=True,text=True,check=True,timeout=30,env=env)
        line=response.stdout.strip().splitlines()
        if len(line)!=1 or not line[0].endswith('\tHEAD'):
            raise ValueError('Missing or ambiguous upstream HEAD')
        observed=line[0].split('\t',1)[0]
        if not runtime.SHA_RE.fullmatch(observed):
            raise ValueError('Upstream returned invalid revision')
    except (OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired,ValueError):
        return [dict(id=r['id'],status='source_unavailable',reviewed_revision=r['reviewed_revision'],
                     observed_head=None,checked_at=checked_at) for r in records]

    # A different HEAD does not inherit the reviewed status. Only inspect whether
    # its selected path still exists. We do not claim ancestry from SHA inequality.
    if all(r['reviewed_revision']==observed for r in records):
        return [dict(id=r['id'],status='unchanged',reviewed_revision=r['reviewed_revision'],
                     observed_head=observed,checked_at=checked_at) for r in records]
    try:
        with tempfile.TemporaryDirectory(prefix='karma-drift-') as temporary:
            checkout=Path(temporary)
            runtime._checkout_revision(url,observed,checkout,allow_local=allow_local)
            statuses=[]
            for record in records:
                if record['reviewed_revision']==observed:
                    status='unchanged'
                else:
                    try:
                        runtime._checked_skill_path(checkout,record['reviewed_path'])
                        status='upstream_changed'
                    except ValueError:
                        status='skill_path_missing'
                statuses.append(dict(id=record['id'],status=status,
                    reviewed_revision=record['reviewed_revision'],
                    observed_head=observed,checked_at=checked_at))
            return statuses
    except (OSError,ValueError,subprocess.CalledProcessError,subprocess.TimeoutExpired):
        return [dict(id=r['id'],status='verification_unavailable',
                     reviewed_revision=r['reviewed_revision'],observed_head=observed,
                     checked_at=checked_at) for r in records]


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description='Check reviewed upstream HEAD; offline by default')
    parser.add_argument('--online',action='store_true',help='Explicitly permit bounded GitHub requests')
    args=parser.parse_args(argv)
    entries=runtime.load_catalog()
    failures=runtime.validate_catalog(entries)
    if failures:
        parser.error('Invalid catalog: '+', '.join(failures[:3]))
    reviewed=[r for r in entries if r['status']=='reviewed']
    if not args.online:
        results=[dict(id=r['id'],status='not_checked_offline',
                      reviewed_revision=r['reviewed_revision'],observed_head=None,
                      checked_at=None) for r in reviewed]
    else:
        grouped: dict[str,list[dict]]={}
        for r in reviewed:
            grouped.setdefault(r['install']['repo'],[]).append(r)
        results=[]
        for repo,group in grouped.items():
            results.extend(check_repository('https://github.com/'+repo+'.git',group))
    print(json.dumps({'network_enabled':args.online,'promoted':False,
                      'results':sorted(results,key=lambda x:x['id'])},indent=2))
    return 0 if not args.online or all(r['status']=='unchanged' for r in results) else 1


if __name__=='__main__':
    raise SystemExit(main())
