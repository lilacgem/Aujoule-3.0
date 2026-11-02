import importlib.util
from pathlib import Path
import tempfile
import unittest

READY=all(importlib.util.find_spec(name) for name in ('soundfile','numpy','scipy','matplotlib'))
if READY:
    import numpy as np
    import soundfile as sf
    from scripts.compare_sample_rates import compare, convert, error_metrics, spectrum
    from scripts.analyze_audio import sha256

@unittest.skipUnless(READY,'Install optional requirements-audio.txt')
class RateComparisonTests(unittest.TestCase):
    def test_identity_timing_pitch_and_silence(self):
        rate=48000;t=np.arange(rate)/rate
        source=(.5*np.sin(2*np.pi*1000*t))[:,None]
        np.testing.assert_array_equal(convert(source,rate,rate),source)
        for target in (36369,66666,99369):
            derived=convert(source,rate,target)
            self.assertEqual(len(derived),int(np.ceil(len(source)*target/rate)))
            spec=spectrum(derived,target)
            peak=spec['frequencyHz'][np.argmax(spec['meanPowerSpectralDensity'])]
            self.assertLess(abs(peak-1000),8)
            restored=convert(derived,target,rate)
            self.assertLess(error_metrics(source[100:-100],restored[100:len(source)-100])['rmse'],.001)
        self.assertEqual(error_metrics(np.zeros((10,1)),np.zeros((10,1)))['snrStatus'],'exact-match')

    def test_downsampling_filters_above_new_nyquist(self):
        t=np.arange(48000)/48000
        tone=np.sin(2*np.pi*20000*t)[:,None]
        down=convert(tone,48000,36369)
        self.assertLess(float(np.sqrt(np.mean(down[100:-100]**2))),.01)

    def test_stereo_and_derived_file_reports_preserve_original(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'original.wav'
            t=np.arange(6000)/48000;tone=.3*np.sin(2*np.pi*1000*t)
            sf.write(source,np.column_stack([tone,-tone]),48000,subtype='FLOAT')
            before=sha256(source)
            report=compare(source,root/'experiment',[36369,66369])
            self.assertEqual(sha256(source),before)
            self.assertEqual(len(report['conditions']),3)
            for item in report['conditions']:
                info=sf.info(root/'experiment'/item['file'])
                self.assertEqual(info.samplerate,item['targetRateHz'])
                self.assertEqual(info.channels,2)
                self.assertEqual(sha256(root/'experiment'/item['file']),item['sha256'])
                self.assertFalse(item['newCapturedFrequencyInformation'])
            self.assertTrue((root/'experiment/comparison.html').is_file())
            self.assertTrue((root/'experiment/spectra.png').is_file())
            original=(root/'experiment/comparison.json').read_bytes()
            with self.assertRaises(ValueError):compare(source,root/'experiment',[48000])
            self.assertEqual((root/'experiment/comparison.json').read_bytes(),original)

    def test_dry_run_and_invalid_rates_do_not_create_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source.wav'
            sf.write(source,np.zeros(1000),48000)
            compare(source,root/'preview',[66369],dry_run=True)
            self.assertFalse((root/'preview').exists())
            with self.assertRaises(ValueError):compare(source,root/'bad',[0])
            self.assertFalse((root/'bad').exists())

if __name__=='__main__':unittest.main()
