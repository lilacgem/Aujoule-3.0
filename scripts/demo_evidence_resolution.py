"""Synthetic evidence-file integrity demo; no real recording or history changes."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile

try:
    from scripts.demo_session_transition import synthetic_state,rehash
    from scripts.build_audio_state import build_state
    from scripts.resolve_state_evidence import resolve_evidence,save_resolution
    from scripts.adapt_lineage import canonical_bytes,LineageError
except ModuleNotFoundError:
    from demo_session_transition import synthetic_state,rehash
    from build_audio_state import build_state
    from resolve_state_evidence import resolve_evidence,save_resolution
    from adapt_lineage import canonical_bytes,LineageError


def make_fixture(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    base=synthetic_state()['payload']
    descriptor=b'synthetic descriptor, not an audio file'
    source=root/'synthetic-source.txt';source.write_bytes(descriptor)
    derived=root/'synthetic-derived.txt';derived.write_bytes(descriptor)
    comparison={'schema':'AUEVO-SampleRateComparison/v0.1','experimentType':'software-resampling-not-native-capture',
                'fixtureOrigin':'synthetic descriptions only; no audio captured or converted',
                'source':base['sourceRef'],
                'conditions':[{'targetRateHz':48000,'sha256':hashlib.sha256(descriptor).hexdigest(),'file':derived.name}]}
    comparison_raw=canonical_bytes(comparison)
    comparison_path=root/'comparison.json';comparison_path.write_bytes(comparison_raw)
    observations=base['measurementRecord']['observations']
    features={'schema':'AUEVO-MatchedAudioFeatures/v0.2','source':base['sourceRef'],
              'comparisonRef':{'filename':'comparison.json','sha256':hashlib.sha256(comparison_raw).hexdigest()},
              'method':base['measurementRecord']['method'],'symbolicExperiment':base['symbolicOverlay']['experimentRef'],
              'originalWindows':observations,
              'conditions':[{'rateHz':48000,'sourceSha256':base['sourceRef']['sha256'],'windows':copy.deepcopy(observations)}]}
    raw=canonical_bytes(features);feature_hash=hashlib.sha256(raw).hexdigest()
    feature_path=root/'features.json';feature_path.write_bytes(raw)
    summary={key:features[key] for key in ('schema','source','method')}
    summary.update(fullRecordsSha256=feature_hash,originalWindowCount=len(observations),
                   conditions=[{key:value for key,value in item.items() if key!='windows'} for item in features['conditions']])
    summary_path=root/'summary.json';summary_path.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    state=build_state(features,summary,feature_hash)
    state_path=root/'audio-state.json';state_path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    return {'state':state_path,'features':feature_path,'summary':summary_path,'comparison':comparison_path,'source':source,'derived':derived}


def run_demo(output=None):
    if output is None:
        runtime=Path(__file__).resolve().parents[1]/'runtime';runtime.mkdir(exist_ok=True)
        output=Path(tempfile.mkdtemp(prefix='evidence-demo-',dir=runtime))
    else:output=Path(output);output.mkdir(parents=True,exist_ok=False)
    files=make_fixture(output/'fixtures')
    def resolve(paths,**kwargs):return resolve_evidence(paths['state'],paths['features'],paths['summary'],paths['comparison'],**kwargs)
    result=resolve(files,source_path=files['source'],verify_derived=True)
    save_resolution(output/'accepted',result)
    cases=[]
    def reject(name,paths,code,**kwargs):
        try:resolve(paths,**kwargs)
        except LineageError as error:
            if error.code!=code:raise
            cases.append({'case':name,'code':error.code})
        else:raise AssertionError(f'Expected rejection: {name}')
    reject('missing-feature',{**files,'features':output/'missing.json'},'EVIDENCE_MISSING')
    altered=output/'altered-features.json';altered.write_text('{}')
    reject('altered-feature',{**files,'features':altered},'FEATURE_HASH_MISMATCH')
    state=json.loads(files['state'].read_text());state['payload']['measurementRecord']['observations'][0]['rmsLinear']=.15
    changed=output/'altered-state.json';changed.write_text(json.dumps(rehash(state)))
    reject('state-observation-mismatch',{**files,'state':changed},'OBSERVATION_MISMATCH')
    altered_comparison=output/'altered-comparison.json';altered_comparison.write_text('{}')
    reject('comparison-mismatch',{**files,'comparison':altered_comparison},'COMPARISON_HASH_MISMATCH')
    altered_source=output/'wrong-source.txt';altered_source.write_bytes(b'wrong')
    reject('source-byte-mismatch',files,'SOURCE_HASH_MISMATCH',source_path=altered_source)
    files['derived'].write_bytes(b'tampered')
    reject('derivative-byte-mismatch',files,'DERIVATIVE_HASH_MISMATCH',verify_derived=True)
    # Restore test fixture for review; no real media is involved.
    files['derived'].write_bytes(files['source'].read_bytes())
    report={'schema':'AUEVO-EvidenceDemo/v0.1','synthetic':True,'accepted':1,'rejected':cases,
            'historyAdvanced':False,'mediaScope':'Text descriptors used to test byte hashing; no audio/capture claim.'}
    (output/'demo-summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    page='<!doctype html><html lang="en"><meta charset="utf-8"><title>Evidence resolver demo</title><style>body{font:16px system-ui;max-width:1000px;margin:auto;padding:24px}pre{white-space:pre-wrap}</style><h1>Synthetic evidence resolver demo</h1><p>No audio or history changed. These fixtures are test descriptions, not real capture evidence.</p><pre>'+json.dumps(report,indent=2)+'</pre><p><a href="accepted/evidence-resolution.html">Accepted resolution</a> • <a href="demo-summary.json">Summary JSON</a></p></html>'
    (output/'demo.html').write_text(page,encoding='utf-8')
    print(f'PASS: one resolved chain, six expected rejections. Open {output/"demo.html"}')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    run_demo(parser.parse_args().output)
