# Aujoule / AUEVO

The project turns intensity, focus, and an initial into Compiler 2 state,
then combines that state with activity and complexity to drive the EvoSpace orb.
No API keys, database, or administrator access are needed.

## Architecture status and next-stage specifications

The existing work repaired and stabilized parts of the AUEVO compiler foundation.
It did not complete the full architectural scope of Compiler 1, Compiler 2, or
Compiler 3. The current State Compiler produces Orb-oriented settings; the full
Third Compiler still needs traceable inputs, lineage/provenance, permissions,
versioned outputs, change records, experience directives, validation and tests.
Evo Media supports live audio-reactive visuals, recording and session metadata;
four-mode playback and complete player controls remain unfinished.

- [Current implementation and source evidence](docs/PROJECT_STATUS.md)
- [Third Compiler specification v0.1 — DRAFT](docs/THIRD_COMPILER_SPEC_v0.1.md)
- [Evo Media specification v0.1 — DRAFT](docs/EVO_MEDIA_SPEC_v0.1.md)
- [Decision and document register](docs/DECISIONS_AND_DOCUMENT_REGISTER.md)

Master overview v1.2 remains a draft, Power Platform remains paused, and NFT
export is obsolete. Proposed logic is not a final AUEVO equation. These new
specifications describe future work, not implemented capabilities.

## Linux / cloud / macOS with GCC

