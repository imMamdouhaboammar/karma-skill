"""Offline two-commit supply-chain fixtures; never fetch third-party code."""
import contextlib
import io
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from karma import mcp_service, runtime
from scripts import check_reviewed_drift as drift


def git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, check=True, text=True,
                          capture_output=True).stdout.strip()


class ReviewIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'source'
        self.repo.mkdir()
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.email', 'fixture@example.invalid')
        git(self.repo, 'config', 'user.name', 'Fixture')
        self.skill = self.repo / 'skills' / 'tdd'
        self.skill.mkdir(parents=True)
        (self.skill / 'SKILL.md').write_text('---\nname: tdd\n---\nreviewed fixture\n')
        (self.skill / 'script.txt').write_text('reviewed contents')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'reviewed')
        self.reviewed_sha = git(self.repo, 'rev-parse', 'HEAD')
        (self.skill / 'SKILL.md').write_text('---\nname: tdd\n---\nUNREVIEWED HEAD\n')
        (self.skill / 'script.txt').write_text('unreviewed contents')
        git(self.repo, 'commit', '-qam', 'changed after review')
        self.head_sha = git(self.repo, 'rev-parse', 'HEAD')

    def record(self, **changes):
        item = {
            'id':'tdd-fixture', 'name':'Fixture', 'source':'https://github.com/fixture/skills',
            'kind':'skill', 'lane':'testing', 'summary':'Fixture', 'benefit':'Fixture',
            'signals':['task:testing'], 'tags':['tdd'], 'status':'reviewed',
            'reviewed_revision':self.reviewed_sha, 'reviewed_path':'skills/tdd',
            'reviewed_at':'2026-10-23T00:00:00Z',
            'evidence':f'https://github.com/fixture/skills/blob/{self.reviewed_sha}/skills/tdd/SKILL.md',
            'install':{'method':'skills', 'repo':'fixture/skills','skill':'tdd'},
        }
        item.update(changes)
        return item

    def test_actual_checkout_is_first_commit_despite_mutable_head(self):
        checkout = self.root / 'checkout'
        checkout.mkdir()
        runtime._checkout_revision(str(self.repo),self.reviewed_sha,checkout,allow_local=True)
        self.assertEqual(git(checkout,'rev-parse','HEAD'), self.reviewed_sha)
        self.assertEqual((checkout/'skills/tdd/script.txt').read_text(), 'reviewed contents')
        self.assertNotEqual(self.reviewed_sha,self.head_sha)

    def test_installer_copies_exact_reviewed_files_without_running_skills_cli(self):
        project = self.root / 'project'
        project.mkdir()
        actual_checkout = runtime._checkout_revision
        def fixture_checkout(_url, revision, path):
            return actual_checkout(str(self.repo),revision,path,allow_local=True)
        with patch('karma.runtime._checkout_revision',side_effect=fixture_checkout), patch('shutil.which',return_value='/usr/bin/git'):
            dest = runtime._install_reviewed(self.record(),'codex',project)
        self.assertEqual(dest, project/'.agents/skills/tdd')
        self.assertEqual((dest/'script.txt').read_text(), 'reviewed contents')
        self.assertNotIn('UNREVIEWED', (dest/'SKILL.md').read_text())
        with patch('karma.runtime._checkout_revision',side_effect=fixture_checkout):
            with self.assertRaisesRegex(ValueError,'Destination exists'):
                # Existing destination is never overwritten (even if the pinned checkout succeeds).
                runtime._install_reviewed(self.record(),'codex',project)

    def test_schema_fails_closed_on_invalid_review_identity(self):
        cases = [
            ('missing SHA', {'reviewed_revision':None}),
            ('short SHA', {'reviewed_revision':'a'*12}),
            ('bad hex', {'reviewed_revision':'z'*40}),
            ('mutable tag', {'reviewed_revision':'v1.0.0'}),
            ('missing evidence', {'evidence':''}),
            ('wrong SHA evidence', {'evidence':'https://github.com/fixture/skills/blob/main/skills/tdd/SKILL.md'}),
            ('path traversal', {'reviewed_path':'../malicious'}),
            ('unsafe repo', {'install':{'method':'skills','repo':'fixture/skills;evil'}}),
            ('wrong repo identity', {'source':'https://github.com/other/repo'}),
            ('wrong skill selector', {'install':{'method':'skills','repo':'fixture/skills','skill':'other'}}),
            ('manual method', {'install':{'method':'manual','repo':'fixture/skills'}}),
            ('missing time', {'reviewed_at':None}),
            ('unparseable time', {'reviewed_at':'yesterday'}),
            ('unaware time', {'reviewed_at':'2026-10-23T00:00:00'}),
            ('future time', {'reviewed_at':'2099-01-01T00:00:00Z'}),
        ]
        self.assertEqual(runtime.validate_catalog([self.record()]), [])
        for label,changes in cases:
            with self.subTest(label=label):
                item=self.record(**changes)
                self.assertTrue(runtime.validate_catalog([item]))
                with self.assertRaises(ValueError):
                    runtime.install_argv(item,'codex')

    def test_candidate_requires_no_revision_and_cannot_install(self):
        candidate=self.record(status='candidate', reviewed_revision=None, reviewed_at=None)
        self.assertEqual(runtime.validate_catalog([candidate]), [])
        with self.assertRaises(ValueError):
            runtime.install_argv(candidate,'codex')
        self.assertIn('Unreviewed candidate',runtime.install_instructions(candidate,'codex'))

    def test_offline_guidance_contains_real_reviewed_sha_and_no_mutable_installer(self):
        guide = runtime.install_instructions(self.record(),'codex')
        self.assertIn(self.reviewed_sha, guide)
        self.assertIn('karma install tdd-fixture', guide)
        self.assertNotIn('skills add', guide)
        with patch('subprocess.run',side_effect=AssertionError('unexpected process')):
            self.assertEqual(runtime.install_instructions(self.record(),'codex'),guide)

    def test_fetch_missing_revision_never_mistakes_head_for_target(self):
        checkout=self.root/'missing'
        checkout.mkdir()
        with self.assertRaises(subprocess.CalledProcessError):
            runtime._checkout_revision(str(self.repo),'f'*40,checkout,allow_local=True)

    def test_symlinked_source_skill_is_rejected(self):
        checkout=self.root/'link-checkout'
        checkout.mkdir()
        (checkout/'skills').mkdir()
        (checkout/'skills/tdd').symlink_to(self.skill,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):
            runtime._checked_skill_path(checkout,'skills/tdd')

    def test_shell_metacharacters_never_reach_install_or_guidance(self):
        item=self.record(reviewed_path='skills/tdd;touch-pwned')
        self.assertTrue(runtime.validate_catalog([item]))
        with self.assertRaises(ValueError):
            runtime.install_instructions(item,'codex')

    def test_mcp_offline_no_unreviewed_install_or_network(self):
        with patch('subprocess.run',side_effect=AssertionError('subprocess')) as proc, patch('urllib.request.urlopen',side_effect=AssertionError('network')) as net:
            guide=mcp_service.get_skill_guide('matt-tdd')
            result=mcp_service.recommend_skills('React frontend quality',project_signals=['framework:react'])
        self.assertEqual(guide['drift_status'],'not_checked_offline')
        self.assertTrue(result['recommendations'])
        self.assertTrue(all(r['reviewed_revision'] for r in result['recommendations']))
        proc.assert_not_called()
        net.assert_not_called()

    def test_live_drift_probe_detects_new_head_without_promoting_it(self):
        results=drift.check_repository(str(self.repo),[self.record()],allow_local=True)
        self.assertEqual(results[0]['status'],'upstream_changed')
        self.assertEqual(results[0]['observed_head'],self.head_sha)
        self.assertEqual(results[0]['reviewed_revision'],self.reviewed_sha)

    def test_unchanged_reviewed_head_is_distinguished_from_drift(self):
        current=self.record(reviewed_revision=self.head_sha)
        result=drift.check_repository(str(self.repo),[current],allow_local=True)
        self.assertEqual(result[0]['status'],'unchanged')

    def test_missing_path_is_not_reported_as_current_or_safe(self):
        git(self.repo,'rm','-r','skills/tdd')
        git(self.repo,'commit','-qm','remove reviewed path')
        result=drift.check_repository(str(self.repo),[self.record()],allow_local=True)
        self.assertEqual(result[0]['status'],'skill_path_missing')

    def test_unavailable_source_does_not_count_as_verification(self):
        result=drift.check_repository(str(self.root/'absent'),[self.record()],allow_local=True)
        self.assertEqual(result[0]['status'],'source_unavailable')
        self.assertIsNone(result[0]['observed_head'])

    def test_offline_drift_command_does_not_launch_git(self):
        buf=io.StringIO()
        with patch('subprocess.run',side_effect=AssertionError('git was launched')):
            with contextlib.redirect_stdout(buf):
                self.assertEqual(drift.main([]),0)
        result=__import__('json').loads(buf.getvalue())
        self.assertFalse(result['network_enabled'])
        self.assertFalse(result['promoted'])
        self.assertTrue(all(x['status']=='not_checked_offline' for x in result['results']))

    def test_all_portable_catalogs_match_reviewed_source(self):
        root=Path(__file__).resolve().parents[1]
        canonical=(root/'catalog/curated.json').read_bytes()
        for relative in ('src/karma/catalog.json','skills/find-karma/assets/catalog.json',
                         'src/karma/portable/assets/catalog.json',
                         'src/karma/portable/find-karma/assets/catalog.json'):
            with self.subTest(relative=relative):
                self.assertEqual((root/relative).read_bytes(),canonical)


if __name__ == '__main__':
    unittest.main()
