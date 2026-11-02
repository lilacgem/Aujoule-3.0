import importlib.util
from pathlib import Path
import tempfile
import unittest

READY=all(importlib.util.find_spec(name) for name in ('soundfile','numpy','scipy','matplotlib'))
if READY:
    import copy
    from scripts.demo_session_transition import synthetic_state,rehash,request_for,run_demo
    from scripts.review_session_transition import review_transition,save_review,diff_payload
    from scripts.adapt_lineage import LineageError

@unittest.skipUnless(READY,'Install optional audio requirements')
class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.prior=synthetic_state();self.candidate=synthetic_state(2)

    def test_reanalysis_links_and_replay_do_not_modify_snapshots(self):
        before=copy.deepcopy(self.prior);after=copy.deepcopy(self.candidate)
        request=request_for(self.prior,self.candidate,'reanalysis')
        result=review_transition(self.prior,self.candidate,request)
        self.assertEqual(self.prior,before);self.assertEqual(self.candidate,after)
        self.assertEqual(result['review']['status'],'valid-for-review-not-commit')
        self.assertGreater(result['review']['changes']['totalChangedFields'],0)
        self.assertFalse(result['review']['historyAdvanced']);self.assertFalse(result['review']['authorizedForHistoryCommit'])
        replay=request_for(self.prior,self.prior,'replay')
        a=review_transition(self.prior,self.prior,replay);b=review_transition(self.prior,self.prior,replay)
        self.assertEqual(a['reviewId'],b['reviewId'])
        self.assertEqual(a['review']['status'],'replay-no-advance')
        self.assertEqual(a['review']['changes']['totalChangedFields'],0)

    def test_stale_hash_conflicts_and_permissions_reject(self):
        request=request_for(self.prior,self.candidate,'reanalysis')
        cases=[]
        stale=copy.deepcopy(request);stale['expectedCurrentStateRef']['contentHash']='0'*64
        cases.append((self.prior,self.candidate,stale,'STALE_CURRENT_STATE'))
        conflict=copy.deepcopy(request);conflict['claims']=[{'recordId':'x','targetPath':'/measurementRecord/observations/0/rmsLinear','value':999}]
        cases.append((self.prior,self.candidate,conflict,'CONFLICT_UNRESOLVED'))
        boolean=copy.deepcopy(request);boolean['claims']=[{'recordId':'typed','targetPath':'/measurementRecord/observations/0/startSeconds','value':False}]
        cases.append((self.prior,self.candidate,boolean,'CONFLICT_UNRESOLVED'))
        denied=copy.deepcopy(request);denied['permissions']['allowTransitionReview']=False
        cases.append((self.prior,self.candidate,denied,'PERMISSION_DENIED'))
        grant=copy.deepcopy(request);grant['permissions']['allowHistoryCommit']=True
        cases.append((self.prior,self.candidate,grant,'UNSUPPORTED_PERMISSION'))
        corrupted=copy.deepcopy(self.candidate);corrupted['payload']['sourceRef']['filename']='tampered'
        cases.append((self.prior,corrupted,request,'STATE_INVALID'))
        for prior,candidate,req,code in cases:
            with self.subTest(code=code),self.assertRaises(LineageError) as caught:review_transition(prior,candidate,req)
            self.assertEqual(caught.exception.code,code)

    def test_numeric_corrections_and_unexplained_metadata_not_allowed(self):
        corrected=copy.deepcopy(self.prior);corrected['payload']['sourceRef']['filename']='synthetic-label.json';corrected=rehash(corrected)
        request=request_for(self.prior,corrected,'metadata-correction')
        request['corrections']=[{'recordId':'c1','targetStateRef':request['priorStateRef'],
                                 'targetPath':'/sourceRef/filename','before':self.prior['payload']['sourceRef']['filename'],
                                 'after':'synthetic-label.json','author':'synthetic author','createdAt':'2026-01-01T00:00:00Z','reason':'Synthetic test'}]
        self.assertEqual(review_transition(self.prior,corrected,request)['review']['status'],'valid-for-review-not-commit')
        missing=copy.deepcopy(request);missing['corrections'][0]['author']=''
        with self.assertRaises(LineageError):review_transition(self.prior,corrected,missing)
        numeric=copy.deepcopy(request);numeric['corrections'][0]['targetPath']='/measurementRecord/observations/0/rmsLinear'
        with self.assertRaises(LineageError) as caught:review_transition(self.prior,corrected,numeric)
        self.assertEqual(caught.exception.code,'CORRECTION_SCOPE_UNSUPPORTED')
        contradictory=copy.deepcopy(request);second=copy.deepcopy(request['corrections'][0]);second.update(recordId='c2',after='different');contradictory['corrections'].append(second)
        with self.assertRaises(LineageError) as caught:review_transition(self.prior,corrected,contradictory)
        self.assertEqual(caught.exception.code,'CONFLICT_UNRESOLVED')

    def test_new_source_and_detailed_diff_limits(self):
        changed=copy.deepcopy(self.candidate);changed['payload']['sourceRef']['sha256']='a'*64;changed['payload']['sourceRef']['filename']='new-synthetic.json';changed=rehash(changed)
        result=review_transition(self.prior,changed,request_for(self.prior,changed,'new-source'))
        self.assertEqual(result['review']['status'],'valid-for-review-not-commit')
        prior=copy.deepcopy(self.prior)
        prior['payload']['alternativeConditions'].append({'rateHz':36369,'sourceSha256':'b'*64,'relationship':'same-source-software-derivative-not-new-session','featureRecordsRef':{'sha256':'c'*64,'selector':'synthetic'}})
        prior=rehash(prior)
        derivative=copy.deepcopy(changed);derivative['payload']['sourceRef']['sha256']='b'*64;derivative=rehash(derivative)
        with self.assertRaises(LineageError) as caught:review_transition(prior,derivative,request_for(prior,derivative,'new-source'))
        self.assertEqual(caught.exception.code,'DERIVATIVE_NOT_NEW_SESSION')
        diff=diff_payload(list(range(500)),list(range(1,501)),limit=3)
        self.assertEqual(diff['totalChangedFields'],500);self.assertEqual(len(diff['details']),3);self.assertTrue(diff['detailsTruncated'])

    def test_demo_and_report_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'demo';report=run_demo(output)
            self.assertEqual(len(report['accepted']),3);self.assertEqual(len(report['rejected']),5)
            self.assertTrue((output/'demo.html').is_file())
            result=review_transition(self.prior,self.prior,request_for(self.prior,self.prior,'replay'))
            target=Path(directory)/'review';save_review(target,result);before=(target/'transition-review.json').read_bytes()
            with self.assertRaises(LineageError):save_review(target,result)
            self.assertEqual((target/'transition-review.json').read_bytes(),before)
            result['review']['request']['permissions']['allowLocalReviewReport']=False
            with self.assertRaises(LineageError):save_review(Path(directory)/'denied',result)
            self.assertFalse((Path(directory)/'denied').exists())

if __name__=='__main__':unittest.main()
