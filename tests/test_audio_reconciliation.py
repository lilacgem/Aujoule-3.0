import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

READY = all(importlib.util.find_spec(n) for n in ('numpy', 'soundfile', 'scipy', 'matplotlib'))
if READY:
    import numpy as np
    import soundfile as sf
    from scripts.demo_evidence_resolution import make_fixture
    from scripts.build_audio_state import build_state
    from scripts.compare_audio_samples import compare, digest
    from scripts.reconcile_audio_evidence import reconcile
    from scripts.adapt_lineage import canonical_bytes


@unittest.skipUnless(READY, 'Optional audio dependencies required')
class ReconciliationTests(unittest.TestCase):
    def test_real_sample_recheck_links_chain_and_rejects_altered_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = make_fixture(root/'evidence')
            current = root/'current.wav'
            control = paths['comparison'].parent/'control.wav'
            x = np.arange(128, dtype=np.float32)/256
            sf.write(current, x, 48000, subtype='FLOAT')
            sf.write(control, x, 48000, subtype='DOUBLE')
            comp = json.loads(paths['comparison'].read_text())
            comp['conditions'][0].update(conversion='identity-control', file=control.name, sha256=digest(control))
            paths['comparison'].write_text(json.dumps(comp))
            features = json.loads(paths['features'].read_text())
            features['comparisonRef']['sha256'] = digest(paths['comparison'])
            features['conditions'][0]['sourceSha256'] = digest(control)
            paths['features'].write_bytes(canonical_bytes(features))
            summary = json.loads(paths['summary'].read_text())
            summary['fullRecordsSha256'] = digest(paths['features'])
            summary['conditions'][0]['sourceSha256'] = digest(control)
            paths['summary'].write_text(json.dumps(summary))
            paths['state'].write_text(json.dumps(build_state(features, summary, digest(paths['features']))))
            sample = root/'sample.json'
            sample.write_text(json.dumps(compare(current, paths['comparison'])))
            def run():
                return reconcile(current, sample, paths['state'], paths['features'], paths['summary'], paths['comparison'])
            before = {str(p): digest(p) for p in [current, control, sample, *[paths[k] for k in ('state', 'features', 'summary', 'comparison')]]}
            result = run()['reconciliation']
            self.assertFalse(result['strictSourceByteMatch'])
            self.assertTrue(result['decodedControlSampleMatch'])
            self.assertFalse(result['originalHashReplaced'])
            self.assertEqual(before, {p: digest(p) for p in before})
            saved = json.loads(sample.read_text()); saved['differentChannelSamples'] = 1
            sample.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError, 'differs from the fresh'):
                run()
            sf.write(current, x+.01, 48000, subtype='FLOAT')
            sample.write_text(json.dumps(compare(current, paths['comparison'])))
            with self.assertRaisesRegex(ValueError, 'samples differ'):
                run()
