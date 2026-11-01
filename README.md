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
