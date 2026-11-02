import importlib.util
from pathlib import Path
import tempfile
import unittest

READY=all(importlib.util.find_spec(name) for name in ('soundfile','numpy','scipy','matplotlib'))
if READY:
    import json,hashlib,copy
    import numpy as np
    import soundfile as sf
    from scripts.compare_audio_features import measure_windows
    from scripts.build_audio_state import build_state,verify_state,export_state
    from scripts.run_evo_trial import CORE
    from scripts.analyze_audio import sha256
    from scripts.adapt_lineage import canonical_bytes

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(READY,'Install optional audio requirements')
class AudioStateDraftTests(unittest.TestCase):
    def fixture(self,root):
        source=root/'synthetic.wav';rate=48000
        time=np.arange(24000)/rate;sf.write(source,.1*np.sin(2*np.pi*1000*time),rate,subtype='FLOAT')
        windows=measure_windows(source,.5,18000,.25,.125,None)
        features={'schema':'AUEVO-MatchedAudioFeatures/v0.2',
                  'source':{'filename':source.name,'sha256':sha256(source),'sampleRateHz':rate,'channels':1},
                  'comparisonRef':{'sha256':hashlib.sha256(b'synthetic comparison').hexdigest()},
                  'method':{'windowCount':len(windows),'commonUpperHz':18000,'bandIntegration':{'id':'fractional-bin-cell-overlap/v1'}},
                  'symbolicExperiment':{'enabled':False,'receivedCoreSha256':sha256(CORE)},
                  'originalWindows':windows,'conditions':[{'rateHz':48000,'sourceSha256':sha256(source),'windows':copy.deepcopy(windows)}]}
        return features

    def inputs(self,features):
        raw=json.dumps(features).encode();digest=hashlib.sha256(raw).hexdigest()
        summary={key:features[key] for key in ('schema','source','method')}
        summary.update(fullRecordsSha256=digest,originalWindowCount=len(features['originalWindows']),
                       conditions=[{key:value for key,value in item.items() if key!='windows'} for item in features['conditions']])
        return digest,summary,raw

    def test_all_observations_preserved_and_alternatives_not_sessions(self):
        with tempfile.TemporaryDirectory() as directory:
            features=self.fixture(Path(directory));digest,summary,_=self.inputs(features)
            state=build_state(features,summary,digest);payload=state['payload']
            self.assertEqual(payload['measurementRecord']['observations'],features['originalWindows'])
            self.assertEqual(payload['symbolicOverlay']['records'],[])
            self.assertEqual(payload['symbolicOverlay']['status'],'not-attached')
            self.assertFalse(payload['lineage']['persistentEvolutionAdvanced'])
            self.assertIsNone(payload['experience']['directives'])
            self.assertEqual(payload['alternativeConditions'][0]['relationship'],'same-source-software-derivative-not-new-session')
            self.assertEqual(build_state(features,summary,digest)['stateId'],state['stateId'])
            changed=copy.deepcopy(features);changed['originalWindows'][0]['rmsLinear']+=1e-6
            new_hash,new_summary,_=self.inputs(changed)
            self.assertNotEqual(build_state(changed,new_summary,new_hash)['stateId'],state['stateId'])

    def test_symbolic_overlay_separated_and_no_silent_unknown_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            features=self.fixture(Path(directory));features['symbolicExperiment']['enabled']=True
            for row in features['originalWindows']:row['evoMetricsExperiment']={'digitalRoot':2,'historyAdvanced':False}
            digest,summary,_=self.inputs(features);state=build_state(features,summary,digest)
            self.assertEqual(len(state['payload']['symbolicOverlay']['records']),3)
            self.assertTrue(all('evoMetricsExperiment' not in row for row in state['payload']['measurementRecord']['observations']))
            self.assertTrue(all(row['verificationStatus']=='preserved-not-recomputed' for row in state['payload']['symbolicOverlay']['records']))
            features['originalWindows'][0]['unknownField']=1
            digest,summary,_=self.inputs(features)
            with self.assertRaises(ValueError):build_state(features,summary,digest)

    def test_export_hash_refusal_overwrite_and_unsupported_transition(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);features=self.fixture(root);digest,summary,raw=self.inputs(features)
            path=root/'features.json';path.write_bytes(raw)
            small=root/'summary.json';small.write_text(json.dumps(summary))
            state=export_state(path,small,root/'draft');verify_state(state)
            review=json.loads((root/'draft/state-review.json').read_text())
            self.assertEqual(review['stateFileSha256'],sha256(root/'draft/audio-state.json'))
            with self.assertRaises(ValueError):export_state(path,small,root/'draft')
            corrupted=copy.deepcopy(state);corrupted['payload']['lineage']['persistentEvolutionAdvanced']=True
            new_hash=hashlib.sha256(canonical_bytes(corrupted['payload'])).hexdigest()
            corrupted.update(contentHash=new_hash,stateId=f'audio-draft:sha256:{new_hash}')
            with self.assertRaises(ValueError):verify_state(corrupted)
            bad=copy.deepcopy(state);bad['payload']['measurementRecord']['observations'][0]['rmsLinear']=float('nan')
            with self.assertRaises(ValueError):verify_state(bad)

    @unittest.skipUnless(importlib.util.find_spec('jsonschema'),'Optional schema review check requires jsonschema')
    def test_candidate_json_schema_accepts_export_and_rejects_permission_expansion(self):
        import jsonschema
        schema=json.loads((ROOT/'schemas/audio-state-draft-v0.1.schema.json').read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        validator=jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker())
        with tempfile.TemporaryDirectory() as directory:
            features=self.fixture(Path(directory));digest,summary,_=self.inputs(features)
            state=build_state(features,summary,digest);validator.validate(state)
            state['payload']['permissions']['grantsCloudUpload']=True
            with self.assertRaises(jsonschema.ValidationError):validator.validate(state)

if __name__=='__main__':unittest.main()
