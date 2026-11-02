"""One-factor-at-a-time diagnostics on fixed corrected audio measurements."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import platform
import shutil
import tempfile

try:
    from scripts.run_evo_trial import validate_inputs,trial_records,summarize,CORE
    from scripts.evo_metrics_experiment import validate_config
    from scripts.compile_package import load_json
    from scripts.analyze_audio import sha256
except ModuleNotFoundError:
    from run_evo_trial import validate_inputs,trial_records,summarize,CORE
    from evo_metrics_experiment import validate_config
    from compile_package import load_json
    from analyze_audio import sha256

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/evo-sensitivity-study.json'


def variants(plan):
    if plan.get('schema')!='AUEVO-EvoSensitivityPlan/v0.1':raise ValueError('Unsupported study plan.')
    baseline=validate_config(plan['baseline'])
    if not baseline['enabled']:raise ValueError('Baseline must explicitly enable the diagnostic.')
    factors=plan.get('factors')
    if not isinstance(factors,dict) or set(factors)!={'bandRmsReference','configuredFocus','sessionCount'}:
        raise ValueError('Exactly the three declared factors are supported.')
    result=[{'id':'baseline','factor':'baseline','value':None,'config':dict(baseline)}]
    for key,values in factors.items():
        if not isinstance(values,list) or not 1<=len(values)<=20:raise ValueError('Each factor needs 1–20 values.')
        seen=set()
        for value in values:
            config={**baseline,key:value};validate_config(config)
            if value==baseline[key] or value in seen:raise ValueError('Duplicate/baseline factor value.')
            seen.add(value)
            result.append({'id':f'{key}={value}','factor':key,'value':value,'config':config})
    return result


def output_differences(reference,condition):
    if len(reference)!=len(condition):raise ValueError('Unaligned symbolic outputs.')
    voice=[abs(b['symbolic']['voiceEnergy']-a['symbolic']['voiceEnergy']) for a,b in zip(reference,condition)]
    return {'differentRootWindows':sum(a['symbolic']['digitalRoot']!=b['symbolic']['digitalRoot'] for a,b in zip(reference,condition)),
            'differentGateWindows':sum(a['symbolic']['isGate']!=b['symbolic']['isGate'] for a,b in zip(reference,condition)),
            'differentShapeWindows':sum(a['symbolic']['shape']!=b['symbolic']['shape'] for a,b in zip(reference,condition)),
            'meanAbsoluteVoiceDifference':sum(voice)/len(voice),'maxAbsoluteVoiceDifference':max(voice)}


def contribution_summary(records):
    shares=[]
    for row in records:
        symbolic=row['symbolic'];total=symbolic['audioContribution']+symbolic['sessionCountContribution']
        if total>0:shares.append(symbolic['sessionCountContribution']/total)
    return {'sessionContributionShare':{'mean':sum(shares)/len(shares) if shares else None,
                                       'minimum':min(shares) if shares else None,'maximum':max(shares) if shares else None,
                                       'validWindows':len(shares),'undefinedZeroTotalWindows':len(records)-len(shares)},
            'scope':'Shares refer to raw positive formula terms before rounding, carry and digital-root reduction; not a causal importance score.'}


def run_study(feature_path,summary_path,output,plan_path=PLAN):
    feature_path,summary_path,plan_path,output=map(Path,(feature_path,summary_path,plan_path,output))
    output=output.resolve()
    if output.exists():raise ValueError('Output exists; choose a new study directory.')
    hashes={str(path):sha256(path) for path in (feature_path,summary_path,plan_path)}
    features=load_json(feature_path);summary=load_json(summary_path);plan=load_json(plan_path)
    validate_inputs(features,summary,hashes[str(feature_path)])
    settings=variants(plan)
    original=features['originalWindows']
    baseline=trial_records(original,settings[0]['config'])
    report={'schema':'AUEVO-EvoSensitivityStudy/v0.1','status':'experimental-not-canonical-state',
            'inputs':{'featureSha256':hashes[str(feature_path)],'summarySha256':hashes[str(summary_path)],
                      'planSha256':hashes[str(plan_path)],'audioSource':features['source'],'measurementMethod':features['method']},
            'producer':{'version':'0.1.0','buildHash':sha256(__file__),'python':platform.python_version(),
                        'coreSha256':sha256(CORE),'adaptationSha256':sha256(Path(__file__).with_name('evo_metrics_experiment.py'))},
            'plan':plan,'variants':[],
            'limitations':['One factor changes at a time; no interaction study or gate-maximizing optimization.',
                           'Same fixed measurements are reused; no audio files or persistent history are accessed/changed.',
                           'Overlapping window counts are not independent observations, significance tests or time percentages.',
                           'Symbolic counts, gates and shapes are rule outputs, not physical resonance, emotion or human state.',
                           'Raw session-count dominance and digital-root sensitivity are different properties.',
                           'Session count caps at 100 in the original formula; values above that are saturation controls.',
                           'Normalization clipping is not audio clipping. Focus is configured, not camera measured.']}
    for setting in settings:
        print(f"Evaluating {setting['id']}...",flush=True)
        records=trial_records(original,setting['config'])
        sequence=[(row['symbolic']['digitalRoot'],row['symbolic']['isGate'],row['symbolic']['shape']['p'],row['symbolic']['shape']['q']) for row in records]
        signature=hashlib.sha256(json.dumps(sequence,separators=(',',':')).encode('utf-8')).hexdigest()
        result={**setting,'originalSummary':summarize(records),
                'symbolicSequenceSha256':signature,'sequenceHashScope':'Ordered original-window root/gate/p/q tuples only, not full audio or all continuous outputs',
                'versusBaseline':output_differences(baseline,records),
                'contributions':contribution_summary(records),'rateConditions':[],
                'historyAdvanced':False}
        # Evaluate every rate under the same setting, avoiding factor/rate confounding.
        for condition in features['conditions']:
            compared=trial_records(condition['windows'],setting['config'])
            changed=[]
            for before,after in zip(records,compared):
                a,b=before['symbolic'],after['symbolic']
                if a['digitalRoot']!=b['digitalRoot'] and len(changed)<50:
                    changed.append({'index':before['index'],'centerSeconds':before['centerSeconds'],
                                    'originalRoot':a['digitalRoot'],'conditionRoot':b['digitalRoot'],
                                    'originalScaledDelta':a['evolutionDelta']*100,'conditionScaledDelta':b['evolutionDelta']*100,
                                    'originalThresholdMargin':before['roundingThresholdMarginScaledUnits'],
                                    'note':'Same configured rules; bucket crossing does not establish physical significance.'})
            result['rateConditions'].append({'rateHz':condition['rateHz'],
                                              'versusOriginalAtSameSetting':output_differences(records,compared),
                                              'changedRootDetails':changed,'changedRootDetailLimit':50,
                                              'normalizationClippedWindows':sum(bool(row['symbolic']['normalizationClippedBands']) for row in compared)})
        report['variants'].append(result)
    groups={}
    for item in report['variants']:groups.setdefault(item['symbolicSequenceSha256'],[]).append(item['id'])
    report['sameSymbolicSequenceGroups']=[group for group in groups.values() if len(group)>1]
    for path in (feature_path,summary_path,plan_path):
        if sha256(path)!=hashes[str(path)]:raise ValueError('An input changed during study.')
    output.parent.mkdir(parents=True,exist_ok=True)
    staged=Path(tempfile.mkdtemp(prefix='.sensitivity-',dir=output.parent))
    try:
        (staged/'sensitivity-summary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        render(report,staged)
        output.mkdir()
        try:
            for item in staged.iterdir():shutil.move(str(item),output/item.name)
        except OSError:shutil.rmtree(output);raise
        print(f"Study finished. Open {output/'sensitivity.html'}",flush=True)
        return report
    finally:shutil.rmtree(staged,ignore_errors=True)


def render(report,folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,1,figsize=(13,11))
    for axis,factor in zip(axes,('bandRmsReference','configuredFocus','sessionCount')):
        values=[report['variants'][0]]+[item for item in report['variants'] if item['factor']==factor]
        labels=['baseline']+[str(item['value']) for item in values[1:]]
        axis.bar(range(len(values)),[item['versusBaseline']['differentRootWindows'] for item in values])
        axis.set_xticks(range(len(values)),labels);axis.set(title=f'Change only {factor}',ylabel='Root windows differing\nfrom fixed baseline')
    fig.tight_layout();fig.savefig(folder/'sensitivity.png');plt.close(fig)
    rows=[]
    for item in report['variants']:
        summary=item['originalSummary'];shares=item['contributions']['sessionContributionShare']
        share='undefined' if shares['mean'] is None else f"{shares['mean']*100:.3f}%"
        rows.append(f"<tr><td>{html.escape(item['id'])}</td><td>{item['versusBaseline']['differentRootWindows']}</td><td>{item['versusBaseline']['differentGateWindows']}</td><td>{summary['sessionNumberOneWindows']}</td><td>{summary['normalizationClippedWindows']}</td><td>{share}</td><td>{max(row['versusOriginalAtSameSetting']['differentRootWindows'] for row in item['rateConditions'])}</td></tr>")
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>evoMetrics sensitivity study</title><style>body{{font:16px system-ui;max-width:1300px;margin:auto;padding:24px;line-height:1.5}}table{{border-collapse:collapse}}td,th{{border:1px solid #aaa;padding:8px}}img{{max-width:100%}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}</style>
<h1>evoMetrics sensitivity — one factor at a time</h1><p><strong>Diagnostic study, not a recommended production formula or a search for more gates.</strong></p>
<p>Source: {html.escape(report['inputs']['audioSource']['filename'])}. {report['variants'][0]['originalSummary']['windowCount']} overlapping windows per setting. No audio opened or history updated.</p>
<table><tr><th>Setting</th><th>Changed roots vs baseline</th><th>Changed gates vs baseline</th><th>Minimum session-number windows</th><th>Normalization-clipped windows</th><th>Mean raw session-term share</th><th>Max changed roots across rates at this setting</th></tr>{''.join(rows)}</table>
<img src="sensitivity.png" alt="Root-output sensitivity to each independently changed setting">
<p>The raw contribution share does not measure causal importance after modulo/digital-root processing. Below the session cap, session-count increments add nominal multiples of 369 after scaling by 100; 369 is divisible by 9. Digital-root reduction can therefore erase these increments except where floor/rounding behavior matters. Floating-point thresholds must still be checked. The zero-focus row is a control, not missing camera data.</p>
<h2>Identical root/gate/shape sequences</h2><pre>{html.escape(json.dumps(report['sameSymbolicSequenceGroups'],indent=2))}</pre><p>These groups match only the hashed symbolic sequence, not all continuous values or audio files.</p><h2>Predeclared plan</h2><pre>{html.escape(json.dumps(report['plan'],indent=2))}</pre><p><a href="sensitivity-summary.json">Complete study summary, settings, counts and per-rate comparisons</a></p><ul>{''.join('<li>'+html.escape(item)+'</li>' for item in report['limitations'])}</ul></html>'''
    (folder/'sensitivity.html').write_text(page,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--features',type=Path);parser.add_argument('--summary',type=Path)
    parser.add_argument('--plan',type=Path,default=PLAN);parser.add_argument('--output',type=Path,default=Path('runtime/evo-sensitivity-001'))
    args=parser.parse_args()
    try:
        path=args.features
        if path is None:
            import tkinter as tk
            from tkinter import filedialog
            root=tk.Tk();root.withdraw()
            try:selected=filedialog.askopenfilename(title='Select corrected features.json inside matched-features-002',filetypes=[('JSON features','*.json')])
            finally:root.destroy()
            if not selected:print('Cancelled; nothing changed.');return
            path=Path(selected)
        run_study(path,args.summary or path.parent/'summary.json',args.output,args.plan)
    except KeyboardInterrupt:parser.exit(1,'Cancelled; no audio/history changed.\n')
    except Exception as error:parser.exit(1,f'Sensitivity study failed: {error}\n')

if __name__=='__main__':main()
