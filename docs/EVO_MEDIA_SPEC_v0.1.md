# EVO_MEDIA_SPEC_v0.1

Status: DRAFT for founder review. Date: 1 November 2026.
Scope: local browser prototype specification; requirements are not implemented
unless explicitly identified below. Companion:
[Third Compiler v0.1](THIRD_COMPILER_SPEC_v0.1.md).
Source authority and limitations: [project status](PROJECT_STATUS.md).

## 1. Product boundary and current position

Evo Media is the media-expression, recording and playback surface for permitted
AUEVO state. It should connect original media, technical measurements, compiled
state, visual/spatial behavior and portable artifacts while preserving lineage.
It is not an emotion detector, diagnostic system or proof of a person's identity.
The proposed Experiential Master is a linked, versioned record family, not a claim
that an original source is currently preserved by the visualizer.

Current verified behavior: live rendering; microphone-responsive parameters;
recording video with audio; separate video and `AuEvo-Recording/v1` JSON downloads;
a sampled session timeline with summary and correct filename. A user recording
was inspected for matching file, duration, dimensions, audio/video and changing
telemetry. The four-mode system, preview/discard/review, playback controls,
canonical-state adapter, source hashing and complete accessibility are not yet
implemented. Export currently happens automatically on stop, which does not meet
the proposed review-before-export flow.

No NFT, token minting, blockchain integration or NFT-style export requirement.
The historical design review's NFT artifact view is superseded by current user
direction. Fixed identity can exist in a labeled identity record if needed; do not
insert it into a microphone measurement field or silently restore removed labels.

## 2. User flow and modes

Start locally without microphone access. Display the chosen mode, loaded state
status/version, source status and a short notice explaining local processing,
recording, export and retention. Do not request the microphone until Live Audio is
selected and the user activates it. No automatic cloud upload.

| Mode | Input and experience | Controls and boundary |
| --- | --- | --- |
| Ambient Mode | Deliberately configured ambient scene; no microphone required. If a valid compiled baseline exists, label its source; otherwise label the scene Ambient/uncompiled. | Start/pause visuals, reduced motion, contrast, text status; never claim ambient fallback is a loaded compiled state. |
| Live Audio Mode | Valid baseline plus temporary microphone telemetry via bounded RenderProfile modulation. | Enable/disable mic, device/status, start/stop recording, visible recording indicator; silence and mic-off restore baseline without mutating it. |
| State Playback Mode | Validated Compiler 3 state package and, for time-based playback, a versioned timestamped directive sequence. A single state is a static baseline, not an invented timeline. | Load, play/pause, seek, restart, time display, selectable playback rate where supported. No microphone access unless user explicitly switches mode. |
| Recorded Session Mode | Locally selected recording and optional matching session metadata. Video plays its recorded frames/audio; telemetry can show a synchronized overlay. | Play/pause, scrub, elapsed/duration, volume/mute, captions/text panel, metadata review, unload. Missing metadata allows ordinary playback with an explicit unlinked status. |

A first local vertical slice can implement state loading and recorded playback
without requiring any account, enterprise service, hardware or AI model.
Switching modes while recording asks the user to stop and preview or remain in
Live Audio; it cannot silently discard a recording or leave the microphone on.

## 3. Adapter and render contract

Accept only supported, validated state package versions through a dedicated
adapter. Verify hashes and referenced RenderProfile, schema/ranges, permission
scope and lineage before enabling controlled-state recording/export. Treat
canonical state as read-only. Legacy v3 Orb JSON may load only as explicitly
labeled legacy/unverified state; it cannot satisfy the full provenance gate.
Invalid data keeps the previous valid state and shows a named error.

Maintain two stores: immutable compiled baseline and ephemeral telemetry/render
response. `rendered(channel)=clamp(baseline+boundedModulation,0,1)` for normalized
channels; hue is circular. Record profile/version/envelope and experimental
mapping status. Restore baseline on mic-off and settle toward it in silence.
Provide an explicit ambient mode if no valid state exists. Do not export a
controlled Compiler 3 artifact without its canonical-state reference; a standalone
recording can be separately labeled unlinked with no false canonical claim.

State timeline playback uses recorded directives or pinned deterministic
transforms; it does not recompute from a newly live microphone. Seeking restores
the applicable state and clears stale modulation. Media playback uses the media
element's currentTime as the overlay clock; pause/seek/rate changes keep it aligned.
For sparse telemetry show gaps as unavailable rather than fabricated samples.
A telemetry timeline alone cannot reproduce the exact original shader frames;
recorded video is the preserved rendered artifact.

## 4. Audio measurements, transformations and research

Separate measured features (with method/settings/units) from AUEVO-defined mapping
results. Current byte FFT magnitudes are smoothed, dB-scaled browser output; their
sum is not calibrated energy. Current RMS is a normalized browser-stream level.
Visual hue and audioResponseFactor are derived display values. Digital-root 3/6/9
behavior is a defined experimental symbolic transformation, not evidence of a
hidden human state. Constant 369 is AUEVO_DEFINED, not measured resonance.

