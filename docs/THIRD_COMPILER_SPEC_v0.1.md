# THIRD_COMPILER_SPEC_v0.1

Status: DRAFT for founder review. Date: 1 November 2026.
Scope: proposed local contract, not implemented or approved canonical logic.
Authority and evidence: [project status](PROJECT_STATUS.md). Companion:
[Evo Media v0.1](EVO_MEDIA_SPEC_v0.1.md).

## 1. Purpose and boundaries

Compiler 1 is the original symbolic/source foundation. It must not be described
as a completed media-ingestion or research system. Compiler 2's intended equation
is Original Source + Prior Logic + Prior Output + Founder History + New Evidence
+ New Learning = New Compiled State. Its current text writer implements only a
small subset; absent equation terms must be declared missing, not fabricated.

Compiler 3 orchestrates validation, classified evidence, lineage, permissions,
reconciliation, deterministic state compilation, explanation, and versioned output.
The repaired State Compiler is its Orb-settings calculation component; its v3 JSON
is not a completed Compiler 3 package. EvoSpace consumes permitted experience
directives and session telemetry; it must not mutate canonical state.

Prototype boundary: local files, synthetic inputs first, optional explicit local
export. Power Platform, Dataverse, Azure, AI services and hardware are outside the
critical path. Audio-analysis stage ownership is an open design decision.

## 2. Labels, record envelope and input package

Proposed record envelope: `recordId`, `recordType`, `schemaVersion`, UTC
`createdAt`, `producer {name, version, buildHash}`, `runId`, `inputs[]`,
`outputHash`, `evidenceClass`, `reviewStatus`, `supersedes` (empty for no predecessor).
Each cross-record input includes `recordId`, `role`, and SHA-256. An absent build
hash is `null` with `UNAVAILABLE` status, never a made-up digest. Controlled release
requires resolved producer versions/builds. Raw media hashes cover exact bytes;
JSON hash rules are defined in section 7. IDs are identifiers, not evidence of
ownership or scientific validity.

| Evidence class | Meaning |
| --- | --- |
| SOURCE | Original source bytes/reference preserved unchanged |
| MEASURED | Technical result with method, units, settings and uncertainty |
| CONFIGURED | Explicit settings chosen by a user or application |
| FOUNDER | Attributed founder statement or correction, not automatically verified fact |
| DERIVED | Named deterministic transformation of referenced inputs |
| AI_INTERPRETED | Optional model interpretation, separately stored and reviewed |
| TELEMETRY | Temporary session measurements and render response |
| ARCHIVED | Preserved artifact; original evidence classification retained in its referenced records |

Classification is per record and per dimension. A mixed record links separately
classified values. `symbolic` values additionally use `origin: AUEVO_DEFINED`;
that origin is not a physical measurement. Uncertainty has status `KNOWN`,
`ESTIMATED` or `UNKNOWN`, with method/rationale; unknown is explicit and carries
no invented confidence score. Review status is `UNREVIEWED`, `REVIEWED` or
`REJECTED`, with reviewer reference when reviewed.

Accepted entry point: proposed `Compiler2Lineage/v0.1` package containing an
envelope and resolved references to:

| Record | Required content |
| --- | --- |
| SourceRecord | Original identifier, byte hash, local reference, read technical properties where applicable, rights reference, unchanged-source attestation, derived-copy references. Unknown properties are labeled unknown. |
| Prior outputs and prior state | IDs, hashes, versions; null prior only for a declared initial generation |
| FounderInput | Author, UTC time, content, configured intensity/focus/activity/complexity where used, target and prior value for a correction |
| MeasurementRecord | Method/library version, feature value/unit, window/hop/FFT size/window function as applicable, actual analyzed sample rate, resampling and capture-processing settings, uncertainty |
| ExperimentConfig | Controls, hypothesis, parameters, approved inputs and expected comparisons; not evidence of a result |
| TransformSet | Immutable ID/version/hash; formulas, parameter ranges, default/clamp policies and symbolic constants |
| Rights/permissions record | Subject/source, permitted operations and recipients, retention and persistence choices, grant origin and time |
| Learning/rule changes | Referenced versioned rule changes and reasons, not a claim that the existing executable learns autonomously |

