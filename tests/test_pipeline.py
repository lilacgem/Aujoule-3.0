import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUFFIX = '.exe' if os.name == 'nt' else ''

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / 'compiler2_state.txt'
        self.output = Path(self.temp.name) / 'evo_state.json'

    def run_tool(self, name, args, text):
        return subprocess.run([str(ROOT / 'build' / (name + SUFFIX)), *map(str, args)], input=text, text=True, capture_output=True, cwd=self.temp.name)

    def compile_input(self, text='8\n0.6\nl\n'):
        result = self.run_tool('second-compiler', [self.state], text)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pipeline_and_versioning(self):
        self.compile_input()
        self.compile_input()
        self.assertEqual(self.state.read_text().splitlines()[0], '2')
        result = self.run_tool('state-compiler', [self.state, self.output], '0.7\n0.4\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(self.output.read_text())
        self.assertEqual(data['intensity'], 8)
        self.assertAlmostEqual(data['focus'], .6)
        for key, value in dict(glow=.8, density=.5, motion=.7, complexity=.4, coreIntensity=.7).items():
            self.assertAlmostEqual(data['orb'][key], value)
        self.assertEqual(data['resonance'], 369)
        self.assertEqual(self.state.read_text().splitlines()[3], 'L')

    def test_windows_line_endings(self):
        self.compile_input()
        self.state.write_bytes(self.state.read_bytes().replace(b'\n', b'\r\n'))
        self.assertEqual(self.run_tool('state-compiler', [self.state, self.output], '.7\n.4\n').returncode, 0)
        self.compile_input()

    def test_invalid_input_preserves_state(self):
        self.compile_input()
        original = self.state.read_bytes()
        for text in ['11\n.5\nL\n', '5\n2\nL\n', 'bad\n', '5\n.5\n"\n']:
            self.assertNotEqual(self.run_tool('second-compiler', [self.state], text).returncode, 0)
            self.assertEqual(self.state.read_bytes(), original)

    def test_missing_and_corrupt_state(self):
        self.assertNotEqual(self.run_tool('state-compiler', [self.state, self.output], '.7\n.4\n').returncode, 0)
        self.state.write_text('broken\n')
        self.assertNotEqual(self.run_tool('state-compiler', [self.state, self.output], '.7\n.4\n').returncode, 0)
        self.assertNotEqual(self.run_tool('second-compiler', [self.state], '8\n.6\nL\n').returncode, 0)
        self.assertFalse(self.output.exists())

    def test_invalid_activity_and_unwritable_output(self):
        self.compile_input()
        for text in ['2\n.4\n', '.7\n-1\n', 'bad\n']:
            self.assertNotEqual(self.run_tool('state-compiler', [self.state, self.output], text).returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertNotEqual(self.run_tool('state-compiler', [self.state, self.output / 'missing.json'], '.7\n.4\n').returncode, 0)

if __name__ == '__main__':
    unittest.main()
