import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.adapt_lineage import adapt, LineageError
from scripts.compile_package import compile_package, load_json, persist, verify_package

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/lineage'


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.lineage = adapt((FIXTURES / 'baseline.txt').read_bytes(), .7, .4)
        self.policy = load_json(FIXTURES / 'local-permissions.json')
        self.package = compile_package(self.lineage, self.policy)

    def test_baseline_channels_references_and_labels(self):
        state = self.package['state']
        for name, value in dict(glow=.8, density=.5, motion=.7, complexity=.4, coreIntensity=.7).items():
            self.assertEqual(state['legacyOrb'][name], value)
        self.assertEqual(state['symbolic']['origin'], 'AUEVO_DEFINED')
        self.assertEqual(state['inputs']['lineageHash'], self.lineage['contentHash'])
        self.assertEqual(state['generation'], 1)
        self.assertIsNone(state['priorStateId'])
        self.assertEqual(verify_package(self.package), self.package)

    def test_changed_state_preserves_prior_and_explains_differences(self):
        original = copy.deepcopy(self.package)
        lineage = adapt((FIXTURES / 'changed.txt').read_bytes(), .7, .4)
        changed = compile_package(lineage, self.policy, self.package)
        self.assertEqual(self.package, original)
        self.assertEqual(changed['state']['generation'], 2)
        self.assertEqual(changed['state']['priorStateId'], original['state']['stateId'])
        self.assertEqual(changed['state']['legacyOrb']['glow'], .5)
        self.assertEqual(changed['state']['legacyOrb']['coreIntensity'], .55)
        self.assertEqual({change['field'] for change in changed['changes']}, {'legacyOrb.glow', 'legacyOrb.coreIntensity'})

    def test_conflicts_fail_without_writing_or_mutating_history(self):
        original = copy.deepcopy(self.package)
        with self.assertRaises(LineageError) as caught:
            compile_package(self.lineage, self.policy, self.package, load_json(FIXTURES / 'conflicting-claims.json'))
        self.assertEqual(caught.exception.code, 'CONFLICT_UNRESOLVED')
        self.assertEqual(self.package, original)

    def test_replay_is_deterministic_and_does_not_advance(self):
        self.assertEqual(compile_package(self.lineage, self.policy), self.package)
        self.assertEqual(compile_package(self.lineage, self.policy, self.package), self.package)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'state.json'
            persist(output, self.package)
            before = output.stat().st_mtime_ns
            persist(output, self.package)
            self.assertEqual(output.stat().st_mtime_ns, before)

    def test_tamper_schema_and_policy_rejections(self):
        broken = copy.deepcopy(self.package)
        broken['state']['legacyOrb']['glow'] = .1
        with self.assertRaises(LineageError) as caught:
            compile_package(self.lineage, self.policy, broken)
        self.assertEqual(caught.exception.code, 'HASH_MISMATCH')
        for key, value in [('allowCompile', False), ('allowCloudUpload', True), ('allowExport', True)]:
            policy = {**self.policy, key: value}
            with self.assertRaises(LineageError):
                compile_package(self.lineage, policy)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'denied.json'
            package = compile_package(self.lineage, {**self.policy, 'allowPersist': False})
            with self.assertRaises(LineageError):
                persist(output, package)
            self.assertFalse(output.exists())

    def test_no_overwrite_and_strict_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'state.json'
            persist(output, self.package)
            original = output.read_bytes()
            changed = compile_package(adapt((FIXTURES / 'changed.txt').read_bytes(), .7, .4), self.policy, self.package)
            with self.assertRaises(LineageError):
                persist(output, changed)
            self.assertEqual(output.read_bytes(), original)
            for text in ['{"x":1,"x":2}', '{"x":NaN}']:
                invalid = Path(directory) / 'bad.json'
                invalid.write_text(text)
                with self.assertRaises(LineageError):
                    load_json(invalid)

    def test_cli_baseline_and_conflicting_input(self):
        with tempfile.TemporaryDirectory() as directory:
            lineage = Path(directory) / 'lineage.json'
            lineage.write_text(json.dumps(self.lineage))
            output = Path(directory) / 'package.json'
            command = [sys.executable, str(ROOT / 'scripts/compile_package.py'), '--lineage', str(lineage),
                       '--permissions', str(FIXTURES / 'local-permissions.json'), '--output', str(output)]
            result = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            verify_package(load_json(output))
            failed_output = Path(directory) / 'failed.json'
            command[-1] = str(failed_output)
            result = subprocess.run(command + ['--claims', str(FIXTURES / 'conflicting-claims.json')], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('CONFLICT_UNRESOLVED', result.stderr)
            self.assertFalse(failed_output.exists())


if __name__ == '__main__':
    unittest.main()
