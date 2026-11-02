"""Synthetic transition validation cases, not real audio or persistent evolution."""
import argparse
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import tempfile

try:
    from scripts.build_audio_state import build_state,verify_state
    from scripts.review_session_transition import review_transition,reference,save_review
    from scripts.run_evo_trial import CORE
    from scripts.adapt_lineage import canonical_bytes,LineageError
    from scripts.analyze_audio import sha256
except ModuleNotFoundError:
    from build_audio_state import build_state,verify_state
    from review_session_transition import review_transition,reference,save_review
    from run_evo_trial import CORE
    from adapt_lineage import canonical_bytes,LineageError
    from analyze_audio import sha256


def synthetic_state(revision=1):
    spectral={'centroidHz':1000.,'bandwidthHz':100.,'rolloff85Hz':1100.,'flatness':.1}
    observation={'index':0,'startSeconds':0.,'endSeconds':.25,'centerSeconds':.125,
                 'actualStartSeconds':0.,'actualEndSeconds':.25,'windowSamples':12000,'binSpacingHz':4.,
                 'evidenceClass':'MEASURED','rmsLinear':.1 if revision==1 else .12,'samplePeak':.2 if revision==1 else .24,
                 'crestFactor':2.,'rmsChangeDb':None,'positiveBandChange':None,
                 'commonBandPower':{'bass':.001,'mid':.002,'high':.0001},'fullBand':spectral,'commonBand':spectral.copy()}
    source={'filename':'SYNTHETIC-no-audio-description.json','sha256':hashlib.sha256(b'synthetic descriptor, not an audio file').hexdigest(),
            'kind':'synthetic-fixture-not-native-audio','sampleRateHz':48000,'channels':1}
    features={'schema':'AUEVO-MatchedAudioFeatures/v0.2','source':source,
              'comparisonRef':{'sha256':hashlib.sha256(b'synthetic comparison description').hexdigest()},
              'method':{'windowCount':1,'bandIntegration':{'id':'fractional-bin-cell-overlap/v1'},
                        'origin':'synthetic contract fixture; no FFT analysis performed','syntheticRevision':revision},
              'symbolicExperiment':{'enabled':False,'receivedCoreSha256':sha256(CORE)},
              'originalWindows':[observation],
              'conditions':[{'rateHz':48000,'sourceSha256':source['sha256'],'windows':[copy.deepcopy(observation)]}]}
    digest=hashlib.sha256(canonical_bytes(features)).hexdigest()
    summary={key:features[key] for key in ('schema','source','method')}
    summary.update(fullRecordsSha256=digest,originalWindowCount=1,
                   conditions=[{key:value for key,value in item.items() if key!='windows'} for item in features['conditions']])
    return build_state(features,summary,digest)


def rehash(state):
    result=copy.deepcopy(state)
    digest=hashlib.sha256(canonical_bytes(result['payload'])).hexdigest()
    result.update(contentHash=digest,stateId=f'audio-draft:sha256:{digest}',createdAt=datetime.now(timezone.utc).isoformat())
    return verify_state(result)


def request_for(prior,candidate,kind):
    return {'schema':'AUEVO-SessionTransitionRequest/v0.1','requestId':f'synthetic-{kind}',
            'priorStateRef':reference(prior),'expectedCurrentStateRef':reference(prior),'candidateStateRef':reference(candidate),
            'session':{'sessionId':f'synthetic-session-{kind}','kind':kind,'origin':'synthetic-test',
                       'purpose':'Synthetic validation only; not a new recorded session.'},
            'permissions':{'allowTransitionReview':True,'allowLocalReviewReport':True,'allowHistoryCommit':False,
                           'allowCloudUpload':False,'allowIdentityMemory':False,'retentionNote':'Local synthetic test reports; delete manually.'},
            'corrections':[],'claims':[]}


