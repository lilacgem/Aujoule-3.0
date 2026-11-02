"""Compare measured audio features on common physical windows; optional symbolic experiment."""
import argparse
import html
import json
import math
from pathlib import Path
import platform
import shutil
import tempfile

import numpy as np
import scipy
import soundfile as sf

try:
    from scripts.analyze_audio import sha256
    from scripts.compile_package import load_json
    from scripts.evo_metrics_experiment import validate_config, evaluate
except ModuleNotFoundError:
    from analyze_audio import sha256
    from compile_package import load_json
    from evo_metrics_experiment import validate_config, evaluate

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'docs/source_records/evo-metrics-received/evoMetrics.js'


def fractional_bin_weights(frequency, nyquist, lower, upper):
    """Fraction of each FFT bin's power assigned to a band by bin-cell overlap.

    Bin cells meet at frequency midpoints, clipped to 0..Nyquist. Endpoint
    cells retain their full discrete PSD-bin mass, conserving sum(PSD)*df.
    This is a uniform-within-cell estimate, not recovered sub-bin information.
    """
    frequency=np.asarray(frequency,dtype=float)
    if frequency.ndim!=1 or len(frequency)<2 or not np.all(np.isfinite(frequency)) or frequency[0]!=0 or np.any(np.diff(frequency)<=0):
        raise ValueError('An increasing one-sided FFT frequency grid starting at zero is required.')
    if not all(math.isfinite(value) for value in (nyquist,lower,upper)) or nyquist<=0 or lower<0 or upper<lower:
        raise ValueError('Invalid frequency integration limits.')
    if frequency[-1]>nyquist+1e-9*(frequency[1]-frequency[0]):raise ValueError('Frequency grid exceeds Nyquist.')
    edges=np.concatenate(([0.],(frequency[:-1]+frequency[1:])/2,[nyquist]))
    widths=np.diff(edges)
    if np.any(widths<=0):raise ValueError('Invalid FFT bin-cell widths.')
    overlap=np.maximum(0,np.minimum(edges[1:],min(upper,nyquist))-np.maximum(edges[:-1],lower))
    return np.clip(overlap/widths,0,1)


def integrate_band(power,frequency,nyquist,lower,upper):
    weights=fractional_bin_weights(frequency,nyquist,lower,upper)
    return float(np.dot(power,weights)*(frequency[1]-frequency[0]))


def spectral_features(power, frequency, upper, nyquist):
    weights=fractional_bin_weights(frequency,nyquist,0,upper)
    weighted=power*weights
    total=float(weighted.sum())
    if total<=1e-20:return {'centroidHz':None,'bandwidthHz':None,'rolloff85Hz':None,'flatness':None}
    centroid=float(np.sum(weighted*frequency)/total)
    active=weights>0
    flatness=float(np.exp(np.sum(weights[active]*np.log(np.maximum(power[active],1e-30)))/weights.sum())/(total/weights.sum()))
    return {'centroidHz':centroid,'bandwidthHz':float(np.sqrt(np.sum(weighted*(frequency-centroid)**2)/total)),
            'rolloff85Hz':float(frequency[np.searchsorted(np.cumsum(weighted),total*.85)]),
            'flatness':flatness}


