# Local draft checkpoint archive v0.1

This local SQLite archive preserves a supported draft snapshot with fresh
reconciliation receipts. It is a checkpoint of reviewed material, not a new
personal session, canonical evolution history, permission escalation, or an
implementation of persistent symbolic carry. The draft's history permissions
remain false and unchanged. Source-byte mismatch remains explicit.

## Verification and storage

`archive_audio_checkpoint.py` reads the archive's current checkpoint before doing
media work, freshly runs the measurement resolver and decoded-sample reconciliation,
then rereads the state bytes and verifies their exact digest against the receipt.
The CLI does not accept a saved reconciliation JSON as sufficient authority.
The current implementation accepts the reconciled, byte-different/sample-identical
case only; ordinary byte-identical sources can still use the strict resolver.
It rechecks the identity-control WAV, not the other derivative audio files.

SQLite holds the first state envelope for each payload content hash, and separate
hash-addressed fresh verification receipts. No original input file is moved,
rewritten or deleted. Repeated verification of the same state reuses its checkpoint;
a new receipt can record another verification without creating a new session.

An immediate write transaction checks the expected current checkpoint inside the
actual database before inserting any records. A stale writer rolls back. A different
current state is refused: no automatic transition or overwrite policy is implemented.
Checkpoint and receipt inserts and the initial pointer are committed together.
SQLite is part of Python; no additional package installation is needed.

`--inspect` opens the existing database read-only, checks stored state and receipt
hashes, required receipt scope and links, and checks that every stored state has
a receipt and that the current pointer exists. It does not recheck media bytes.

## Limits

This is a local, manually retained draft archive. It has no authenticated user
identity, ownership authority, digital signatures, encryption, retention scheduler,
cloud synchronization, learning equation or supported cross-state advancement.
A person with write access can alter SQLite; integrity checks detect inconsistent
records, not a coordinated rewrite of records and hashes. The low-level archive
API checks record integrity and links; only the CLI's fresh reconciliation path
rechecks media. It is not a security boundary against untrusted Python callers.

SQLite transaction semantics provide local writer serialization and atomic writes;
this does not claim distributed consistency or guaranteed disk survival. Backups,
retention and deletion are manual. Original recordings and feature/comparison files
remain external dependencies; the archive stores snapshots and receipts, not copies
of the full audio or feature dataset. Keep these files in their original locations.
The archive contains private draft measurements and should remain local under the
ignored runtime folder.

## Use

From the repository folder on Windows:

```bat
.venv-audio\Scripts\python scripts\archive_audio_checkpoint.py
```

Select the current original WAV. Defaults use the existing `audio-state-draft-001`,
`matched-features-002`, `rate-comparison-001` and `audio-sample-check-001` folders
under runtime. The archive is
`runtime/local-draft-checkpoints/checkpoints.sqlite3`. All paths have CLI overrides.

Inspect stored integrity without another audio decode:

```bat
.venv-audio\Scripts\python scripts\archive_audio_checkpoint.py --inspect
```

Tests cover initialization, idempotent checkpoint/receipt insertion, stale writer
rollback, incompatible current pointers, altered/unlinked receipts, unchanged input
snapshots and detection of altered stored receipts. Earlier reconciliation tests
exercise actual synthetic WAVs and reject sample inequality and altered reports.
