# EVOLVED_AUDIO_STATE_MODEL_v0.1

Status: DRAFT, candidate observation contract for review. It does not approve a
final AUEVO equation, rename existing artifacts as complete compilers, or release
the draft master overview. Companion: [Third Compiler specification](THIRD_COMPILER_SPEC_v0.1.md).

## Purpose and evidence

Preserve the information needed for an audio-derived experience without reducing
state to one root, gate, intensity number or session counter. The completed study
shows that normalization/focus strongly change discrete results, a floor compresses
many inputs, and a large count term can disappear under digital-root reduction.
These findings describe one recording and a limited diagnostic matrix, not a
universal law or evidence of physical resonance.

The model therefore keeps original media, technical features, continuous changes,
configured transformations, symbolic interpretation and rendered artifacts in
separate linked records. Both continuous values and symbolic outputs can be
retained; neither replaces the source. No new human-state dimensions are inferred.

## Candidate record layers

| Layer | Retained contents | Interpretation |
| --- | --- | --- |
| Source reference | Original file digest, observed format/rate/channels/duration, capture and rights status | A reference to preserved evidence; not inferred authorship or consent |
| Measurement record | Exact input feature-file hash, method/version, units, frequency bands, all timed observations and actual sample boundaries | Computed technical measurements with unknown calibration/uncertainty where applicable |
| Continuous feature vector | RMS, sample peak, crest factor, RMS change, positive band change, band powers, common/full-band centroid, bandwidth, rolloff and flatness | Separate observable features; no automatic averaging into a universal human score |
| Transform configuration | Mapping IDs/hashes, normalization ranges, clipping policy, configured focus, symbolic constants | Choices made by a versioned experiment, not measured facts |
| Symbolic overlay | Original root/gate/shape/carry outputs and the configuration that produced them | Optional experimental interpretation; no physical, medical or identity inference |
| Evolution transition | Prior state/hash, explicit session boundary, referenced new inputs, permitted correction records and explained changes | Append-only candidate transition; not implemented by this draft exporter |
| Experience profile | Versioned bounded mappings to Orb/media channels; accessibility settings | A future presentation choice, not a rewrite of measurements |
| Artifact/session record | Rendered media hash, session/time/configuration, permissions and release/retention choice | A distinct output, not the original source or full state |

The five compatibility Orb channels remain renderer outputs. This draft does not
declare them to be the final canonical dimensions. Sample rate is recorded as
source/acquisition configuration; symbolic 369 remains AUEVO_DEFINED and is not
silently converted into measured Hz.

## Observation contract

The first executable export uses `AUEVO-AudioStateDraft/v0.1` inside
`AUEVO-AudioStateDraftEnvelope/v0.1`. Its JSON Schema is
[here](../schemas/audio-state-draft-v0.1.schema.json).

Every original measurement window is copied without changing its values. Window
index/start/end/center and actual rounded boundaries are retained. The measurement
method fixes the common-band upper frequency and exact band definitions. Unit
metadata is centralized and kept beside the observations. Null features remain
unavailable, not zeros. For example a silent window can have RMS=0 and an
undefined centroid/crest factor.

If a corrected input already contains per-window evoMetrics output, it is placed
in `symbolicOverlay.records`, removed from the measured observations, and labeled
`preserved-not-recomputed`. It is not verified as a final rule or promoted to
technical measurement. If the input has no overlay, `not-attached` is explicit.
Separate trial/sensitivity artifacts remain separate source records; the exporter
does not automatically import them from the same folder.

All rate conditions point to their existing hashed feature records. They are
alternative software derivatives of the same source, not distinct life/session
experiences. Neither a 125 ms window nor a converted file increments session count.

This schema is a structural review aid. The exporter also checks numeric
finiteness, field disposition, ordering inherited from validated inputs, input
hashes and its supported scope. JSON Schema alone does not verify hashes,
authorship, permissions, physical calibration or semantic truth. It is not a
production canonical-state validator.

## What evolution should retain between sessions — proposed contract

A session boundary must be an explicit action/record with a declared purpose. A
new window, file reload, playback or parameter trial is not implicitly a session.
Before committing any persistent evolution transition, the implementation must:

