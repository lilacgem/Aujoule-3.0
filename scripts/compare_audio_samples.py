"""Read-only exact decoded-sample comparison against a hash-linked identity control."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import numpy as np
import soundfile as sf


def digest(path):
    result = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def compare(current, comparison):
    current, comparison = Path(current), Path(comparison)
    before = {'current': digest(current), 'comparison': digest(comparison)}
    record = json.loads(comparison.read_text(encoding='utf-8'))
    source = record['source']
    controls = [c for c in record['conditions'] if c.get('conversion') == 'identity-control'
                and c.get('targetRateHz') == source['sampleRateHz']]
    if len(controls) != 1:
        raise ValueError('Expected exactly one identity control at the original rate.')
    control = controls[0]
    name = control['file']
    if not isinstance(name, str) or Path(name).name != name or '/' in name or '\\' in name:
        raise ValueError('Control must be a filename beside comparison.json.')
    path = (comparison.parent / name).resolve()
    if path.parent != comparison.parent.resolve():
        raise ValueError('Control escapes comparison folder.')
    control_hash = digest(path)
    if control_hash != control['sha256']:
        raise ValueError('Control file hash does not match comparison.json; comparison stopped.')
    count = 0
    first = None
    peak = 0.0
    with sf.SoundFile(current) as a, sf.SoundFile(path) as b:
        properties = lambda f: {'sampleRateHz': f.samplerate, 'frames': f.frames, 'channels': f.channels}
        current_info, control_info = properties(a), properties(b)
        if current_info != control_info:
            raise ValueError('Rate, frame count or channel count differs; exact aligned comparison stopped.')
        offset = 0
        while True:
            x = a.read(65536, dtype='float64', always_2d=True)
            y = b.read(65536, dtype='float64', always_2d=True)
            if x.shape != y.shape:
                raise ValueError('Input length changed during comparison.')
            if not len(x):
                break
            if not np.isfinite(x).all() or not np.isfinite(y).all():
                raise ValueError('Non-finite samples; refusing an equivalence result.')
            different = x != y
            count += int(np.count_nonzero(different))
            if first is None and different.any():
                frame, channel = np.argwhere(different)[0]
                first = {'frame': offset + int(frame), 'channel': int(channel) + 1}
            peak = max(peak, float(np.max(np.abs(x-y))))
            offset += len(x)
        if offset != current_info['frames']:
            raise ValueError('Decoded frame count differs from header.')
    if digest(current) != before['current'] or digest(comparison) != before['comparison'] or digest(path) != control_hash:
        raise ValueError('Input changed during comparison; refusing result.')
    return {'schema': 'AUEVO-DecodedSampleComparison/v0.1',
            'status': 'decoded-samples-identical' if count == 0 else 'decoded-samples-differ',
            'current': {'filename': current.name, 'sha256': before['current'], **current_info},
            'control': {'filename': name, 'sha256': control_hash, **control_info},
            'comparisonSha256': before['comparison'], 'declaredEarlierSourceSha256': source['sha256'],
            'method': 'Streaming float64 decode; exact numeric comparison, no tolerance, alignment or resampling.',
            'differentChannelSamples': count, 'firstDifference': first, 'maximumAbsoluteDifference': peak,
            'historyAdvanced': False, 'inputsModified': False,
            'limitations': ['Comparison record is hash-linked but not authenticated.',
                'Equality applies to decoded samples against this control, not original WAV bytes or all metadata.',
                'Does not identify why file bytes changed or override existing evidence hashes.']}


def choose(title):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk(); root.withdraw()
    try:
        return filedialog.askopenfilename(title=title)
    finally:
        root.destroy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', type=Path)
    parser.add_argument('--comparison', type=Path)
    parser.add_argument('--output', type=Path, default=Path('runtime/audio-sample-check-001'))
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError('Output already exists; choose a new --output folder.')
        current = args.current or choose('Select current original WAV')
        comparison = args.comparison or choose('Select earlier rate-comparison-001 comparison.json')
        if not current or not comparison:
            raise ValueError('Selection cancelled.')
        print('Checking control hash and comparing decoded samples...', flush=True)
        result = compare(current, comparison)
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / 'sample-comparison.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        page = '<!doctype html><meta charset="utf-8"><title>Decoded sample comparison</title><h1>Decoded sample comparison</h1><pre>'+html.escape(json.dumps(result, indent=2))+'</pre>'
        (args.output / 'sample-comparison.html').write_text(page, encoding='utf-8')
        print(result['status'])
        print('Open '+str(args.output / 'sample-comparison.html'))
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
        parser.exit(1, f'Comparison stopped: {error}\n')


if __name__ == '__main__':
    main()
