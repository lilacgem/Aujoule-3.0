"""Resolve draft state to actual feature, summary and comparison files; no history commit."""
import argparse
from datetime import datetime,timezone
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import tempfile

try:
    from scripts.build_audio_state import verify_state,build_state,validate_observation
    from scripts.review_session_transition import same_json
    from scripts.run_evo_trial import validate_inputs
    from scripts.compile_package import load_json
    from scripts.adapt_lineage import canonical_bytes,LineageError
    from scripts.analyze_audio import sha256
except ModuleNotFoundError:
    from build_audio_state import verify_state,build_state,validate_observation
    from review_session_transition import same_json
    from run_evo_trial import validate_inputs
    from compile_package import load_json
    from adapt_lineage import canonical_bytes,LineageError
    from analyze_audio import sha256


def fail(code,message,path=None):raise LineageError(code,message,path)


def file_digest(path,role):
    path=Path(path)
    if not path.is_file():fail('EVIDENCE_MISSING',f'{role} file is missing or not a file.',role)
    try:return sha256(path)
    except OSError as error:raise LineageError('EVIDENCE_UNREADABLE',f'Cannot read {role}.',role) from error


def read_json(path,role):
    try:return load_json(path)
    except (ValueError,OSError,TypeError) as error:raise LineageError('EVIDENCE_INVALID',f'Invalid {role} JSON: {error}',role) from error


