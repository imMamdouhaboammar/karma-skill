"""Behavioral contract of the shipped UI-Master Bash entry points."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / 'skills/ui-master/scripts'
PORTABLE = REPO / 'src/karma/portable/ui-master/scripts'


class UIMLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='uim launcher space ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        (self.root / 'other working directory').mkdir()
        # Only commands required by the launcher are visible. In particular,
        # a machine's installed Cargo or global uim cannot influence the tests.
        (self.bin / 'dirname').symlink_to(shutil.which('dirname'))
        (self.bin / 'readlink').symlink_to(shutil.which('readlink'))
        (self.bin / 'bash').symlink_to('/bin/bash')
        (self.bin / 'python3').symlink_to(sys.executable)
        self.env = {**os.environ, 'PATH': str(self.bin)}
        self.env.pop('UIM_CARGO_RUN', None)
        self.env.pop('UIM_ENGINE', None)
        self.env['HOME'] = str(self.root / 'home')
        self.launcher = self.install_launcher(SOURCE, self.root / 'checkout')

    def install_launcher(self, source, root):
        scripts = root / 'skills/ui-master/scripts'
        scripts.mkdir(parents=True)
        for name in ('uim', 'bridge.py'):
            shutil.copy2(source / name, scripts / name)
        manifest = root / 'crates/ui-master-engine/Cargo.toml'
        manifest.parent.mkdir(parents=True)
        manifest.write_text('[package]\nname = "ui-master-engine"\n')
        return scripts / 'uim'

    def fake_engine(self, path, label='native', code=0, contracted=False):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '#!' + sys.executable + '\n'
            'import json, sys\n'
            'if sys.argv[1:3] == ["audit-contract", "--json"]:\n'
            f'    print(json.dumps({{"audit_contract": {"comprehensive-v1" if contracted else "legacy"!r}, "engine": "rust", "supported_rules": ["anti-slop/purple-gradient", "layout/viewport-hscreen", "motion/layout-thrashing", "a11y/focus-outline", "layout/arbitrary-spacing", "typography/excess-scale"]}}))\n'
            '    sys.exit(0)\n'
            f'if sys.argv[1:2] == ["mcp"]:\n'
            '    for line in sys.stdin:\n'
            '        request = json.loads(line)\n'
            '        print(json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": {"server": "native"}}), flush=True)\n'
            'else:\n'
            f'    print(json.dumps({{"engine": "{label}", "args": sys.argv[1:]}}))\n'
            f'    print("{label}: diagnostics", file=sys.stderr)\n'
            f'    sys.exit({code})\n'
        )
        path.chmod(0o755)

    def fake_cargo(self, code=0):
        path = self.bin / 'cargo'
        path.write_text(
            '#!' + sys.executable + '\n'
            'import json, sys\n'
            'args = sys.argv[1:]\n'
            'if args[-1:] == ["mcp"]:\n'
            '    for line in sys.stdin:\n'
            '        request = json.loads(line)\n'
            '        print(json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": {"server": "cargo"}}), flush=True)\n'
            'else:\n'
            '    print(json.dumps({"engine": "cargo", "args": args}))\n'
            '    print("cargo: diagnostics", file=sys.stderr)\n'
            f'    sys.exit({code})\n'
        )
        path.chmod(0o755)

    def run_uim(self, *args, launcher=None, extra_env=None, cwd=None, input=None):
        return subprocess.run(
            ['/bin/bash', str(launcher or self.launcher), *args],
            cwd=cwd or self.root, env={**self.env, **(extra_env or {})},
            input=input, text=True, capture_output=True, timeout=5,
        )

    def test_native_only_commands_route_through_cargo_without_opt_in(self):
        self.fake_cargo()
        for command, args in (
            ('crx', ['./path with spaces', '--json']),
            ('skills', ['micro-interactions', '--json']),
            ('get-skill', ['contrast']),
            ('rig', ['list']),
            ('trace', ['show', 'abc']),
        ):
            with self.subTest(command=command):
                result = self.run_uim(command, *args)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload['engine'], 'cargo')
                self.assertEqual(payload['args'][-(len(args) + 1):], [command, *args])
                self.assertEqual(payload['args'][:3], ['run', '--offline', '--locked'])
                self.assertNotIn('cargo: diagnostics', result.stdout)

    def test_native_only_command_without_cargo_has_actionable_error(self):
        for command in ('crx', 'skills', 'mcp'):
            with self.subTest(command=command):
                result = self.run_uim(command)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')
                self.assertIn(command, result.stderr)
                self.assertIn('Cargo', result.stderr)
                self.assertNotIn('invalid choice', result.stderr)

    def test_native_mcp_stdio_stdout_stays_protocol_only(self):
        self.fake_cargo()
        result = self.run_uim('mcp', input='{"jsonrpc":"2.0","id":7,"method":"ping"}\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['id'], 7)
        self.assertEqual(json.loads(result.stdout)['result']['server'], 'cargo')

    def test_compiled_engine_is_preferred_and_propagates_output_and_exit(self):
        self.fake_cargo()
        native = self.root / 'checkout/crates/ui-master-engine/target/release/ui-master-engine'
        self.fake_engine(native, code=17)
        result = self.run_uim('crx', 'a b', '--json')
        self.assertEqual(result.returncode, 17)
        self.assertEqual(json.loads(result.stdout)['args'], ['crx', 'a b', '--json'])
        self.assertIn('native: diagnostics', result.stderr)

    def test_external_independent_uim_is_preferred(self):
        self.fake_cargo()
        self.fake_engine(self.bin / 'uim', label='external', code=23)
        result = self.run_uim('skills', 'a quoted query')
        self.assertEqual(result.returncode, 23)
        self.assertEqual(json.loads(result.stdout), {
            'engine': 'external', 'args': ['skills', 'a quoted query'],
        })

    def test_debug_engine_is_used_if_release_is_absent(self):
        self.fake_cargo()
        self.fake_engine(self.root / 'checkout/crates/ui-master-engine/target/debug/ui-master-engine')
        result = self.run_uim('crx', '.', '--json')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['engine'], 'native')

    def test_contrast_uses_available_python_bridge_without_cargo(self):
        result = self.run_uim('contrast', '#ffffff', '#000000', '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['ratio'], 21.0)

    def test_audit_without_native_must_not_report_false_clean(self):
        target = self.root / 'missing-focus.tsx'
        target.write_text('<button className="outline-none">Continue</button>\n')
        result = self.run_uim('audit', str(target), '--json')
        self.assertEqual(result.returncode, 69, (result.stdout, result.stderr))
        self.assertNotIn('"violations_count": 0', result.stdout)
        self.assertIn('native Rust engine', result.stderr)

    def test_explicit_partial_audit_discloses_coverage_and_returns_nonzero(self):
        target = self.root / 'focus with spaces.tsx'
        target.write_text('<button className="outline-none">Continue</button>\n')
        result = self.run_uim('audit', str(target), '--partial', '--json')
        self.assertEqual(result.returncode, 3, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['engine'], 'python')
        self.assertIs(payload['complete'], False)
        self.assertIs(payload['partial'], True)
        self.assertEqual(payload['supported_rules'], ['layout/viewport-hscreen'])
        self.assertIn('a11y/focus-outline', payload['unavailable_rules'])
        self.assertEqual(payload['violations_count'], 0)
        self.assertIn('PARTIAL', result.stderr)

    def test_partial_hscreen_matches_native_rule_id_and_severity(self):
        target = self.root / 'viewport.tsx'
        target.write_text('<div className="h-screen">Content</div>\n')
        result = self.run_uim('audit', str(target), '--partial', '--json')
        self.assertEqual(result.returncode, 3, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['blocks'], 0)
        self.assertEqual(payload['flags'], 1)
        violation = payload['violations'][0]
        self.assertEqual((violation['rule'], violation['severity']), ('layout/viewport-hscreen', 'FLAG'))
        self.assertEqual(violation['line'], 1)
        self.assertTrue(violation['fix'])

    def test_partial_with_no_supported_files_is_not_clean(self):
        target = self.root / 'empty'
        target.mkdir()
        (target / 'README.md').write_text('nothing to scan')
        result = self.run_uim('audit', str(target), '--partial', '--json')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIs(json.loads(result.stdout)['complete'], False)

    def test_partial_missing_target_is_invalid_input(self):
        result = self.run_uim('audit', str(self.root / 'missing.tsx'), '--partial', '--json')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIs(json.loads(result.stdout)['complete'], False)

    def test_default_comprehensive_audit_uses_offline_cargo_when_available(self):
        self.fake_cargo()
        result = self.run_uim('audit', 'path with spaces', '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['engine'], 'cargo')
        self.assertEqual(payload['args'][:3], ['run', '--offline', '--locked'])
        self.assertEqual(payload['args'][-3:], ['audit', 'path with spaces', '--json'])

    def test_stale_external_uim_cannot_return_legacy_false_clean(self):
        old = self.bin / 'uim'
        old.write_text('#!' + sys.executable + '\nprint(\'{"files_scanned":1,"violations_count":0,"blocks":0,"flags":0,"violations":[]}\')\n')
        old.chmod(0o755)
        target = self.root / 'focus.tsx'
        target.write_text('<button className="outline-none">Continue</button>')
        result = self.run_uim('audit', str(target), '--json')
        self.assertEqual(result.returncode, 69, (result.stdout, result.stderr))
        self.assertNotIn('"violations_count":0', result.stdout)
        self.assertIn('unverified audit executable', result.stderr)

    def test_stale_local_compiled_engine_is_not_accepted_for_comprehensive_audit(self):
        native = self.root / 'checkout/crates/ui-master-engine/target/debug/ui-master-engine'
        self.fake_engine(native, label='stale')
        target = self.root / 'focus.tsx'
        target.write_text('<button className="outline-none">Continue</button>')
        result = self.run_uim('audit', str(target), '--json')
        self.assertEqual(result.returncode, 69, (result.stdout, result.stderr))
        self.assertIn('unverified audit executable', result.stderr)

    def test_verified_native_engine_handles_audit_without_python_on_path(self):
        native = self.root / 'checkout/crates/ui-master-engine/target/debug/ui-master-engine'
        self.fake_engine(native, contracted=True)
        (self.bin / 'python3').unlink()
        result = self.run_uim('audit', 'component.tsx', '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['engine'], 'native')

    def test_partial_is_explicit_even_if_native_engine_exists(self):
        self.fake_engine(self.root / 'checkout/crates/ui-master-engine/target/debug/ui-master-engine')
        target = self.root / 'clean.tsx'
        target.write_text('<div>Clean</div>')
        result = self.run_uim('audit', str(target), '--partial', '--json')
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(json.loads(result.stdout)['engine'], 'python')

    def test_portable_partial_audit_has_same_contract(self):
        portable_launcher = self.install_launcher(PORTABLE, self.root / 'installed')
        target = self.root / 'viewport.tsx'
        target.write_text('<div className="h-screen" />')
        result = self.run_uim('audit', str(target), '--partial', '--json', launcher=portable_launcher)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIs(json.loads(result.stdout)['complete'], False)

    def test_direct_python_bridge_refuses_implicit_comprehensive_audit(self):
        result = subprocess.run(
            [sys.executable, str(SOURCE / 'bridge.py'), 'audit', str(REPO / 'tests/fixtures/ui_audit/focus.tsx'), '--json'],
            capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, 69)
        self.assertIs(json.loads(result.stdout)['complete'], False)

    def test_partial_audit_rejects_undecodable_file_instead_of_skipping(self):
        target = self.root / 'invalid.tsx'
        target.write_bytes(b'\xff\xfe')
        result = self.run_uim('audit', str(target), '--partial', '--json')
        self.assertEqual(result.returncode, 70, result.stderr)
        self.assertIs(json.loads(result.stdout)['complete'], False)
        self.assertIn('error', json.loads(result.stdout))

    def test_partial_scan_respects_exclusions_and_stable_order(self):
        for directory in ('node_modules', '.hidden', 'dist', 'target'):
            hidden = self.root / directory
            hidden.mkdir()
            (hidden / 'skip.tsx').write_text('h-screen')
        nested = self.root / 'components'
        nested.mkdir()
        (nested / 'z.tsx').write_text('h-screen')
        (nested / 'a.tsx').write_text('h-screen')
        (self.root / 'notes.md').write_text('h-screen')
        result = self.run_uim('audit', str(self.root), '--partial', '--json')
        self.assertEqual(result.returncode, 3, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['files_scanned'], 2)
        self.assertEqual([Path(v['file']).name for v in payload['violations']], ['a.tsx', 'z.tsx'])

    def test_path_with_shell_metacharacters_is_passed_as_one_argument(self):
        target = self.root / 'component;touch dangerous.tsx'
        target.write_text('h-screen')
        result = self.run_uim('audit', str(target), '--partial', '--json')
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(json.loads(result.stdout)['files_scanned'], 1)
        self.assertFalse((self.root / 'dangerous.tsx').exists())

    def test_no_python_bridge_has_direct_diagnostic(self):
        (self.root / 'checkout/skills/ui-master/scripts/bridge.py').unlink()
        result = self.run_uim('contrast', '#fff', '#000')
        self.assertEqual(result.returncode, 69)
        self.assertIn('Python bridge', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_no_python_executable_has_direct_diagnostic(self):
        (self.bin / 'python3').unlink()
        result = self.run_uim('contrast', '#fff', '#000')
        self.assertEqual(result.returncode, 69)
        self.assertIn('python3', result.stderr)

    def test_explicit_cargo_mode_routes_bridge_commands_to_cargo(self):
        self.fake_cargo()
        result = self.run_uim('contrast', '#fff', '#000', '--json', extra_env={'UIM_CARGO_RUN': '1'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['engine'], 'cargo')

    def test_disabled_cargo_mode_does_not_disable_native_commands(self):
        self.fake_cargo()
        result = self.run_uim('skills', 'focus', extra_env={'UIM_CARGO_RUN': '0'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['engine'], 'cargo')

    def test_invalid_cargo_setting_is_rejected(self):
        result = self.run_uim('contrast', '#fff', '#000', extra_env={'UIM_CARGO_RUN': 'nonsense'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('UIM_CARGO_RUN', result.stderr)

    def test_true_cargo_setting_is_supported(self):
        self.fake_cargo()
        result = self.run_uim('contrast', '#fff', '#000', extra_env={'UIM_CARGO_RUN': 'true'})
        self.assertEqual(json.loads(result.stdout)['engine'], 'cargo')

    def test_explicit_cargo_mode_missing_tool_reports_failure(self):
        result = self.run_uim('contrast', '#fff', '#000', extra_env={'UIM_CARGO_RUN': '1'})
        self.assertEqual(result.returncode, 69)
        self.assertIn('Cargo', result.stderr)

    def test_cargo_failure_is_propagated_without_swallowing_stderr(self):
        self.fake_cargo(code=31)
        result = self.run_uim('crx', '.', '--json')
        self.assertEqual(result.returncode, 31)
        self.assertIn('cargo: diagnostics', result.stderr)
        self.assertNotIn('diagnostics', result.stdout)

    def test_unknown_command_fails_without_bridge_argparse(self):
        self.fake_cargo()
        result = self.run_uim('not-a-command')
        self.assertEqual(result.returncode, 2)
        self.assertIn('unknown command', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_launcher_help_lists_every_supported_command(self):
        for argv in ((), ('help',), ('--help',), ('-h',)):
            with self.subTest(argv=argv):
                result = self.run_uim(*argv)
                self.assertEqual(result.returncode, 0, result.stderr)
                for command in ('contrast', 'audit', 'crx', 'skills', 'mcp',
                                'rig', 'get-skill', 'trace'):
                    self.assertIn(command, result.stdout)
                self.assertNotIn('invalid choice', result.stderr)

    def test_self_on_path_does_not_recurse(self):
        (self.bin / 'uim').symlink_to(self.launcher)
        result = self.run_uim('contrast', '#fff', '#000', '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['ratio'], 21.0)

    def test_bash_invocation_from_script_directory_uses_local_launcher(self):
        result = subprocess.run(
            ['/bin/bash', 'uim', 'contrast', '#fff', '#000', '--json'],
            cwd=self.launcher.parent, env=self.env,
            text=True, capture_output=True, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['ratio'], 21.0)

    def test_self_first_on_path_does_not_hide_later_native_engine(self):
        (self.bin / 'uim').symlink_to(self.launcher)
        native_bin = self.root / 'independent engine'
        self.fake_engine(native_bin / 'uim', label='later-native')
        result = self.run_uim(
            'skills', 'motion',
            extra_env={'PATH': str(self.bin) + os.pathsep + str(native_bin)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['engine'], 'later-native')

    def test_launcher_invoked_through_symlink_resolves_its_own_resources(self):
        alias = self.bin / 'uim'
        alias.symlink_to(self.launcher)
        result = self.run_uim('contrast', '#fff', '#000', '--json', launcher=alias)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['ratio'], 21.0)

    def test_direct_launcher_directory_on_path_does_not_recurse(self):
        result = self.run_uim(
            'contrast', '#fff', '#000', '--json',
            extra_env={'PATH': str(self.launcher.parent) + os.pathsep + str(self.bin)},
            cwd=self.root / 'other working directory',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['ratio'], 21.0)

    def test_package_node_shim_on_path_does_not_reenter_launcher(self):
        # npm exposes bin/ui-master.js under the name uim. That JS entrypoint
        # delegates back to the shell script when no compiled engine exists.
        package_root = self.root / 'checkout'
        script = package_root / 'bin/ui-master.js'
        script.parent.mkdir()
        shutil.copy2(REPO / 'bin/ui-master.js', script)
        (self.bin / 'uim').symlink_to(script)
        (self.bin / 'node').symlink_to(shutil.which('node'))
        result = self.run_uim('contrast', '#fff', '#000', '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['ratio'], 21.0)

    def test_portable_install_reports_missing_engine_without_argparse(self):
        portable_launcher = self.install_launcher(PORTABLE, self.root / 'installed')
        (self.root / 'installed/crates/ui-master-engine/Cargo.toml').unlink()
        result = self.run_uim('crx', '.', '--json', launcher=portable_launcher)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('crx', result.stderr)
        self.assertIn('requires the native Rust engine', result.stderr)
        self.assertIn('Cargo manifest is not bundled', result.stderr)
        self.assertNotIn('invalid choice', result.stderr)

    def test_portable_install_uses_independent_external_binary(self):
        portable_launcher = self.install_launcher(PORTABLE, self.root / 'installed')
        (self.root / 'installed/crates/ui-master-engine/Cargo.toml').unlink()
        self.fake_engine(self.bin / 'uim', label='installed-native')
        result = self.run_uim('skills', 'color', '--json', launcher=portable_launcher)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['engine'], 'installed-native')

    def test_shipped_launchers_match_generated_source(self):
        self.assertEqual((SOURCE / 'uim').read_bytes(), (PORTABLE / 'uim').read_bytes())


if __name__ == '__main__':
    unittest.main()
