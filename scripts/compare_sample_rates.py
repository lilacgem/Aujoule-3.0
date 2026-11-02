"""Controlled, local software-resampling comparisons. Not native capture."""
import argparse
import gc
import html
import json
import math
import os
from pathlib import Path
import platform
import shutil
import tempfile

import numpy as np
import scipy
from scipy.signal import resample_poly, firwin, kaiserord
import soundfile as sf

try:
    from scripts.analyze_audio import sha256
except ModuleNotFoundError:
    from analyze_audio import sha256

RATES = [44100, 48000, 96000, 66666, 66369, 36369, 63369, 99369, 93369, 96369]


def filter_parameters(source_rate, target_rate):
    divisor = math.gcd(source_rate, target_rate)
    up, down = target_rate // divisor, source_rate // divisor
    if up == down:
        return {'applied': False, 'up': 1, 'down': 1, 'numTaps': 0}
    factor = max(up, down)
    taps, beta = kaiserord(100, .1 / factor)
    if taps % 2 == 0: taps += 1
    if taps > 10000001:
        raise ValueError('This rate ratio requires an oversized prototype filter; choose a supported ratio or a dedicated multistage resampler.')
    return {'applied': True, 'up': up, 'down': down, 'numTaps': taps,
            'kaiserBeta': float(beta), 'normalizedCutoff': .95 / factor,
            'normalizedTransitionWidth': .1 / factor,
            'nominalPassbandUpperHz': .90 * min(source_rate, target_rate) / 2,
            'nominalStopbandLowerHz': min(source_rate, target_rate) / 2,
            'attenuationDesignDb': 100}


def convert(audio, source_rate, target_rate):
    settings = filter_parameters(source_rate, target_rate)
    if not settings['applied']:
        return audio.copy()
    coefficients = firwin(settings['numTaps'], settings['normalizedCutoff'], window=('kaiser', settings['kaiserBeta']))
    return resample_poly(audio, settings['up'], settings['down'], axis=0, window=coefficients, padtype='constant')


def levels(audio):
    channels = audio.shape[1]
    squares = np.zeros(channels); peaks = np.zeros(channels)
    for start in range(0, len(audio), 65536):
        block = audio[start:start + 65536]
        if not np.all(np.isfinite(block)): raise ValueError('Audio contains non-finite samples.')
        squares += (block * block).sum(axis=0)
        peaks = np.maximum(peaks, np.abs(block).max(axis=0))
    return {'rmsPerChannel': np.sqrt(squares / len(audio)).tolist(), 'samplePeakPerChannel': peaks.tolist()}


def error_metrics(original, restored):
    count = min(len(original), len(restored))
    square_error = square_source = 0.; peak = 0.
    for start in range(0, count, 65536):
        a, b = original[start:min(start + 65536, count)], restored[start:min(start + 65536, count)]
        delta = b - a
        square_error += float(np.sum(delta * delta)); square_source += float(np.sum(a * a))
        peak = max(peak, float(np.max(np.abs(delta))))
    denominator = count * original.shape[1]
    return {'comparedFrames': count, 'rmse': math.sqrt(square_error / denominator),
            'peakAbsoluteError': peak,
            'snrDb': 10 * math.log10(square_source / square_error) if square_source > 0 and square_error > 0 else None,
            'snrStatus': 'finite' if square_source > 0 and square_error > 0 else 'exact-match' if square_error == 0 else 'undefined-silent-source',
            'alignment': 'start-aligned resample_poly; no fitted gain, time shift or normalization'}