def run_demo(output=None):
    root=Path(__file__).resolve().parents[1]
    if output is None:
        runtime=root/'runtime';runtime.mkdir(exist_ok=True)
        output=Path(tempfile.mkdtemp(prefix='transition-demo-',dir=runtime))
    else:
        output=Path(output);output.mkdir(exist_ok=False,parents=True)
    prior=synthetic_state();changed=synthetic_state(2)
    corrected=copy.deepcopy(prior);corrected['payload']['sourceRef']['filename']='SYNTHETIC-corrected-display-label.json';corrected=rehash(corrected)
    correction_request=request_for(prior,corrected,'metadata-correction')
    correction_request['corrections']=[{'recordId':'synthetic-correction-1','targetStateRef':reference(prior),
                                       'targetPath':'/sourceRef/filename','before':prior['payload']['sourceRef']['filename'],
                                       'after':corrected['payload']['sourceRef']['filename'],'author':'synthetic-test-author',
                                       'createdAt':'2026-01-01T00:00:00Z','reason':'Synthetic label correction; original remains unchanged.'}]
    success=[('replay',prior,request_for(prior,prior,'replay')),
             ('reanalysis',changed,request_for(prior,changed,'reanalysis')),
             ('metadata-correction',corrected,correction_request)]
    report={'schema':'AUEVO-TransitionDemo/v0.1','synthetic':True,'accepted':[],'rejected':[],'historyAdvanced':False}
    for name,candidate,request in success:
        result=review_transition(prior,candidate,request)
        save_review(output/name,result)
        report['accepted'].append({'case':name,'status':result['review']['status'],'changedFields':result['review']['changes']['totalChangedFields']})
    bad_claim=request_for(prior,changed,'reanalysis');bad_claim['claims']=[{'recordId':'conflicting-synthetic-claim','targetPath':'/measurementRecord/observations/0/rmsLinear','value':999}]
    bad_permission=request_for(prior,changed,'reanalysis');bad_permission['permissions']['allowHistoryCommit']=True
    bad_prior=request_for(prior,changed,'reanalysis');bad_prior['priorStateRef']['contentHash']='0'*64
    bad_before=copy.deepcopy(correction_request);bad_before['corrections'][0]['before']='wrong previous value'
    failures=[('conflict',changed,bad_claim,None,'CONFLICT_UNRESOLVED'),
              ('stale-current',changed,request_for(prior,changed,'reanalysis'),changed,'STALE_CURRENT_STATE'),
              ('history-permission',changed,bad_permission,None,'UNSUPPORTED_PERMISSION'),
              ('wrong-prior',changed,bad_prior,None,'PRIOR_STATE_MISMATCH'),
              ('wrong-correction-before',corrected,bad_before,None,'CORRECTION_BEFORE_MISMATCH')]
    for name,candidate,request,current,expected in failures:
        try:review_transition(prior,candidate,request,current)
        except LineageError as error:
            if error.code!=expected:raise
            report['rejected'].append({'case':name,'code':error.code})
        else:raise AssertionError(f'Expected rejection: {name}')
    (output/'demo-summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for name,state in [('prior',prior),('candidate-reanalysis',changed),('candidate-correction',corrected)]:
        (output/f'{name}.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    page='<!doctype html><html lang="en"><meta charset="utf-8"><title>Transition validator demo</title><style>body{font:16px system-ui;max-width:1000px;margin:auto;padding:24px}pre{white-space:pre-wrap}</style><h1>Synthetic session-transition validator demo</h1><p>No actual recorded session, carry, persistent history or current-state pointer was changed.</p><pre>'+json.dumps(report,indent=2)+'</pre><p><a href="replay/transition-review.html">Replay</a> • <a href="reanalysis/transition-review.html">Reanalysis</a> • <a href="metadata-correction/transition-review.html">Correction</a> • <a href="demo-summary.json">Summary JSON</a></p></html>'
    (output/'demo.html').write_text(page,encoding='utf-8')
    print(f'PASS: 3 accepted review cases, 5 expected rejections. Open {output/"demo.html"}')
    print('Synthetic fixtures only. No audio, original state or persistent evolution modified.')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    run_demo(parser.parse_args().output)