def measure_windows(path, source_duration, common_upper, window_seconds, hop_seconds, config):
    records=[];previous_band=None;previous_rms=None
    with sf.SoundFile(path) as audio:
        rate=audio.samplerate
        count=max(0,math.floor((source_duration-window_seconds)/hop_seconds)+1)
        if count<1:raise ValueError('Source is shorter than the requested window; choose a smaller window.')
        for index in range(count):
            start=index*hop_seconds;end=start+window_seconds
            first=round(start*rate);last=round(end*rate)
            if last>audio.frames:raise ValueError('A target does not cover the complete common time interval.')
            audio.seek(first);data=audio.read(last-first,dtype='float64',always_2d=True)
            if len(data)!=last-first or not np.all(np.isfinite(data)):raise ValueError('Invalid audio samples or incomplete read.')
            size=len(data);window=np.hanning(size)
            transformed=np.fft.rfft((data-data.mean(axis=0))*window[:,None],axis=0)
            power=(np.abs(transformed)**2).mean(axis=1)/(rate*np.sum(window**2))
            if size%2:power[1:]*=2
            else:power[1:-1]*=2
            frequency=np.fft.rfftfreq(size,1/rate);df=rate/size
            bands={name:integrate_band(power,frequency,rate/2,lo,hi)
                   for name,lo,hi in [('bass',20,250),('mid',250,4000),('high',4000,common_upper)]}
            rms=float(np.sqrt(np.mean(data*data)));peak=float(np.abs(data).max())
            amplitudes=np.sqrt(list(bands.values()))
            record={'index':index,'startSeconds':start,'endSeconds':end,'centerSeconds':(start+end)/2,
                    'actualStartSeconds':first/rate,'actualEndSeconds':last/rate,'windowSamples':size,'binSpacingHz':df,
                    'evidenceClass':'MEASURED','rmsLinear':rms,'samplePeak':peak,
                    'crestFactor':peak/rms if rms>0 else None,
                    'rmsChangeDb':20*math.log10(rms/previous_rms) if rms>0 and previous_rms is not None and previous_rms>0 else None,
                    'positiveBandChange':float(np.maximum(amplitudes-previous_band,0).sum()) if previous_band is not None else None,
                    'commonBandPower':bands,'fullBand':spectral_features(power,frequency,rate/2,rate/2),
                    'commonBand':spectral_features(power,frequency,common_upper,rate/2)}
            if config:record['evoMetricsExperiment']=evaluate(bands,config)
            records.append(record);previous_band=amplitudes;previous_rms=rms
    return records


def differences(reference,condition):
    fields={'rmsLinear':lambda x:x['rmsLinear'],'samplePeak':lambda x:x['samplePeak'],
            'centroidHz':lambda x:x['commonBand']['centroidHz'],'bandwidthHz':lambda x:x['commonBand']['bandwidthHz'],
            'rolloff85Hz':lambda x:x['commonBand']['rolloff85Hz'],
            **{f'{name}Power':lambda x,key=name:x['commonBandPower'][key] for name in ('bass','mid','high')}}
    result={}
    for name,read in fields.items():
        delta=[read(b)-read(a) for a,b in zip(reference,condition) if read(a) is not None and read(b) is not None]
        result[name]={'comparedWindows':len(delta),'meanSignedDifference':float(np.mean(delta)) if delta else None,
                      'meanAbsoluteDifference':float(np.mean(np.abs(delta))) if delta else None,
                      'maxAbsoluteDifference':float(np.max(np.abs(delta))) if delta else None}
    return result


def validate_comparison(comparison,folder):
    if comparison.get('schema')!='AUEVO-SampleRateComparison/v0.1' or comparison.get('experimentType')!='software-resampling-not-native-capture':
        raise ValueError('Select a supported comparison.json from the sample-rate experiment.')
    conditions=comparison.get('conditions')
    if not isinstance(conditions,list) or not conditions:raise ValueError('Comparison has no conditions.')
    files=[];rates=set()
    for item in conditions:
        name=item.get('file');rate=item.get('targetRateHz')
        if not isinstance(name,str) or Path(name).name!=name or '/' in name or '\\' in name:raise ValueError('Unsafe derived filename.')
        path=(folder/name).resolve()
        if path.parent!=folder.resolve() or path in files:raise ValueError('Derived file must be unique and inside the comparison folder.')
        if type(rate) is not int or rate<=0 or rate in rates:raise ValueError('Invalid or duplicate condition rate.')
        if sha256(path)!=item.get('sha256'):raise ValueError(f'Derived file hash mismatch: {name}')
        info=sf.info(path)
        if info.samplerate!=rate or info.frames!=item.get('frames') or info.channels!=comparison['source']['channels']:
            raise ValueError(f'Derived header mismatch: {name}')
        files.append(path);rates.add(rate)
    return list(zip(conditions,files))


