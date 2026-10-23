"""Compiled-engine smoke tests, enabled by UIM_TEST_RUST=1 in CI."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
LAUNCHER = REPO / 'skills/ui-master/scripts/uim'
PORTABLE_LAUNCHER = REPO / 'src/karma/portable/ui-master/scripts/uim'
ENGINE = REPO / 'crates/ui-master-engine/target/debug/ui-master-engine'


@unittest.skipUnless(os.environ.get('UIM_TEST_RUST') == '1', 'Requires the compiled Rust engine')
class UIMNativeSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='uim native smoke ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = {**os.environ, 'HOME': str(self.root)}
        self.env.pop('UIM_CARGO_RUN', None)
        self.assertTrue(ENGINE.is_file(), 'cargo build the debug engine before smoke tests')

    def run_uim(self, *args, launcher=LAUNCHER, input=None, env=None):
        return subprocess.run(
            ['/bin/bash', str(launcher), *args], cwd=self.root,
            env=env or self.env, input=input, text=True, capture_output=True, timeout=10,
        )

    def test_source_commands_reach_actual_rust_engine(self):
        contrast = self.run_uim('contrast', '#ffffff', '#000000', '--json')
        self.assertEqual(contrast.returncode, 0, contrast.stderr)
        self.assertEqual(json.loads(contrast.stdout)['ratio'], 21.0)

        target = self.root / 'component.tsx'
        target.write_text('<button className="outline-none">Next</button>')
        audit = self.run_uim('audit', str(target), '--json')
        self.assertEqual(audit.returncode, 0, audit.stderr)
        self.assertGreater(json.loads(audit.stdout)['violations_count'], 0)
        self.assertIs(json.loads(audit.stdout)['complete'], True)
        self.assertEqual(json.loads(audit.stdout)['engine'], 'rust')
        self.assertEqual(len(json.loads(audit.stdout)['supported_rules']), 6)
        self.assertEqual(json.loads(audit.stdout)['unavailable_rules'], [])

        extension = self.root / 'extension folder'
        extension.mkdir()
        (extension / 'manifest.json').write_text('{"manifest_version":3}')
        crx = self.run_uim('crx', str(extension), '--json')
        self.assertEqual(crx.returncode, 0, crx.stderr)
        self.assertTrue(json.loads(crx.stdout)['is_manifest_v3'])

        registry = self.root / '.gemini/antigravity/ui-skills-catalog/registry.json'
        registry.parent.mkdir(parents=True)
        registry.write_text(json.dumps({'registry': [
            {'slug': 'micro-interactions', 'name': 'Micro Interactions',
             'topics': ['motion'], 'description': 'motion details'},
        ]}))
        skills = self.run_uim('skills', 'micro-interactions', '--json')
        self.assertEqual(skills.returncode, 0, skills.stderr)
        self.assertEqual(json.loads(skills.stdout)[0]['slug'], 'micro-interactions')

    def test_actual_rust_mcp_stdio_handshake(self):
        request = {"jsonrpc": "2.0", "id": 41, "method": "initialize",
                   "params": {"protocolVersion": "2024-11-05"}}
        result = self.run_uim('mcp', input=json.dumps(request) + '\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 1, f'Unexpected stdout: {result.stdout!r}')
        response = json.loads(lines[0])
        self.assertEqual(response['id'], 41)
        self.assertEqual(response['result']['serverInfo']['name'], 'ui-master-rig')

    def test_native_help_lists_mcp_mode(self):
        result = self.run_uim('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('mcp', result.stdout)
        self.assertIn('stdio', result.stdout)

    def test_native_capability_probe_matches_complete_audit(self):
        probe = subprocess.run(
            [str(ENGINE), 'audit-contract', '--json'],
            text=True, capture_output=True, timeout=5,
        )
        self.assertEqual(probe.returncode, 0, probe.stderr)
        contract = json.loads(probe.stdout)
        self.assertEqual(contract['audit_contract'], 'comprehensive-v1')
        report = self.run_uim('audit', str(REPO / 'tests/fixtures/ui_audit/clean.tsx'), '--json')
        self.assertEqual(report.returncode, 0, report.stderr)
        self.assertEqual(contract['supported_rules'], json.loads(report.stdout)['supported_rules'])

    def test_native_audit_errors_never_look_clean(self):
        missing = self.run_uim('audit', str(self.root / 'missing.tsx'), '--json')
        self.assertEqual(missing.returncode, 2, missing.stderr)
        self.assertIs(json.loads(missing.stdout)['complete'], False)

        empty = self.root / 'empty'
        empty.mkdir()
        (empty / 'readme.md').write_text('unsupported')
        unsupported = self.run_uim('audit', str(empty), '--json')
        self.assertEqual(unsupported.returncode, 2, unsupported.stderr)
        self.assertIs(json.loads(unsupported.stdout)['complete'], False)

        bad = self.root / 'bad.tsx'
        bad.write_bytes(b'\xff\xfe')
        unreadable = self.run_uim('audit', str(bad), '--json')
        self.assertEqual(unreadable.returncode, 70, unreadable.stderr)
        self.assertIs(json.loads(unreadable.stdout)['complete'], False)

        unknown_flag = self.run_uim('audit', str(bad), '--unknown', '--json')
        self.assertEqual(unknown_flag.returncode, 2)
        self.assertIs(json.loads(unknown_flag.stdout)['complete'], False)

    def test_native_rig_and_mcp_disclose_identical_complete_coverage(self):
        target = self.root / 'focus.tsx'
        target.write_text('<button className="outline-none">Continue</button>')
        raw_args = json.dumps({'path': str(target)})
        rig = self.run_uim('rig', 'call', 'ui_anti_slop_lint', raw_args)
        self.assertEqual(rig.returncode, 0, rig.stderr)
        rig_report = json.loads(rig.stdout)
        self.assertIs(rig_report['complete'], True)
        self.assertEqual(rig_report['violations'][0]['rule'], 'a11y/focus-outline')

        request = {
            'jsonrpc': '2.0', 'id': 19, 'method': 'tools/call',
            'params': {'name': 'ui_anti_slop_lint', 'arguments': {'path': str(target)}},
        }
        mcp = self.run_uim('mcp', input=json.dumps(request) + '\n')
        self.assertEqual(mcp.returncode, 0, mcp.stderr)
        payload = json.loads(mcp.stdout)
        self.assertIs(payload['result']['isError'], False)
        mcp_report = json.loads(payload['result']['content'][0]['text'])
        self.assertEqual(mcp_report, rig_report)

    def test_native_directory_scan_rule_set_and_count_are_stable(self):
        target = REPO / 'tests/fixtures/ui_audit'
        a = self.run_uim('audit', str(target), '--json')
        b = self.run_uim('audit', str(target), '--json')
        self.assertEqual(a.returncode, 0, a.stderr)
        self.assertEqual(a.stdout, b.stdout)
        report = json.loads(a.stdout)
        self.assertEqual(report['files_scanned'], 8)
        self.assertEqual(report['violations_count'], 8)
        self.assertEqual(report['blocks'], 5)
        self.assertEqual(report['flags'], 3)

    def test_portable_launcher_finds_installed_native_engine(self):
        binary = self.root / 'bin/uim'
        binary.parent.mkdir()
        binary.symlink_to(ENGINE)
        env = {**self.env, 'PATH': str(binary.parent) + os.pathsep + os.environ['PATH']}
        result = self.run_uim('contrast', '#fff', '#000', '--json',
                              launcher=PORTABLE_LAUNCHER, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['ratio'], 21.0)


if __name__ == '__main__':
    unittest.main()
