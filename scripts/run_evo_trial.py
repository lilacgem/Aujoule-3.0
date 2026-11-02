"""Evaluate the approved fixed-context diagnostic trial on corrected feature records."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import platform
import shutil
import tempfile

try:
    from scripts.compile_package import load_json
    from scripts.analyze_audio import sha256
    from scripts.evo_metrics_experiment import evaluate,validate_config
except ModuleNotFoundError:
    from compile_package import load_json
    from analyze_audio import sha256
    from evo_metrics_experiment import evaluate,validate_config

ROOT=Path(__file__).resolve().parents[1]
PRESET=ROOT/'experiments/evo-metrics-fixed-focus-trial.json'
CORE=ROOT/'docs/source_records/evo-metrics-received/evoMetrics.js'


def validate_inputs(features,summary,feature_hash):
    if features.get('schema')!='AUEVO-MatchedAudioFeatures/v0.2' or summary.get('schema')!=features['schema']:
        raise ValueError('Corrected v0.2 features and their matching summary are required.')
    if summary.get('fullRecordsSha256')!=feature_hash:raise ValueError('Feature bytes do not match the summary hash.')
    if summary.get('source')!=features.get('source') or summary.get('method')!=features.get('method'):
        raise ValueError('Feature and summary source/method mismatch.')
    if features['method'].get('bandIntegration',{}).get('id')!='fractional-bin-cell-overlap/v1':
        raise ValueError('Fractional-bin measurement correction required.')
    reference=features.get('originalWindows')
    if not isinstance(reference,list) or not reference or len(reference)!=features['method']['windowCount'] or len(reference)!=summary['originalWindowCount']:
        raise ValueError('Invalid original window count.')
    expected=[]
    previous=-1
    for record in reference:
        start,end=record.get('startSeconds'),record.get('endSeconds')
        if any(type(value) not in (int,float) or not math.isfinite(value) for value in (start,end)) or start<0 or start<=previous or end<=start:
            raise ValueError('Invalid reference window timing.')
        expected.append((start,end));previous=start
    conditions=features.get('conditions')
    if not isinstance(conditions,list) or not conditions:raise ValueError('No feature conditions.')
    rates=set()
    for condition in conditions:
        rate=condition.get('rateHz')
        if type(rate) is not int or rate<=0 or rate in rates:raise ValueError('Invalid/duplicate condition rate.')
        rates.add(rate)
        if [(record.get('startSeconds'),record.get('endSeconds')) for record in condition.get('windows',[])]!=expected:
            raise ValueError('Condition windows are not aligned with original.')
    compact=[{key:value for key,value in condition.items() if key!='windows'} for condition in conditions]
    if compact!=summary.get('conditions'):raise ValueError('Summary condition metadata mismatch.')
    # Recognize only deterministic LF/CRLF conversion of the archived core, not unknown edits.
    core=CORE.read_bytes().replace(b'\r\n',b'\n')
    allowed={hashlib.sha256(core).hexdigest(),hashlib.sha256(core.replace(b'\n',b'\r\n')).hexdigest()}
    if features.get('symbolicExperiment',{}).get('receivedCoreSha256') not in allowed:
        raise ValueError('Unrecognized core source reference; explicit reconciliation needed.')


def trial_records(windows,config):
    output=[]
    for record in windows:
        symbolic=evaluate(record['commonBandPower'],config)
        scaled=abs(symbolic['evolutionDelta'])*100
        margin=1.5-scaled if scaled<1.5 else abs(scaled-(math.floor(scaled)+.5))
        output.append({'index':record['index'],'startSeconds':record['startSeconds'],'endSeconds':record['endSeconds'],
                       'centerSeconds':record['centerSeconds'],'measuredBandPower':record['commonBandPower'],
                       'symbolic':symbolic,'roundingThresholdMarginScaledUnits':margin})
    return output


def summarize(records):
    count=len(records)
    roots={str(root):0 for root in range(10)}
    for record in records:roots[str(record['symbolic']['digitalRoot'])]+=1
    values=[record['symbolic']['voiceEnergy'] for record in records]
    contributions=[record['symbolic']['audioContribution'] for record in records]
    return {'windowCount':count,'digitalRootHistogram':roots,
            'gateWindows':sum(record['symbolic']['isGate'] for record in records),
            'gateWindowFraction':sum(record['symbolic']['isGate'] for record in records)/count,
            'normalizationClippedWindows':sum(bool(record['symbolic']['normalizationClippedBands']) for record in records),
            'sessionNumberOneWindows':sum(record['symbolic']['sessionNumber']==1 for record in records),
            'voiceEnergy':{'minimum':min(values),'mean':sum(values)/count,'maximum':max(values)},
            'audioContribution':{'minimum':min(contributions),'mean':sum(contributions)/count,'maximum':max(contributions)},
            'sessionCountContribution':records[0]['symbolic']['sessionCountContribution'],
            'minimumRoundingThresholdMargin':min(record['roundingThresholdMarginScaledUnits'] for record in records),
            'interpretation':'Counts of overlapping diagnostic windows, not time percentages, human states or independent sessions.'}


def run_trial(feature_path,summary_path,output,config_path=PRESET):
    feature_path,summary_path,config_path,output=map(Path,(feature_path,summary_path,config_path,output))
    output=output.resolve()
    if output.exists():raise ValueError('Output exists; choose a new trial directory.')
    feature_hash=sha256(feature_path);summary_hash=sha256(summary_path);config_hash=sha256(config_path)
    features=load_json(feature_path);summary=load_json(summary_path);config=validate_config(load_json(config_path))
    if not config['enabled']:raise ValueError('Trial configuration must explicitly enable symbolic evaluation.')
    validate_inputs(features,summary,feature_hash)
    print('Running independent-window symbolic trial; no audio access or history changes.',flush=True)
    original=trial_records(features['originalWindows'],config)
    original_summary=summarize(original)
    record={'schema':'AUEVO-EvoMetricsTrial/v0.1','status':'experimental-diagnostic-not-canonical-state',
            'inputs':{'featureSha256':feature_hash,'summarySha256':summary_hash,'configSha256':config_hash,
                      'audioSource':features['source'],'comparisonRef':features['comparisonRef'],
                      'measurementMethod':features['method'],
                      'archivedCoreSha256':sha256(CORE),
                      'measurementReportedCoreSha256':features['symbolicExperiment']['receivedCoreSha256'],
                      'coreReferenceNote':'LF/CRLF-only conversion recognized; code was not silently modified.'},
            'producer':{'version':'0.1.0','buildHash':sha256(__file__),'python':platform.python_version(),
                        'adaptationSha256':sha256(Path(__file__).with_name('evo_metrics_experiment.py'))},
            'config':config,'original':{'summary':original_summary,'windows':original},'conditions':[],
            'zeroInputControl':evaluate({'bass':0.,'mid':0.,'high':0.},config),
            'limitations':['Experimental input normalization; not calibrated energy or an approved final equation.',
                           'Focus is configured, not camera brightness or measured psychological focus.',
                           'No carry/session history advances; each window uses identical fixed context.',
                           'Gate/root/shape values are symbolic transformations, not detected physical resonance.',
                           'Rounding and minimum session number can collapse different inputs or amplify tiny differences.',
                           'Gate-window fractions count overlapping analysis windows, not independent observations or duration.',
                           'No scientific advantage, emotion, identity or health claim; no source audio was opened or modified.']}
    for condition in features['conditions']:
        windows=trial_records(condition['windows'],config)
        differences=[]
        for before,after in zip(original,windows):
            a,b=before['symbolic'],after['symbolic']
            if a['digitalRoot']!=b['digitalRoot'] or a['isGate']!=b['isGate']:
                differences.append({'index':before['index'],'centerSeconds':before['centerSeconds'],
                                    'originalRoot':a['digitalRoot'],'conditionRoot':b['digitalRoot'],
                                    'originalGate':a['isGate'],'conditionGate':b['isGate'],
                                    'originalScaledDelta':a['evolutionDelta']*100,'conditionScaledDelta':b['evolutionDelta']*100,
                                    'originalThresholdMargin':before['roundingThresholdMarginScaledUnits'],
                                    'voiceEnergyDifference':b['voiceEnergy']-a['voiceEnergy']})
        continuous={}
        for key in ('voiceEnergy','audioContribution','evolutionDelta'):
            delta=[b['symbolic'][key]-a['symbolic'][key] for a,b in zip(original,windows)]
            continuous[key]={'meanAbsoluteDifference':sum(abs(value) for value in delta)/len(delta),
                             'maxAbsoluteDifference':max(abs(value) for value in delta)}
        record['conditions'].append({'rateHz':condition['rateHz'],'sourceSha256':condition['sourceSha256'],
                                     'summary':summarize(windows),'continuousDifferences':continuous,
                                     'differentRootWindows':sum(a['symbolic']['digitalRoot']!=b['symbolic']['digitalRoot'] for a,b in zip(original,windows)),
                                     'differentGateWindows':sum(a['symbolic']['isGate']!=b['symbolic']['isGate'] for a,b in zip(original,windows)),
                                     'differentShapeWindows':sum(a['symbolic']['shape']!=b['symbolic']['shape'] for a,b in zip(original,windows)),
                                     'changedSymbolicWindows':differences,'windows':windows})
    for path,digest in ((feature_path,feature_hash),(summary_path,summary_hash),(config_path,config_hash)):
        if sha256(path)!=digest:raise ValueError('An input changed during the trial.')
    output.parent.mkdir(parents=True,exist_ok=True)
    staged=Path(tempfile.mkdtemp(prefix='.evo-trial-',dir=output.parent))
    try:
        with (staged/'trial.json').open('w',encoding='utf-8') as stream:json.dump(record,stream,allow_nan=False)
        small={key:value for key,value in record.items() if key not in ('original','conditions')}
        small['originalSummary']=original_summary
        small['conditions']=[{key:value for key,value in condition.items() if key!='windows'} for condition in record['conditions']]
        small['fullTrialSha256']=sha256(staged/'trial.json')
        (staged/'trial-summary.json').write_text(json.dumps(small,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        render(record,staged)
        output.mkdir()
        try:
            for item in staged.iterdir():shutil.move(str(item),output/item.name)
        except OSError:shutil.rmtree(output);raise
        print(f"Trial complete. Open {output/'trial.html'}",flush=True)
        return record
    finally:shutil.rmtree(staged,ignore_errors=True)


def render(record,folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    windows=record['original']['windows'];times=[item['centerSeconds'] for item in windows]
    fig,axes=plt.subplots(3,1,figsize=(13,9),sharex=True)
    axes[0].plot(times,[item['symbolic']['voiceEnergy'] for item in windows],label='Experimental normalized voiceEnergy')
    axes[0].set_ylabel('Configured scale, 0–1');axes[0].legend()
    axes[1].plot(times,[item['symbolic']['audioContribution'] for item in windows],label='Audio × configured focus')
    axes[1].plot(times,[item['symbolic']['sessionCountContribution'] for item in windows],label='Session-count × 369')
    axes[1].set_ylabel('Formula contribution');axes[1].legend()
    axes[2].step(times,[item['symbolic']['digitalRoot'] for item in windows],where='mid',label='Original symbolic root')
    axes[2].set(xlabel='Analysis window center (s)',ylabel='Symbolic root',ylim=(0,10));axes[2].legend()
    fig.tight_layout();fig.savefig(folder/'trial-timeline.png');plt.close(fig)
    rows=[]
    for condition in record['conditions']:
        rows.append(f"<tr><td>{condition['rateHz']}</td><td>{condition['continuousDifferences']['voiceEnergy']['maxAbsoluteDifference']:.6g}</td><td>{condition['differentRootWindows']}</td><td>{condition['differentGateWindows']}</td><td>{condition['differentShapeWindows']}</td><td>{condition['summary']['normalizationClippedWindows']}</td></tr>")
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Controlled evoMetrics trial</title><style>body{{font:16px system-ui;max-width:1200px;margin:auto;padding:24px;line-height:1.5}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}img{{max-width:100%}}td,th{{border:1px solid #aaa;padding:8px}}table{{border-collapse:collapse}}</style>
<h1>Controlled evoMetrics diagnostic trial</h1><p><strong>Experimental symbolic mapping, not measured human state or canonical Compiler 3 output.</strong> Source: {html.escape(record['inputs']['audioSource']['filename'])}.</p>
<h2>Fixed configuration</h2><pre>{html.escape(json.dumps(record['config'],indent=2))}</pre>
<p>Band RMS normalization reference 0.1 is a chosen experimental amplitude scale, not calibrated energy. Camera brightness is not being measured. No evolution history is updated.</p>
<h2>Original source summary</h2><pre>{html.escape(json.dumps(record['original']['summary'],indent=2))}</pre>
<img src="trial-timeline.png" alt="Experimental normalized input, separated formula contributions and symbolic root over time">
<h2>Differences from original</h2><table><tr><th>Rate</th><th>Max |Δ voiceEnergy|</th><th>Different root windows</th><th>Different gate windows</th><th>Different shape windows</th><th>Normalization-clipped windows</th></tr>{''.join(rows)}</table>
<p>Identical roots do not imply identical audio: small input differences may be hidden by quantization. A zero session-count contribution also means this trial does not test the 369 multiplier at nonzero session count.</p><h2>Zero-input control</h2><pre>{html.escape(json.dumps(record['zeroInputControl'],indent=2))}</pre><p>The original minimum/rounding rules can yield nonzero symbolic output for zero input. This is rule behavior, not detected sound.</p>
<p><a href="trial-summary.json">Small trial summary</a> • <a href="trial.json">Full per-window trial</a></p><ul>{''.join('<li>'+html.escape(item)+'</li>' for item in record['limitations'])}</ul></html>'''
    (folder/'trial.html').write_text(page,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--features',type=Path);parser.add_argument('--summary',type=Path)
    parser.add_argument('--config',type=Path,default=PRESET)
    parser.add_argument('--output',type=Path,default=Path('runtime/evo-trial-001'))
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
        run_trial(path,args.summary or path.parent/'summary.json',args.output,args.config)
    except KeyboardInterrupt:parser.exit(1,'Trial cancelled; no audio or history changed.\n')
    except Exception as error:parser.exit(1,f'Trial failed: {error}\n')

if __name__=='__main__':main()
