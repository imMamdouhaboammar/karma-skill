"""Node UI-Master adapter must never turn subprocess failure into success."""

from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('node'), 'Node is not installed')
class NodeUIAdapterTests(unittest.TestCase):
    def test_node_audit_uses_verified_home_bun_engine_candidate(self):
        with tempfile.TemporaryDirectory(prefix='uim node home ') as temp:
            package = Path(temp) / 'package'
            entry = package / 'bin/ui-master.js'
            entry.parent.mkdir(parents=True)
            shutil.copyfile(REPO / 'bin/ui-master.js', entry)
            (package / 'package.json').write_text('{"type":"module"}')
            scripts = package / 'skills/ui-master/scripts'
            scripts.mkdir(parents=True)
            for name in ('uim', 'bridge.py'):
                shutil.copy2(REPO / 'skills/ui-master/scripts' / name, scripts / name)
            home = Path(temp) / 'home'
            native = home / '.bun/bin/ui-master-engine'
            native.parent.mkdir(parents=True)
            native.write_text(
                '#!/bin/sh\n'
                'if [ "$1" = audit-contract ]; then\n'
                '  echo \'{"audit_contract":"comprehensive-v1","engine":"rust","supported_rules":["anti-slop/purple-gradient","layout/viewport-hscreen","motion/layout-thrashing","a11y/focus-outline","layout/arbitrary-spacing","typography/excess-scale"]}\'\n'
                'else\n'
                '  echo \'{"engine":"rust","complete":true,"files_scanned":1,"violations_count":0}\'\n'
                'fi\n'
            )
            native.chmod(0o755)
            target = package / 'clean.tsx'
            target.write_text('<div>Clean</div>')
            result = subprocess.run(
                [shutil.which('node'), str(entry), 'audit', str(target), '--json'],
                env={**os.environ, 'HOME': str(home)}, capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
            self.assertIn('"complete":true', result.stdout)

    def test_native_candidate_cannot_bypass_audit_contract_probe(self):
        with tempfile.TemporaryDirectory(prefix='uim node stale ') as temp:
            package = Path(temp)
            entry = package / 'bin/ui-master.js'
            entry.parent.mkdir(parents=True)
            shutil.copyfile(REPO / 'bin/ui-master.js', entry)
            (package / 'package.json').write_text('{"type":"module"}')
            scripts = package / 'skills/ui-master/scripts'
            scripts.mkdir(parents=True)
            for name in ('uim', 'bridge.py'):
                shutil.copy2(REPO / 'skills/ui-master/scripts' / name, scripts / name)
            native = package / 'crates/ui-master-engine/target/debug/ui-master-engine'
            native.parent.mkdir(parents=True)
            native.write_text('#!/bin/sh\necho \'{"files_scanned":1,"violations_count":0}\'\n')
            native.chmod(0o755)
            target = package / 'focus.tsx'
            target.write_text('<button className="outline-none">Continue</button>')
            result = subprocess.run(
                [shutil.which('node'), str(entry), 'audit', str(target), '--json'],
                capture_output=True, text=True, timeout=5,
            )
            self.assertNotEqual(result.returncode, 0, (result.stdout, result.stderr))
            self.assertNotIn('"violations_count":0', result.stdout)

    def test_explicit_partial_is_not_intercepted_by_compiled_binary(self):
        with tempfile.TemporaryDirectory(prefix='uim node partial ') as temp:
            package = Path(temp)
            entry = package / 'bin/ui-master.js'
            entry.parent.mkdir(parents=True)
            shutil.copyfile(REPO / 'bin/ui-master.js', entry)
            (package / 'package.json').write_text('{"type":"module"}')
            scripts = package / 'skills/ui-master/scripts'
            scripts.mkdir(parents=True)
            for name in ('uim', 'bridge.py'):
                shutil.copy2(REPO / 'skills/ui-master/scripts' / name, scripts / name)
            native = package / 'crates/ui-master-engine/target/debug/ui-master-engine'
            native.parent.mkdir(parents=True)
            native.write_text('#!/bin/sh\necho native-instead-of-partial\n')
            native.chmod(0o755)
            target = package / 'clean.tsx'
            target.write_text('<div>Clean</div>')
            result = subprocess.run(
                [shutil.which('node'), str(entry), 'audit', str(target), '--partial', '--json'],
                capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(result.returncode, 3, (result.stdout, result.stderr))
            self.assertIn('"engine": "python"', result.stdout)

    def test_child_terminated_by_signal_does_not_report_success(self):
        with tempfile.TemporaryDirectory(prefix='uim node signal ') as temp:
            package = Path(temp)
            entry = package / 'bin/ui-master.js'
            entry.parent.mkdir(parents=True)
            shutil.copyfile(REPO / 'bin/ui-master.js', entry)
            (package / 'package.json').write_text('{"type":"module"}')
            launcher = package / 'skills/ui-master/scripts/uim'
            launcher.parent.mkdir(parents=True)
            launcher.write_text('#!/bin/sh\nkill -TERM $$\n')
            launcher.chmod(0o755)
            result = subprocess.run(
                [shutil.which('node'), str(entry), 'audit', 'fixture.tsx', '--json'],
                capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(result.returncode, 143, (result.stdout, result.stderr))


if __name__ == '__main__':
    unittest.main()
