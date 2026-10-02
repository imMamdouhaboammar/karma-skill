"""Explicit, reviewable seed. This is NOT a dump of every starred repository.

Provenance: public GitHub starred listings sampled on 2026-10-02 and repo root/README
checks for reviewed entries. 'reviewed' means source structure/docs inspected,
NOT proof of downstream performance or security audit.
"""
import json
from pathlib import Path

items=[]

def add(id, repo, name, lane, benefit, signals, tags='', *, kind='skill',method='skills',skill=None,hosts=None,status='reviewed',provenance='user-stars',instructions=None):
    entry={
        'id':id,'name':name, 'source':f'https://github.com/{repo}',
        'kind':kind, 'lane':lane,'summary':benefit.split('.')[0]+'.',
        'benefit':benefit,'signals':signals.split(),
        'tags':tags.lower().split(), 'status':status, 'provenance':provenance,
        'evidence':f'https://github.com/{repo}#readme',
        'review_note':'Repository structure and/or README inspected. No independent benchmark or security guarantee.' if status=='reviewed' else 'Starred or surfaced; installation path and claims still need review.',
        'install': {'method':method, 'repo':repo}
    }
    if skill: entry['install']['skill']=skill
    if hosts: entry['hosts']=hosts
    if instructions: entry['install']['instructions']=instructions
    items.append(entry)