1. Resolve an explicitly permitted prior state ID/hash and source lineage.
2. Retain the prior state unchanged; verify input and method references.
3. Preserve new source/measurement records, actual configuration, gaps and errors.
4. Keep corrections as attributed records with target, author, time and reason.
5. Distinguish changed sound from changed analysis settings or changed symbolic rules.
6. Produce an explained changeset and unresolved-conflict list.
7. Check persistence purpose, retention/deletion choices and sharing scope.
8. Atomically append the validated version; advance the current pointer only if the
   expected predecessor is still current. Exact replay does not advance history.

A prior scalar leftover is insufficient to establish lineage. If kept for legacy
reproduction, its value, predecessor, transform version and update rule belong to
a separate symbolic-state branch. That branch cannot overwrite measured features
or imply that the level always increases. No persistent carry should be introduced
until its rule, consent and tests are defined.

The actual mathematical rule for combining successive sessions remains OPEN. This
draft defines what information must survive, not a fabricated learning equation.
Source preservation and append-only versioning do not imply indefinite retention
of private media; retention and deletion need an explicit policy with disclosed
limits for already-exported copies.

## Corrections, conflicts and changing methods

- Correcting metadata retains the earlier record and records who changed what and why.
- Reanalysing the same source with new FFT/integration settings creates a distinct
  measurement record. It is a method change, not proof the source changed.
- Altering normalization/focus/session-count settings creates a named experiment.
  Do not relabel extra gates as improved state or choose parameters to force them.
- Conflicting source claims remain distinct. A required unresolved conflict blocks
  a controlled transition; timestamp recency or model agreement is not truth.
- AI interpretation, if later added, is optional, separately referenced, attributed
  to model/version/inputs, reviewable and correctable. It cannot replace evidence.

## Permissions and current executable boundary

`build_audio_state.py` exports a local review artifact only. Its operation grants
no microphone/recording, cloud upload, identity memory or source rights. It does
not read the original WAV or verify its physical capture chain. Source metadata
is inherited from linked measurements, with that scope made explicit.

The initial draft has no parent state, no history commit, no persistent evolution
advance and no render directives. This is deliberate: implementing persistent
carry or selecting a final canonical dimension set is a separate decision, not
an incidental effect of exporting a file. Missing permissions/rights are not
invented. The exporter refuses existing output and preserves input records.

No emotion, thought, disability, medical condition, protected characteristic,
honesty or identity inference is allowed. No NFT export or new sample-rate benefit
is claimed. Power Platform remains paused and outside the local critical path.

## Hashing and reproducibility

Content hash covers the complete draft payload using the explicitly named Python
sorted-JSON UTF-8 encoding, not a claim of JCS compliance. State ID derives from
that hash; createdAt is outside it. Exact payload replay retains the state ID;
the exported envelope's byte hash may change with run time. Producer build/source
bytes and method/input digests are part of reproducibility; different builds or
line-ending digests can change identity even when observed values agree.

Drafts are review artifacts, not signed identities or proof of rights. Before
production promotion, resolve canonical serialization, cross-platform numeric
rules, immutable storage, input authority, session/correction semantics and policy
enforcement. Keep this draft and prior reports as evidence of the design process.

## Acceptance cases

- All original measurements, including null values, survive export unchanged.
- Optional symbolic values exist only in the separate overlay, not measured fields.
- Changing a continuous input changes content identity even if its root is unchanged.
- Rate alternatives cannot become parent sessions or increment counters.
- Replay keeps content ID while createdAt/run envelope remains distinct.
- A mismatched feature hash, unsupported method or unknown field fails without
  replacing an older draft. No silent dropping or zero substitution.
- Parent state commits, permission expansion and new render directives are rejected
  by this exporter rather than represented as implemented features.
- Identity fields/source ownership are not inferred from audio or session count.

## Next implementation slices

Review the candidate feature/units contract and session-boundary definition, then
implement a versioned transition validator using synthetic before/after/correction
and conflict fixtures. Preserve continuous deltas and their method provenance.
Only afterward connect a separately versioned RenderProfile to the state, retaining
read-only baseline and bounded live modulation. Use multiple recordings and
controlled signals before generalizing a mapping. This draft does not authorize
or automatically perform those later changes.
