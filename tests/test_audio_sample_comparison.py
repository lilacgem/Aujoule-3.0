import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

READY = all(importlib.util.find_spec(n) for n in ('numpy', 'soundfile'))
if READY:
    import numpy as np
    import soundfile as sf
    from scripts.compare_audio_samples import compare, digest


@unittest.skipUnless(READY, 'Optional audio dependencies required')
class SampleComparisonTests(unittest.TestCase):
    def test_equal_samples_with_different_container_bytes_and_changed_sample(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            x = np.arange(70000, dtype=np.float32)/140000
            current, control = root/'current.wav', root/'derived-44100Hz.wav'
            sf.write(current, x, 44100, subtype='FLOAT')
            sf.write(control, x, 44100, subtype='DOUBLE')
            record = root/'comparison.json'
            def write_record():
                record.write_text(json.dumps({'source': {'sampleRateHz': 44100, 'sha256': 'a'*64},
                    'conditions': [{'conversion': 'identity-control', 'targetRateHz': 44100,
                                    'file': control.name, 'sha256': digest(control)}]}))
            write_record()
            before = digest(current)
            self.assertNotEqual(before, digest(control))
            result = compare(current, record)
            self.assertEqual(result['status'], 'decoded-samples-identical')
            self.assertEqual(digest(current), before)
            x[69000] += .01
            sf.write(control, x, 44100, subtype='FLOAT')
            with self.assertRaisesRegex(ValueError, 'hash'):
                compare(current, record)
            write_record()
            result = compare(current, record)
            self.assertEqual(result['differentChannelSamples'], 1)
            self.assertEqual(result['firstDifference'], {'frame': 69000, 'channel': 1})
            sf.write(control, x[:-1], 44100, subtype='FLOAT')
            write_record()
            with self.assertRaisesRegex(ValueError, 'frame count'):
                compare(current, record)
