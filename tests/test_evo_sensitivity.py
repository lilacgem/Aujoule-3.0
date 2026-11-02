import importlib.util
from pathlib import Path
import tempfile
import unittest

READY=all(importlib.util.find_spec(name) for name in ('soundfile','numpy','scipy','matplotlib'))
if READY:
    import json,hashlib,copy
    from scripts.run_evo_sensitivity import variants,run_study,PLAN,contribution_summary
    from scripts.run_evo_trial import trial_records,CORE,PRESET
    from scripts.evo_metrics_experiment import evaluate
    from scripts.analyze_audio import sha256

@unittest.skipUnless(READY,'Install optional audio requirements')
class SensitivityTests(unittest.TestCase):
    def fixture(self,root):
        windows=[{'index':i,'startSeconds':i*.125,'endSeconds':i*.125+.25,'centerSeconds':i*.125+.125,
                  'commonBandPower':{'bass':value,'mid':value,'high':value}}
                 for i,value in enumerate((0.,.00000025,.0004))]
        features={'schema':'AUEVO-MatchedAudioFeatures/v0.2','source':{'filename':'synthetic.wav'},
                  'method':{'windowCount':3,'bandIntegration':{'id':'fractional-bin-cell-overlap/v1'}},
                  'symbolicExperiment':{'receivedCoreSha256':sha256(CORE)},'originalWindows':windows,
                  'conditions':[{'rateHz':44100,'sourceSha256':hashlib.sha256(b'synthetic').hexdigest(),'windows':copy.deepcopy(windows)}]}
        path=root/'features.json';path.write_text(json.dumps(features))
        summary={key:features[key] for key in ('schema','source','method')}
        summary.update(fullRecordsSha256=sha256(path),originalWindowCount=3,
                       conditions=[{key:value for key,value in item.items() if key!='windows'} for item in features['conditions']])
        small=root/'summary.json';small.write_text(json.dumps(summary))
        return path,small

    def test_every_variant_changes_one_factor_only(self):
        plan=json.loads(PLAN.read_text());settings=variants(plan)
        self.assertEqual(plan['baseline'],json.loads(PRESET.read_text()))
        self.assertEqual(len(settings),13)
        for setting in settings[1:]:
            changed={key for key,value in setting['config'].items() if value!=settings[0]['config'][key]}
            self.assertEqual(changed,{setting['factor']})
        with self.assertRaises(ValueError):variants({**plan,'factors':{'sessionCount':[0]}})

    def test_raw_dominance_modulo_invariance_floor_and_cap(self):
        config=json.loads(PRESET.read_text())
        bands={'bass':.0004,'mid':.0004,'high':.0004}
        base=evaluate(bands,config)
        results=[evaluate(bands,{**config,'sessionCount':count}) for count in (1,10,100,101)]
        self.assertTrue(all(result['digitalRoot']==base['digitalRoot'] for result in results))
        self.assertGreater(results[2]['sessionCountContribution'],results[0]['sessionCountContribution'])
        self.assertEqual(results[2],results[3])
        quiet={key:.00000025 for key in bands}
        self.assertNotEqual(evaluate(quiet,config)['digitalRoot'],evaluate(quiet,{**config,'sessionCount':1})['digitalRoot'])
        records=trial_records([{'index':0,'startSeconds':0,'endSeconds':.25,'centerSeconds':.125,'commonBandPower':quiet}],{**config,'configuredFocus':0})
        shares=contribution_summary(records)['sessionContributionShare']
        self.assertIsNone(shares['mean']);self.assertEqual(shares['undefinedZeroTotalWindows'],1)

    def test_study_report_identity_integrity_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path,small=self.fixture(root);before=path.read_bytes()
            report=run_study(path,small,root/'study')
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(len(report['variants']),13)
            self.assertTrue(all(item['rateConditions'][0]['versusOriginalAtSameSetting']['differentRootWindows']==0 for item in report['variants']))
            self.assertTrue(all(not item['historyAdvanced'] for item in report['variants']))
            self.assertTrue((root/'study/sensitivity.html').is_file())
            self.assertTrue((root/'study/sensitivity.png').is_file())
            old=(root/'study/sensitivity-summary.json').read_bytes()
            with self.assertRaises(ValueError):run_study(path,small,root/'study')
            self.assertEqual((root/'study/sensitivity-summary.json').read_bytes(),old)
            path.write_text('{}')
            with self.assertRaises(ValueError):run_study(path,small,root/'rejected')
            self.assertFalse((root/'rejected').exists())

if __name__=='__main__':unittest.main()