Future RenderSessionRecord must include actual AudioContext rate, applied track
settings (echo cancellation, noise suppression, automatic gain control where
exposed), requested constraints, unavailable settings explicitly marked, analyser
FFT size, smoothing, dB bounds, feature method version, sampling cadence,
RenderProfile, engine version and visualizer build hash. Do not assume requested
constraints were applied. Keep default browser-friendly microphone behavior
separate from a deliberate measurement experiment.

For founder-music Prototype 001, preserve the designated original bytes/hash,
read codec/sample rate/channels/duration, establish source rights, and create
separate derived analysis copies. Do not relabel a test session as that original.
The proposed 66,666/99,999 sample rates, ultrasonic effects, envelope values,
perceptual meaning and physical Sphere/Cylinder devices remain hypotheses.
Resampling does not recover uncaptured frequencies. The current browser path
cannot establish a native unconventional sample-rate experiment.

## 5. Recording, review, discard and export

Proposed lifecycle:

`idle → recording → stopping → preview → export OR discard → idle`.

Permission/error transitions are explicit. Allow only one active recording and
freeze that session's record before asynchronous export. A second session must
not reuse the first one's chunks, measurements or metadata. Disable conflicting
controls while stopping/exporting and expose progress through text status.

- **Start:** explicit action, live audio/video track check, MIME capability check,
  immutable session ID/time, baseline/profile references and actual capture settings.
- **Record:** visible elapsed time and recording indicator; bounded-cadence telemetry
  with monotonic elapsed timestamps; capture gaps, interruptions and resolution changes.
- **Stop:** finalize bytes/session duration, snapshot records, stop sampling, then
  preview locally. No automatic download or upload in the proposed reviewed flow.
- **Preview:** ordinary video playback with synchronized metadata panel, session
  summary, gaps/limitations, state linkage and rights/retention choices.
- **Discard:** remove in-memory chunks, session metadata and object URLs without
  export or a new archive record. Do not delete prior source, compiled state or
  previously saved artifacts. Release capture resources when leaving the mode.
- **Download:** explicit direct video download and JSON companion; optional ZIP only
  if supported. Missing JSZip leaves direct downloads available, not a broken flow.
- **Unload:** revoke URLs and release tracks/resources; disclose that previously
  downloaded files must be removed by the user outside the app.

Record actual MediaRecorder MIME type; use a matching extension. Do not report
WebM (container) as an audio codec. Record codecs only when actually known.
Measure duration rather than claiming the nominal 30 fps is a measured frame
rate. Record actual capture dimensions and requested frame rate separately;
variable sizing/frame timing must be disclosed. Handle multiple-download blocking
with individual accessible download controls and guidance, not silent success.

## 6. Session and artifact metadata

Existing `AuEvo-Recording/v1` exports a per-session timeline and is a compatibility
format. It does not yet contain the full canonical-state/provenance contract.
Do not silently change its meaning; add a major-version adapter for future records.

Proposed separate records:

| Record | Required fields |
| --- | --- |
| RenderSessionRecord | Envelope/version, session ID and UTC start, monotonic duration, canonicalStateId/hash or explicitly unlinked status, RenderProfile ID/hash, engine/build versions, telemetry/capture settings, sampled timeline and summary, interruption/gap flags, permissions/retention references |
| ArtifactManifest | Artifact/session/source/state references, actual filename and MIME type, SHA-256 of final video bytes, verified duration/dimensions as available, rights/consent, local/private release status, session record hash and exporter version |
| Identity record (optional) | Explicit creator/entity/lineage labels with origin/review status; kept separate from measured features |

Metadata is derived from frozen session/artifact records rather than DOM text or
whatever the live microphone does during export. Timeline entries include elapsed
milliseconds, microphone RMS, derived hue/audioResponseFactor and symbolic root,
with per-field evidence classes/units and transform references. Summary is based
on actual samples: count, average/peak level and final captured sample. State
whether averages are sample-weighted; use documented duration weighting if
reporting a time average. No samples means unavailable/null, not a fabricated zero.

Hash scope: video digest covers exact exported bytes; session hash covers a
canonical serialized snapshot excluding its own digest. Artifact manifest links
both without a self-hash cycle. Verify actual downloaded filename association and
reject mismatched links. Session/asset IDs do not by themselves prove authorship,
ownership, consent, scientific validity or permanent authenticity.

## 7. Permissions, privacy and errors

Microphone access, recording, persistence and sharing are distinct user actions.
Local processing by default, no cloud upload or model training. Clearly describe
what is measured and what is stored/exported. Allow microphone disable at any
time; stop tracks and recording safely. Temporary context must not become
persistent memory implicitly. Do not solicit employer/client restricted material.