Requires Python 3 and GCC/G++ supporting C++20 (or set CC and CXX to Clang).
From the repository folder:

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests -v
python3 scripts/run.py
```

Enter intensity (1–10), focus (0–1), an alphabetic initial, activity (0–1),
and complexity (0–1) when prompted. This starts the local static server on
port 8000. On your own PC, open your browser to localhost on that port.
Use `--port 8001` if 8000 is occupied. Stop with Ctrl+C, then run again to
update the inputs. Refresh the browser after restarting.

The runner keeps generated state and copied web files in ignored `runtime/`;
it does not overwrite the tracked baseline JSON. Delete runtime/compiler2_state.txt
only if you want to reset the state version. Restart the server in each new cloud
task; processes do not survive environment publication.

## Windows / Visual Studio

Install Python 3 and Visual Studio's **Desktop development with C++** workload.
The existing projects target toolset v145 and Windows SDK 10.0; install those
components or retarget to your installed toolset through Visual Studio.
Open and build these solutions with **Debug | x64**:

- `EvoRoot/AU/AU.slnx`
- `EvoRoot/AUEVO_StateCompiler/AUEVO_StateCompiler/AUEVO_StateCompiler.slnx`

Copy the newly built `AU.exe` and `AUEVO_StateCompiler.exe` into a `build`
folder at the repository root, naming the copies `second-compiler.exe` and
`state-compiler.exe`. Then run `py scripts/run.py` from the repository folder.
Alternatively, GCC/MinGW users can run `py scripts/build.py` first.
The Visual Studio build itself has not been tested in the Linux cloud workspace.

## Compiler command line

Both programs read interactive values from standard input and return a nonzero
exit code on invalid input or file errors. Paths are relative to the current
working directory unless absolute paths are supplied:

```text
second-compiler [state-file]
state-compiler [input-state] [output-json]
```

Defaults are `compiler2_state.txt` and `evo_state.json` in the current directory.
Run the second compiler first. The state compiler now requires valid preceding
state instead of silently producing an orb with zero intensity/focus.

## Browser requirements and checks

EvoSpace loads Three.js r128 over HTTPS from `cdnjs.cloudflare.com`; allow that
host in cloud network settings. WebGL is required. Serve the page over HTTP rather
than opening the HTML as a file, so it can fetch the JSON state.

On your PC use localhost, or HTTPS for a deployed site, to enable microphone
access. Click **ENGAGE MIRROR CORE**, grant microphone access, speak, and check
that the orb reacts. Click **RECORD**, wait, then click **STOP RECORDING** to
save a video and one recording metadata JSON file. Allow multiple downloads if the browser asks.
A cloud browser check verified rendering and recording using simulated audio;
your physical microphone and device permissions still need this manual check.
The optional JSZip integration is absent, so recordings download as separate
files rather than a zip. Nothing here deploys a public website.

Recording metadata uses schema `AuEvo-Recording/v1` and references the exact
downloaded video filename. It samples RMS microphone level (0–1), visual hue,
audio-driven visual resonance, and the digital root of FFT magnitudes about every
100 ms while recording. Timestamps are elapsed milliseconds; background tabs may
produce gaps. Average and peak levels summarize the collected samples. Every new
recording starts a fresh timeline. These values describe the audio-driven visuals,
not measured emotion, calibrated loudness, or an asserted 432 Hz frequency.
There is no NFT metadata export. JSON is a snapshot of the completed recording.
Run `node --test tests/test_recording_metadata.cjs` for the telemetry tests.
Optional browser integration test: with Playwright and its Chromium installed,
start the web server and run `node tests/test_recording_browser.cjs`.
It supplies controlled synthetic audio and checks changing levels, session
isolation, and two matching downloads per recording. `EVOSPACE_URL` selects
another local server; `CHROMIUM_PATH` selects an existing Chromium executable.
In restricted cloud tests, `THREE_JS_PATH` can point to the exact CDN JavaScript
downloaded with TLS verification through the configured proxy.

After pulling web changes on Windows, stop the server with Ctrl+C, run
`py scripts\run.py` again to refresh the runtime web files, and reload the
browser with Ctrl+F5. No C++ rebuild is needed for web-only changes.

Regression tests exercise the compiler handoff, computed orb values, version
increments, Windows line endings, malformed inputs, and file errors. The repository
also contains old tracked Visual Studio caches and binaries; these are preserved,
but new generated files are ignored. Rebuild executables instead of relying on
those old binaries.

## Legacy lineage adapter (first Compiler 3 preparation step)

`py scripts/adapt_lineage.py --input runtime/compiler2_state.txt --activity 0.7 --complexity 0.4 --output runtime/lineage-001.json --allow-persist`

Run this from the repository folder after the second compiler has produced the
input file. On Linux use `python3` in place of `py`. Use the actual activity and
complexity you chose for that session. Choose a new output name each time.
`--allow-persist` explicitly requests this local snapshot; it grants no source
rights, sharing, cloud upload or recording permission. The output directory must
already exist and support hard links (for example local NTFS); no existing output
is replaced. Windows execution has not yet been independently verified.

The adapter preserves the exact source bytes as base64 plus SHA-256, all seven
parsed legacy values, configured inputs and a deterministic content identifier.
Run time/ID are separate from the content hash. This version uses a named Python
sorted-JSON serialization, not RFC 8785 canonical JSON. Changing the adapter build
changes the content identity; replay comparisons require the same implementation.
Historical lineage, founder attribution, prior-state links and rights remain
explicitly unknown. Its `AUEVO-LegacyLineage/v0.1` output is **not** a completed
`Compiler2Lineage` contract, canonical state, correction/reconciliation engine,
or working player integration. It does not change the current startup command.

Synthetic adapter fixtures are in `tests/fixtures/lineage/`. Run
`python3 -m unittest discover -s tests -v` to exercise preservation, tampering,
replays, malformed/trailing records, changed inputs and exclusive local writes.

## Compiler 3 local package prototype

This is the next implementation slice, not completion of Compiler 3. It creates
`AUEVO-Compiler3Prototype/v0.1` with a linked legacy-derived state, input snapshot,
hashed member manifest, change report, explanation and baseline directives.
It preserves unknown lineage/rights and uses only the existing compatibility
formulas; there are no approved new canonical dimensions or player integration.

To demonstrate it with invented inputs (no C++ rebuild, microphone or network):

```bat
py scripts\demo_compiler3.py
```

The command creates a fresh ignored `runtime/compiler3-demo-*` folder with
baseline/changed packages and a demo report. It checks replay and rejects the
synthetic conflicting claims. Synthetic fixture permissions allow these local
files only; do not reuse them as consent for real source media.

For an already adapted local lineage record:

```bat
py scripts\compile_package.py --lineage runtime\lineage-001.json --permissions YOUR_LOCAL_PERMISSIONS.json --output runtime\package-001.json
```

Supply your own permission record using the exact schema shown in
`tests/fixtures/lineage/local-permissions.json`, including an explicit retention
choice. The command refuses sharing/cloud grants; they are unsupported in this
prototype. Compilation can run in memory without persistence through its Python
API, but the CLI needs `allowPersist: true` to save. Add `--prior` with a prior
package to preserve its state ID/hash and advance the generation. Existing outputs
are never replaced; an identical replay is an idempotent no-op. `--claims` accepts
an array of `{recordId, field, value}` assertions: any conflict with the preserved
input stops compilation. It does not implement approval of founder corrections,
merge policies or trusted evidence authentication. Hashes detect byte changes;
they do not prove authorship. The current sorted-JSON encoding is not JCS.

Run `python3 -m unittest discover -s tests -v` (or `py -m unittest discover -s tests -v`
on Windows) for the compiler, adapter and package tests. The prototype is tested
on Linux; Windows execution of these Python commands remains to be verified.

## View the saved prototype states

After pulling the latest changes, run from your repository folder on Windows:

```bat
py scripts\demo_compiler3.py --view
```

Leave the command window open and open `http://localhost:8001` on your own PC.
Use **Saved state** to switch from the baseline (generation 1) to the changed
state (generation 2). The Orb baseline changes from glow .8/coreIntensity .7 to
.5/.55. The screen identifies this as a prototype with incomplete lineage.
No C++ rebuild is needed. Stop with Ctrl+C; use `--port 8002` if needed.

