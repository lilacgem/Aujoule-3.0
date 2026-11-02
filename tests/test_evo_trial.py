import importlib.util
from pathlib import Path
import tempfile
import unittest

READY=all(importlib.util.find_spec(name) for name in ('soundfile','numpy','scipy','matplotlib'))
if READY:
    import json,hashlib,copy
    from scripts.run_evo_trial import run_trial,validate_inputs,CORE,PRESET
    from scripts.analyze_audio import sha256

@unittest.skipUnless(READY,'Install optional audio requirements')
class EvoTrialTests(unittest.TestCase):
    def fixture(self,folder):
        windows=[]
        for index,power in enumerate((0.,.0001,.01)):
            windows.append({'index':index,'startSeconds':index*.125,'endSeconds':index*.125+.25,
                            'centerSeconds':index*.125+.125,'commonBandPower':{'bass':power,'mid':0.,'high':0.}})
        conditions=[{'rateHz':44100,'sourceSha256':hashlib.sha256(b'synthetic source record').hexdigest(),'windows':copy.deepcopy(windows)},
                    {'rateHz':48000,'sourceSha256':hashlib.sha256(b'synthetic derived record').hexdigest(),'windows':copy.deepcopy(windows)}]
        conditions[1]['windows'][1]['commonBandPower']['bass']=.00010001
        features={'schema':'AUEVO-MatchedAudioFeatures/v0.2','source':{'filename':'synthetic-input.wav'},
                  'comparisonRef':{'sha256':hashlib.sha256(b'synthetic comparison').hexdigest()},
                  'method':{'windowCount':3,'bandIntegration':{'id':'fractional-bin-cell-overlap/v1'}},
                  'symbolicExperiment':{'receivedCoreSha256':sha256(CORE)},'originalWindows':windows,'conditions':conditions}
        path=folder/'features.json';path.write_text(json.dumps(features))
        summary={key:features[key] for key in ('schema','source','method')}
        summary.update(fullRecordsSha256=sha256(path),originalWindowCount=3,
                       conditions=[{key:value for key,value in item.items() if key!='windows'} for item in conditions])
        summary_path=folder/'summary.json';summary_path.write_text(json.dumps(summary))
        return path,summary_path,features,summary

    def test_trial_outputs_continuous_differences_without_false_root_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path,small,_,_=self.fixture(root)
            original=path.read_bytes()
            report=run_trial(path,small,root/'trial')
            self.assertEqual(path.read_bytes(),original)
            self.assertEqual(report['config']['configuredFocus'],.5)
            self.assertEqual(report['config']['sessionCount'],0)
            self.assertEqual(report['original']['summary']['digitalRootHistogram']['2'],1)
            self.assertEqual(report['zeroInputControl']['digitalRoot'],2)
            self.assertEqual(report['conditions'][0]['differentRootWindows'],0)
            self.assertEqual(report['conditions'][1]['differentRootWindows'],0)
            self.assertGreater(report['conditions'][1]['continuousDifferences']['voiceEnergy']['maxAbsoluteDifference'],0)
            for name in ('trial.html','trial.json','trial-summary.json','trial-timeline.png'):
                self.assertGreater((root/'trial'/name).stat().st_size,0)
            saved=json.loads((root/'trial/trial-summary.json').read_text())
            self.assertEqual(saved['fullTrialSha256'],sha256(root/'trial/trial.json'))
            self.assertNotIn('windows',saved['conditions'][0])
            before=(root/'trial/trial.json').read_bytes()
            with self.assertRaises(ValueError):run_trial(path,small,root/'trial')
            self.assertEqual((root/'trial/trial.json').read_bytes(),before)

    def test_invalid_hash_old_method_timing_and_core_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path,small,features,summary=self.fixture(root)
            with self.assertRaises(ValueError):validate_inputs(features,summary,'bad hash')
            for mutate in (lambda x:x.update(schema='AUEVO-MatchedAudioFeatures/v0.1'),
                           lambda x:x['conditions'][1]['windows'][0].update(startSeconds=.01),
                           lambda x:x['symbolicExperiment'].update(receivedCoreSha256='unknown')):
                altered=copy.deepcopy(features);mutate(altered)
                with self.assertRaises(ValueError):validate_inputs(altered,summary,summary['fullRecordsSha256'])
            path.write_text('tampered')
            with self.assertRaises(ValueError):run_trial(path,small,root/'rejected')
            self.assertFalse((root/'rejected').exists())

    def test_line_endings_recognized_and_fixed_context_not_advanced(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path,small,features,summary=self.fixture(root)
            raw=CORE.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
            features['symbolicExperiment']['receivedCoreSha256']=hashlib.sha256(raw).hexdigest()
            validate_inputs(features,summary,summary['fullRecordsSha256'])
            from scripts.run_evo_trial import trial_records
            config=json.loads(PRESET.read_text())
            repeated=[features['originalWindows'][1],features['originalWindows'][1]]
            records=trial_records(repeated,config)
            self.assertEqual(records[0]['symbolic'],records[1]['symbolic'])
            self.assertFalse(records[0]['symbolic']['historyAdvanced'])

if __name__=='__main__':unittest.main()