def spectrum(audio, rate):
    # Match physical window duration rather than using the same FFT count at all rates.
    size = max(8, round(rate * .25))
    hop = max(1, size // 2)
    window = np.hanning(size)
    frequencies = np.fft.rfftfreq(size, 1 / rate)
    total = np.zeros(len(frequencies)); count = 0
    padded = len(audio) < size
    if padded:
        audio = np.pad(audio, ((0, size - len(audio)), (0, 0)))
    views = np.lib.stride_tricks.sliding_window_view(audio, size, axis=0)[::hop]
    batch_size = max(1, 1000000 // (size * audio.shape[1]))
    for start in range(0, len(views), batch_size):
        frames = views[start:start + batch_size]
        transformed = np.fft.rfft((frames - frames.mean(axis=-1, keepdims=True)) * window, axis=-1)
        power = (np.abs(transformed) ** 2).mean(axis=1) / (rate * np.sum(window ** 2))
        if size % 2: power[:, 1:] *= 2
        else: power[:, 1:-1] *= 2
        total += power.sum(axis=0); count += len(frames)
    return {'frequencyHz': frequencies.tolist(), 'meanPowerSpectralDensity': (total / count).tolist(),
            'windowSamples': size, 'hopSamples': hop, 'actualWindowSeconds': size / rate,
            'binSpacingHz': rate / size, 'windows': count, 'shortClipPadded': padded}


def available_memory():
    if os.name == 'nt':
        try:
            import ctypes
            class Status(ctypes.Structure):
                _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [(name, ctypes.c_ulonglong) for name in ('totalPhysical', 'availablePhysical', 'totalPage', 'availablePage', 'totalVirtual', 'availableVirtual', 'availableExtended')]
            value = Status(); value.length = ctypes.sizeof(value)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value)): return value.availablePhysical
        except (AttributeError, OSError): pass
    try:
        return os.sysconf('SC_AVPHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')
    except (ValueError, AttributeError, OSError): return None


def plan(info, rates):
    if info.format not in ('WAV', 'WAVEX', 'RF64') or info.frames < 1 or not 1 <= info.channels <= 64:
        raise ValueError('Select a nonempty WAV with 1–64 channels.')
    if not rates or any(type(rate) is not int or not 8000 <= rate <= 384000 for rate in rates):
        raise ValueError('Target sample rates must be integers from 8000 to 384000.')
    rates = list(dict.fromkeys([info.samplerate, *rates]))
    for rate in rates: filter_parameters(info.samplerate, rate)
    disk = sum(math.ceil(info.frames * rate / info.samplerate) * info.channels * 4 for rate in rates) + 30 * 1024 * 1024
    memory = math.ceil(info.frames * info.channels * 8 * (3 + 3 * max(rates) / info.samplerate)) + 128 * 1024 * 1024
    return rates, disk, memory