This viewer verifies hashes and compatibility values before starting and serves
only web assets and display directives, not raw source/provenance files. It binds
to loopback and rejects foreign Host headers. It does not authenticate authorship
or provide a production security boundary. Microphone/recording are disabled in
this baseline-only mode because the current local compile policy does not grant
those operations. The ordinary `py scripts\run.py` live-audio workflow is separate.
This viewer supports configured timed state playback; recorded-video playback
and the complete four-mode player remain unfinished. Invalid loads retain the previously valid baseline.

For your own verified prototype packages:

```bat
py scripts\serve_package.py --package YOUR_PACKAGE.json --package ANOTHER_PACKAGE.json
```

Server startup refuses invalid packages; files are validated into memory at
startup, so restart to consume changed files. The optional Playwright browser
check `node tests/test_package_viewer_browser.cjs` expects the two demo packages
on port 8001 and uses the same CHROMIUM_PATH/THREE_JS_PATH/EVOSPACE_URL options
as the recording browser test.

## Timed state playback

In the package viewer, **Play states** starts the configured timeline and changes
to **Pause states** while playing. **Restart** returns to the first state and stays
paused. Drag **Position** (or focus it and use arrow/Home/End keys) to seek; seeking
pauses playback. Selecting a saved state also pauses and seeks to that state's
start. At the end, playback stops; Play starts again from the beginning.

The demo holds each package for five seconds in supplied order. This is an
explicitly configured demonstration, not timestamps reconstructed from source
media, microphone telemetry or compiler generation times. Transitions are steps,
not interpolation. Pause stops timeline advancement; the ambient Orb animation
continues. Package files and compiled states are not modified. Microphone and
recording stay disabled in this mode. No audio/video playback or baseline/live
modulation redesign is included.

Unit checks: `node --test tests/test_state_playback.cjs`. Optional browser checks:
`node tests/test_state_playback_browser.cjs` against the running two-state demo,
using the same browser-path and URL environment options described above.