| Condition | Required behavior |
| --- | --- |
| Microphone denied/unavailable | Explain in text, keep ambient scene usable, offer user-initiated retry; no automatic repeated permission prompts |
| AudioContext suspended/device interrupted | Display status; resume only through appropriate user action; flag interruption/gap in the session |
| MediaRecorder/MIME unsupported | Keep non-recording experience usable; disable record with explanation; no empty export |
| Invalid/missing state | Keep previous valid state; label ambient/legacy fallback, show named issue; no false compiled-state badge |
| No canonical reference | Controlled package export blocked; explicitly unlinked standalone recording remains distinct |
| Missing JSZip | Direct video/JSON downloads remain available |
| Interrupted recording/export failure | Preserve recoverable preview data, display error, allow retry/discard; never announce success before bytes exist |
| Invalid playback media or mismatched metadata | Keep selected source unchanged, report mismatch; permit explicitly unlinked playback only |
| Retention/export not permitted | Block operation and explain applicable choice; no silent persistence |

Prohibited inference includes emotion, internal thought, identity, disability,
medical conditions, protected characteristics and honesty. Text describing visual
features must not be presented as a psychological or diagnostic assessment.

## 8. Accessibility

All modes require keyboard-operable labeled controls, visible focus, logical tab
order, escape/cancel where appropriate, no keyboard traps, and screen-reader text
for mode, state, microphone, recording, loading and error status. Avoid announcing
every telemetry frame; provide a restrained live region and a reviewable text panel.

Honor prefers-reduced-motion and provide an override. Reduced motion materially
reduces/disables rotation, displacement, star movement and camera drift, not just
one CSS transition. High contrast must affect actual controls/text; distinguish
recording/permission/state status with text/icons rather than color alone. Support
adjustable text and adequate target sizes.

Allow user-supplied captions/transcripts for recorded sessions and accessible
text alternatives describing controls and observable audio/visual features.
Captions are not generated by the current code; do not claim microphone telemetry
transcribes speech. Missing captions are explicitly labeled. Any future automatic
transcription requires separate consent and accuracy review. Support mute/volume,
visual alternatives to audio cues, pause and user-controlled pacing.

## 9. Acceptance tests and completion gates

These tests are proposed unless explicitly covered by existing tests in the
[status record](PROJECT_STATUS.md).

| Test | Passing behavior |
| --- | --- |
| Ambient first load | No permission request, stable scene, explicit uncompiled/compiled label |
| Permission denial | Text explanation and ambient controls remain usable; no state loss |
| Live audio | Synthetic silence/tone/level changes alter bounded directives without human inference; mic-off restores baseline; canonical object/hash unchanged |
| State package | Valid fixture loads; invalid schema/hash/range rejected; last valid state unchanged |
| State playback | Play/pause/seek/restart yield expected timestamped directives without enabling microphone |
| Recorded playback | Media with matching metadata plays; scrub/rate changes align telemetry; gaps shown unavailable |
| Preview/export | Stop opens preview and downloads nothing; review then explicit download yields playable video + matching metadata and hashes |
| Discard | No new downloads/persistence, resources released, original source and prior state unchanged |
| Isolation | Consecutive sessions have independent IDs/chunks/timelines; rapid repeat clicks cannot mix exports |
| Capture failure | Unsupported recorder, denied mic, ended track and export failure have distinct usable recovery paths |
| Metadata | Actual filename/MIME, valid sample statistics, compiler/prototype/profile versions, state linkage and permissions recorded; no NFT file |
| Reduced motion | Observable reduction in all motion sources; settings and keyboard controls persist as explicitly permitted |
| Accessibility | Keyboard-only operation, visible focus, contrast check, non-color labels, screen-reader status and captions/text alternative path manually verified |
| Local independence | Demonstration works without Power Platform, cloud storage or an AI provider |
| Reproduction | Same pinned canonical inputs/profile yield same state hash; no promise that live capture or GPU frames are bit-identical |

Existing browser tests cover synthetic-audio recording and changing metadata only;
they do not satisfy the full mode, permission, governance or accessibility matrix.

## 10. Implementation slices

1. Implement the documented Compiler 3 input contract/fixtures and read-only adapter.
2. Separate renderer, audio analyser, recorder, session store, adapter and controls;
   retain the tested legacy path while migrating with explicit status labels.
3. Add Ambient/Live modes, mic-off cleanup, bounded baseline modulation and notices.
4. Add preview/discard/review plus direct downloads and controlled artifact linkage.
5. Add Recorded Session playback, then state timeline playback and synchronization.
6. Add accessibility and privacy checks in each slice; finish the full acceptance
   matrix before claiming a controlled accessible four-mode prototype.

Keep Power Platform paused. Full historical reconciliation and designated founder
source ingestion remain separate prerequisites for an Experiential Master demo;
working live recording is not completion of that broader package.
