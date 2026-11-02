import importlib.util
from pathlib import Path
import tempfile
import unittest

READY=all(importlib.util.find_spec(name) for name in ('soundfile','numpy','scipy','matplotlib'))
if READY:
    import json,copy
    from scripts.demo_evidence_resolution import make_fixture,run_demo
    from scripts.resolve_state_evidence import resolve_evidence,save_resolution
    from scripts.demo_session_transition import rehash
    from scripts.adapt_lineage import LineageError

@unittest.skipUnless(READY,'Install optional audio requirements')
class EvidenceTests(unittest.TestCase):
    def resolve(self,files,**kwargs):
        return resolve_evidence(files['state'],files['features'],files['summary'],files['comparison'],**kwargs)

    def test_resolves_actual_files_and_optional_bytes_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            files=make_fixture(Path(directory)/'inputs');before={key:path.read_bytes() for key,path in files.items()}
            result=self.resolve(files,source_path=files['source'],verify_derived=True)['resolution']
            self.assertEqual(result['status'],'measurement-chain-resolved')
            self.assertTrue(result['checks']['primaryObservationsMatch'])
            self.assertEqual(result['sourceBytes']['status'],'sha256-matched')
            self.assertFalse(result['sourceBytes']['mediaHeaderChecked'])
            self.assertEqual(len(result['derivedBytes']['results']),1)
            self.assertFalse(result['authorizedForHistoryCommit'])
            for key,path in files.items():self.assertEqual(path.read_bytes(),before[key])
            partial=self.resolve(files)['resolution']
            self.assertEqual(partial['sourceBytes']['status'],'not-provided')
            self.assertFalse(partial['derivedBytes']['requested'])

    def test_missing_hash_summary_and_observation_mismatches_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);files=make_fixture(root/'inputs')
            with self.assertRaises(LineageError) as caught:self.resolve({**files,'features':root/'missing.json'})
            self.assertEqual(caught.exception.code,'EVIDENCE_MISSING')
            changed=root/'changed.json';changed.write_text('{}')
            with self.assertRaises(LineageError) as caught:self.resolve({**files,'features':changed})
            self.assertEqual(caught.exception.code,'FEATURE_HASH_MISMATCH')
            summary=json.loads(files['summary'].read_text());summary['fullRecordsSha256']='0'*64
            wrong=root/'summary.json';wrong.write_text(json.dumps(summary))
            with self.assertRaises(LineageError) as caught:self.resolve({**files,'summary':wrong})
            self.assertEqual(caught.exception.code,'SUMMARY_LINK_MISMATCH')
            state=json.loads(files['state'].read_text());state['payload']['measurementRecord']['observations'][0]['rmsLinear']=.25
            changed.write_text(json.dumps(rehash(state)))
            with self.assertRaises(LineageError) as caught:self.resolve({**files,'state':changed})
            self.assertEqual(caught.exception.code,'OBSERVATION_MISMATCH')

    def test_source_metadata_override_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);files=make_fixture(root/'inputs')
            state=json.loads(files['state'].read_text());state['payload']['sourceRef']['filename']='corrected-description.json'
            changed=root/'state.json';changed.write_text(json.dumps(rehash(state)))
            with self.assertRaises(LineageError) as caught:self.resolve({**files,'state':changed})
            self.assertEqual(caught.exception.code,'STATE_EVIDENCE_MISMATCH')

    def test_demo_and_save_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);report=run_demo(root/'demo')
            self.assertEqual(report['accepted'],1);self.assertEqual(len(report['rejected']),6)
            files=make_fixture(root/'inputs');result=self.resolve(files)
            target=root/'resolved';save_resolution(target,result);before=(target/'evidence-resolution.json').read_bytes()
            with self.assertRaises(LineageError):save_resolution(target,result)
            self.assertEqual((target/'evidence-resolution.json').read_bytes(),before)
            altered=copy.deepcopy(result);altered['resolution']['historyAdvanced']=True
            with self.assertRaises(LineageError):save_resolution(root/'tampered-report',altered)
            self.assertFalse((root/'tampered-report').exists())

if __name__=='__main__':unittest.main()