## Recorded Session: open your saved video and metadata

After pulling changes, restart the viewer (`Ctrl+C`, then
`py scripts\demo_compiler3.py --view`) and refresh the browser with Ctrl+F5.
Open **Recorded Session — open saved files** at the top right.

1. Under **Open recording**, select the `.webm` video from Windows Downloads.
2. Optionally select its matching `_metadata.json` under **Open metadata**.
3. Use the video controls to play, pause, seek, change volume or mute.
4. The text below the video follows its playback position with recorded microphone
   level, hue, audio response and root. Sampling gaps show as unavailable.
5. Expand **Review metadata** to inspect the JSON. **Close recording** releases
   browser references and restores the previous state-viewer controls.

Video playback works without metadata. Supported metadata is
`AuEvo-Recording/v1`; older NFT/asset formats are not silently relabeled. Wrong
filenames, invalid ranges/timestamps and inconsistent summaries are rejected,
keeping the previously linked metadata. Association is by filename, with a
basic duration consistency check when available; this format has no video digest
and cannot authenticate the file or its creator. Captions are not generated.
Native browser controls handle playback rate where supported.

Files remain local browser object URLs: no upload, server write or persistent
browser storage. Loading a recording pauses the state timeline, stops any live
microphone/canvas capture and disables conflicting controls. An active recording
or export must finish first. The original source files are not deleted by Close;
previous downloads remain on your PC. Collapsing the panel does not stop video;
use Pause or Close. Full preview-before-export, discard, captions and reduced-motion
controls remain future work; this slice plays already saved recordings.

Checks: `node --test tests/test_recorded_session.cjs`. The optional
`tests/test_recorded_session_browser.cjs` takes `TEST_RECORDING` and
`TEST_RECORDING_METADATA` paths to a real matching export pair, plus the same
Chromium/server environment options as the other browser tests.

## Offline WAV analysis on Windows

This first research tool measures your original WAV at its existing rate. It does
not resample, change pitch, modify the original, apply the 369 formulas, or upload
any audio. Keep originals outside the repository and preserve them unchanged.

From Command Prompt in the repository folder, create an isolated environment:

```bat
py -m venv .venv-audio
.venv-audio\Scripts\python -m pip install -r requirements-audio.txt
.venv-audio\Scripts\python scripts\analyze_audio.py --output runtime\audio-report-001
```

Select your original WAV in the file dialog. If a dialog is unavailable, supply
the quoted WAV path after `analyze_audio.py` instead (Windows **Copy as path** is
useful). Cancelling the dialog changes nothing. Open `runtime\audio-report-001\report.html` in your browser. No server
or Visual Studio rebuild is needed. The output directory must be new; choose
`audio-report-002` for another run. The HTML report opens locally with no external
assets. Keep its accompanying image/JSON files together.

Outputs: report.html/report.md, measurements.json, waveform.png, levels.png,
spectrum.png and spectrogram.png. Measurements include format/subtype precision,
source hash, rate/channels/duration, per-channel RMS/sample peak/DC offset,
near-full-scale candidates, averaged power spectrum, named band powers,
centroid/bandwidth/85% rolloff/flatness timelines, silence fraction, onset candidates
and an **experimental** global pulse/tempo estimate. No meter, musical beat certainty,
true-peak, calibrated loudness, pitch, emotion or hidden state is claimed.

The audio is read in chunks; frame FFT batches are bounded. Original byte hash
is verified before/after analysis. Stereo spectra average channel power, avoiding
phase cancellation from mono mixing. Spectral frames use a Hann window with
per-frame DC removal; report methods specify FFT/hop, actual bin spacing and
software versions. Source-wide level measurements include every sample; a final
incomplete spectral frame is omitted except that a very short clip is explicitly
zero-padded. Display timelines/spectrograms sample at most about 2,000 windows;
aggregate PSD covers all full analysis frames. Long recordings can take time and
pulse analysis still uses an in-memory per-frame onset envelope.

