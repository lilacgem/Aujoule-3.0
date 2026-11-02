import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

READY = all(importlib.util.find_spec(n) for n in ('numpy', 'soundfile', 'scipy', 'matplotlib'))
if READY:
    from scripts.demo_evidence_resolution import make_fixture
    from scripts.resolve_state_evidence import resolve_evidence
    from scripts.archive_audio_checkpoint import archive, read_head, inspect_archive, hash_content


@unittest.skipUnless(READY, 'Optional audio dependencies required')
class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        files = make_fixture(root/'fixtures')
        state = json.loads(files['state'].read_text())
        resolved = resolve_evidence(*(files[k] for k in ('state', 'features', 'summary', 'comparison')))
        old = state['payload']['sourceRef']['sha256']; current = 'b'*64
        report = {'schema': 'AUEVO-AudioEvidenceReconciliation/v0.1',
                  'status': 'source-bytes-differ-decoded-control-samples-identical',
                  'stateRef': resolved['resolution']['stateRef'],
                  'inputs': {**resolved['resolution']['inputs'], 'current': {'filename': 'synthetic.wav', 'sha256': current}},
                  'earlierSourceSha256': old, 'currentSourceSha256': current,
                  'strictSourceByteMatch': False, 'decodedControlSampleMatch': True,
                  'measurementChainResolution': resolved,
                  'freshSampleComparison': {'status': 'decoded-samples-identical', 'differentChannelSamples': 0,
                      'maximumAbsoluteDifference': 0, 'firstDifference': None, 'current': {'sha256': current},
                      'declaredEarlierSourceSha256': old,
                      'comparisonSha256': resolved['resolution']['inputs']['comparison']['sha256']},
                  **{key: False for key in ('historyAdvanced', 'authorizedForHistoryCommit', 'stateFilesModified', 'originalHashReplaced')}}
        self.state = state
        self.receipt = self.wrap(report)
        self.database = root/'archive.sqlite3'

    def wrap(self, report):
        key = hash_content(report)
        return {'contentHash': key, 'reconciliationId': 'audio-reconciliation:sha256:'+key, 'reconciliation': report}

    def test_archive_replay_and_stale_writer(self):
        before = copy.deepcopy(self.state)
        self.assertIsNone(read_head(self.database))
        self.assertEqual(archive(self.database, self.state, self.receipt, None)['status'], 'checkpoint-archived')
        key = self.state['contentHash']
        self.assertEqual(archive(self.database, self.state, self.receipt, key)['status'], 'checkpoint-reused')
        summary = inspect_archive(self.database)
        self.assertEqual(summary['checkpointCount'], 1)
        self.assertEqual(summary['verificationReceiptCount'], 1)
        with self.assertRaisesRegex(ValueError, 'Stale checkpoint'):
            archive(self.database, self.state, self.receipt, None)
        self.assertEqual(inspect_archive(self.database), summary)
        self.assertEqual(self.state, before)

    def test_invalid_receipt_rejected_before_database_created(self):
        bad = copy.deepcopy(self.receipt)
        bad['reconciliation']['originalHashReplaced'] = True
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            archive(self.database, self.state, bad, None)
        bad = self.wrap(bad['reconciliation'])
        with self.assertRaisesRegex(ValueError, 'unsupported state/history'):
            archive(self.database, self.state, bad, None)
        self.assertFalse(self.database.exists())
        bad = copy.deepcopy(self.receipt['reconciliation'])
        bad['freshSampleComparison']['comparisonSha256'] = 'c'*64
        with self.assertRaisesRegex(ValueError, 'link mismatch'):
            archive(self.database, self.state, self.wrap(bad), None)
        self.assertFalse(self.database.exists())

    def test_stored_tampering_detected_and_different_head_refused(self):
        archive(self.database, self.state, self.receipt, None)
        with self.assertRaisesRegex(ValueError, 'automatic transition'):
            archive(self.database, self.state, self.receipt, 'c'*64)
        with sqlite3.connect(self.database) as connection:
            connection.execute('UPDATE receipts SET receipt_json=?', ('{}',))
        with self.assertRaises((KeyError, ValueError)):
            inspect_archive(self.database)
        with self.assertRaises((KeyError, ValueError)):
            archive(self.database, self.state, self.receipt, self.state['contentHash'])

