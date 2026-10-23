import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from karma import runtime


class KarmaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, rel, content=''):
        f = self.root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding='utf-8')

    def test_detect_next_and_typescript_without_reading_source(self):
        self.write('package.json', '{"dependencies":{"next":"^15.0.0","react":"^19.0.0"},"devDependencies":{"typescript":"^5.0.0"}}')
        self.write('app/page.tsx', 'export default function Page(){}')
        got = runtime.detect_project(self.root)
        self.assertIn('framework:nextjs', got)
        self.assertIn('language:typescript', got)
        self.assertIn('task:frontend', got)

    def test_security_goal_dominates_irrelevant_motion(self):
        self.write('Cargo.toml', '[package]\nname="safe"\nversion="0.1.0"')
        found = runtime.find(runtime.load_catalog(), runtime.detect_project(self.root), goal='security audit secrets', limit=5)
        self.assertTrue(found)
        self.assertTrue(all(item['reviewed_revision'] for item in found))
        self.assertNotIn('motion-graphics', [x['id'] for x in found])

    def test_find_results_include_reasons_and_install_instructions(self):
        self.write('package.json', '{"dependencies":{"react":"^19.0.0"}}')
        out = runtime.find(runtime.load_catalog(), runtime.detect_project(self.root), goal='frontend ui quality', limit=4)
        self.assertTrue(out)
        for item in out:
            self.assertTrue(item['why'])
            self.assertTrue(item['install'])
            self.assertTrue(item['source'].startswith('https://github.com/'))

    def test_no_unreviewed_candidates_in_curated_ranking(self):
        item = {'id':'bad', 'name':'Bad', 'source':'https://github.com/x/y', 'kind':'skill', 'status':'candidate', 'signals':['task:frontend'], 'tags':[], 'install':{'method':'skills','repo':'x/y'}}
        self.assertEqual(runtime.find([item], {'task:frontend'}, goal='frontend'), [])

    def test_invalid_catalog_rejects_malicious_install_source(self):
        item = {'id':'mal', 'name':'Malicious', 'source':'https://github.com/good/repo', 'kind':'skill', 'status':'reviewed', 'summary':'ok','benefit':'ok','signals':['task:security'], 'tags':['security'], 'lane':'security','install':{'method':'skills','repo':'good/repo;rm -rf /'}}
        self.assertTrue(runtime.validate_catalog([item]))
        with self.assertRaises(ValueError):
            runtime.install_argv(item, 'codex')

    def test_install_is_dry_run_by_default(self):
        item = next(x for x in runtime.load_catalog() if x['id']=='matt-tdd')
        argv = runtime.install_argv(item, 'codex')
        self.assertEqual(argv[:3], ['karma', 'install', 'matt-tdd'])
        self.assertIn('--execute', argv)
        self.assertNotIn('sh', argv)

    def test_agent_only_entry_does_not_install_in_wrong_host(self):
        item = next(x for x in runtime.load_catalog() if x['id']=='matt-tdd')
        item = {**item, 'hosts':['claude-code']}
        self.assertIsNone(runtime.install_argv(item, 'codex'))

    def test_diversify_recommendations(self):
        corpus = runtime.load_catalog()
        found = runtime.find(corpus, {'task:frontend','language:typescript'}, goal='frontend ui polish',limit=5)
        lanes = [x['lane'] for x in found]
        self.assertEqual(len(lanes),len(set(lanes)))

    def test_strict_goal_evidence_is_opt_in_for_mcp_without_changing_cli_find(self):
        catalog = runtime.load_catalog()
        project_only = next(x for x in catalog if x['id'] == 'matt-tdd').copy()
        relevant = next(x for x in catalog if x['id'] == 'ui-master').copy()
        project_only.update(signals=['task:testing', 'task:review', 'language:typescript'], tags=[])
        relevant.update(signals=['task:frontend'], tags=['wcag', 'accessibility'])
        signals = {'task:frontend', 'task:testing', 'task:review', 'language:typescript'}
        ordinary = runtime.find([project_only, relevant], signals, goal='wcag accessibility', limit=1)
        strict = runtime.find([project_only, relevant], signals, goal='wcag accessibility',
                              limit=1, require_goal_evidence=True)
        self.assertEqual([item['id'] for item in ordinary], ['matt-tdd'])
        self.assertEqual([item['id'] for item in strict], ['ui-master'])

    def test_stars_classified_as_candidates_not_curated(self):
        repos = [{'full_name':'invented/skillpack','html_url':'https://github.com/invented/skillpack','description':'skills for python'}]
        out=runtime.star_candidates(repos, {x['source'].removeprefix('https://github.com/') for x in runtime.load_catalog()})
        self.assertEqual(out[0]['status'],'candidate')
        self.assertEqual(out[0]['repo'],'invented/skillpack')
        self.assertTrue(out[0]['likely_skill'])

    def test_star_sync_paginates_and_stops_on_short_page(self):
        pages=[]
        def fake_fetch(url,token=None):
            pages.append(url)
            return [{'full_name':f'org/repo{i}', 'html_url':f'https://github.com/org/repo{i}', 'description':'agent skill'} for i in range(2)]
        out=runtime.fetch_stars('user',page_size=100,max_pages=6,fetcher=fake_fetch)
        self.assertEqual(len(out),2)
        self.assertEqual(len(pages),1)

    def test_readonly_find_has_no_side_effects(self):
        self.write('package.json','{}')
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*'))
        runtime.find(runtime.load_catalog(),runtime.detect_project(self.root),goal='testing')
        after = sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*'))
        self.assertEqual(before, after)

    def test_json_cli_valid(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = runtime.main(['find','--project',str(self.root),'--goal','security','--json'])
        self.assertEqual(rc,0)
        data=json.loads(out.getvalue())
        self.assertIn('recommendations',data)
        self.assertIn('project_signals',data)

    def test_init_agent_only_writes_selected_project_folder(self):
        rc = runtime.main(['init-agent','--project',str(self.root),'--agent','codex'])
        self.assertEqual(rc,0)
        self.assertTrue((self.root/'.agents/skills/find-karma/SKILL.md').exists())
        self.assertFalse((self.root/'.claude/skills/find-karma').exists())
        self.assertTrue((self.root/'.agents/skills/find-karma/scripts/karma.py').exists())

    def test_install_command_previews_without_execution(self):
        with patch('subprocess.run') as run:
            result=runtime.main(['install','matt-tdd','--agent','codex'])
            self.assertEqual(result,0)
            run.assert_not_called()

    def test_security_audit_does_not_suggest_skill_scanner_without_skill_context(self):
        self.write('pyproject.toml','[project]\nname="a"')
        out=runtime.find(runtime.load_catalog(),runtime.detect_project(self.root),goal='security audit',limit=8)
        names=[x['id'] for x in out]
        self.assertNotIn('skill-scanner', names)
        self.assertNotIn('skillspector', names)

    def test_results_do_not_repeat_same_repo(self):
        out=runtime.find(runtime.load_catalog(),{'task:review'},goal='security audit',agent='claude-code',limit=10)
        sources=[x['source'] for x in out]
        self.assertEqual(len(sources),len(set(sources)))

    def test_ui_skills_preferred_to_general_repo_maintenance_for_ui_work(self):
        self.write('package.json','{"dependencies":{"react":"^19","typescript":"^5"}}')
        out=runtime.find(runtime.load_catalog(),runtime.detect_project(self.root),goal='frontend UI quality review',limit=5)
        self.assertEqual(out[0]['lane'],'frontend-quality')

    def test_explicit_frontend_goal_does_not_include_weak_generic_quality_matches(self):
        self.write('package.json','{"dependencies":{"next":"^15","react":"^19"}}')
        out=runtime.find(runtime.load_catalog(),runtime.detect_project(self.root),goal='React UI quality',limit=10)
        self.assertNotIn('matt-tdd',[x['id'] for x in out])
        self.assertNotIn('stark-skills',[x['id'] for x in out])

    def test_init_agent_denies_symlinked_target_parent(self):
        outside=tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        (self.root/'.agents').symlink_to(outside.name,target_is_directory=True)
        result=runtime.main(['init-agent','--project',str(self.root),'--agent','codex'])
        self.assertEqual(result,2)
        self.assertFalse((Path(outside.name)/'skills').exists())

    def test_external_symlinks_not_followed(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        Path(outside.name,'secret.py').write_text('')
        (self.root/'node_modules').symlink_to(outside.name, target_is_directory=True)
        signals=runtime.detect_project(self.root)
        self.assertNotIn('language:python', signals)

    def test_init_agent_supports_windsurf(self):
        rc = runtime.main(['init-agent', '--project', str(self.root), '--agent', 'windsurf'])
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / '.windsurf/skills/find-karma/SKILL.md').exists())
        self.assertTrue((self.root / '.windsurf/skills/find-karma/scripts/karma.py').exists())

    def test_init_alias_supports_all_agents(self):
        rc = runtime.main(['init', '--project', str(self.root), '--agent', 'claude-code'])
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / '.claude/skills/find-karma/SKILL.md').exists())

    def test_init_dry_run_does_not_mutate_disk(self):
        rc = runtime.main(['init', '--project', str(self.root), '--agent', 'cursor', '--dry-run'])
        self.assertEqual(rc, 0)
        self.assertFalse((self.root / '.cursor/skills/find-karma').exists())

    def test_init_force_allows_overwrite(self):
        # first init
        rc1 = runtime.main(['init', '--project', str(self.root), '--agent', 'gemini'])
        self.assertEqual(rc1, 0)
        # re-init without force fails
        rc2 = runtime.main(['init', '--project', str(self.root), '--agent', 'gemini'])
        self.assertEqual(rc2, 2)
        # re-init with force succeeds
        rc3 = runtime.main(['init', '--project', str(self.root), '--agent', 'gemini', '--force'])
        self.assertEqual(rc3, 0)

    def test_install_execute_without_yes_raises_error(self):
        with patch('subprocess.run') as mock_run:
            rc = runtime.main(['install', 'matt-tdd', '--agent', 'codex', '--execute'])
            self.assertEqual(rc, 2)
            mock_run.assert_not_called()

    def test_install_unreviewed_candidate_raises_error(self):
        # Even if someone asks to install an unreviewed candidate, it must be rejected
        with patch('karma.runtime.load_catalog', return_value=[{
            'id': 'cand', 'name': 'Candidate', 'source': 'https://github.com/a/b',
            'kind': 'skill', 'status': 'candidate', 'signals': ['task:security'],
            'tags': ['security'], 'lane': 'security', 'summary': 's', 'benefit': 'b',
            'evidence': 'e', 'install': {'method': 'skills', 'repo': 'a/b'}
        }]):
            rc = runtime.main(['install', 'cand', '--agent', 'codex'])
            self.assertEqual(rc, 2)

    def test_install_approved_runs_expected_cmd(self):
        with patch('karma.runtime._install_reviewed', return_value=self.root/'installed') as verified, patch('shutil.which', return_value='/usr/bin/git'):
            rc = runtime.main(['install', 'matt-tdd', '--agent', 'codex', '--execute', '--yes'])
            self.assertEqual(rc, 0)
            verified.assert_called_once()
            self.assertEqual(verified.call_args.args[0]['id'], 'matt-tdd')
            self.assertEqual(verified.call_args.args[1], 'codex')

    def test_detect_database_signals_from_prisma_and_supabase(self):
        self.write('prisma/schema.prisma', 'datasource db { provider = "postgresql" }')
        got = runtime.detect_project(self.root)
        self.assertIn('task:database', got)

    def test_goal_signals_detect_database_docs_and_devops(self):
        db_signs = runtime._goal_signals('postgres schema migration with supabase')
        self.assertIn('task:database', db_signs)

        docs_signs = runtime._goal_signals('co-authoring documentation and technical specs')
        self.assertIn('task:docs', docs_signs)

        devops_signs = runtime._goal_signals('multi-stage docker container deploy')
        self.assertIn('task:devops', devops_signs)

    def test_init_agent_supports_ui_master(self):
        rc = runtime.main(['init-agent', '--project', str(self.root), '--agent', 'claude-code', '--skill', 'ui-master'])
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / '.claude/skills/ui-master/SKILL.md').exists())
        self.assertTrue((self.root / '.claude/skills/ui-master/agents/claude-code.md').exists())
        self.assertTrue((self.root / '.claude/skills/ui-master/scripts/bridge.py').exists())

    def test_init_agent_supports_vscode_and_copilot(self):
        rc1 = runtime.main(['init-agent', '--project', str(self.root), '--agent', 'vscode', '--skill', 'ui-master'])
        self.assertEqual(rc1, 0)
        self.assertTrue((self.root / '.vscode/skills/ui-master/SKILL.md').exists())

        rc2 = runtime.main(['init-agent', '--project', str(self.root), '--agent', 'copilot', '--skill', 'ui-master'])
        self.assertEqual(rc2, 0)
        self.assertTrue((self.root / '.github/skills/ui-master/SKILL.md').exists())

    def test_init_agent_all_installs_both_skills(self):
        rc = runtime.main(['init-agent', '--project', str(self.root), '--agent', 'antigravity', '--skill', 'all'])
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / '.agent/skills/find-karma/SKILL.md').exists())
        self.assertTrue((self.root / '.agent/skills/ui-master/SKILL.md').exists())

    def test_find_recommends_ui_master_for_crx_and_wcag(self):
        recs = runtime.find(runtime.load_catalog(), set(), goal='Chrome Extension popup WCAG contrast audit and anti-slop', limit=5)
        ids = [x['id'] for x in recs]
        self.assertIn('ui-master', ids)


if __name__=='__main__':
    unittest.main()