Defaults: FFT=2048, hop=512, silence threshold=-60 dBFS. Change explicitly with
`--fft-size`, `--hop-size`, `--silence-db`; settings change the measurements and are
recorded. Bin spacing is not a claim of frequency accuracy. Near-full-scale counts
are possible clipping evidence, not proof. Silence is represented with null dBFS
instead of invalid infinite JSON values. Capture chain/rights/uncertainty remain
unknown unless independently documented. Up to 64 WAV channels are supported;
non-WAV inputs are rejected rather than silently converted.

Your proposed 66,666 / 66,369 / 36,369 / 63,369 / 99,369 / 93,369 / 96,369 rates
and conventional 44.1/48/96 kHz references are listed as **not executed** research
conditions. Native capture and software-resampling experiments are distinct next
steps. The original rate is inspected, never assumed. The recovered evoMetrics
formula remains a separate experimental transformation, not a measured result.

On Linux/macOS use `python3 -m venv .venv-audio`, then `.venv-audio/bin/python`
for the installation and analysis commands. Audio dependency ranges are in
requirements-audio.txt; exact versions/build/source hashes are in each report.
Test the audio suite with `.venv-audio\Scripts\python -m unittest discover -s tests -p test_audio_analysis.py -v`.
Without optional dependencies these audio cases are skipped, not counted as passed.

## Software sample-rate comparison experiment

Use the same `.venv-audio` environment from the inspection step; no new packages
or Visual Studio rebuild are needed. From the repository folder:

```bat
.venv-audio\Scripts\python scripts\compare_sample_rates.py --output runtime\rate-comparison-001
```

Select the **original WAV** in the file picker. The command prints resource
estimates, then works through the rates sequentially. For your roughly 342-second
mono recording, the default derived WAVs require about 1 GiB of disk space and a
working-RAM budget around 1.3 GiB. Actual free resources are checked; close other
large applications if necessary. This can take several minutes. Leave the command
window open. It never changes the original and verifies the source hash again
before publishing the results. Cancelling removes the staged conversion files.

Open `runtime\rate-comparison-001\comparison.html` after it finishes. Keep that
folder's WAVs, JSON and spectrum image together. Existing output is not replaced;
choose `rate-comparison-002` for a separate experiment. Outputs use 32-bit FLOAT
WAV; their actual rates, sample counts and hashes are verified after writing.
Do not commit original or derived media to GitHub; `runtime/` is ignored.

Defaults: original-rate identity control, 44,100, 48,000, 96,000, 66,666, 66,369,
36,369, 63,369, 99,369, 93,369 and 96,369 samples/second, with duplicate rates removed.
**36,369 is a downsampling condition** for a 44,100-rate source. These are software
conversion conditions, not native ADC measurements or assumed quality rankings.
The 369-related transformation logic is not applied in this experiment.

For a resource preview only, add `--dry-run` (select the WAV again). To test a
subset, add for example `--rates 36369 66369 99369`; the original-rate control is
always retained. A quoted WAV path can replace the file picker, as in the audio
inspection command.

Method: rational polyphase resampling with an explicitly designed Kaiser FIR.
The design targets 100 dB attenuation, passband up to about 90% of the lower
Nyquist, and stopband beginning at that Nyquist; exact tap count, beta, cutoff,
ratios and software versions are recorded. These are filter design targets, not
a claim of measured capture quality. Near-Nyquist content can be attenuated even
on upsampling; there is no new captured information. Extremely costly ratios
requiring more than 10,000,001 taps are rejected instead of silently using a
lower-quality filter. The identity control bypasses filtering but still uses the
same FLOAT output subtype; an original of higher precision may incur quantization.