`lineageTerms` records the equation's terms as present/missing/not-applicable with
reasons. A synthetic fixture can explicitly omit external research; a package
must never claim full archival coverage from a text state file. Every consumed
reference must resolve and verify. Unreferenced files are not ingested merely
because they are in the same folder.

### Legacy adapter

Read the seven-line `compiler2_state.txt` as version, intensity, focus, initial,
pattern, color, symbolic resonance. Preserve its exact bytes/hash, all parsed
fields and a report of fields consumed, retained-only, discarded, or defaulted.
Record activity and complexity as explicit user-configured inputs. Legacy `369`
is a defined symbolic value. Validate the observed current ranges: intensity
integer 1–10, focus/activity/complexity finite numbers 0–1, alphabetic initial.
These are compatibility ranges, not physiological dimensions. Report unknown
provenance/rights; do not synthesize founder authorship or media ownership.
This adapter produces `legacy-adapted` status, never full-lineage certification.

## 3. Permissions, persistence and exclusions

Temporary live context and persistent records are separate. Permission fields
include purpose, `allowCompile`, `allowLiveAudio`, `allowRecord`,
`allowPersist`, `allowExport`, permitted recipient scopes and retention/deletion
choices. Missing permission is not a grant. Browser microphone permission alone
is not permission to record, export, retain, train a model, or upload. Local export
requires a user action; cloud upload is off by default. Withdrawal blocks future
use and triggers the documented local deletion flow; disclose that downloaded
copies cannot be remotely recalled.

Keep employer/customer/client/restricted material out unless authorized. No
hidden emotion, medical condition, protected characteristic, honesty, thought,
identity or disability inference. No claim to capture complete human state.
No automatic model training or persistent memory from microphone data. No NFT,
blockchain export, medical feature, ultrasonic benefit or hardware claim.
Optional AI is outside the first implementation: it must remain a separately
referenced `InterpretationRecord` with provider/model/version, prompt hash,
input references, uncertainty and human review; never replace source evidence.

## 4. Processing and reconciliation

1. Validate schemas, versions, referenced hashes, numerical ranges and permissions
   before touching current state. Reject unknown major versions and non-finite numbers.
2. Classify and normalize allowed inputs while retaining original records unchanged.
3. Resolve explicit corrections by target ID and supersedes relationship, with
   author/time/reason. Preserve both corrected and superseded values.
4. Detect conflicting claims and missing evidence. Do not pick the newest timestamp
   or a model majority as truth. An unresolved conflict in a required dimension blocks
   controlled compilation; unrelated conflicts can remain visible with an explicit
   unresolved status if they do not affect the emitted directives.
5. Apply the exact referenced deterministic TransformSet. Each output dimension
   records its contributing inputs, formula ID, units, range and uncertainty.
6. Produce a changeset and human-readable explanation. Keep defaults, clamps,
   corrections and unresolved issues visible. No silent fallback to zeros.
7. Filter experience output by permissions; validate the consumer contract.
8. Stage and verify an immutable package; atomically promote the current pointer
   only after success. Errors leave the last valid package intact.

Any clamping must be explicitly permitted by the named transform and recorded
with before/after/rationale. Invalid required inputs otherwise fail; a clamp is
not permission to hide invalid source data.

## 5. Current-state package

Proposed local `AUEVO-Compiler3Package/v0.1`, comprising:

| Member | Contract |
| --- | --- |
| `state.json` | Proposed `AUEVO-EvoState/v4-PROPOSED`; `stateId`, `priorStateId`, `generation`, compilation time, producer, referenced inputs, TransformSet, dimensions, permissions reference and package status |
| `provenance.json` | Every consumed source/input ID and verified hash, producer versions, parsing and validation report, measurement/transform lineage, supersedes relationships |
| `changes.json` | Added/changed/corrected/superseded/unresolved fields; before/after references, reasons, rules and sources |
| `experience.json` | Versioned RenderProfile reference, bounded visual directives, compatibility `legacyOrb`, permission-filtered fields |
| `explanation.md` | Concise reasons, missing evidence, uncertainties and limitations traceable to changeset entries |
| `manifest.json` | Member filenames and SHA-256 hashes, schema/version, references and package hash scope |
| `audit.json` | Validation outcomes and non-secret operation log; rejected attempts are stored separately only if allowed |