def resolve_evidence(state_path,feature_path,summary_path,comparison_path,*,source_path=None,verify_derived=False):
    paths={key:Path(value) for key,value in [('state',state_path),('features',feature_path),('summary',summary_path),('comparison',comparison_path)]}
    hashes={role:file_digest(path,role) for role,path in paths.items()}
    state=read_json(paths['state'],'state')
    try:verify_state(state)
    except (ValueError,KeyError,TypeError,AttributeError) as error:raise LineageError('STATE_INVALID','State snapshot is invalid.','state') from error
    payload=state['payload'];features=read_json(paths['features'],'features');summary=read_json(paths['summary'],'summary')
    try:
        expected_hash=payload['measurementRecord']['featureSha256']
        if hashes['features']!=expected_hash:fail('FEATURE_HASH_MISMATCH','Feature bytes do not match the state reference.','features')
        if summary.get('fullRecordsSha256')!=hashes['features']:fail('SUMMARY_LINK_MISMATCH','Summary refers to different feature bytes.','summary')
        validate_inputs(features,summary,hashes['features'])
        expected=build_state(features,summary,hashes['features'])['payload']
        # Ignore only builder artifact bytes, which may differ by supported build/line endings.
        if payload['producer'].get('name')!=expected['producer']['name'] or payload['producer'].get('version')!=expected['producer']['version']:
            fail('BUILDER_UNSUPPORTED','Unknown draft exporter name/version.','state.producer')
        if set(payload)!=set(expected):fail('STATE_EVIDENCE_MISMATCH','State payload fields differ from the supported exporter.','state')
        for name,value in expected.items():
            if name=='producer':continue
            if not same_json(payload[name],value):
                code='OBSERVATION_MISMATCH' if name=='measurementRecord' else 'STATE_EVIDENCE_MISMATCH'
                fail(code,f'State {name} does not match the resolved measurement evidence.',name)
        # Resolve and validate alternative-rate selectors, not just the primary observations.
        for condition in features['conditions']:
            for index,raw in enumerate(condition['windows']):
                observed=dict(raw);overlay=observed.pop('evoMetricsExperiment',None)
                validate_observation(observed)
                if observed['index']!=index or (overlay is not None)!=features['symbolicExperiment']['enabled']:
                    fail('ALTERNATIVE_INVALID','Alternative feature records have inconsistent indices or overlay disposition.')
        if hashes['comparison']!=features['comparisonRef']['sha256']:
            fail('COMPARISON_HASH_MISMATCH','Comparison bytes do not match the feature reference.','comparison')
        comparison=read_json(paths['comparison'],'comparison')
        if comparison.get('schema')!='AUEVO-SampleRateComparison/v0.1' or comparison.get('experimentType')!='software-resampling-not-native-capture':
            fail('COMPARISON_INVALID','Unsupported comparison record.','comparison')
        if not same_json(comparison.get('source'),features['source']):
            fail('SOURCE_METADATA_MISMATCH','Comparison/source metadata does not match the feature evidence.','comparison.source')
        conditions=comparison.get('conditions')
        if not isinstance(conditions,list):fail('COMPARISON_INVALID','Comparison conditions must be a list.')
        by_rate={}
        for condition in conditions:
            rate=condition.get('targetRateHz')
            if type(rate) is not int or rate<=0 or rate in by_rate:fail('COMPARISON_INVALID','Invalid/duplicate comparison rate.')
            digest=condition.get('sha256')
            if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest):fail('COMPARISON_INVALID','Invalid derivative hash.')
            by_rate[rate]=condition
        if set(by_rate)!={item['rateHz'] for item in features['conditions']}:
            fail('CONDITION_LINK_MISMATCH','Feature and comparison condition sets differ.')
        for item in features['conditions']:
            if item['sourceSha256']!=by_rate[item['rateHz']]['sha256']:
                fail('CONDITION_LINK_MISMATCH','Alternative feature source digest differs from comparison.')
    except LineageError:raise
    except (ValueError,KeyError,TypeError,AttributeError,IndexError) as error:
        raise LineageError('EVIDENCE_INVALID','Unsupported or inconsistent measurement evidence.') from error
    source={'status':'not-provided','mediaHeaderChecked':False}
    if source_path is not None:
        print('Checking optional source bytes...',flush=True)
        source_hash=file_digest(source_path,'source-bytes')
        if source_hash!=payload['sourceRef'].get('sha256'):fail('SOURCE_HASH_MISMATCH','Source bytes do not match the declared digest.')
        source={'status':'sha256-matched','sha256':source_hash,'mediaHeaderChecked':False}
    derivatives=[];extra_hashes={}
    if verify_derived:
        for rate,condition in sorted(by_rate.items()):
            print(f'Checking optional derivative bytes: {rate} Hz...',flush=True)
            name=condition.get('file')
            if not isinstance(name,str) or Path(name).name!=name or '/' in name or '\\' in name:
                fail('DERIVATIVE_PATH_INVALID','Derivative filename must be a local basename.')
            path=(paths['comparison'].parent/name).resolve()
            if path.parent!=paths['comparison'].parent.resolve():fail('DERIVATIVE_PATH_INVALID','Derivative escapes comparison folder.')
            digest=file_digest(path,f'derivative-{rate}')
            if digest!=condition['sha256']:fail('DERIVATIVE_HASH_MISMATCH','Derivative bytes do not match the comparison.')
            derivatives.append({'rateHz':rate,'sha256':digest,'status':'sha256-matched','mediaHeaderChecked':False})
            extra_hashes[str(path)]=digest
    for role,path in paths.items():
        if file_digest(path,role)!=hashes[role]:fail('INPUT_CHANGED','Evidence changed while resolving.',role)
    if source_path is not None and file_digest(source_path,'source-bytes')!=source['sha256']:fail('INPUT_CHANGED','Source bytes changed during resolution.')
    for path,digest in extra_hashes.items():
        if file_digest(path,'derivative')!=digest:fail('INPUT_CHANGED','Derivative changed during resolution.')
    report={'schema':'AUEVO-StateEvidenceResolution/v0.1','status':'measurement-chain-resolved',
            'stateRef':{'stateId':state['stateId'],'contentHash':state['contentHash']},
            'inputs':{role:{'filename':path.name,'sha256':hashes[role]} for role,path in paths.items()},
            'checks':{'stateContentHash':True,'featureHash':True,'summaryLink':True,'measurementMethod':True,
                      'primaryObservationsMatch':True,'sourceMetadataMatches':True,'symbolicDispositionMatches':True,
                      'alternativeReferencesMatch':True,'comparisonHash':True,'comparisonConditionsMatch':True},
            'observationCount':len(payload['measurementRecord']['observations']),
            'alternativeConditionCount':len(payload['alternativeConditions']),
            'sourceBytes':source,'derivedBytes':{'requested':verify_derived,'results':derivatives},
            'producerBuildVerification':'declared exporter name/version supported; build artifact identity not authenticated',
            'correctionScope':'Strict reproduction only. A metadata-corrected state needs a separately implemented attributed-evidence reconciliation path; no silent overrides.',
            'historyAdvanced':False,'authorizedForHistoryCommit':False,'stateFilesModified':False,
            'limitations':['Resolved hashes/content are not authorship, ownership, permission or scientific-validity proofs.',
                           'Without optional byte inputs, original/derived media files are not independently checked.',
                           'Optional media checks are byte hashes, not native-capture verification or analysis reruns.',
                           'No retention enforcement, trusted identity authority, persistent store or atomic history commit is implemented.'],
            'producer':{'version':'0.1.0','buildHash':sha256(__file__)}}
    digest=hashlib.sha256(canonical_bytes(report)).hexdigest()
    return {'resolutionId':f'evidence-resolution:sha256:{digest}','contentHash':digest,
            'createdAt':datetime.now(timezone.utc).isoformat(),'resolution':report}


