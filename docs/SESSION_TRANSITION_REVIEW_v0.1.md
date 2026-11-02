# SESSION_TRANSITION_REVIEW_v0.1

Status: prototype review contract, not persistent evolution or a final canonical
state transition. Companion: [draft evolved audio model](EVOLVED_AUDIO_STATE_MODEL_v0.1.md).

## Scope

The validator checks two independently valid draft snapshots and a proposed
request. It produces an explained review record without modifying either state,
advancing session count/carry, updating a current pointer, or granting rights.
A valid review is explicitly **not authorized for history commit**.

Inputs are the supported `AUEVO-AudioStateDraftEnvelope/v0.1` snapshots and an
`AUEVO-SessionTransitionRequest/v0.1`. Hashes establish snapshot integrity and
reference association, not authenticated authorship or truth. External source
and measurement bytes are not independently resolved by this reviewer. Those
unresolved provenance checks are blockers for a future persistent commit, not
claims of verified capture/ownership.

## Request fields

| Field | Required meaning |
| --- | --- |
| schema / requestId | Supported request schema and explicit operation ID |
| priorStateRef | Exact prior stateId/contentHash |
| expectedCurrentStateRef | Exact reference expected before review; must match supplied current and prior snapshots |
| candidateStateRef | Exact candidate stateId/contentHash |
| session | sessionId, kind, origin and nonempty purpose; origin is explicit-user-action or synthetic-test |
| permissions | Explicit boolean allowTransitionReview, allowLocalReviewReport, allowHistoryCommit, allowCloudUpload, allowIdentityMemory, plus retentionNote |
| corrections | Explicit list of attributed proposed descriptive changes |
| claims | Explicit list of read-only assertions to compare against candidate data |

Allowed kinds:

- **replay:** identical content state, no correction records, no new history.
- **new-source:** different declared source digest. Review does not verify original
  media bytes or classify a new recording as trusted evidence. A digest already
  listed as an alternative rate derivative in the prior state is rejected as
  DERIVATIVE_NOT_NEW_SESSION, not silently accepted as a fresh source session.
- **reanalysis:** same declared source, different measurement reference; a method
  or analysis change is not automatically learning or a later personal session.
- **metadata-correction:** same source with only the declared descriptive changes.

A new time window, playback, converted rate, file reopen or counter value does not
create a session automatically. Request session IDs are declarations, not
persistently reserved identities; this prototype has no session registry.

`allowTransitionReview` must be true. Saving needs allowLocalReviewReport=true.
HistoryCommit, CloudUpload and IdentityMemory must all be false. Missing/nonboolean
choices are rejected. A retention note documents the local choice; deletion is
manual, not an implemented retention scheduler. Supplying true for a forbidden
operation cannot activate it.

## Corrections and conflict handling

Each correction records `recordId`, `targetStateRef`, `targetPath`, `before`,
`after`, `author`, UTC `createdAt` and `reason`. Target reference must match the
prior snapshot; before/after must match prior/candidate values. This prototype
allows only `/sourceRef/filename` and `/sourceRef/captureChain` descriptive fields.
Both fields must already exist in the snapshots. Metadata attribution is not
verified identity, source rights or a permission grant.

Numeric measurement changes cannot be corrections in place: produce a new
measurement record and a reanalysis candidate. Rights, policy, symbolic/carry and
renderer changes are outside correction scope. Conflicting correction values
block the review; duplicate IDs/targets are rejected rather than last-write-wins.
Descriptive changes for the same source must be explained by correction records.

Claims contain `recordId`, `targetPath` and `value`, using JSON pointers under
sourceRef or measurement observations. They never overwrite data. A mismatching
claim gives CONFLICT_UNRESOLVED. Boolean values are not accepted as numeric zero
or one; ordinary finite integer/float values compare numerically. Metadata
recency and claim volume are not evidence of truth. Caller-supplied claims are
not independently retrieved or authenticated source records.

## Predecessor and concurrency boundary

The prior/candidate snapshots must pass their content-hash and supported-scope
checks. The request must identify each exact snapshot. `--current` supplies a
separate current snapshot for stale-reference checks; otherwise the supplied
prior snapshot is used as current for review only.

This is **not an atomic compare-and-swap against a persistent store**. The report
states the boundary explicitly. A future commit path must resolve immutable
provenance, policy and expected-current state in the actual store, then append
atomically. Do not interpret this snapshot comparison as a live-store guarantee.

## Output and errors

`AUEVO-SessionTransitionReview/v0.1` is wrapped with content hash, review ID and
createdAt outside that hash. Request, prior/candidate/current references, producer
version/build, correction attribution, scope warnings and changes are recorded.
Status is replay-no-advance or valid-for-review-not-commit. HistoryAdvanced,
authorizedForHistoryCommit and stateFilesModified are always false.

Changes report total changed fields and up to 200 detailed JSON-pointer entries,
with an explicit truncation flag. Added/removed/changed values remain distinct.
Numeric representation changes can appear separately even if numerically equal.
This diff is an observation, not a semantic claim about learning or improvement.
Saving verifies the review content hash and refuses existing outputs.

Named failures include STATE_INVALID, REQUEST_INVALID, PRIOR_STATE_MISMATCH,
CANDIDATE_STATE_MISMATCH, STALE_CURRENT_STATE, PERMISSION_DENIED,
UNSUPPORTED_PERMISSION, CONFLICT_UNRESOLVED, CORRECTION_BEFORE_MISMATCH,
CORRECTION_AFTER_MISMATCH, CORRECTION_SCOPE_UNSUPPORTED,
UNEXPLAINED_METADATA_CHANGE, REPLAY_KIND_REQUIRED, TRANSITION_KIND_MISMATCH,
REFERENCE_UNRESOLVED and OUTPUT_EXISTS. Failure does not modify state snapshots
or publish a successful review. These are validation outcomes, not evidence of
malicious behavior or missing credentials.

## Demonstration and tests

`demo_session_transition.py` creates clearly labeled synthetic snapshots and
requests, not a real audio session. It demonstrates accepted replay, reanalysis
and attributed descriptive correction; rejects conflicting measurement claims,
stale current snapshot, history-commit permission, wrong prior hash and wrong
correction-before value. State JSON fixtures retain synthetic origin labels.

Regression tests also cover malformed/tampered state, missing authors, numeric
correction rejection, contradictory corrections, strict boolean claims, different
source review, bounded diff details, deterministic review replay and overwrite
refusal. The demo and validation tool write local review artifacts only.

## Later work remains explicit

No persistent carry implementation, trusted evidence resolver, identity store,
authenticated correction authority, final canonical dimensions, renderer change,
AI interpretation or Power Platform connection is introduced here. Those remain
separate implementations and decisions. Neither setting a permission flag nor
publishing this code completes that architecture.
