# Aujoule / AUEVO

The project turns intensity, focus, and an initial into Compiler 2 state,
then combines that state with activity and complexity to drive the EvoSpace orb.
No API keys, database, or administrator access are needed.

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