add('matt-engineering','mattpocock/skills','Matt Pocock Engineering Skills','engineering','Focused engineering routines for requirement clarification, architecture, TDD and review.','task:planning task:testing task:architecture task:review language:typescript','engineering review tdd typescript')
add('matt-tdd','mattpocock/skills','Matt TDD','testing','Structured red-green-refactor cycles for code changes, guided by meaningful test evidence.','task:testing task:debugging task:quality','tdd tests regression',skill='tdd')
add('trailofbits-security','trailofbits/skills','Trail of Bits Security Marketplace','security','Specialist code-audit plugins including differential review, static analysis and supply-chain risk.','task:security task:review task:ci language:rust','security audit threat',kind='plugin',method='manual',instructions='/plugin marketplace add trailofbits/skills (Claude Code); then /plugin menu. Codex: codex plugin marketplace add trailofbits/skills, then codex plugin list and choose a plugin.')
add('claude-plugin-review','trailofbits/skills','Trail of Bits Claude Plugins','claude-workflow','Browse selective security plugins inside Claude Code instead of bulk installing.','task:security task:review','claude plugins security',kind='plugin',method='manual',hosts=['claude-code'],instructions='/plugin marketplace add trailofbits/skills; /plugin menu; select only required plugin.')
add('science-skills','K-Dense-AI/scientific-agent-skills','Scientific Agent Skills','research','Domain workflows for experiment and scientific research tasks.','task:research language:python task:statistics','research experiments scientific')
add('motion-graphics','imMamdouhaboammar/motion-graphics-skills','Motion Graphics Skills','motion','Creative direction and programmatic animation production using a large skills pack.','task:motion task:video task:design','motion animation video graphics')
add('dokion','imMamdouhaboammar/dokion','Dokion Playbook Runtime','governance','User-authored hardening playbooks with explicit approvals and independent verification.','task:security task:quality task:governance task:ci','playbooks governance security',kind='tool',method='manual',instructions='Docs specify bun add --global dokion@0.3.0 (requires Bun >=1.3.14). Read the compatibility matrix and approve playbook before running.')
add('agent-kernel','imMamdouhaboammar/agent-kernel','Agent Kernel','governance','Persistent agent governance, memory, lessons and guardrails within coding repos.','task:governance task:orchestration task:architecture','memory governance agent')
add('delegate-team','imMamdouhaboammar/delegate-team','Delegate Team','orchestration','Task routing and bounded multi-agent engineering collaboration.','task:orchestration task:planning task:review','orchestration delegation agents')
add('skill-scanner','cisco-ai-defense/skill-scanner','Cisco Skill Scanner','skill-security','Scan skill packages for suspicious instructions and risks before adoption.','task:skills task:security task:plugin','skills scanner supplychain',kind='tool',method='manual',instructions='Follow pinned instructions in repository README; review scanner findings before installing any third-party skill.')
add('skillspector','NVIDIA/SkillSpector','NVIDIA SkillSpector','skill-security','Security analysis for agent skill files and prompt-driven risks.','task:skills task:security task:plugin','skill security audit',kind='tool',method='manual',instructions='Use the documented SkillSpector CLI in its README after checking Python/runtime requirements.')
add('eval-skills','ai-evals-course/evals-skills','AI Evals Skills','evaluation','Plan and implement product-specific AI evaluations and measurable checks.','task:evals task:testing task:llm task:research','evals testing llm')
add('council','kitze/council','Council','collaboration','Solicit explicit multi-agent viewpoints during demanding planning or design decisions.','task:architecture task:planning task:orchestration','architecture planning secondopinion')
add('ui-skills','ibelick/ui-skills','UI Skills','frontend-quality','Design engineering skill guidance for visual polish and interface quality.','task:frontend framework:react language:typescript task:design','ui frontend design')
add('daymade-claude','daymade/claude-code-skills','daymade Claude Skills','workflow','Specialized workflows for repo maintenance, QA, research and visual verification.','task:debugging task:review task:frontend task:qa','claude qa review skills',method='manual',instructions='Inspect the repo skills and plugin manifest, and select the specific skill via README or the skills CLI --list mode.')
add('portfolio-interview','imMamdouhaboammar/portfolio-interview','Portfolio Interview','frontend-quality','Interactive intake and portfolio implementation guidance.','task:portfolio task:frontend task:design','portfolio design frontend')
add('skill-building','Songhonglei/build-better-skills','Build Better Skills','skill-authoring','Procedures to write, test, review and release agent skills.','task:skills task:plugin task:testing','skills author evals')
add('stark-skills','stark-ai-de/agent-skills','Stark Agent Skills','workflow','Operator workflows for codebase maintenance across multiple coding agents.','task:review task:quality task:architecture','agents workflows maintenance')
add('vercel-agent-skills','vercel-labs/agent-skills','Vercel Agent Skills','frontend-quality','React and Next.js-focused coding practices and web design review workflows.','framework:nextjs framework:react task:frontend','react nextjs frontend',provenance='ecosystem-docs')
add('find-skills','vercel-labs/skills','Vercel Find Skills','discovery','General ecosystem search for agent skills when KARMA catalog lacks a suitable match.','task:skills task:plugin task:discovery','skill discovery search',skill='find-skills',provenance='ecosystem-docs')
add('motion-hyperframes','heygen-com/hyperframes','HyperFrames','motion-runtime','Video rendering engine and reusable motion production components; not itself proof of finished video quality.','task:motion task:video language:typescript','hyperframes animation render',provenance='ecosystem-docs')
# Initial starred sources not yet subjected to the same repository-level verification.
add('security-audit','teng-lin/security-audit-skill','Security Audit Skill','security','Multi-phase code security auditing workflow.','task:security task:review','security audit',status='candidate')
add('oss-maintainer','Git-on-my-level/oss-maintainer','OSS Maintainer','maintenance','Review and triage recurring open-source maintenance work.','task:ci task:review','oss maintenance',status='candidate')
add('review-super','OmniTensorLabs/SuperReview','SuperReview','review','Evidence-oriented code review workflows.','task:review task:quality','code review',status='candidate')
add('quality-gate','smixs/code-quality','Code Quality Gate','testing','Local code quality gates and linting workflow.','task:quality task:testing','quality lint',status='candidate')
add('responsive-craft','kylezantos/responsive-craft','Responsive Craft','frontend-quality','Responsive interface review for in-between viewport sizes.','task:frontend task:design','responsive ui',status='candidate')
add('agent-browser','Tencent/BrowserSkill','BrowserSkill','browser','Use existing logged-in browsers for test and inspection tasks with appropriate permissions.','task:browser task:qa task:frontend','browser automation',status='candidate')
add('jev-router','himomohi/jev-skill-router','Jev Skill Router','discovery','Route large skill catalogs without loading all skill instructions into context.','task:skills task:discovery','skills routing',status='candidate')
add('design-system','fracazo/design-system','Agent Native Design System','design-system','Keep reusable UI decisions and tokens machine-readable for agents.','task:frontend task:design','design tokens',status='candidate')
add('spec-evidence','GanyuanRan/Aegis','Aegis','architecture','Compare architectural baseline and evidence for drift.','task:architecture task:quality','architecture evidence',status='candidate')
add('scientific-openresearch','alphaXiv/OpenResearch','OpenResearch','research','Research tooling inside coding agent workflows.','task:research task:llm','research scientific',status='candidate')
add('mcp-scenarios','inity13/scenariosim-mcp','ScenarioSim MCP','simulation','Scenario simulations for project decision evaluation; setup and data handling need review.','task:statistics task:research','simulation mcp',status='candidate',kind='plugin')
add('frontend-design-polish','Nutlope/hallmark','Hallmark Design','frontend-quality','Review visual conventions and reduce generic interface patterns.','task:frontend task:design','frontend polish',status='candidate')
add('trufflehog','trufflesecurity/trufflehog','TruffleHog','security-scan','Secret discovery and exposed credential analysis.','task:security task:ci','secrets scan',status='candidate',kind='tool')
add('skills-manager','xingkongliang/skills-manager','Skills Manager','discovery','Manage agent skill inventories across coding clients.','task:skills task:plugin','skills management',status='candidate',kind='tool')
add('skillware','ARPAHLS/skillware','Skillware','skill-authoring','Framework for modular programmatic skills.','task:skills task:architecture','skills framework',status='candidate',kind='tool')

for item in items:
    if item['id'] in ('skill-scanner','skillspector'):
        item['require_any']=['task:skills','task:plugin']
    if item['id']=='delegate-team':
        item['require_any']=['task:orchestration']
    if item['id']=='dokion':
        item['require_any']=['task:governance','task:security']
    if item['id']=='daymade-claude':
        item['signals'].remove('task:frontend')
root=Path(__file__).resolve().parents[1]
(root/'catalog/curated.json').write_text(json.dumps({'schema_version':1,'updated':'2026-10-02','review_policy':'Docs/structure review, not guaranteed performance; candidates excluded from recommendations.','items':items},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(f'Seeded {len(items)} records: {sum(x["status"]=="reviewed" for x in items)} reviewed; {sum(x["status"]=="candidate" for x in items)} candidates')
