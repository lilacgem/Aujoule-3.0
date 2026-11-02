# STATE_EVIDENCE_RESOLUTION_v0.1

Status: read-only evidence resolver for supported draft state snapshots. It does
not implement persistent evolution, source-rights authentication or final
canonical-state promotion. Companion:
[transition review](SESSION_TRANSITION_REVIEW_v0.1.md).

## What is resolved

The resolver reads actual files explicitly selected by the user:

1. `audio-state.json`: verify its supported draft scope and content ID/hash.
2. Corrected `features.json`: verify exact bytes match the state's feature digest.
3. Its `summary.json`: verify the full feature hash and source/method/condition
   association, including corrected v0.2 integration and window alignment.
4. Referenced `comparison.json`: verify exact digest, supported software-conversion
   schema, source metadata, condition set and each derivative reference digest.

The expected draft is reconstructed from the feature record, then every payload
field other than the producer artifact digest is compared. Producer name/version
must match the supported exporter; a build digest alone is not authenticated
code provenance. Original observations, units, methods, overlay disposition,
alternative references, source metadata and scope must match. Alternative
feature observations are validated as well as their selectors and identities.
No fields are silently replaced, defaulted or merged.

The resulting `AUEVO-StateEvidenceResolution/v0.1` report records input filenames
and hashes, exact state reference, completed checks and explicit remaining limits.
CreatedAt sits outside the hashed resolution content. Report saving verifies its
own hash/scope and refuses an existing output directory. No state or evidence
file is modified. Inputs are hashed again before final reporting to catch changes
during the operation; this is a point-in-time check, not a locked archive.

## Optional source and derivative bytes

`--source` hashes an explicitly supplied original byte file against the declared
source digest. `--verify-derived` hashes the derivative files beside comparison.json.
`--check-media` enables both and opens a fourth picker for the original WAV if its
path was not supplied. These are streaming byte hashes, not full decoded audio
buffers or new resampling. Derived paths must remain inside the comparison folder;
path traversal and escaping symlinks are rejected.

Media headers, capture chain, ADC/DAC behavior, native rates, actual ownership,
consent and measurement correctness are not established by a matching digest.
The report distinguishes not-provided media bytes from sha256-matched bytes and
states mediaHeaderChecked=false. A selected file could be a synthetic descriptor;
the byte check must not be relabeled as a real audio/capture test. The included
demo explicitly uses text fixtures to test this boundary.

## Errors and blocked cases

Named errors include EVIDENCE_MISSING, EVIDENCE_UNREADABLE, EVIDENCE_INVALID,
STATE_INVALID, FEATURE_HASH_MISMATCH, SUMMARY_LINK_MISMATCH,
COMPARISON_HASH_MISMATCH, COMPARISON_INVALID, SOURCE_METADATA_MISMATCH,
CONDITION_LINK_MISMATCH, OBSERVATION_MISMATCH, ALTERNATIVE_INVALID,
STATE_EVIDENCE_MISMATCH, BUILDER_UNSUPPORTED, SOURCE_HASH_MISMATCH,
DERIVATIVE_PATH_INVALID, DERIVATIVE_HASH_MISMATCH, INPUT_CHANGED and OUTPUT_EXISTS.
A failed resolution does not publish a successful report or alter evidence.

A valid transition-review report alone does **not** bypass these checks. A state
with an attributed descriptive correction can still differ from its original
measurement metadata; this resolver rejects that mismatch until a separately
implemented, explicitly attributed reconciliation path resolves it. Measured
numbers cannot be patched simply by rehashing a snapshot. Rights/permissions
are not inferred from the presence of a file.

## Relation to the earlier transition validator

The snapshot reviewer marked external measurement references unresolved. This
component now resolves the supported local measurement chain for an unchanged,
reproducible draft snapshot. Its report can be inspected alongside a transition
review, but neither is an authorization to commit persistent history.

The prototype does not automatically consume a resolver report as a production
commit token, authenticate its producer, lock a persistent store, resolve
correction-author authority, enforce retention or promote a draft canonical model.
HistoryAdvanced, authorizedForHistoryCommit and stateFilesModified remain false.
Those later mechanisms require their own implementation and evidence.

## Demonstration and tests

`demo_evidence_resolution.py` creates real fixture files with consistent hashes
and a synthetic draft. One chain resolves; six expected cases reject: missing
feature, altered feature, state-observation mismatch, changed comparison,
source-byte mismatch and derivative-byte mismatch. These are not recordings or
new personal sessions.

Tests additionally verify summary mismatch, strict metadata reconciliation,
unchanged input bytes, optional media status, report hash checks and overwrite
refusal. The actual user-provided state/features/summary/comparison chain has also
been checked locally; the original and derivative audio bytes were not available
in that cloud check and are explicitly left unverified there.
