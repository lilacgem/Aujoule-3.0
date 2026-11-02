"""Review proposed state transitions without committing history or altering state."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import tempfile

try:
    from scripts.build_audio_state import verify_state
    from scripts.compile_package import load_json
    from scripts.adapt_lineage import canonical_bytes,LineageError
    from scripts.analyze_audio import sha256
except ModuleNotFoundError:
    from build_audio_state import verify_state
    from compile_package import load_json
    from adapt_lineage import canonical_bytes,LineageError
    from analyze_audio import sha256

REQUEST_SCHEMA='AUEVO-SessionTransitionRequest/v0.1'
CORRECTION_PATHS={'/sourceRef/filename','/sourceRef/captureChain'}


def fail(code,message,path=None):raise LineageError(code,message,path)


def reference(state):return {'stateId':state['stateId'],'contentHash':state['contentHash']}


def text(value,name):
    if not isinstance(value,str) or not value.strip():fail('REQUEST_INVALID',f'{name} must be nonempty text.',name)


def same_json(a,b):
    if type(a) in (int,float) and type(b) in (int,float):
        return math.isfinite(a) and math.isfinite(b) and a==b
    if type(a)!=type(b):return False
    if isinstance(a,dict):return set(a)==set(b) and all(same_json(a[key],b[key]) for key in a)
    if isinstance(a,list):return len(a)==len(b) and all(same_json(x,y) for x,y in zip(a,b))
    return a==b


def resolve(payload,pointer):
    if not isinstance(pointer,str) or not pointer.startswith('/') or re.search(r'~(?![01])',pointer):
        fail('REQUEST_INVALID','Invalid JSON pointer.',str(pointer))
    value=payload
    try:
        for part in pointer[1:].split('/'):
            part=part.replace('~1','/').replace('~0','~')
            if isinstance(value,list):
                if not re.fullmatch(r'0|[1-9][0-9]*',part):raise KeyError(part)
                value=value[int(part)]
            else:value=value[part]
    except (KeyError,TypeError,IndexError):fail('REFERENCE_UNRESOLVED','Referenced field does not exist.',pointer)
    return value


def utc_time(value):
    text(value,'createdAt')
    try:
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
        if parsed.tzinfo is None or parsed.utcoffset().total_seconds()!=0:raise ValueError()
    except ValueError:fail('REQUEST_INVALID','Correction timestamp must be UTC ISO-8601.','createdAt')


def diff_payload(before,after,limit=200):
    details=[];total=0
    def record(path,old,new,kind):
        nonlocal total
        total+=1
        if len(details)<limit:details.append({'path':path,'before':old,'after':new,'kind':kind})
    def walk(a,b,path):
        if isinstance(a,dict) and isinstance(b,dict):
            for key in sorted(set(a)|set(b)):
                target=path+'/'+str(key).replace('~','~0').replace('/','~1')
                if key not in a:record(target,None,b[key],'added')
                elif key not in b:record(target,a[key],None,'removed')
                else:walk(a[key],b[key],target)
        elif isinstance(a,list) and isinstance(b,list):
            for index in range(max(len(a),len(b))):
                target=path+'/'+str(index)
                if index>=len(a):record(target,None,b[index],'added')
                elif index>=len(b):record(target,a[index],None,'removed')
                else:walk(a[index],b[index],target)
        elif type(a)!=type(b) or a!=b:record(path,a,b,'changed')
    walk(before,after,'')
    return {'totalChangedFields':total,'detailLimit':limit,'detailsTruncated':total>len(details),'details':details}


def review_transition(prior,candidate,request,current=None):
    for name,state in [('prior',prior),('candidate',candidate),('current',current if current is not None else prior)]:
        try:
            verify_state(state)
            payload=state['payload']
            for value in (payload['sourceRef']['sha256'],payload['measurementRecord']['featureSha256']):
                if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('Invalid source/measurement reference digest.')
            text(payload['sourceRef']['filename'],'source filename')
            utc_time(state['createdAt'])
            previous=-1
            for index,observation in enumerate(payload['measurementRecord']['observations']):
                if observation['index']!=index or observation['startSeconds']<=previous:raise ValueError('Observation index/time order mismatch.')
                previous=observation['startSeconds']
        except (ValueError,KeyError,TypeError,AttributeError) as error:fail('STATE_INVALID',f'{name} snapshot failed validation: {error}',name)
    current=prior if current is None else current
    required={'schema','requestId','priorStateRef','expectedCurrentStateRef','candidateStateRef','session','permissions','corrections','claims'}
    if not isinstance(request,dict) or set(request)!=required or request['schema']!=REQUEST_SCHEMA:
        fail('REQUEST_INVALID','Unsupported or incomplete transition request.')
    text(request['requestId'],'requestId')
    if request['priorStateRef']!=reference(prior):fail('PRIOR_STATE_MISMATCH','Prior state reference does not match supplied snapshot.','priorStateRef')
    if request['candidateStateRef']!=reference(candidate):fail('CANDIDATE_STATE_MISMATCH','Candidate reference does not match supplied snapshot.','candidateStateRef')
    if request['expectedCurrentStateRef']!=reference(current) or reference(current)!=reference(prior):
        fail('STALE_CURRENT_STATE','Expected current state does not match the supplied current snapshot.','expectedCurrentStateRef')
    permissions=request['permissions']
    keys={'allowTransitionReview','allowLocalReviewReport','allowHistoryCommit','allowCloudUpload','allowIdentityMemory','retentionNote'}
    if not isinstance(permissions,dict) or set(permissions)!=keys or any(type(permissions[key]) is not bool for key in keys-{'retentionNote'}):
        fail('REQUEST_INVALID','Explicit boolean review permissions and retention note required.','permissions')
    if not permissions['allowTransitionReview']:fail('PERMISSION_DENIED','Transition review is not allowed.','permissions')
    if permissions['allowHistoryCommit'] or permissions['allowCloudUpload'] or permissions['allowIdentityMemory']:
        fail('UNSUPPORTED_PERMISSION','This validator cannot commit history, upload or create identity memory.','permissions')
    text(permissions['retentionNote'],'retentionNote')
    session=request['session']
    if not isinstance(session,dict) or set(session)!={'sessionId','kind','origin','purpose'}:fail('REQUEST_INVALID','Explicit session declaration required.','session')
    text(session['sessionId'],'sessionId');text(session['purpose'],'purpose')
    if session['origin'] not in ('explicit-user-action','synthetic-test'):fail('REQUEST_INVALID','Session origin must be explicit.','session.origin')
    if session['kind'] not in ('replay','new-source','reanalysis','metadata-correction'):fail('REQUEST_INVALID','Unsupported transition kind.','session.kind')
    a,b=prior['payload'],candidate['payload']
    corrections=request['corrections'];claims=request['claims']
    if not isinstance(corrections,list) or not isinstance(claims,list):fail('REQUEST_INVALID','Corrections and claims must be explicit lists.')
    correction_ids=set();targets={}
    for correction in corrections:
        required={'recordId','targetStateRef','targetPath','before','after','author','createdAt','reason'}
        if not isinstance(correction,dict) or set(correction)!=required:fail('REQUEST_INVALID','Incomplete correction record.')
        for key in ('recordId','author','reason'):text(correction[key],key)
        if correction['recordId'] in correction_ids:fail('REQUEST_INVALID','Duplicate correction ID.')
        correction_ids.add(correction['recordId']);utc_time(correction['createdAt'])
        path=correction['targetPath']
        if path not in CORRECTION_PATHS:fail('CORRECTION_SCOPE_UNSUPPORTED','Only descriptive filename/capture-chain corrections are supported; regenerate measurements for numeric corrections.',str(path))
        if correction['targetStateRef']!=reference(prior):fail('PRIOR_STATE_MISMATCH','Correction targets another state.',path)
        if path in targets and targets[path]!=correction['after']:fail('CONFLICT_UNRESOLVED','Corrections disagree on a value.',path)
        if path in targets:fail('REQUEST_INVALID','Duplicate correction target.',path)
        targets[path]=correction['after']
        text(correction['after'],'after')
        if resolve(a,path)!=correction['before']:fail('CORRECTION_BEFORE_MISMATCH','Correction before-value does not match prior state.',path)
    claim_ids=set()
    for claim in claims:
        if not isinstance(claim,dict) or set(claim)!={'recordId','targetPath','value'}:fail('REQUEST_INVALID','Incomplete read-only claim.')
        text(claim['recordId'],'recordId')
        if claim['recordId'] in claim_ids:fail('REQUEST_INVALID','Duplicate claim ID.')
        claim_ids.add(claim['recordId']);path=claim['targetPath']
        if not isinstance(path,str) or not (path.startswith('/sourceRef/') or path.startswith('/measurementRecord/observations/')):
            fail('CLAIM_SCOPE_UNSUPPORTED','Claims may reference source metadata or measurement observations only.',str(path))
        if not same_json(resolve(b,path),claim['value']):fail('CONFLICT_UNRESOLVED','Claim conflicts with the candidate; no automatic override.',path)
    for path,value in targets.items():
        if resolve(b,path)!=value:fail('CORRECTION_AFTER_MISMATCH','Candidate does not contain the proposed after-value.',path)
    same=reference(prior)==reference(candidate)
    source_same=a['sourceRef'].get('sha256')==b['sourceRef'].get('sha256')
    kind=session['kind']
    if same:
        if kind!='replay' or corrections:fail('REPLAY_KIND_REQUIRED','An identical content state is replay, not a new evolution session.')
    elif kind=='replay':fail('REPLAY_CONTENT_MISMATCH','Replay requires identical content state.')
    elif kind=='new-source':
        if source_same:fail('TRANSITION_KIND_MISMATCH','new-source requires a different declared source hash.')
        known={item.get('sourceSha256') for item in a['alternativeConditions'] if isinstance(item,dict)}
        if b['sourceRef'].get('sha256') in known:fail('DERIVATIVE_NOT_NEW_SESSION','A known rate derivative cannot be relabeled as new source-session evidence.')
    elif kind=='reanalysis':
        if not source_same or a['measurementRecord']['featureSha256']==b['measurementRecord']['featureSha256']:
            fail('TRANSITION_KIND_MISMATCH','Reanalysis requires the same source and a different measurement reference.')
    elif kind=='metadata-correction':
        if not source_same or not corrections:fail('TRANSITION_KIND_MISMATCH','Metadata correction needs the same source and explicit correction records.')
        expected=copy.deepcopy(a)
        for path,value in targets.items():expected['sourceRef'][path.split('/')[-1]]=value
        if expected!=b:fail('CORRECTION_SCOPE_UNSUPPORTED','Candidate contains changes beyond the declared metadata corrections.')
    for field in sorted(set(a['sourceRef'])|set(b['sourceRef'])):
        if source_same and field in ('filename','captureChain') and a['sourceRef'].get(field)!=b['sourceRef'].get(field) and f'/sourceRef/{field}' not in targets:
            fail('UNEXPLAINED_METADATA_CHANGE','Descriptive metadata changes need explicit correction attribution.',f'/sourceRef/{field}')
    report={'schema':'AUEVO-SessionTransitionReview/v0.1','status':'replay-no-advance' if same else 'valid-for-review-not-commit',
            'inputs':{'priorStateRef':reference(prior),'candidateStateRef':reference(candidate),'currentStateRef':reference(current),
                      'requestSha256':hashlib.sha256(canonical_bytes(request)).hexdigest()},
            'request':copy.deepcopy(request),'changes':diff_payload(a,b),
            'historyAdvanced':False,'authorizedForHistoryCommit':False,'stateFilesModified':False,
            'corrections':{'records':copy.deepcopy(corrections),'authorityStatus':'caller-attributed, not authenticated'},
            'concurrencyScope':'Only the supplied current snapshot is compared; no atomic persistent-store operation is performed.',
            'unresolvedExternalProvenance':['Source rights/identity are not established by snapshot hashes.',
                                           'External measurement/source bytes are not independently resolved by this snapshot reviewer.'],
            'limitations':['This reviews draft snapshots only; it is not the complete lineage compiler or persistent carry system.',
                           'No measured numbers are patched, source records overwritten or permissions inferred.',
                           'Read-only claims can block review on conflict; recency is not truth.',
                           'Valid review is not authorization for recording, personal memory, sharing or committing history.'],
            'producer':{'version':'0.1.0','buildHash':sha256(__file__)}}
    digest=hashlib.sha256(canonical_bytes(report)).hexdigest()
    return {'reviewId':f'transition-review:sha256:{digest}','contentHash':digest,
            'createdAt':datetime.now(timezone.utc).isoformat(),'review':report}


def verify_review(result):
    try:
        review=result['review'];digest=hashlib.sha256(canonical_bytes(review)).hexdigest()
        if result['contentHash']!=digest or result['reviewId']!=f'transition-review:sha256:{digest}':
            fail('REVIEW_HASH_MISMATCH','Review content hash is invalid.')
        if review['schema']!='AUEVO-SessionTransitionReview/v0.1' or review['status'] not in ('replay-no-advance','valid-for-review-not-commit'):
            fail('REVIEW_INVALID','Unsupported review status.')
        if any(review[key] is not False for key in ('historyAdvanced','authorizedForHistoryCommit','stateFilesModified')):
            fail('REVIEW_INVALID','Review may not claim history commit or state mutation.')
    except LineageError:raise
    except (KeyError,TypeError,ValueError) as error:raise LineageError('REVIEW_INVALID','Malformed review.') from error
    return result


def save_review(output,result):
    verify_review(result)
    if not result['review']['request']['permissions']['allowLocalReviewReport']:fail('PERMISSION_DENIED','Saving a local review report is not permitted.')
    output=Path(output).resolve()
    if output.exists():fail('OUTPUT_EXISTS','Review output already exists.')
    output.parent.mkdir(parents=True,exist_ok=True)
    staged=Path(tempfile.mkdtemp(prefix='.transition-review-',dir=output.parent))
    try:
        (staged/'transition-review.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Session transition review</title><style>body{{font:16px system-ui;max-width:1100px;margin:auto;padding:24px;line-height:1.5}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}</style><h1>Session transition review — no history commit</h1><p>A successful review does not authorize persistent evolution. External provenance is unresolved; this checks supplied snapshots only.</p><pre>{html.escape(json.dumps(result,indent=2))}</pre><p><a href="transition-review.json">Review JSON</a></p></html>'''
        (staged/'transition-review.html').write_text(page,encoding='utf-8')
        output.mkdir()
        try:
            for item in staged.iterdir():shutil.move(str(item),output/item.name)
        except OSError:shutil.rmtree(output);raise
    finally:shutil.rmtree(staged,ignore_errors=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prior',type=Path,required=True);parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--request',type=Path,required=True);parser.add_argument('--current',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        paths=[args.prior,args.candidate,args.request]+([args.current] if args.current else [])
        before={str(path):sha256(path) for path in paths}
        result=review_transition(load_json(args.prior),load_json(args.candidate),load_json(args.request),load_json(args.current) if args.current else None)
        if any(sha256(path)!=before[str(path)] for path in paths):fail('INPUT_CHANGED','An input changed during review.')
        save_review(args.output,result)
        print(f"Review saved to {args.output}; no history advanced.")
    except LineageError as error:parser.exit(1,json.dumps({'code':error.code,'message':str(error),'path':error.path})+'\n')
    except (ValueError,OSError,KeyError,TypeError) as error:parser.exit(1,f'Review failed: {error}\n')

if __name__=='__main__':main()
