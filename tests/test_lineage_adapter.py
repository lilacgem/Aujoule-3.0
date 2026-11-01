import base64
import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.adapt_lineage import LineageError, adapt, canonical_bytes, validate_record, write_record

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/lineage'


class LineageAdapterTests(unittest.TestCase):
    def setUp(self):
        self.raw = (FIXTURES / 'baseline.txt').read_bytes()
        self.record = adapt(self.raw, .7, .4)

    def test_preserves_every_field_and_source_byte(self):
        payload = self.record['payload']
        self.assertEqual(base64.b64decode(payload['source']['originalBytesBase64']), self.raw)
        self.assertEqual(payload['source']['sha256'], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(len(payload['parseReport']['consumed']), 7)
        self.assertEqual(payload['parseReport']['discarded'], [])
        self.assertEqual(payload['source']['parsed']['colorHue'], 'Gold')
        self.assertEqual(payload['source']['parsed']['patternStyle'], 'Deep Thinking Fractal Geometry')
        self.assertIsNone(payload['provenance']['rights'])
        self.assertEqual(payload['provenance']['priorStateStatus'], 'UNRESOLVED')
        self.assertFalse(payload['symbolic']['measured'])
        self.assertEqual(validate_record(self.record), self.record)

    def test_deterministic_payload_and_changed_input(self):
        self.assertEqual(adapt(self.raw, .7, .4), self.record)
        changed = adapt((FIXTURES / 'changed.txt').read_bytes(), .7, .4)
        self.assertNotEqual(changed['contentHash'], self.record['contentHash'])
        self.assertEqual(changed['payload']['source']['parsed']['intensity'], 5)
        self.assertNotEqual(adapt(self.raw, .8, .4)['contentHash'], self.record['contentHash'])

    def test_windows_line_endings_preserved_not_normalized_away(self):
        windows = self.raw.replace(b'\n', b'\r\n')
        record = adapt(windows, .7, .4)
        self.assertEqual(record['payload']['source']['parsed'], self.record['payload']['source']['parsed'])
        self.assertNotEqual(record['contentHash'], self.record['contentHash'])
        self.assertEqual(base64.b64decode(record['payload']['source']['originalBytesBase64']), windows)

    def test_rejects_corrupt_extra_and_conflicting_records(self):
        for raw in [b'broken', self.raw + b'9\n', self.raw + (FIXTURES / 'changed.txt').read_bytes(),
                    self.raw.replace(b'0.6', b'nan'), self.raw.replace(b'\n8\n', b'\n11\n'),
                    self.raw.replace(b'\n369\n', b'\n432\n'), self.raw.replace(b'\nL\n', b'\nLL\n')]:
            with self.subTest(raw=raw), self.assertRaises(LineageError):
                adapt(raw, .7, .4)
        for value in [float('nan'), float('inf'), -.1, 1.1, None, True]:
            with self.subTest(value=value), self.assertRaises(LineageError):
                adapt(self.raw, value, .4)

    def test_detects_tampering_even_after_rehash_of_inconsistent_fields(self):
        damaged = copy.deepcopy(self.record)
        damaged['payload']['source']['originalBytesBase64'] = base64.b64encode(b'altered').decode()
        with self.assertRaises(LineageError):
            validate_record(damaged)
        damaged = copy.deepcopy(self.record)
        damaged['payload']['source']['parsed']['intensity'] = 3
        new_hash = hashlib.sha256(canonical_bytes(damaged['payload'])).hexdigest()
        damaged.update(contentHash=new_hash, recordId=f'legacy-lineage:sha256:{new_hash}')
        with self.assertRaises(LineageError):
            validate_record(damaged)
        damaged = copy.deepcopy(self.record)
        damaged['payload']['schema'] = 'AUEVO-LegacyLineage/v99'
        with self.assertRaises(LineageError) as caught:
            validate_record(damaged)
        self.assertEqual(caught.exception.code, 'SCHEMA_UNSUPPORTED')

    def test_explicit_local_persistence_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'snapshot.json'
            with self.assertRaises(LineageError):
                write_record(output, self.record)
            self.assertFalse(output.exists())
            first = write_record(output, self.record, allow_persist=True)
            original = output.read_bytes()
            with self.assertRaises(LineageError) as caught:
                write_record(output, self.record, allow_persist=True)
            self.assertEqual(caught.exception.code, 'OUTPUT_EXISTS')
            self.assertEqual(output.read_bytes(), original)
            second = write_record(Path(directory) / 'replay.json', self.record, allow_persist=True)
            self.assertNotEqual(first['runId'], second['runId'])
            self.assertEqual(first['contentHash'], second['contentHash'])

    def test_cli_creates_snapshot_and_reports_named_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'snapshot.json'
            cmd = [sys.executable, str(ROOT / 'scripts/adapt_lineage.py'), '--input', str(FIXTURES / 'baseline.txt'),
                   '--activity', '.7', '--complexity', '.4', '--output', str(output)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('PERMISSION_DENIED', result.stderr)
            self.assertFalse(output.exists())
            result = subprocess.run(cmd + ['--allow-persist'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.is_file())


if __name__ == '__main__':
    unittest.main()
