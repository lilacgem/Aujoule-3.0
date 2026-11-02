import importlib.util
from pathlib import Path
import tempfile
import unittest

READY=all(importlib.util.find_spec(name) for name in ('soundfile','numpy','scipy','matplotlib'))
if READY:
    import numpy as np
    import soundfile as sf
    from scripts.compare_sample_rates import compare
    from scripts.compare_audio_features import measure_windows,compare_features
    from scripts.evo_metrics_experiment import evaluate,validate_config
    from scripts.analyze_audio import sha256

CONFIG={'schema':'AUEVO-EvoMetricsExperiment/v0.1','enabled':True,'configuredFocus':.5,
        'sessionCount':0,'priorLeftover':1,'bandRmsReference':.1,'evaluationMode':'independent-windows-fixed-context'}

@unittest.skipUnless(READY,'Install optional requirements-audio.txt')
class MatchedFeatureTests(unittest.TestCase):
    def test_symbolic_core_is_explicit_separate_and_not_cumulative(self):
        zero=evaluate({'bass':0.,'mid':0.,'high':0.},CONFIG)
        self.assertEqual(zero['gRootLevel'],2)
        self.assertEqual(zero['shape'],{'p':2,'q':5})
        self.assertFalse(zero['historyAdvanced'])
        self.assertEqual(zero,evaluate({'bass':0.,'mid':0.,'high':0.},CONFIG))
        self.assertEqual(zero['focusOrigin'],'CONFIGURED_NOT_CAMERA_MEASURED')
        loud=evaluate({'bass':1.,'mid':1.,'high':1.},CONFIG)
        self.assertEqual(loud['voiceEnergy'],1.)
        self.assertEqual(len(loud['normalizationClippedBands']),3)
        self.assertAlmostEqual(loud['audioContribution'],.5)
        self.assertEqual(loud['sessionCountContribution'],0)
        self.assertIsNone(evaluate({'bass':0.,'mid':0.,'high':0.},{**CONFIG,'enabled':False}))
        for update in [{'configuredFocus':float('nan')},{'priorLeftover':10},{'sessionCount':-1},{'bandRmsReference':0}]:
            with self.assertRaises(ValueError):validate_config({**CONFIG,**update})

    def test_matching_times_stereo_power_and_silence(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'source.wav'
            t=np.arange(48000)/48000;tone=.5*np.sin(2*np.pi*1000*t)
            sf.write(path,np.column_stack([tone,-tone]),48000,subtype='FLOAT')
            records=measure_windows(path,1,18000,.25,.125,None)
            self.assertEqual(len(records),7)
            self.assertEqual(records[0]['startSeconds'],0)
            self.assertEqual(records[-1]['endSeconds'],1)
            self.assertAlmostEqual(records[0]['rmsLinear'],.5/np.sqrt(2),places=6)
            self.assertAlmostEqual(records[0]['commonBand']['centroidHz'],1000,places=2)
            self.assertGreater(records[0]['commonBandPower']['mid'],.12)
            self.assertNotIn('evoMetricsExperiment',records[0])
            sf.write(path,np.zeros(48000),48000)
            silent=measure_windows(path,1,18000,.25,.125,CONFIG)
            self.assertIsNone(silent[0]['commonBand']['centroidHz'])
            self.assertIsNone(silent[0]['crestFactor'])

    def test_end_to_end_hashes_common_windows_identity_and_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'original.wav'
            t=np.arange(24000)/48000
            sf.write(source,.2*np.sin(2*np.pi*1000*t),48000,subtype='FLOAT')
            original_hash=sha256(source)
            compare(source,root/'rates',[36369])
            result=compare_features(source,root/'rates/comparison.json',root/'features',config=CONFIG)
            self.assertEqual(sha256(source),original_hash)
            self.assertEqual(result['method']['commonUpperHz'],18184.5)
            self.assertEqual(result['method']['windowCount'],3)
            identity=next(x for x in result['conditions'] if x['rateHz']==48000)
            self.assertEqual(identity['differencesFromOriginal']['rmsLinear']['maxAbsoluteDifference'],0)
            self.assertEqual(identity['symbolicComparison']['differentRootWindows'],0)
            self.assertTrue((root/'features/features.html').is_file())
            import json
            summary=json.loads((root/'features/summary.json').read_text())
            self.assertNotIn('originalWindows',summary)
            self.assertTrue(all('windows' not in condition for condition in summary['conditions']))
            self.assertEqual(summary['fullRecordsSha256'],sha256(root/'features/features.json'))
            before=(root/'features/features.json').read_bytes()
            with self.assertRaises(ValueError):compare_features(source,root/'rates/comparison.json',root/'features')
            self.assertEqual((root/'features/features.json').read_bytes(),before)
            derived=root/'rates/derived-36369Hz.wav';derived.write_bytes(b'tampered')
            with self.assertRaises(ValueError):compare_features(source,root/'rates/comparison.json',root/'rejected')
            self.assertFalse((root/'rejected').exists())

if __name__=='__main__':unittest.main()
