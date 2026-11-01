"""Optional audio suite: install requirements-audio.txt first."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

READY = all(importlib.util.find_spec(name) for name in ('soundfile', 'numpy', 'scipy', 'matplotlib'))
if READY:
    import numpy as np
    import soundfile as sf
    from scripts.analyze_audio import inspect_audio, sha256, pulse_estimate
ROOT = Path(__file__).resolve().parents[1]

@unittest.skipUnless(READY, 'Install requirements-audio.txt for the optional audio tests')
class AudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, signal, rate=48000, subtype='PCM_16'):
        path = self.root / 'source.wav'
        sf.write(path, signal, rate, subtype=subtype)
        return path

    def test_known_tone_levels_frequency_and_source_integrity(self):
        rate=48000
        signal=.5*np.sin(2*np.pi*1000*np.arange(rate)/rate)
        path=self.write(signal)
        original=sha256(path)
        report, _, _=inspect_audio(path, fft_size=4096, hop_size=1024)
        self.assertEqual(sha256(path), original)
        self.assertEqual(report['source']['sampleRateHz'], rate)
        self.assertEqual(report['source']['bitsPerSample'],16)
        self.assertAlmostEqual(report['levels']['rmsLinearPerChannel'][0], .5/np.sqrt(2), places=4)
        frequencies=np.array(report['spectrum']['frequencyHz'])
        power=np.array(report['spectrum']['meanPowerSpectralDensity'])
        self.assertLess(abs(frequencies[power.argmax()]-1000),rate/4096)
        self.assertAlmostEqual(float(power.sum()*rate/4096), .125, places=4)
        self.assertGreater(report['spectrum']['bandPower']['mid']['power'],.12)

    def test_opposite_phase_stereo_does_not_cancel(self):
        t=np.arange(48000)/48000
        tone=.5*np.sin(2*np.pi*1000*t)
        report,_,_=inspect_audio(self.write(np.column_stack([tone,-tone])))
        self.assertGreater(report['spectrum']['bandPower']['mid']['power'],.12)
        self.assertEqual(report['source']['channels'],2)

    def test_silence_has_no_fabricated_tempo_or_infinite_json(self):
        report,_,_=inspect_audio(self.write(np.zeros(48000)))
        self.assertIsNone(report['pulseEstimate']['tempoBpm'])
        self.assertEqual(report['levels']['rmsDbfsPerChannel'],[None])
        self.assertTrue(all(item['spectralCentroidHz'] is None for item in report['timeline']))
        json.dumps(report,allow_nan=False)

    def test_near_full_scale_and_short_clip(self):
        report,_,_=inspect_audio(self.write(np.array([1.,-1.,0.])))
        self.assertEqual(report['levels']['nearFullScaleSamplesPerChannel'],[2])
        self.assertTrue(report['method']['paddedShortClip'])
        self.assertEqual(report['source']['frames'],3)

    def test_pulse_estimator_on_known_periodic_onsets(self):
        rate=100
        envelope=np.zeros(1200);envelope[10::50]=1
        pulse=pulse_estimate(envelope,rate)
        self.assertAlmostEqual(pulse['tempoBpm'],120)
        self.assertEqual(pulse['status'],'experimental-estimate')

    def test_cli_outputs_and_refuses_to_overwrite(self):
        path=self.write(.5*np.sin(2*np.pi*1000*np.arange(12000)/48000))
        output=self.root/'report'
        cmd=[sys.executable,str(ROOT/'scripts/analyze_audio.py'),str(path),'--output',str(output)]
        result=subprocess.run(cmd,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        for filename in ['measurements.json','report.md','report.html','waveform.png','levels.png','spectrum.png','spectrogram.png']:
            self.assertGreater((output/filename).stat().st_size,0)
        before=(output/'measurements.json').read_bytes()
        result=subprocess.run(cmd,text=True,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((output/'measurements.json').read_bytes(),before)

    def test_invalid_settings_and_nonfinite_samples(self):
        path=self.write(np.zeros(100))
        with self.assertRaises(ValueError):inspect_audio(path,fft_size=1000)
        with self.assertRaises(ValueError):inspect_audio(path,hop_size=3000)
        path=self.write(np.array([float('nan'),0]),subtype='FLOAT')
        with self.assertRaises(ValueError):inspect_audio(path)

if __name__=='__main__':unittest.main()