def verify_resolution(result):
    try:
        report=result['resolution'];digest=hashlib.sha256(canonical_bytes(report)).hexdigest()
        if result['contentHash']!=digest or result['resolutionId']!=f'evidence-resolution:sha256:{digest}':
            fail('RESOLUTION_HASH_MISMATCH','Resolution report content hash does not match.')
        if report['schema']!='AUEVO-StateEvidenceResolution/v0.1' or report['status']!='measurement-chain-resolved':
            fail('RESOLUTION_INVALID','Unsupported resolution report.')
        if any(report[key] is not False for key in ('historyAdvanced','authorizedForHistoryCommit','stateFilesModified')):
            fail('RESOLUTION_INVALID','Evidence resolution may not claim history commit or state mutation.')
        if not report['checks'] or any(value is not True for value in report['checks'].values()):
            fail('RESOLUTION_INVALID','Successful report contains failed checks.')
    except LineageError:raise
    except (ValueError,KeyError,TypeError) as error:raise LineageError('RESOLUTION_INVALID','Malformed resolution report.') from error
    return result


def save_resolution(output,result):
    verify_resolution(result)
    output=Path(output).resolve()
    if output.exists():fail('OUTPUT_EXISTS','Evidence report output already exists.')
    output.parent.mkdir(parents=True,exist_ok=True)
    staged=Path(tempfile.mkdtemp(prefix='.evidence-',dir=output.parent))
    try:
        (staged/'evidence-resolution.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>State evidence resolution</title><style>body{{font:16px system-ui;max-width:1100px;margin:auto;padding:24px;line-height:1.5}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}</style><h1>State evidence resolution</h1><p>Referenced measurement files have been read, hashed and compared with this draft state. This is not a history commit or proof of source rights. Check the optional media-byte status separately.</p><pre>{html.escape(json.dumps(result,indent=2))}</pre><p><a href="evidence-resolution.json">Resolution JSON</a></p></html>'''
        (staged/'evidence-resolution.html').write_text(page,encoding='utf-8')
        output.mkdir()
        try:
            for item in staged.iterdir():shutil.move(str(item),output/item.name)
        except OSError:shutil.rmtree(output);raise
    finally:shutil.rmtree(staged,ignore_errors=True)


def choose(title,types=None):
    import tkinter as tk
    from tkinter import filedialog
    root=tk.Tk();root.withdraw()
    try:return filedialog.askopenfilename(title=title,filetypes=types or [('JSON evidence','*.json')])
    finally:root.destroy()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('state','features','summary','comparison','source'):parser.add_argument('--'+key,type=Path)
    parser.add_argument('--check-media',action='store_true',help='Also select/hash original source bytes and hash all derivatives')
    parser.add_argument('--verify-derived',action='store_true',help='Also hash derivative files beside comparison.json')
    parser.add_argument('--output',type=Path,default=Path('runtime/evidence-resolution-001'))
    args=parser.parse_args()
    try:
        state=args.state or choose('1. Select audio-state.json in audio-state-draft-001')
        if not state:print('Cancelled; nothing changed.');return
        features=args.features or choose('2. Select features.json in matched-features-002')
        if not features:print('Cancelled; nothing changed.');return
        comparison=args.comparison or choose('3. Select comparison.json in rate-comparison-001')
        if not comparison:print('Cancelled; nothing changed.');return
        source=args.source
        if args.check_media and source is None:
            source=choose('4. Select original WAV for byte-hash verification',[('WAV source','*.wav'),('All files','*.*')])
            if not source:print('Cancelled; nothing changed.');return
        print('Resolving selected state and measurement files...',flush=True)
        result=resolve_evidence(state,features,args.summary or Path(features).parent/'summary.json',comparison,
                                source_path=source,verify_derived=args.verify_derived or args.check_media)
        save_resolution(args.output,result)
        print(f'Evidence resolved. Open {args.output / "evidence-resolution.html"}. No history advanced.')
    except KeyboardInterrupt:parser.exit(1,'Cancelled; nothing modified.\n')
    except LineageError as error:parser.exit(1,json.dumps({'code':error.code,'message':str(error),'path':error.path})+'\n')
    except Exception as error:parser.exit(1,f'Evidence resolution failed: {error}\n')

if __name__=='__main__':main()