Comparisons include duration rounding, per-channel sample peaks/RMS, common
~250 ms Hann PSD windows (about 4 Hz bins), and round-trip error after reading the
saved WAV and converting it back to the original rate. Error is start-aligned,
with no fitted gain/time shift or normalization. Whole-file and interior errors
(excluding 0.1 seconds at each edge when possible) are separate. SNR is an error
metric, not a listening score; an exact match has a label rather than a fabricated
finite dB value. A player or Windows driver may resample again during listening;
these reports do not establish the DAC's physical rate.

This prototype decodes the source into memory and processes one target at a time;
it is not a streaming resampler. The free-RAM/disk preflight is an estimate, not
a guarantee. JSON has raw spectral data and source/derived hashes. Tests cover
identity, duration and tone preservation, rejection above a lower Nyquist,
stereo, silence, actual saved headers/hashes, dry-run and overwrite refusal.

## Compare features on matching time windows

After pulling this increment, use the existing audio environment; no additional
packages, conversion rerun or Visual Studio rebuild are needed:

```bat
.venv-audio\Scripts\python scripts\compare_audio_features.py --output runtime\matched-features-001
```

First select the unchanged original WAV. Then select **comparison.json** inside
`runtime\rate-comparison-001` (not measurements.json from the earlier inspection).
Leave the derived WAVs beside that comparison file; their hashes and headers are
verified before use. The command reads small windows, so it does not need the
previous resampler's full-file RAM budget. It retains feature records in memory,
not complete decoded recordings, and supports at most 50,000 windows per condition.
Long runs can still take time and produce a sizeable full dataset.

Open `runtime\matched-features-001\features.html`. Upload **summary.json** for
review; features.json keeps the complete window data locally. The report compares
RMS, sample peak, common-band centroid/bandwidth/rolloff and band powers against
the original. JSON also has full-band values, spectral flatness, crest factor,
adjacent RMS changes and positive band-amplitude changes. These are defined
measurements, not a complete musical or transient interpretation.

Defaults are 250 ms physical windows with 125 ms hop. Start/end positions are
rounded to each file's nearest sample and recorded, not fitted by correlation.
The common upper limit is the lowest Nyquist across files, capped at 20 kHz.
Bands are bass 20–250 Hz, mid 250–4000 Hz and high 4000 Hz to that common limit.
This equalizes comparison bandwidth; full-band metrics remain separate. FFT-bin
placement and rounding still affect values. Use `--window-seconds` and
`--hop-seconds` for explicitly recorded alternatives. A final incomplete window
is excluded. Same-grid identity comparisons should be exact for the existing
32-bit-float source/control. No original/derived audio is rewritten.

### Optional evoMetrics experiment — off by default

The received JavaScript is preserved unchanged in
`docs/source_records/evo-metrics-received/`; its hash is recorded in output.
`scripts/evo_metrics_experiment.py` adapts only its defined formula, rounding,
carry/gate and shape behavior for validated inputs. This is **not** a completed
new canonical equation or a promoted production rule.

The new proposed input adapter is explicit: take RMS of the three common-band
powers, divide each by configured `bandRmsReference`, clip individually to 0–1,
then average to produce voiceEnergy. This is an experimental normalization, not
calibrated physical energy or proof of the historical input definition. Clipped
bands, audio contribution and session-count contribution are reported separately.

Focus is **not** inferred from sound or silently treated as camera brightness.
For an explicit trial, copy `experiments/evo-metrics-template.json` into your
ignored runtime folder. Choose its focus, session count, prior leftover and RMS
reference, then deliberately set enabled to true. Add `--evo-config` pointing to
that file. Template numbers are illustrative settings, not user consent or
founder-approved semantics. Without that option, symbolic computation stays off.

Every window is an **independent diagnostic evaluation** with the same configured
context; time windows do not become new identities or sessions, and carry/history
is not advanced. Root/gate differences can result from rounding thresholds, not
new physical resonance. The received core's monotonic-level comment is not a
working guarantee; the source remains archived, not silently repaired.
The template is `independent-windows-fixed-context` only; no camera, database,
cloud upload, identity inference or persistent evolution is enabled.