`state.json` includes `inputs[] {role, recordId, sha256}`, `transformSet {id,
version, sha256}`, `dimensions` with `value`, `range`, `unit`, `evidenceClass`,
`derivedFrom[]`, `transformId`, `uncertainty`, plus `symbolic`, `palette`,
`interpretationRef` (null when absent) and `legacyOrb` compatibility channels.
Final canonical dimension names/meanings remain OPEN. Compatibility channels
are not automatically adopted as the final human-state model.

Preserve glow, density, motion, complexity and coreIntensity (0–1) plus palette
`#D62BB7`, `#27BDE2`, `#FFD98A` in `legacyOrb`. Tag configured palette separately
from derived colors. Legacy TransformSet reproduces existing formulas:
`glow=clamp(intensity/10)`, `density=clamp((focus+complexity)/2)`,
`motion=clamp(activity)`, `complexity=clamp(complexity)`,
`coreIntensity=clamp((glow+focus)/2)`. Clamp range is 0–1. Formula redesign needs a
new transform version and evaluation; compatibility is not a final AUEVO equation.
`symbolic.resonanceConstant` is 369 with `origin: AUEVO_DEFINED`; live response
uses a different field name, `audioResponseFactor`.

## 6. Experience directives and baseline

Renderer baseline is read-only. A RenderProfile maps canonical dimensions to
bounded channels. Proposed rule:

`rendered(channel) = clamp(baseline(channel) + boundedModulation(telemetry), 0, 1)`.

Hue uses documented circular mapping instead of an assumed linear channel.
Modulation has explicit bounds, neutral condition and easing. On silence or mic
off it returns to zero and restores the baseline; do not overwrite canonical
state or present a fallback look as successfully compiled state. Envelope values,
digital-root behavior and audio/visual correlations are experimental mappings
pending tests. Session summaries go into a RenderSessionRecord, not back into
canonical state. This separation is not yet guaranteed by current Visualizer.js.

## 7. Determinism, hashing and versioning

Proposed decision: portable local JSON is the prototype source of truth; any future
Dataverse integration is a mirror, not currently required or implemented.

Use UTF-8 and a documented canonical JSON serialization (proposed RFC 8785/JCS).
Reject duplicate keys and unsupported/non-finite numbers. Never hash an object
including its own hash. Define two distinct products:

- **Deterministic state payload:** semantic dimensions, symbolic/configured values,
  input IDs/hashes, prior state reference, policy, TransformSet and RenderProfile
  versions. Exclude run ID, execution time and outputHash. Its SHA-256 is
  `stateContentHash`; derive stable stateId from that digest.
- **Run/package envelope:** supplied/frozen UTC time, run ID, explanations and
  manifest; exact member bytes are hashed excluding the manifest's self-hash.
  Re-running at another time may change the run/package hash while preserving
  stateContentHash. Byte-for-byte package reproduction requires the same envelope
  metadata and tool versions, not just the same measurements.

Freeze source inputs and transformation versions; record any random seed when
adapting symbolic randomness. Exclude runtime RNG, wall-clock values and live
microphone streams from a deterministic canonical computation. Recorded live
signals can become explicit hashed inputs to a later generation only with consent.

Persist generations immutably. `priorStateId=null` only for the initial state;
new transitions reference the prior content hash and increment generation.
An exact replay returns the same content-addressed state without overwriting it
or advancing generation. Concurrent updates to a current pointer require a
compare-and-swap check. Rejected transitions cannot erase previous state.

## 8. Validation and error contract

Error object: `code`, `stage`, `path`, `recordId` if known, safe `message`,
`recoverable`, `retryAction`; omit secret contents and raw private audio.
No partial package is published to a consumer on failure.

