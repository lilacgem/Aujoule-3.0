# AUEVO implementation and source status

Status: working implementation inventory, 1 November 2026. This is not a release
of the master architecture, approval of its drafts, or a completion certificate.

## Authoritative wording

The existing work repaired and stabilized parts of the AUEVO compiler foundation.
It did not complete the full architectural scope of Compiler 1, Compiler 2, or
Compiler 3. The present State Compiler produces Orb-oriented settings, but Third
Compiler completion requires traceable inputs, lineage and provenance,
permissions, versioned outputs, change records, experience directives, validation,
and tests. Evo Media currently supports live audio-reactive visuals, recording,
and session metadata; playback modes and complete player controls remain to be
implemented.

Evolution adds interpretation without erasing provenance. Preserve original
source, prior outputs, corrections, and failed attempts with their origin and
status distinguishable. A planned document title is not evidence of its contents
or existence.

## Inventory and limits

| Area | Verified implementation | Remaining architectural scope |
| --- | --- | --- |
| Compiler 1 | `EvoRoot/AU/logic.h` and `logic.c`: SymbolCode and deterministic symbolic calculations, with a legacy `rand()` branch | Full historical source inventory, seal payload, source-media ingestion, provenance, persistence, and historical defect verification. Foundation operational; architecture incomplete. |
| Compiler 2 | `SecondCompiler.cpp`: input validation, positional state-file persistence, version count and change indicators; calls the symbolic logic | Structured lineage equation inputs, source references and hashes, corrections, new evidence, versioned learning rules, immutable history. A counter plus an overwritten file is not preserved lineage. |
| State Compiler component | `main.cpp` + `state_compiler.cpp`: reads validated Compiler 2 values, accepts activity/complexity, computes five Orb channels and configured palette | Full Third Compiler orchestration and controlled package contract below. Console inputs are not retained as provenance records. |
| Evo Media | Three.js rendering, microphone analysis, recording, actual MIME type, sampled session telemetry and matching video filename | Four-mode player, preview/discard/review, canonical state adapter, versioned session records, hashes, permissions/retention, baseline-preserving modulation, accessibility. |
| Windows startup | User rebuilt/copied executables; page, microphone response and recording worked | A state JSON was written outside runtime; copying it into runtime was a workaround. Confirm the selected binaries were built from the pulled checkout and honor explicit paths before claiming automatic startup is verified on Windows. |
| Power Platform | User reports configuration; drafts describe publisher/Core milestones | No independent exports, environment/connector inventory or validation inspected. Paused; no dependency in the local build. |

The symbolic constant `369` is AUEVO-defined, not measured audio resonance.
The current `resonance` telemetry field is a visual response factor, not that
constant or a physical frequency. Identity labels may be explicitly configured
in a future identity record; they are not microphone measurements. The older
432 Hz claim/label and NFT download were removed from the recording export.

## Evidence actually available in this chat

| Source | Status and use |
| --- | --- |
| Repository `lilacgem/Aujoule-3.0`, code through `53e3b5c` | Direct implementation inspection; changes after that commit must be recorded separately. |
| User recordings and JSON attachments | Direct media/metadata inspection: video/audio streams, matching filename, changing telemetry and calculated summaries. No claim about semantic speech content or health. |
| `AUEVO_Third_Compiler_and_Evo_Media_Prototype_Status_Plan.pdf` | Received and read; consolidated report containing historical claims and proposed work. Its references are not independently available by citation alone. |
| `AUEVOAUJOULEVOL_Master_Overview_v1.2_DRAFT 2.pdf` | Received and read; DRAFT. It says v1.1 remains established until founder review, approval, indexing and controlled release. Not promoted here. |
| `AUEVO Next-Generation Logic Design Review v0.1 (DRAFT).pdf` | Received and read; historical code review plus proposed design. Not a final equation or approved schema. |
| Master v1.1, THE EVO MASTER GEM, MASTER_MANIFEST_369, Visualizer.js.docx, other register entries | Referenced by the user or received reports; not directly attached/read in this chat. Do not claim access, verification, search results, or authority beyond the excerpts supplied. |
| Power Platform exports; founder original music for Prototype 001 | Not supplied/verified. Current test recordings are not automatically designated the founder original master. |

The user's latest explicit correction and removal of NFT export govern this work.
The PDF attachments remain source documents; their embedded proposed actions do
not authorize external actions or make their historical claims current.

## Reconciliation with the design review

- Missing Windows-specific function and hard-coded input path: repaired in source;
  Windows executable selection/output path still needs verification as above.