Tests: `.venv-audio\Scripts\python -m unittest discover -s tests -p test_matched_features.py -v`.
Optional command-line paths `--original` and `--comparison` replace the dialogs.
Existing output folders are refused; use a new suffix for a separate run.

## Matched-feature method 0.2: fractional FFT-bin boundaries

The first matched-feature reports used whole bins selected by center frequency.
A boundary bin near 4,000 Hz could switch entirely between mid and high bands
when the sample grid changed, producing a large apparent transfer of band power.
Version 0.2 replaces that step with fractional overlap of FFT-bin cells and
physical band intervals. Cells meet halfway between adjacent frequencies and
are clipped to 0..Nyquist. Each cell retains its original `PSD*df` mass, including
DC/Nyquist endpoints. Adjacent band partitions therefore conserve discrete power.
Common-band spectral moments/rolloff/flatness also use fractional upper-edge
weights. Centroid still uses bin centers and rolloff remains bin-quantized.

This is an explicit uniform-within-bin model, not a new high-resolution spectrum.
Finite windows, leakage, sample boundaries and genuine filtering changes remain.
Do not interpret remaining differences or optional root threshold crossings as
proof of a special frequency rate. The original received evoMetrics is unchanged;
symbolic output remains off unless explicitly configured.

Rerun only the feature analysis, using the **same original and comparison.json**:

```bat
.venv-audio\Scripts\python scripts\compare_audio_features.py --output runtime\matched-features-002
```

No conversion rerun, dependency install or Visual Studio rebuild is needed.
Keep matched-features-001 as the prior method's record. New reports identify
`AUEVO-MatchedAudioFeatures/v0.2`, method 0.2.0 and
`fractional-bin-cell-overlap/v1`; upload summary.json from the new folder for
comparison. Synthetic boundary tests cover 20, 250 and 4,000 Hz across multiple
sample grids; conservation tests cover even/odd FFT sizes and split bins. These
test the method, not native hardware capture or a promised audible improvement.

## Controlled evoMetrics fixed-focus trial

This diagnostic uses **corrected features**, not the original WAV, and does not
repeat measurement or conversion. The approved preset is
`experiments/evo-metrics-fixed-focus-trial.json`: focus=.5, sessionCount=0,
priorLeftover=1, bandRmsReference=.1, independent windows. The normalization
reference remains an experimental scale, not calibrated energy. The preset's
configured values are not claims about actual camera brightness or identity history.

```bat
.venv-audio\Scripts\python scripts\run_evo_trial.py
```

Select **features.json inside matched-features-002**. Its sibling summary.json
must be present. The tool verifies the full feature hash, corrected method,
window alignment and core-source reference. It recognizes the known LF/CRLF
conversion of the archived JavaScript instead of treating Windows line endings
as changed logic. Unknown core edits require explicit reconciliation.

Open `runtime\evo-trial-001\trial.html`. Outputs include trial-timeline.png,
trial-summary.json (small review file) and trial.json (all windows). The report
separates continuous audio/formula differences from root/gate/shape changes,
counts clipped normalization windows and minimum-session-number buckets, and
includes a zero-input control. Input/source hashes, configuration and producer
versions remain linked. Gate fractions count overlapping windows, not time
percentages or independent sessions. All roots can stay identical despite small
continuous changes; a floor/quantizer can hide input differences.

The original rules produce symbolic root 2 even for zero input with this preset;
that is not measured sound. Session count 0 makes the 369 contribution zero, so
this run does not test its influence at nonzero counts. No camera, microphone,
source audio, identity database or persistent history is accessed/advanced.
This is neither canonical Compiler 3 state nor an approved final equation.

Use `--features` and `--summary` for explicit file paths. For another run use a new
`--output runtime\evo-trial-002`; existing trial folders are not replaced.
Future parameter experiments can pass an explicit copied `--config` file, with
each change documented. Do not tune parameters merely to produce desired gates.
Tests are `test_evo_trial.py` in the optional audio test suite.