def compare(path, output, rates, *, dry_run=False):
    path, output = Path(path), Path(output).resolve()
    if output.exists(): raise ValueError('Output exists. Choose a new directory; existing experiments are never replaced.')
    info = sf.info(path)
    rates, disk, memory = plan(info, rates)
    print(f'Source {info.samplerate} Hz; {info.duration:.2f}s; {info.channels} channel(s).', flush=True)
    print(f'Estimated derived-file disk space: {disk / 1024**3:.2f} GiB; working RAM budget: {memory / 1024**3:.2f} GiB.', flush=True)
    if dry_run:
        print('Preview only: no conversions, source changes or output files.'); return None
    memory_available = available_memory()
    if memory_available is not None and memory > memory_available * .7:
        raise ValueError('Insufficient available RAM for this prototype. Close other applications or use a shorter explicitly derived test excerpt.')
    output.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(output.parent).free < disk:
        raise ValueError('Insufficient disk space for separate derived WAVs and reports.')
    original_hash = sha256(path)
    source, source_rate = sf.read(path, dtype='float64', always_2d=True)
    if source_rate != info.samplerate or source.shape != (info.frames, info.channels):
        raise ValueError('Source properties changed while loading; refusing comparison.')
    original_levels = levels(source)
    source_spectrum = spectrum(source, source_rate)
    staged = Path(tempfile.mkdtemp(prefix='.rate-comparison-', dir=output.parent))
    results = []
    try:
        for rate in rates:
            print(f'Converting and comparing {rate} samples/second...', flush=True)
            derived = staged / f'derived-{rate}Hz.wav'
            converted = convert(source, source_rate, rate)
            sf.write(derived, converted, rate, subtype='FLOAT')
            del converted; gc.collect()
            stored, actual_rate = sf.read(derived, dtype='float64', always_2d=True)
            if actual_rate != rate or len(stored) != math.ceil(len(source) * rate / source_rate):
                raise ValueError('Derived file rate or sample count failed verification.')
            stored_levels = levels(stored)
            restored = convert(stored, rate, source_rate)
            whole = error_metrics(source, restored)
            margin = round(source_rate * .1)
            interior = error_metrics(source[margin:-margin], restored[margin:len(source) - margin]) if len(source) > 2 * margin else None
            converted_spectrum = spectrum(stored, rate)
            f = np.asarray(source_spectrum['frequencyHz']); power = np.asarray(source_spectrum['meanPowerSpectralDensity'])
            total = float(power.sum())
            removed_fraction = float(power[f >= rate / 2].sum() / total) if total > 0 else None
            divisor = math.gcd(source_rate, rate)
            result = {'targetRateHz': rate, 'actualStoredRateHz': actual_rate,
                      'filter': filter_parameters(source_rate, rate),
                      'conversion': 'identity-control' if rate == source_rate else 'software-resampled',
                      'up': rate // divisor, 'down': source_rate // divisor,
                      'file': derived.name, 'sha256': sha256(derived), 'subtype': 'FLOAT', 'bitsPerSample': 32,
                      'frames': len(stored), 'durationSeconds': len(stored) / rate,
                      'durationDifferenceMs': (len(stored) / rate - len(source) / source_rate) * 1000,
                      'levels': stored_levels, 'roundTripWhole': whole, 'roundTripInterior': interior,
                      'sourcePowerAtOrAboveTargetNyquistFractionEstimate': removed_fraction,
                      'nyquistHz': rate / 2, 'newCapturedFrequencyInformation': False,
                      'spectrum': converted_spectrum}
            results.append(result)
            del stored, restored; gc.collect()
        if sha256(path) != original_hash: raise ValueError('Original changed during comparison; refusing to publish results.')
        report = {'schema': 'AUEVO-SampleRateComparison/v0.1', 'experimentType': 'software-resampling-not-native-capture',
                  'source': {'filename': path.name, 'sha256': original_hash, 'sampleRateHz': source_rate,
                             'subtype': info.subtype, 'channels': info.channels, 'frames': info.frames,
                             'durationSeconds': info.duration, 'unchangedAfterComparison': True, 'levels': original_levels},
                  'method': {'toolVersion': '0.1.0', 'buildHash': sha256(__file__), 'python': platform.python_version(),
                             'numpy': np.__version__, 'scipy': scipy.__version__, 'soundfile': sf.__version__,
                             'libsndfile': sf.__libsndfile_version__, 'resampler': 'scipy.signal.resample_poly',
                             'window': 'Kaiser, beta derived by scipy.signal.kaiserord', 'padding': 'constant zero',
                             'filterDesign': {'attenuationDesignDb': 100, 'normalizedTransitionWidth': '.1/max(up,down)',
                                              'normalizedCutoff': '.95/max(up,down)', 'oddTapCount': 'kaiserord result rounded up to odd',
                                              'nominalPassbandUpperHz': '.90*min(sourceRate,targetRate)/2',
                                              'nominalStopbandLowerHz': 'min(sourceRate,targetRate)/2',
                                              'note': 'Design targets, not measured capture quality; near-Nyquist content is attenuated.'},
                             'normalization': 'none', 'storedSubtype': 'FLOAT (32-bit)',
                             'roundTrip': 'Read saved derived WAV, resample to original rate, compare original-length overlap without gain/time fitting; includes stored float32 quantization.',
                             'interiorExclusionSecondsEachEnd': .1,
                             'spectrum': 'One-sided channel-power-mean PSD; symmetric Hann ~250ms, 50% overlap, frame DC removal. Frequency bins ~4Hz; not a frequency-accuracy claim.'},
                  'sourceSpectrum': source_spectrum, 'conditions': results,
                  'limitations': ['Resampling does not recover uncaptured frequencies or test native ADC capture.',
                                  'Rates below the original can remove frequencies; error is not a universal quality ranking.',
                                  'The specified filter attenuates near the lower Nyquist even during upsampling; inspect nominal passband and stopband, not just target rate.',
                                  'Round-trip error includes both forward/reverse filters, edge behavior and float32 storage.',
                                  'Derived waveforms are start-aligned by the resampler; duration differs by sample-count rounding.',
                                  'No new pitch, speed, mastering, emotion, 369 significance or physiological claim.',
                                  'This experiment does not establish actual DAC playback rate; a player/driver may resample again.',
                                  'Original capture chain and rights remain unknown.']}
        (staged / 'comparison.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        render_report(report, staged)
        output.mkdir()
        try:
            for item in staged.iterdir(): shutil.move(str(item), output / item.name)
        except OSError:
            shutil.rmtree(output); raise
        print(f'Completed. Open {output / "comparison.html"}', flush=True)
        return report
    finally:
        shutil.rmtree(staged, ignore_errors=True)


def render_report(report, folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axis = plt.subplots(figsize=(13, 6))
    for condition in report['conditions']:
        data = condition['spectrum']
        axis.plot(data['frequencyHz'], 10 * np.log10(np.maximum(data['meanPowerSpectralDensity'], 1e-20)), label=f"{condition['targetRateHz']} Hz", linewidth=.8)
    axis.set(xlabel='Frequency (Hz)', ylabel='PSD (dB relative to sample unit²/Hz)', title='Derived-file spectra — software resampling, not native capture')
    axis.legend(ncol=2); axis.grid(alpha=.2); fig.tight_layout(); fig.savefig(folder / 'spectra.png'); plt.close(fig)
    rows = []
    for item in report['conditions']:
        rmse = item['roundTripWhole']['rmse']; snr = item['roundTripWhole']['snrDb']
        rows.append(f'<tr><td>{item["targetRateHz"]}</td><td>{item["nyquistHz"]:g}</td><td>{item["conversion"]}</td><td>{item["durationDifferenceMs"]:.6f}</td><td>{rmse:.6g}</td><td>{snr:.2f}</td><td><a href="{item["file"]}">Derived WAV</a></td></tr>' if snr is not None else f'<tr><td>{item["targetRateHz"]}</td><td>{item["nyquistHz"]:g}</td><td>{item["conversion"]}</td><td>{item["durationDifferenceMs"]:.6f}</td><td>{rmse:.6g}</td><td>{item["roundTripWhole"]["snrStatus"]}</td><td><a href="{item["file"]}">Derived WAV</a></td></tr>')
    name = html.escape(report['source']['filename'])
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Sample-rate comparison</title>
<style>body{{font:16px system-ui;max-width:1300px;margin:30px auto;padding:20px;line-height:1.5}}table{{border-collapse:collapse;width:100%}}td,th{{padding:8px;border:1px solid #aaa;text-align:left}}img{{max-width:100%}}.scroll{{overflow:auto}}</style>
<h1>Sample-rate comparison: {name}</h1><p><strong>Software resampling experiment — not native capture.</strong> No original audio is changed or uploaded. No newly captured frequency information is produced.</p>
<p>Original: {report['source']['sampleRateHz']} samples/second, {report['source']['durationSeconds']:.3f} seconds, {report['source']['channels']} channel(s). SHA-256: {report['source']['sha256']}</p>
<div class="scroll"><table><thead><tr><th>Rate (samples/s)</th><th>Nyquist (Hz)</th><th>Condition</th><th>Duration difference (ms)</th><th>Round-trip RMSE</th><th>Round-trip SNR (dB)</th><th>File</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p>RMSE measures sample differences; it is not a listening-quality score. Exact-match SNR is reported as a label, not a fabricated finite number. Downsampling may deliberately remove high-frequency content. Edge-inclusive and interior metrics are separately recorded in JSON.</p>
<img src="spectra.png" alt="Spectra of derived files; complete numeric data in comparison JSON"><p><a href="comparison.json">Full measurements, hashes, settings and limitations</a></p>
<h2>Limits</h2><ul>{''.join('<li>'+html.escape(item)+'</li>' for item in report['limitations'])}</ul><p>Conventional and 369-related rates are comparison conditions. No advantage is presumed. Keep all files with this report.</p></html>'''
    (folder / 'comparison.html').write_text(page, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audio', nargs='?', type=Path)
    parser.add_argument('--output', type=Path, default=Path('runtime/rate-comparison-001'))
    parser.add_argument('--rates', nargs='+', type=int, default=RATES)
    parser.add_argument('--dry-run', action='store_true', help='Show estimated disk/RAM requirements without converting')
    args = parser.parse_args()
    if args.audio is None:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk(); root.withdraw()
            try: selected = filedialog.askopenfilename(title='Select original WAV for sample-rate comparison', filetypes=[('WAV audio', '*.wav')])
            finally: root.destroy()
        except Exception as error: parser.exit(1, f'File picker unavailable. Supply the quoted WAV path instead: {error}\n')
        if not selected: print('Cancelled; nothing changed.'); return
        args.audio = Path(selected)
    try:
        compare(args.audio, args.output, args.rates, dry_run=args.dry_run)
    except KeyboardInterrupt:
        parser.exit(1, 'Comparison cancelled; original unchanged.\n')
    except (OSError, ValueError, RuntimeError, MemoryError) as error:
        parser.exit(1, f'Comparison failed: {error}\n')


if __name__ == '__main__': main()