def compare_features(original,comparison_path,output,*,window_seconds=.25,hop_seconds=.125,config=None):
    if not all(math.isfinite(x) for x in (window_seconds,hop_seconds)) or not .02<=window_seconds<=5 or not .001<=hop_seconds<=window_seconds:
        raise ValueError('Window must be .02–5 seconds; hop must be .001 seconds to window duration.')
    if config:validate_config(config)
    original,comparison_path,output=Path(original),Path(comparison_path),Path(output).resolve()
    if output.exists():raise ValueError('Output exists; choose a new folder.')
    comparison_hash=sha256(comparison_path)
    comparison=load_json(comparison_path)
    source_hash=sha256(original)
    if source_hash!=comparison['source']['sha256']:raise ValueError('Original hash does not match the comparison experiment.')
    source=sf.info(original)
    if source.samplerate!=comparison['source']['sampleRateHz'] or source.frames!=comparison['source']['frames'] or source.channels!=comparison['source']['channels']:
        raise ValueError('Original header does not match the comparison.')
    files=validate_comparison(comparison,comparison_path.parent)
    common_upper=min(20000.,source.samplerate/2,*[item['targetRateHz']/2 for item,_ in files])
    if common_upper<=4000:raise ValueError('This prototype requires a common upper frequency above 4000 Hz.')
    count=math.floor((source.duration-window_seconds)/hop_seconds)+1
    if not 1<=count<=50000:raise ValueError('This prototype supports 1–50,000 windows per condition; increase hop for longer audio.')
    output.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(output.parent).free < count*(len(files)+1)*4000+20*1024*1024:
        raise ValueError('Insufficient disk space for feature records and plots.')
    print('Comparing matching time windows; original and derived audio are read-only.',flush=True)
    reference=measure_windows(original,source.duration,common_upper,window_seconds,hop_seconds,config)
    report={'schema':'AUEVO-MatchedAudioFeatures/v0.2','source':comparison['source'],
            'comparisonRef':{'filename':comparison_path.name,'sha256':comparison_hash},
            'method':{'version':'0.2.0','buildHash':sha256(__file__),'python':platform.python_version(),
                      'numpy':np.__version__,'scipy':scipy.__version__,'soundfile':sf.__version__,
                      'windowSeconds':window_seconds,'hopSeconds':hop_seconds,'windowCount':count,
                      'window':'symmetric Hann, channel-power mean, per-window DC removal',
                      'timeAlignment':'same physical start/end, nearest sample boundaries; no correlation fitting',
                      'commonUpperHz':common_upper,'bandsHz':{'bass':[20,250],'mid':[250,4000],'high':[4000,common_upper]},
                      'positiveBandChange':'sum positive changes of band RMS between adjacent windows; not full-spectrum flux or a certified transient detector',
                      'dynamics':'window RMS, sample peak, crest factor, adjacent RMS change; not calibrated loudness',
                      'spectralUnit':'one-sided PSD in sample unit squared per Hz; bands integrate discrete bin mass with fractional cell overlap',
                      'bandIntegration':{'id':'fractional-bin-cell-overlap/v1','cells':'midpoints between FFT centers, clipped to 0..Nyquist',
                                         'massConvention':'each bin retains PSD*df mass, including DC/Nyquist endpoints',
                                         'withinCellModel':'uniform distribution of bin power; no recovered sub-bin information',
                                         'spectralMoments':'fractional upper-band weights applied; centroid uses bin centers; rolloff remains bin-quantized; flatness is fraction-weighted'}},
            'symbolicExperiment':{'enabled':bool(config and config['enabled']), 'config':config,
                                  'receivedCoreSha256':sha256(CORE),
                                  'adaptationSha256':sha256(Path(__file__).with_name('evo_metrics_experiment.py')),
                                  'interpretation':'Independent diagnostic evaluation per window. No carry or session history advances. Configured focus is not measured camera brightness. 369 is symbolic, not measured frequency.'},
            'originalWindows':reference,'conditions':[],
            'limitations':['Software-resampled data only, not native sample-rate evidence.',
                           'Full-band metrics have different bandwidths; primary differences use the same common upper frequency.',
                           'Fractional integration reduces all-or-nothing band assignment; finite-window leakage, grid placement and boundary rounding still affect estimates. This is not a quality ranking.',
                           'Version 0.2 changes band integration and common-band weights; older feature reports are retained, not silently equivalent.',
                           'Last incomplete physical window is excluded. No pitch, emotion, medical state or identity inference.',
                           'Experimental normalization is chosen configuration, not original core mathematics or a calibrated energy scale.']}
    staged=Path(tempfile.mkdtemp(prefix='.matched-features-',dir=output.parent))
    try:
        for item,path in files:
            print(f"Analysing {item['targetRateHz']} Hz...",flush=True)
            records=measure_windows(path,source.duration,common_upper,window_seconds,hop_seconds,config)
            if sha256(path)!=item['sha256']:raise ValueError('Derived file changed during analysis.')
            condition={'rateHz':item['targetRateHz'],'sourceFile':path.name,'sourceSha256':item['sha256'],
                       'differencesFromOriginal':differences(reference,records),'windows':records}
            if config and config['enabled']:
                condition['symbolicComparison']={'differentRootWindows':sum(a['evoMetricsExperiment']['digitalRoot']!=b['evoMetricsExperiment']['digitalRoot'] for a,b in zip(reference,records)),
                                                 'differentGateWindows':sum(a['evoMetricsExperiment']['isGate']!=b['evoMetricsExperiment']['isGate'] for a,b in zip(reference,records)),
                                                 'note':'Differences can be threshold/rounding effects; no physical resonance or superiority implied.'}
            report['conditions'].append(condition)
        if sha256(original)!=source_hash or sha256(comparison_path)!=report['comparisonRef']['sha256']:
            raise ValueError('Input changed; no report published.')
        with (staged/'features.json').open('w',encoding='utf-8') as stream:
            json.dump(report,stream,allow_nan=False)
            stream.write('\n')
        summary={key:value for key,value in report.items() if key not in ('originalWindows','conditions')}
        summary['originalWindowCount']=len(reference)
        summary['conditions']=[{key:value for key,value in condition.items() if key!='windows'} for condition in report['conditions']]
        summary['fullRecordsSha256']=sha256(staged/'features.json')
        (staged/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        render(report,staged)
        output.mkdir()
        try:
            for item in staged.iterdir():shutil.move(str(item),output/item.name)
        except OSError:shutil.rmtree(output);raise
        print(f"Finished. Open {output/'features.html'}",flush=True)
        return report
    finally:shutil.rmtree(staged,ignore_errors=True)


def render(report,folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    times=[item['centerSeconds'] for item in report['originalWindows']]
    fig,axes=plt.subplots(3,1,figsize=(13,10),sharex=True)
    selections=[('rmsLinear',lambda x:x['rmsLinear'],'Window RMS (linear)'),
                ('centroidHz',lambda x:x['commonBand']['centroidHz'],'Common-band centroid (Hz)'),
                ('highPower',lambda x:x['commonBandPower']['high'],'Common high-band power')]
    rows=[]
    for condition in report['conditions']:
        for axis,(_,read,label) in zip(axes,selections):
            delta=[read(b)-read(a) if read(a) is not None and read(b) is not None else np.nan for a,b in zip(report['originalWindows'],condition['windows'])]
            axis.plot(times,delta,label=f"{condition['rateHz']} Hz",linewidth=.6);axis.set_ylabel('Δ '+label)
        diff=condition['differencesFromOriginal']
        root=condition.get('symbolicComparison',{}).get('differentRootWindows','off')
        fmt=lambda value:'unavailable' if value is None else f'{value:.6g}'
        rows.append(f"<tr><td>{condition['rateHz']}</td><td>{fmt(diff['rmsLinear']['meanAbsoluteDifference'])}</td><td>{fmt(diff['centroidHz']['meanAbsoluteDifference'])}</td><td>{fmt(diff['highPower']['meanAbsoluteDifference'])}</td><td>{root}</td></tr>")
    axes[0].legend(ncol=3);axes[-1].set_xlabel('Common window center time (s)');fig.tight_layout();fig.savefig(folder/'feature-differences.png');plt.close(fig)
    webpage=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Matched audio features</title><style>body{{font:16px system-ui;max-width:1300px;margin:auto;padding:24px;line-height:1.5}}td,th{{padding:8px;border:1px solid #aaa}}table{{border-collapse:collapse}}img{{max-width:100%}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}</style>
<h1>Matched-window audio features: {html.escape(report['source']['filename'])}</h1><p>Method {report['method']['version']} • fractional-bin integration. Power in a bin crossing a band edge is split by cell overlap, not assigned wholly by its center. This is an estimate within each bin, not newly resolved frequency information.</p><p>Measured audio features and optional experimental symbolic outputs remain separate. No new capture or new physical claim.</p>
<p>{report['method']['windowCount']} windows, {report['method']['windowSeconds']}s each, {report['method']['hopSeconds']}s hop. Common-band upper limit: {report['method']['commonUpperHz']} Hz. Full-band metrics are also in JSON.</p>
<table><tr><th>Rate</th><th>Mean |Δ RMS|</th><th>Mean |Δ centroid| Hz</th><th>Mean |Δ high-band power|</th><th>Different symbolic root windows</th></tr>{''.join(rows)}</table>
<img src="feature-differences.png" alt="Differences from original across matching time windows; data in feature JSON">
<h2>Symbolic experiment</h2><pre>{html.escape(json.dumps(report['symbolicExperiment'],indent=2))}</pre><p><a href="features.json">Full features, provenance, configuration and limitations</a> • <a href="summary.json">Small summary for sharing</a></p><ul>{''.join('<li>'+html.escape(x)+'</li>' for x in report['limitations'])}</ul></html>'''
    (folder/'features.html').write_text(webpage,encoding='utf-8')


def choose(title,types):
    import tkinter as tk
    from tkinter import filedialog
    root=tk.Tk();root.withdraw()
    try:return filedialog.askopenfilename(title=title,filetypes=types)
    finally:root.destroy()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',type=Path);parser.add_argument('--comparison',type=Path)
    parser.add_argument('--output',type=Path,default=Path('runtime/matched-features-001'))
    parser.add_argument('--window-seconds',type=float,default=.25);parser.add_argument('--hop-seconds',type=float,default=.125)
    parser.add_argument('--evo-config',type=Path,help='Optional explicit experimental normalization/focus/context configuration')
    args=parser.parse_args()
    try:
        original=args.original or choose('Select unchanged original WAV',[('WAV audio','*.wav')])
        if not original:print('Cancelled; nothing changed.');return
        comparison=args.comparison or choose('Select comparison.json from rate-comparison-001',[('JSON comparison','*.json')])
        if not comparison:print('Cancelled; nothing changed.');return
        compare_features(original,comparison,args.output,window_seconds=args.window_seconds,hop_seconds=args.hop_seconds,
                         config=load_json(args.evo_config) if args.evo_config else None)
    except KeyboardInterrupt:parser.exit(1,'Cancelled; audio unchanged.\n')
    except Exception as error:parser.exit(1,f'Feature comparison failed: {error}\n')

if __name__=='__main__':main()