## evoMetrics sensitivity study — one factor at a time

This uses the same corrected features, without audio conversions, new packages,
recording, camera access or persistent history changes:

```bat
.venv-audio\Scripts\python scripts\run_evo_sensitivity.py
```

Select **features.json in matched-features-002**, with its sibling summary.json.
Open `runtime\evo-sensitivity-001\sensitivity.html` afterward; the small
`sensitivity-summary.json` contains all settings and per-rate comparisons.
Use a new `--output` folder for another run; previous outputs are not replaced.

The predeclared plan is `experiments/evo-sensitivity-study.json`. It keeps the
fixed-focus trial as baseline and changes exactly one configuration field:

- Band RMS reference: .025, .05, .2, .4 (baseline .1).
- Configured focus: 0, .25, .75, 1 (baseline .5).
- Session count: 1, 10, 100, 101 (baseline 0).

Prior leftover stays 1. Each window is independent. These are diagnostic values,
not a search for more gates or production recommendations. The study evaluates
13 configurations, each against the original and all existing rate conditions.
It separates changes caused by a configured parameter from differences between
sample rates under the **same** parameter. Optional `--features`, `--summary` and
`--plan` paths replace defaults/dialogs.

Metrics include root/gate/shape changes, floor occupancy, normalization clipping,
continuous voice changes and raw session-term share. Clipping here is in the
experimental input mapping, not the WAV. Zero total contribution gives an
undefined share, not 0%. A raw term's size is not its causal importance after
rounding/modulo. A hash of the ordered root/gate/shape sequence identifies equal
symbolic output across settings; it does not identify equal audio or continuous
formula values. Up to 50 changed-root windows per rate/setting retain threshold
margins and scaled deltas; total counts remain complete.

The existing formula caps its count variable at session 100. Before that cap,
scaling the count term by 100 nominally yields multiples of 369, divisible by 9.
Digital-root reduction can erase such increments; floor/rounding still matters.
Compare those measured outputs with the raw contribution report instead of
assuming a larger 369 term must cause proportionately larger symbolic change.
All preset choices, input hashes and method versions are recorded.

## Draft evolved audio state — preserve the continuous feature vector

The candidate model is documented in
[EVOLVED_AUDIO_STATE_MODEL_v0.1](docs/EVOLVED_AUDIO_STATE_MODEL_v0.1.md), with a
[review-only JSON Schema](schemas/audio-state-draft-v0.1.schema.json).
This is not a final canonical dimension set or a new production equation.

```bat
.venv-audio\Scripts\python scripts\build_audio_state.py
```

Select features.json inside matched-features-002 (keep summary.json beside it).
Open `runtime\audio-state-draft-001\state-review.html`. The exporter preserves
all original measurement windows and units, with source/method hashes. Any
symbolic overlay already attached to the feature file is separated and labeled
preserved/unverified, never substituted for measured values. Separate trial and
sensitivity reports are not automatically ingested. Rate conditions remain
alternative derivatives, not new sessions.

The output has no history commit, parent-state transition, renderer mapping or
new recording/upload/memory permission. It is a local review artifact; it does
not read the WAV, update the Orb or silently implement persistent carry. Those
contracts require explicit implementation and validation after reviewing the
model. `--features`, `--summary` and `--output` support command-line paths; use a
new output suffix for another export. No installation or Visual Studio rebuild.

Created time is outside the deterministic payload hash. Same inputs/build yield
the same content identity, while envelope byte hashes may differ across runs.
Hash encoding is explicitly Python sorted-JSON, not JCS or authorship proof.
Unknown fields/invalid observations fail instead of being silently discarded.
The optional JSON Schema review test uses jsonschema if installed; the exporter
itself needs only the existing audio environment and its built-in contract checks.
