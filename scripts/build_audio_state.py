"""Export a review-only audio state that preserves features, not a final canonical model."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import html
import json
import math
from pathlib import Path
import shutil
import tempfile

try:
    from scripts.run_evo_trial import validate_inputs
    from scripts.compile_package import load_json
    from scripts.analyze_audio import sha256
    from scripts.adapt_lineage import canonical_bytes
except ModuleNotFoundError:
    from run_evo_trial import validate_inputs
    from compile_package import load_json
    from analyze_audio import sha256
    from adapt_lineage import canonical_bytes

SCHEMA='AUEVO-AudioStateDraft/v0.1'
ENVELOPE='AUEVO-AudioStateDraftEnvelope/v0.1'
UNITS={'rmsLinear':'normalized sample amplitude','samplePeak':'normalized sample amplitude',
       'crestFactor':'unitless sample peak/RMS','rmsChangeDb':'dB change from preceding window',
       'positiveBandChange':'sum of positive band-RMS changes; normalized sample amplitude',
       'commonBandPower':'sample unit squared; configured Hz bands in measurement method',
       'centroidHz':'Hz','bandwidthHz':'Hz','rolloff85Hz':'Hz','flatness':'unitless ratio',
       'times':'seconds; actual sample-rounded boundaries retained'}


def number(value,*,nullable=False,nonnegative=False):
    if nullable and value is None:return
    if type(value) not in (int,float) or not math.isfinite(value) or (nonnegative and value<0):
        raise ValueError('Invalid finite numeric measurement.')


def validate_observation(record):
    required={'index','startSeconds','endSeconds','centerSeconds','actualStartSeconds','actualEndSeconds',
              'windowSamples','binSpacingHz','evidenceClass','rmsLinear','samplePeak','crestFactor',
              'rmsChangeDb','positiveBandChange','commonBandPower','fullBand','commonBand'}
    if not isinstance(record,dict) or set(record)!=required or record['evidenceClass']!='MEASURED':
        raise ValueError('Unrecognized observation contract; no fields silently dropped.')
    for key in ('index','windowSamples'):
        if type(record[key]) is not int or record[key]<(1 if key=='windowSamples' else 0):raise ValueError('Invalid observation index/sample count.')
    for key in ('startSeconds','endSeconds','centerSeconds','actualStartSeconds','actualEndSeconds','binSpacingHz','rmsLinear','samplePeak'):
        number(record[key],nonnegative=True)
    if record['endSeconds']<=record['startSeconds'] or record['actualEndSeconds']<=record['actualStartSeconds'] or record['binSpacingHz']<=0:
        raise ValueError('Invalid observation boundaries.')
    for key in ('crestFactor','positiveBandChange'):number(record[key],nullable=True,nonnegative=True)
    number(record['rmsChangeDb'],nullable=True)
    bands=record['commonBandPower']
    if not isinstance(bands,dict) or set(bands)!={'bass','mid','high'}:raise ValueError('Unknown band contract.')
    for value in bands.values():number(value,nonnegative=True)
    for key in ('commonBand','fullBand'):
        if not isinstance(record[key],dict) or set(record[key])!={'centroidHz','bandwidthHz','rolloff85Hz','flatness'}:
            raise ValueError('Unknown spectral feature contract.')
        for value in record[key].values():number(value,nullable=True,nonnegative=True)


def build_state(features,summary,feature_hash):
    validate_inputs(features,summary,feature_hash)
    observations=[];symbolic=[]
    enabled=features.get('symbolicExperiment',{}).get('enabled')
    if type(enabled) is not bool:raise ValueError('Explicit symbolic experiment status required.')
    for position,original in enumerate(features['originalWindows']):
        observation=copy.deepcopy(original)
        overlay=observation.pop('evoMetricsExperiment',None)
        validate_observation(observation)
        if observation['index']!=position:raise ValueError('Window index order is inconsistent.')
        if (overlay is not None)!=enabled:raise ValueError('Symbolic record presence conflicts with experiment status.')
        observations.append(observation)
        if overlay is not None:
            symbolic.append({'windowIndex':observation['index'],'classification':'DERIVED_EXPERIMENTAL',
                             'output':copy.deepcopy(overlay),'verificationStatus':'preserved-not-recomputed'})
    # Alternative resampling conditions are evidence branches, not successive sessions.
    alternatives=[{'rateHz':item['rateHz'],'sourceSha256':item['sourceSha256'],
                   'relationship':'same-source-software-derivative-not-new-session',
                   'featureRecordsRef':{'sha256':feature_hash,'selector':f"conditions/rateHz={item['rateHz']}/windows"}}
                  for item in features['conditions']]
    payload={'schema':SCHEMA,'status':'DRAFT-REVIEW-ONLY',
             'sourceRef':copy.deepcopy(features['source']),
             'producer':{'name':'AUEVO draft audio-state exporter','version':'0.1.0','buildHash':sha256(__file__)},
             'measurementRecord':{'featureSha256':feature_hash,'comparisonRef':copy.deepcopy(features['comparisonRef']),
                                  'method':copy.deepcopy(features['method']),'units':UNITS,
                                  'classification':'MEASURED_TECHNICAL_FEATURES','observations':observations},
             'symbolicOverlay':{'status':'preserved-unverified' if symbolic else 'not-attached',
                                'experimentRef':copy.deepcopy(features['symbolicExperiment']),
                                'records':symbolic,'role':'optional interpretation; never replaces measured features'},
             'alternativeConditions':alternatives,
             'lineage':{'parentStateRef':None,'transitionKind':'initial-review-export',
                        'historyCommit':'not-implemented','persistentEvolutionAdvanced':False,
                        'missing':['trusted prior-session record','explicit persistence policy','correction/conflict resolution implementation']},
             'permissions':{'operationScope':'explicit-local-draft-export','sourceRightsStatus':'UNKNOWN',
                            'grantsRecording':False,'grantsCloudUpload':False,'grantsIdentityMemory':False},
             'experience':{'renderProfileRef':None,'directives':None,'status':'not-mapped'},
             'hashEncoding':'python-sorted-json-utf8-v1',
             'limitations':['This candidate observation contract is not the approved final canonical dimension set.',
                            'Input hashes establish file association/integrity, not authorship, consent or native audio verification.',
                            'No audio, camera, microphone, history store or prior state is opened or modified.',
                            'Local draft export does not authorize persistent personal memory or sharing.',
                            'No new equation, symbolic rule, Orb mapping or physiological inference is introduced.']}
    content_hash=hashlib.sha256(canonical_bytes(payload)).hexdigest()
    return {'schema':ENVELOPE,'stateId':f'audio-draft:sha256:{content_hash}','contentHash':content_hash,
            'createdAt':datetime.now(timezone.utc).isoformat(),'payload':payload}


def verify_state(state):
    if state.get('schema')!=ENVELOPE or state.get('payload',{}).get('schema')!=SCHEMA:raise ValueError('Unsupported draft state.')
    payload=state['payload'];digest=hashlib.sha256(canonical_bytes(payload)).hexdigest()
    if state.get('contentHash')!=digest or state.get('stateId')!=f'audio-draft:sha256:{digest}':raise ValueError('Draft content hash mismatch.')
    if payload['status']!='DRAFT-REVIEW-ONLY' or payload['lineage']!={'parentStateRef':None,'transitionKind':'initial-review-export','historyCommit':'not-implemented','persistentEvolutionAdvanced':False,'missing':['trusted prior-session record','explicit persistence policy','correction/conflict resolution implementation']}:
        raise ValueError('Unsupported state transition; this exporter cannot commit evolution.')
    if payload['experience']['directives'] is not None or payload['experience']['renderProfileRef'] is not None:
        raise ValueError('This exporter does not approve render mappings.')
    if payload['permissions']!={'operationScope':'explicit-local-draft-export','sourceRightsStatus':'UNKNOWN','grantsRecording':False,'grantsCloudUpload':False,'grantsIdentityMemory':False}:
        raise ValueError('Unsupported permission grant.')
    for record in payload['measurementRecord']['observations']:validate_observation(record)
    return state


def export_state(feature_path,summary_path,output):
    feature_path,summary_path,output=Path(feature_path),Path(summary_path),Path(output).resolve()
    if output.exists():raise ValueError('Output exists; choose a new draft folder.')
    feature_hash=sha256(feature_path);summary_hash=sha256(summary_path)
    state=verify_state(build_state(load_json(feature_path),load_json(summary_path),feature_hash))
    if sha256(feature_path)!=feature_hash or sha256(summary_path)!=summary_hash:raise ValueError('Input changed during export.')
    output.parent.mkdir(parents=True,exist_ok=True)
    staged=Path(tempfile.mkdtemp(prefix='.audio-state-',dir=output.parent))
    try:
        with (staged/'audio-state.json').open('w',encoding='utf-8') as stream:json.dump(state,stream,allow_nan=False)
        report={'schema':'AUEVO-AudioStateDraftReview/v0.1','stateId':state['stateId'],'contentHash':state['contentHash'],
                'stateFileSha256':sha256(staged/'audio-state.json'),'featureSha256':feature_hash,'summarySha256':summary_hash,
                'observationCount':len(state['payload']['measurementRecord']['observations']),
                'alternativeConditions':state['payload']['alternativeConditions'],
                'symbolicStatus':state['payload']['symbolicOverlay']['status'],
                'symbolicOverlayCount':len(state['payload']['symbolicOverlay']['records']),
                'status':'DRAFT-REVIEW-ONLY','historyAdvanced':False,'renderMappingImplemented':False,
                'design':'docs/EVOLVED_AUDIO_STATE_MODEL_v0.1.md'}
        (staged/'state-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        webpage=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Draft evolved audio state</title><style>body{{font:16px system-ui;max-width:1000px;margin:auto;padding:24px;line-height:1.5}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}</style><h1>Draft evolved audio state</h1><p><strong>Review-only observation model — not a completed architectural compiler or approved equation.</strong></p><pre>{html.escape(json.dumps(report,indent=2))}</pre><p>Every original measured feature window is preserved. Symbolic values, when present, are separate and not promoted to measured facts. Alternative rates are source derivatives, not later sessions. No carry/history or renderer is changed.</p><p><a href="audio-state.json">Full draft state</a> • <a href="state-review.json">Small review record</a></p></html>'''
        (staged/'state-review.html').write_text(webpage,encoding='utf-8')
        output.mkdir()
        try:
            for item in staged.iterdir():shutil.move(str(item),output/item.name)
        except OSError:shutil.rmtree(output);raise
        print(f"Draft exported. Open {output/'state-review.html'}",flush=True)
        return state
    finally:shutil.rmtree(staged,ignore_errors=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--features',type=Path);parser.add_argument('--summary',type=Path)
    parser.add_argument('--output',type=Path,default=Path('runtime/audio-state-draft-001'))
    args=parser.parse_args()
    try:
        path=args.features
        if path is None:
            import tkinter as tk
            from tkinter import filedialog
            root=tk.Tk();root.withdraw()
            try:selected=filedialog.askopenfilename(title='Select corrected features.json in matched-features-002',filetypes=[('JSON features','*.json')])
            finally:root.destroy()
            if not selected:print('Cancelled; nothing changed.');return
            path=Path(selected)
        export_state(path,args.summary or path.parent/'summary.json',args.output)
    except KeyboardInterrupt:parser.exit(1,'Cancelled; no audio/history changed.\n')
    except Exception as error:parser.exit(1,f'Draft export failed: {error}\n')

if __name__=='__main__':main()