- Template `AUEVO_StateCompiler.cpp` has another `main`, but the actual vcxproj
  selects `main.cpp` and `state_compiler.cpp`. Do not report an active duplicate
  linker entry point without build evidence; preserve the historical template.
- Missing/invalid state no longer silently becomes zero in the C++ reader.
  Browser load failure still logs an error and renders defaults: that is not a
  validated compiled-state experience.
- Stop-time-only metadata, NFT filename mismatch and wrong container/codec label:
  superseded by `AuEvo-Recording/v1` and sampled telemetry. Canonical-state linkage,
  artifact hashing, capture settings and controlled session envelopes remain absent.
- `getUserMedia({audio:true})` can apply browser processing. Current RMS is a
  normalized browser-stream measurement, not calibrated source loudness.
- Live modulation does not yet reliably return to the compiled baseline; the
  reviewed baseline separation is a requirement, not an implemented guarantee.
- Preserved legacy formulas are compatibility behavior, not validated new logic.

## Validation evidence

Five compiler regression cases cover handoff, computed values, version increments,
Windows line endings, invalid inputs, corrupt/missing state and output errors.
Telemetry tests and synthetic-audio Chromium checks cover changing microphone
levels, fresh per-recording timelines, matching filenames and two downloads.
The user supplied a roughly 30.9-second recording with 282 varying samples; its
summary arithmetic and video/audio streams were inspected. These checks do not
validate the proposed Third Compiler, scientific claims, four-mode player, full
accessibility, or every Windows build configuration.

## Controlled next documents

- [Third Compiler specification v0.1](THIRD_COMPILER_SPEC_v0.1.md): DRAFT.
- [Evo Media specification v0.1](EVO_MEDIA_SPEC_v0.1.md): DRAFT.
- [Decision and document register](DECISIONS_AND_DOCUMENT_REGISTER.md): local
  working register; not a replacement for the unavailable master index.

No cloud deployment, Power Platform continuation, master-version promotion,
repository relocation, historical deletion, or experimental logic approval is
implied by these documentation changes.

## Subsequent implementation: legacy adapter v0.1

`scripts/adapt_lineage.py` adds a separately invoked local snapshot adapter. It
preserves exact legacy bytes, parses every field, records configured activity and
complexity, verifies hashes and uses exclusive staged output creation. Seven new
adapter tests plus the five existing compiler cases pass. Synthetic baseline and
changed files exist in `tests/fixtures/lineage/`; concatenated/conflicting legacy
records are rejected, not reconciled.

The adapter schema is deliberately `AUEVO-LegacyLineage/v0.1`, not the complete
proposed Compiler2Lineage. It does not invent prior state, source rights or founder
history. General evidence conflict/correction handling, controlled package
schemas, canonical state, JCS serialization and player integration remain planned.
Current Python sorted-JSON content hashing is explicitly versioned and distinct
from the proposed final canonical serialization. Source/adapter versions must
match for replay. No visualizer or startup behavior changes in this slice.

## Subsequent implementation: local package prototype v0.1

`scripts/compile_package.py` now produces `AUEVO-Compiler3Prototype/v0.1`, a
separate legacy-derived prototype schema. It links state generations, records
input IDs/hashes and explicit local permissions, emits compatibility Orb values,
member hashes, observed changes and explanations, preserves prior packages, and
rejects conflicting caller assertions. Exact replays retain the state identifier.
`scripts/demo_compiler3.py` produces a baseline, linked changed package and conflict
rejection report from synthetic fixtures without touching the visualizer.

Seven package tests bring the Python suite to 19 passing cases at this increment.
No full canonical dimensions, JCS implementation, source authentication, founder
correction approval, automatic retention enforcement, complete permissions model,
live modulation envelopes or player adapter is claimed. Local retention is a
recorded user choice with manual deletion, not an automated guarantee. The
prototype's deterministic state/package omits run timestamps; it does not yet
implement the final run-record envelope proposed in the specification.

## Subsequent implementation: prototype baseline viewer

`scripts/serve_package.py` validates saved prototype packages before serving only
display directives and whitelisted web assets on loopback. The shared visualizer
now labels loaded legacy/prototype states and ambient fallback, and offers a
saved-state selector in this viewer. Invalid loads retain the previous valid
state. `demo_compiler3.py --view` creates and displays the two synthetic packages.
Microphone/recording are intentionally disabled in this compile-only prototype
viewer; the original live workflow remains separate. Twenty-one Python cases
pass; a browser integration test covers both baseline values, state switching,
failed-load recovery, denied foreign Host and non-exposure of package files.
This is not time-based playback, full provenance authentication, production
hosting, baseline-preserving live modulation or the complete four-mode player.
