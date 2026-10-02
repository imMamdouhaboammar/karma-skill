#!/usr/bin/env python3
"""KARMA ☯ | A small, portable, offline-first agent skill recommender.

Python 3.10+, stdlib only. No agent vendor credentials, arbitrary command execution,
background service, telemetry, or automatic installation.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

VERSION = '0.1.0'
REPO_RE = re.compile(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z')
SKILL_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]*\Z')
AGENTS = ('codex', 'claude-code', 'cursor', 'gemini', 'opencode', 'antigravity', 'windsurf')
AGENT_PATHS = {
    'codex': '.agents/skills/find-karma',
    'claude-code': '.claude/skills/find-karma',
    'cursor': '.cursor/skills/find-karma',
    'gemini': '.gemini/skills/find-karma',
    'opencode': '.opencode/skills/find-karma',
    'antigravity': '.agent/skills/find-karma',
    'windsurf': '.windsurf/skills/find-karma',
}
SKIP_DIRS = {
    '.git', '.next', '.venv', 'venv', '__pycache__', 'node_modules', 'dist',
    'build', 'coverage', 'target', '.idea', '.turbo', 'vendor', '.svelte-kit',
    '.nuxt', '.output', '.cache', 'out', '.karma', '.mypy_cache',
}
SOURCE_FILES = {'.ts':'language:typescript','.tsx':'language:typescript',
    '.js':'language:javascript','.jsx':'language:javascript',
    '.py':'language:python','.rs':'language:rust','.go':'language:go',
    '.vue':'task:frontend','.svelte':'task:frontend', '.sol':'task:security',
    '.css':'task:frontend','.scss':'task:frontend',
    '.astro':'task:frontend'}
GOAL_WEIGHTS = {'task:frontend': 15, 'task:motion': 18, 'task:video': 12, 'task:security': 16, 'task:testing': 14, 'task:skills': 15, 'task:architecture': 13, 'task:research': 12, 'task:evals': 14, 'task:review': 5, 'task:quality': 3}
GOAL_TERMS = {
    'task:security': 'security secure vulnerability vulnerabilities audit secret secrets auth threat cve hardening penetration supply-chain solidity أمان أمن ثغرات',
    'task:testing': 'testing tests test tdd regression pytest jest vitest unit integration coverage اختبارات اختبار',
    'task:debugging': 'debug bug bugs failing failure fix error traceback إصلاح مشكلة',
    'task:frontend': 'frontend ui ux website web components css page screens react nextjs next.js واجهة تصميم',
    'task:design': 'design aesthetic polish visuals styling typography layout tokens visual',
    'task:motion': 'motion animated animation animate aftereffects kinetic video film explainer موشن أنيميشن تحريك',
    'task:video': 'video cinematic film render frames mp4 فيديو رندر',
    'task:research': 'research scientific reproduce literature experiment paper science بحث علمي',
    'task:statistics': 'statistics bayesian pymc experiment causal statistical stats',
    'task:review': 'review pull request pr code-review critic مراجعة',
    'task:architecture': 'architecture design-system system-design refactor boundaries coupling architecture تصميم معماري',
    'task:planning': 'plan planning spec requirements scope roadmap planify تخطيط خطة',
    'task:orchestration': 'orchestrate multi-agent subagents delegation delegate agents swarm orchestration',
    'task:ci': 'github-actions workflow continuous-integration ci cd release pipeline',
    'task:quality': 'quality lint static-analysis reliability maintainability discipline',
    'task:skills': 'skill skills skill.md agentskill agent-skills skillpack مهارات',
    'task:plugin': 'plugin plugins marketplace mcp connectors إضافات',
    'task:browser': 'browser playwright puppeteer screenshot e2e web-automation',
    'task:qa': 'qa acceptance visual-qa visual-regression smoke',
    'task:evals': 'eval evals evaluator grading benchmark model-eval تقييم',
    'task:llm': 'llm model prompt r ag rag inference evaluation',
    'task:governance': 'governance control approvals permissions policy guardrails',
    'task:portfolio': 'portfolio cv resume personal-site بورتفوليو',
    'task:discovery': 'discover find recommend selection shortlist discover-skills',
}


def catalog_path() -> Path:
    here = Path(__file__).resolve()
    for path in (here.with_name('catalog.json'), here.parents[1] / 'assets' / 'catalog.json'):
        if path.is_file():
            return path
    raise FileNotFoundError('Missing catalog.json: run python scripts/build_skill.py')


def load_catalog(path: str | Path | None = None) -> list[dict[str, Any]]:
    source = Path(path) if path else catalog_path()
    data = json.loads(source.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != 1 or not isinstance(data.get('items'), list):
        raise ValueError('Unsupported or malformed catalog schema')
    return data['items']


def validate_catalog(entries: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for i, item in enumerate(entries):
        name = str(item.get('id',''))
        if not SKILL_RE.fullmatch(name): errors.append(f'entry {i}: invalid id')
        if name in seen: errors.append(f'entry {i}: duplicate id {name}')
        seen.add(name)
        repo = (item.get('install') or {}).get('repo','')
        if not isinstance(repo,str) or not REPO_RE.fullmatch(repo) or '..' in repo:
            errors.append(f'{name}: unsafe repo install source')
        if item.get('source') != 'https://github.com/'+str(repo):
            errors.append(f'{name}: source does not match repo')
        if item.get('status') not in ('candidate','reviewed'):
            errors.append(f'{name}: invalid review status')
        if item.get('kind') not in ('skill','plugin','tool'):
            errors.append(f'{name}: invalid kind')
        if (item.get('install') or {}).get('method') not in ('skills','manual'):
            errors.append(f'{name}: unknown install method')
        sub = (item.get('install') or {}).get('skill')
        if sub and (not isinstance(sub,str) or not SKILL_RE.fullmatch(sub)):
            errors.append(f'{name}: invalid skill selector')
        for key in ('lane','summary','benefit','name','evidence'):
            if not isinstance(item.get(key),str) or not item[key].strip():
                errors.append(f'{name}: missing {key}')
        for key in ('signals','tags'):
            if not isinstance(item.get(key),list) or not all(isinstance(x,str) for x in item[key]):
                errors.append(f'{name}: invalid {key}')
        if item.get('hosts') and (not isinstance(item['hosts'], list) or
            any(host not in AGENTS for host in item['hosts'])):
            errors.append(f'{name}: invalid agent restriction')
        if item.get('require_any') is not None and (not isinstance(item['require_any'],list) or
            not all(isinstance(s,str) and s.startswith(('task:','framework:','language:')) for s in item['require_any'])):
            errors.append(f'{name}: invalid requirement')
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > 256_000: return {}
        val = json.loads(path.read_text(encoding='utf-8'))
        return val if isinstance(val,dict) else {}
    except (OSError, ValueError, UnicodeError):
        return {}


def detect_project(project: Path) -> set[str]:
    """Bounded, read-mostly metadata inspection; never follows directory symlinks."""
    root = project.expanduser().resolve(strict=True)
    if not root.is_dir(): raise NotADirectoryError(f'Not a directory: {root}')
    found: set[str] = set()
    names: set[str] = set()
    files_scanned = 0
    for base, dirs, files in os.walk(root, topdown=True, followlinks=False):
        base_path = Path(base)
        depth = len(base_path.relative_to(root).parts)
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (base_path/d).is_symlink()) if depth < 3 else []
        for filename in sorted(files):
            files_scanned += 1
            if files_scanned > 3500: break
            names.add(filename.lower())
            suffix = Path(filename).suffix.lower()
            if suffix in SOURCE_FILES: found.add(SOURCE_FILES[suffix])
            rel = (base_path / filename).relative_to(root).as_posix().lower()
            if 'test' in filename.lower() or '/tests/' in '/'+rel or '/__tests__/' in '/'+rel:
                found.add('task:testing')
            if rel.startswith('.github/workflows/'):
                found.add('task:ci')
            if filename == 'SKILL.md': found.add('task:skills')
            if filename in ('playwright.config.ts','playwright.config.js','playwright.config.mjs'):
                found.update(('task:browser','task:qa'))
            if filename in ('Dockerfile','docker-compose.yml','compose.yaml'):
                found.add('task:ci')
            if filename in ('next.config.js','next.config.mjs','next.config.ts'):
                found.update(('framework:nextjs','task:frontend'))
            if filename == 'Cargo.toml': found.add('language:rust')
            if filename in ('pyproject.toml','requirements.txt','uv.lock','Pipfile'):
                found.add('language:python')
        if files_scanned > 3500: break
    pkg = _read_json(root/'package.json')
    deps = {**(pkg.get('dependencies') if isinstance(pkg.get('dependencies'),dict) else {}),
            **(pkg.get('devDependencies') if isinstance(pkg.get('devDependencies'),dict) else {})}
    if 'next' in deps: found.update(('framework:nextjs','framework:react','task:frontend'))
    if 'react' in deps: found.update(('framework:react','task:frontend'))
    if 'vue' in deps or 'svelte' in deps or 'astro' in deps: found.add('task:frontend')
    if 'typescript' in deps or 'tsconfig.json' in names: found.add('language:typescript')
    if 'playwright' in ' '.join(deps).lower(): found.update(('task:browser','task:qa'))
    if any(n in names for n in ('remotion.config.ts','remotion.config.js')): found.update(('task:motion','task:video'))
    if 'skills' in (d.name for d in root.iterdir() if d.is_dir() and not d.is_symlink()): found.add('task:skills')
    if 'AGENTS.md' in (p.name for p in root.iterdir() if p.is_file()): found.add('task:governance')
    if not found: found.add('task:planning')
    return found


def _goal_signals(goal: str) -> set[str]:
    words=set(re.findall(r'[\w.-]+',goal.lower()))
    signs: set[str]=set()
    for k,terms in GOAL_TERMS.items():
        if words.intersection(terms.split()): signs.add(k)
    if 'next' in words or 'nextjs' in words or 'next.js' in words: signs.add('framework:nextjs')
    if 'react' in words: signs.add('framework:react')
    if 'rust' in words: signs.add('language:rust')
    if 'python' in words: signs.add('language:python')
    return signs


def install_argv(item: dict[str, Any], agent: str) -> list[str] | None:
    if agent not in AGENTS: raise ValueError(f'Unknown agent: {agent}')
    if item.get('hosts') and agent not in item['hosts']: return None
    install = item['install']
    if install.get('method') != 'skills': return None
    repo = install.get('repo','')
    if not isinstance(repo,str) or not REPO_RE.fullmatch(repo) or '..' in repo:
        raise ValueError('Unsafe install repository name')
    argv = ['npx','--yes','skills','add',repo]
    skill = install.get('skill')
    if skill:
        if not isinstance(skill,str) or not SKILL_RE.fullmatch(skill): raise ValueError('Unsafe skill selector')
        argv.extend(['--skill',skill])
    argv.extend(['-a',agent,'-y'])
    return argv


def install_instructions(item: dict[str, Any], agent: str) -> str:
    if item.get('hosts') and agent not in item['hosts']:
        return f'Not supported for {agent}; check listed hosts.'
    cmd = install_argv(item,agent)
    if cmd:
        return ' '.join(shlex.quote(x) for x in cmd)
    return item['install'].get('instructions') or f'Review README first: {item["source"]}'


def find(entries: list[dict[str, Any]], project_signals: set[str], goal: str='',
         limit: int=5, agent: str='codex') -> list[dict[str, Any]]:
    """Deterministic explainable matching, never based on star counts."""
    if agent not in AGENTS: raise ValueError(f'Unknown agent: {agent}')
    desired = _goal_signals(goal)
    query_tokens = set(re.findall(r'[\w.-]+',goal.lower()))
    ranked = []
    for item in entries:
        if item.get('status') != 'reviewed': continue
        if item.get('hosts') and agent not in item['hosts']: continue
        required=item.get('require_any') or []
        if required and not set(required).intersection(desired | project_signals): continue
        signals = set(item.get('signals',[]))
        goal_hits = signals & desired
        project_hits = signals & project_signals
        tag_hits = set(item.get('tags',[])) & query_tokens
        score = sum(GOAL_WEIGHTS.get(s,9) for s in goal_hits) + 3*len(project_hits) + 2*len(tag_hits)
        if 'task:frontend' in goal_hits and item['lane']=='frontend-quality': score += 5
        # If user supplies a specific goal, a non-matching project-only item is noise.
        if goal.strip() and desired and not (goal_hits or tag_hits): continue
        if score < (7 if goal.strip() and desired else 3): continue
        why=[]
        if goal_hits: why.append('Goal: '+', '.join(sorted(goal_hits)))
        if project_hits: why.append('Repository: '+', '.join(sorted(project_hits)))
        if tag_hits: why.append('Keywords: '+', '.join(sorted(tag_hits)))
        ranked.append((score,item['id'],item,why))
    ranked.sort(key=lambda v:(-v[0],v[1]))
    result=[]
    lanes=set()
    sources=set()
    for score, _, item, why in ranked:
        if item['lane'] in lanes or item['source'] in sources: continue
        result.append({**item, 'score':score,'why':why,
                       'install':install_instructions(item,agent)})
        lanes.add(item['lane'])
        sources.add(item['source'])
        if len(result)>=limit: break
    return result


def star_candidates(repos: list[dict[str, Any]], curated: set[str]) -> list[dict[str, Any]]:
    output=[]
    for repo in repos:
        full=repo.get('full_name','')
        if not isinstance(full,str) or not REPO_RE.fullmatch(full) or full.lower() in curated: continue
        desc=str(repo.get('description') or '')[:400]
        topics=repo.get('topics') if isinstance(repo.get('topics'),list) else []
        text=(full+' '+desc+' '+' '.join(str(t) for t in topics)).lower()
        likely=bool(re.search(r'(^|[- /])(skills?|plugins?|claude|codex|agent-skills)([- /]|$)',text))
        if not likely: continue
        output.append({'repo':full,'url':'https://github.com/'+full,
                       'description':desc,'likely_skill':likely,
                       'status':'candidate','reason':'Metadata heuristic only; verify actual SKILL.md, docs, license and install safety.'})
    return sorted(output,key=lambda x:x['repo'].lower())


def _github_page(url: str, token: str | None=None) -> list[dict[str, Any]]:
    headers={'Accept':'application/vnd.github+json','User-Agent':'find-karma/0.1.0'}
    if token: headers['Authorization']='Bearer '+token
    req=Request(url, headers=headers,method='GET')
    try:
        with urlopen(req,timeout=12) as response:
            data=json.load(response)
    except HTTPError as exc:
        if exc.code in (403,429):
            raise RuntimeError('GitHub rate limit or permission error; retry later or set GITHUB_TOKEN') from exc
        raise RuntimeError(f'GitHub returned HTTP {exc.code}') from exc
    except (URLError,TimeoutError) as exc:
        raise RuntimeError(f'GitHub unavailable: {exc}') from exc
    if not isinstance(data,list): raise RuntimeError('Unexpected GitHub response')
    return data


def fetch_stars(user: str, *, page_size: int=100,max_pages: int=6,
                token: str | None=None, fetcher: Callable[..., list[dict[str, Any]]] | None=None) -> list[dict[str, Any]]:
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?',user):
        raise ValueError('Invalid GitHub username')
    if not 1 <= page_size <= 100 or not 1 <= max_pages <= 20:
        raise ValueError('Bad pagination limits')
    fetch = fetcher or _github_page
    all_repos=[]
    for page in range(1,max_pages+1):
        url=f'https://api.github.com/users/{user}/starred?per_page={page_size}&page={page}'
        part=fetch(url,token=token)
        all_repos.extend(part)
        if len(part)<page_size: break
    return all_repos


def _print_rec(item: dict[str,Any], n: int) -> None:
    print(f'{n}. {item["name"]}   [{item["id"]} | {item["kind"]}]')
    print('   Value: '+item['benefit'])
    print('   Match: '+'; '.join(item['why']))
    print('   Repo:  '+item['source'])
    print('   Add:   '+item['install'])
    print('   Trust: Source/docs checked, not security or performance certified. Review before use.')


def _skill_dir() -> Path:
    here=Path(__file__).resolve()
    # Portable .agents/skills/find-karma/scripts/karma.py
    if here.parent.name=='scripts' and here.parents[1].name=='find-karma':
        return here.parents[1]
    # Development checkout, src/karma/runtime.py
    root=here.parents[2]
    path=root/'skills'/'find-karma'
    if path.is_dir(): return path
    bundled=here.parent/'portable'
    if bundled.is_dir(): return bundled
    raise FileNotFoundError('Portable skill source not found; download full source archive')


def make_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog='karma',description='FIND KARMA ☯ | Contextual AI coding skill discovery (offline by default)')
    p.add_argument('--version',action='version',version='karma '+VERSION)
    sub=p.add_subparsers(dest='command',required=True)
    f=sub.add_parser('find',help='Recommend only reviewed skills for the current project')
    f.add_argument('--project',default='.',help='Project root (read-only)')
    f.add_argument('--goal',default='',help='Immediate coding task or problem')
    f.add_argument('--agent',choices=AGENTS,default='codex')
    f.add_argument('--limit',type=int,default=5)
    f.add_argument('--json',action='store_true',help='Machine-readable output')
    l=sub.add_parser('catalog',help='List reviewed entries or include candidates')
    l.add_argument('--all',action='store_true',help='Include entries pending review')
    l.add_argument('--json',action='store_true')
    l.add_argument('--kind',choices=('skill','plugin','tool'),default=None)
    s=sub.add_parser('show',help='Print one catalog record')
    s.add_argument('id'); s.add_argument('--agent',choices=AGENTS,default='codex')
    s.add_argument('--json',action='store_true')
    i=sub.add_parser('install',help='Preview first; explicit flags required to run skills.sh installer')
    i.add_argument('id'); i.add_argument('--agent',choices=AGENTS,required=True)
    i.add_argument('--execute',action='store_true',help='Execute approved skills CLI install')
    i.add_argument('--yes',action='store_true',help='Confirm reviewed external installation')
    a=sub.add_parser('init-agent',help='Copy self-contained find-karma skill into this project')
    a.add_argument('--project',default='.')
    a.add_argument('--agent',choices=AGENTS,default='codex')
    a.add_argument('--dry-run',action='store_true'); a.add_argument('--force',action='store_true')
    d=sub.add_parser('doctor',help='Check local tooling and skill package')
    d.add_argument('--json',action='store_true')
    v=sub.add_parser('validate',help='Validate bundled catalog and safety constraints')
    v.add_argument('--json',action='store_true')
    st=sub.add_parser('sync-stars',help='Opt-in GitHub sync into UNREVIEWED candidates only')
    st.add_argument('--user',default='imMamdouhaboammar')
    st.add_argument('--project',default='.')
    st.add_argument('--max-pages',type=int,default=6)
    st.add_argument('--output',default=None,help='JSON output path; default .karma/starred-candidates.json')
    st.add_argument('--json',action='store_true')
    return p


def main(argv: list[str] | None=None) -> int:
    parser=make_parser()
    if argv is None and len(sys.argv)==1: argv=['find']
    elif argv==[]: argv=['find']
    args=parser.parse_args(argv)
    try:
        records=load_catalog()
        if args.command=='validate':
            issues=validate_catalog(records)
            if args.json: print(json.dumps({'ok':not issues,'issues':issues,'entries':len(records)}))
            else: print('Catalog OK: '+str(len(records))+' entries' if not issues else '\n'.join(issues))
            return 0 if not issues else 2
        issues=validate_catalog(records)
        if issues: raise ValueError('Bundled catalog is invalid: '+', '.join(issues[:3]))
        if args.command=='catalog':
            rows=[x for x in records if (args.all or x['status']=='reviewed') and (args.kind is None or x['kind']==args.kind)]
            if args.json: print(json.dumps(rows,ensure_ascii=False,indent=2))
            else:
                for item in rows: print(f'{item["id"]:26} {item["status"]:9} {item["kind"]:6} {item["name"]}')
                print(f'{len(rows)} catalog entries')
        elif args.command=='find':
            if not 1<=args.limit<=30: raise ValueError('--limit must be 1..30')
            signals=detect_project(Path(args.project))
            matches=find(records, signals, goal=args.goal, limit=args.limit, agent=args.agent)
            if args.json:
                print(json.dumps({'project_signals':sorted(signals),'goal_signals':sorted(_goal_signals(args.goal)),
                                  'agent':args.agent,'recommendations':matches,
                                  'install_policy':'No install executed; review sources and request approval first.'},ensure_ascii=False,indent=2))
            else:
                print('FIND KARMA ☯')
                print('Project: '+str(Path(args.project).resolve()))
                print('Signals: '+', '.join(sorted(signals)))
                if args.goal: print('Goal: '+args.goal)
                if not matches: print('No confident match. Try --goal "<specific problem>"; no arbitrary fallback installed.')
                for idx,item in enumerate(matches,1): _print_rec(item,idx)
                print('\nNothing installed. Ask user approval before using `karma install ... --execute --yes`.')
        elif args.command=='show':
            matches=[r for r in records if r['id']==args.id]
            if not matches: raise ValueError(f'Unknown id: {args.id}')
            item=matches[0]
            if args.json: print(json.dumps({**item,'install_instructions':install_instructions(item,args.agent)},indent=2))
            else:
                print(json.dumps(item,indent=2,ensure_ascii=False))
                print('Installation: '+install_instructions(item,args.agent))
        elif args.command=='install':
            entry=next((r for r in records if r['id']==args.id),None)
            if not entry: raise ValueError(f'Unknown id: {args.id}')
            if entry['status']!='reviewed': raise ValueError('Candidate not reviewed: cannot install via KARMA')
            cmd=install_argv(entry,args.agent)
            if cmd is None:
                print('Manual installation or incompatible host. Review: '+install_instructions(entry,args.agent))
                return 0 if not args.execute else 2
            print('Installation command: '+' '.join(map(shlex.quote,cmd)),flush=True)
            print('Source: '+entry['source'])
            if not args.execute:
                print('DRY RUN. Use --execute --yes only after reviewing and approving this source.')
                return 0
            if not args.yes:
                raise ValueError('Explicit --yes required with --execute; never silently install')
            if not shutil.which('npx'): raise RuntimeError('npx unavailable; install Node/npm or use the self-contained skill instead')
            print('Executing approved installer in current directory...',flush=True)
            completed=subprocess.run(cmd,check=False)
            return completed.returncode
        elif args.command=='init-agent':
            root=Path(args.project).expanduser().resolve(strict=True)
            if not root.is_dir(): raise ValueError('Project root is not a directory')
            dest=root/AGENT_PATHS[args.agent]
            # A symlink in a destination parent could escape the selected project.
            for component in [root/Path(*Path(AGENT_PATHS[args.agent]).parts[:j]) for j in range(1,len(Path(AGENT_PATHS[args.agent]).parts))]:
                if component.is_symlink(): raise ValueError('Refusing to write through a symlinked agent directory')
            if dest.resolve()==_skill_dir().resolve(): raise ValueError('Source and destination are the same directory')
            print(f'Install portable skill: {_skill_dir()} -> {dest}')
            if not args.dry_run:
                if dest.exists() and not args.force:
                    raise ValueError(f'Target exists: {dest} (use --force to replace)')
                if dest.is_symlink(): raise ValueError('Refusing to overwrite a symlink')
                shutil.copytree(_skill_dir(),dest,dirs_exist_ok=args.force)
                print('Installed. Tell the coding agent: FIND KARMA ☯')
        elif args.command=='doctor':
            data={'python':sys.version.split()[0], 'npx':shutil.which('npx'),
                  'catalog':str(catalog_path()),'records':len(records),
                  'packaged_skill':_skill_dir().is_dir()}
            if args.json: print(json.dumps(data,indent=2))
            else:
                for key,value in data.items(): print(f'{key}: {value}')
        elif args.command=='sync-stars':
            token=os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
            starred=fetch_stars(args.user,max_pages=args.max_pages,token=token)
            known={x['install']['repo'].lower() for x in records}
            candidate_list=star_candidates(starred,known)
            root=Path(args.project).expanduser().resolve(strict=True)
            if not root.is_dir(): raise NotADirectoryError(str(root))
            output=Path(args.output).expanduser() if args.output else root/'.karma'/'starred-candidates.json'
            if not output.is_absolute(): output=root/output
            output.parent.mkdir(parents=True,exist_ok=True)
            document={'source':f'https://github.com/{args.user}?tab=stars','review_status':'unreviewed',
                      'total_stars_fetched':len(starred),'candidates':candidate_list}
            output.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            summary={'stars_fetched':len(starred),'candidate_count':len(candidate_list),'saved_to':str(output),'installed':False,'promoted':False}
            if args.json: print(json.dumps(summary,indent=2))
            else: print(f'Fetched {len(starred)} stars; wrote {len(candidate_list)} UNREVIEWED candidates to {output}. Nothing installed or promoted.')
        return 0
    except (OSError,ValueError,RuntimeError) as exc:
        print('karma: '+str(exc),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
