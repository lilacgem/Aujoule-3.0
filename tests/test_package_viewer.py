import json
from pathlib import Path
import tempfile
import unittest
from scripts.adapt_lineage import adapt, LineageError
from scripts.compile_package import compile_package, load_json
from scripts.serve_package import make_handler, view_state

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/lineage'

class PackageViewerTests(unittest.TestCase):
    def setUp(self):
        self.package = compile_package(adapt((FIXTURES / 'baseline.txt').read_bytes(), .7, .4), load_json(FIXTURES / 'local-permissions.json'))

    def test_view_contains_linked_baseline_but_no_raw_provenance(self):
        state = view_state(self.package)
        self.assertEqual(state['orb']['glow'], .8)
        self.assertEqual(state['prototype']['stateId'], self.package['state']['stateId'])
        self.assertFalse(state['prototype']['liveAudioAllowed'])
        self.assertFalse(state['prototype']['recordingAllowed'])
        self.assertNotIn('provenance', state)
        self.assertNotIn('originalBytesBase64', json.dumps(state))

    def test_tampered_package_refused_before_server_starts(self):
        self.package['state']['legacyOrb']['glow'] = .1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            path.write_text(json.dumps(self.package))
            with self.assertRaises(LineageError):
                make_handler([path])

if __name__ == '__main__':
    unittest.main()