| Code | Trigger and required response |
| --- | --- |
| INPUT_MISSING / SCHEMA_UNSUPPORTED | Absent required record or unsupported major version; stop with named field/version |
| INPUT_INVALID | Wrong type/range, corrupt legacy text, non-finite value or ambiguous duplicate JSON key; reject |
| HASH_MISMATCH / REFERENCE_UNRESOLVED | Bytes changed or linked record unavailable; quarantine input, retain prior valid state |
| PERMISSION_DENIED / RETENTION_UNSET | Required operation not permitted or required persistence decision absent; stop that operation |
| CONFLICT_UNRESOLVED | Contradictory required dimension without explicit correction; report both references |
| TRANSFORM_UNAVAILABLE | Unrecognized or mismatched mapping version/hash; no fallback formula |
| PRIOR_STATE_MISMATCH | Missing/cyclic/wrong predecessor or concurrent pointer update; no advancement |
| OUTPUT_WRITE_FAILED | Failed staging/verification/atomic promotion; preserve prior state and report recoverable error |

## 9. Synthetic fixtures and acceptance tests

These are specified test vectors, not existing Compiler 3 tests or validated
schemas. Implement the validator/fixtures with the adapter before claiming these
passes. Use synthetic names and local dummy media only; fixture hashes must be
calculated from actual fixture bytes during implementation, not placeholder
strings accepted as real hashes.

| Fixture | Defined input | Required result |
| --- | --- | --- |
| baseline | Initial generation; configured intensity=8, focus=.6, activity=.7, complexity=.4; explicit local compile permission; legacy compatibility transform | glow=.8, density=.5, motion=.7, complexity=.4, coreIntensity=.7; palette configured; 369 AUEVO_DEFINED; provenance records all inputs |
| changed-state | Prior baseline ID/hash; founder correction intensity 8→5 with author/time/reason and explicit supersedes; other values unchanged | New generation; glow=.5, coreIntensity=.55; density=.5, motion=.7, complexity=.4; changeset identifies correction and dependent channels; baseline remains readable |
| conflicting-evidence | Two unsuperseded claims for required intensity (5 vs 9), equal applicability | CONFLICT_UNRESOLVED; no new current pointer, fabricated average or overwritten history |
| replay | Exact baseline inputs, predecessor, policy and transform/profile versions replayed with a different run time | Same stateContentHash and stateId; separate run envelope allowed; no extra generation |
| tampered-source | Change source bytes without updating referenced digest | HASH_MISMATCH; prior valid package preserved |
| denied-persistence | Compile allowed for temporary use; persist/export denied | No state written or exported; separate explicit action required to change permission |
| missing-input | No activity, corrupt focus, unknown major version or unresolved prior | Named error; no silent zero/default; prior state preserved |

Additional gates: legacy adapter retains all seven fields and exact bytes;
identity and 369 are not classified MEASURED; clamp/default reports are complete;
withdrawn permission stops further recording/persistence; optional interpretation
cannot overwrite deterministic outputs; renderer mutates no canonical objects;
silence/mic-off restores baseline; audit contains no secrets. Reproducibility
requires pinned serialization, numeric rules, build/transform versions and input
hashes. None of these requirements is satisfied merely by the existing five
compiler regression tests.

## 10. Open decisions and implementation sequence

Open: final dimension set, audio measurement stage ownership, JSON authority for
later production, experimental symbolic mappings, activity/complexity semantics,
identity record retention and exact numeric precision/JCS implementation. Local
JSON, configured manual values and a compatibility-only TransformSet are draft
prototype recommendations, not approvals of a production equation.

Sequence: source inventory → versioned schemas/envelope and legacy adapter → three
synthetic fixtures and rejection tests → deterministic package/explanations →
Evo Media read-only adapter → state playback and session/artifact records →
rights/retention/accessibility gates. Keep original recordings unchanged. Founder
music Prototype 001 needs a designated original and rights/capture record before
source-analysis claims; unconventional sample-rate research is a separate protocol.
