"""Archive a freshly reconciled draft locally; no session/evolution history commit."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

try:
    from scripts.reconcile_audio_evidence import reconcile
    from scripts.compare_audio_samples import choose
    from scripts.build_audio_state import verify_state
    from scripts.resolve_state_evidence import verify_resolution
    from scripts.adapt_lineage import canonical_bytes, LineageError
except ModuleNotFoundError:
    from reconcile_audio_evidence import reconcile
    from compare_audio_samples import choose
    from build_audio_state import verify_state
    from resolve_state_evidence import verify_resolution
    from adapt_lineage import canonical_bytes, LineageError

SCHEMA = 'AUEVO-LocalDraftCheckpointArchive/v0.1'


def hash_content(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def validate_receipt(receipt, state):
    verify_state(state)
    report = receipt['reconciliation']
    expected = hash_content(report)
    if receipt['contentHash'] != expected or receipt['reconciliationId'] != 'audio-reconciliation:sha256:'+expected:
        raise ValueError('Reconciliation hash mismatch.')
    if report['schema'] != 'AUEVO-AudioEvidenceReconciliation/v0.1' or report['status'] != 'source-bytes-differ-decoded-control-samples-identical':
        raise ValueError('Unsupported reconciliation.')
    if report['stateRef'] != {'stateId': state['stateId'], 'contentHash': state['contentHash']}:
        raise ValueError('Reconciliation targets another state.')
    if report['strictSourceByteMatch'] is not False or report['decodedControlSampleMatch'] is not True:
        raise ValueError('Unsupported reconciliation scope.')
    for key in ('historyAdvanced', 'authorizedForHistoryCommit', 'stateFilesModified', 'originalHashReplaced'):
        if report[key] is not False:
            raise ValueError('Reconciliation claims unsupported state/history changes.')
    if report['earlierSourceSha256'] != state['payload']['sourceRef']['sha256']:
        raise ValueError('Source reference mismatch.')
    resolved = report['measurementChainResolution']
    verify_resolution(resolved)
    chain = resolved['resolution']
    sample = report['freshSampleComparison']
    if chain['stateRef'] != report['stateRef']:
        raise ValueError('Resolution/state reference mismatch.')
    for key in ('state', 'features', 'summary', 'comparison'):
        if chain['inputs'][key] != report['inputs'][key]:
            raise ValueError('Resolution input link mismatch.')
    if (sample['status'] != 'decoded-samples-identical' or sample['differentChannelSamples'] != 0
            or sample['maximumAbsoluteDifference'] != 0 or sample['firstDifference'] is not None):
        raise ValueError('Sample equality result inconsistent.')
    if (sample['current']['sha256'] != report['currentSourceSha256']
            or sample['current']['sha256'] != report['inputs']['current']['sha256']
            or sample['declaredEarlierSourceSha256'] != report['earlierSourceSha256']
            or sample['comparisonSha256'] != report['inputs']['comparison']['sha256']
            or report['currentSourceSha256'] == report['earlierSourceSha256']):
        raise ValueError('Sample source/comparison link mismatch.')
    # The caller must freshly generate this receipt through reconcile(), not trust
    # an uploaded or arbitrarily supplied hash as an authorization token.


def read_head(database):
    database = Path(database)
    if not database.exists():
        return None
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro', uri=True) as connection:
        schema = connection.execute('SELECT schema FROM archive_info WHERE singleton=1').fetchone()
        if schema != (SCHEMA,):
            raise ValueError('Unsupported archive schema.')
        row = connection.execute('SELECT state_hash FROM current_checkpoint WHERE singleton=1').fetchone()
        return row[0] if row else None


def archive(database, state, receipt, expected_head):
    """Store a locally rechecked draft; expected_head implements atomic stale-write protection.

    This low-level function validates structure/integrity, not media. CLI always
    invokes reconcile() first; calling this API is not proof that media were checked.
    """
    validate_receipt(receipt, state)
    state_hash = state['contentHash']
    # No automatic transition policy exists yet. A different current checkpoint
    # needs a separately implemented/authorized transition, not a head overwrite.
    if expected_head is not None and expected_head != state_hash:
        raise ValueError('Different current checkpoint; automatic transition is unsupported.')
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database, timeout=15, isolation_level=None)
    try:
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('BEGIN IMMEDIATE')
        connection.execute('CREATE TABLE IF NOT EXISTS archive_info (singleton INTEGER PRIMARY KEY CHECK(singleton=1), schema TEXT NOT NULL)')
        connection.execute('INSERT OR IGNORE INTO archive_info VALUES (1, ?)', (SCHEMA,))
        if connection.execute('SELECT schema FROM archive_info WHERE singleton=1').fetchone() != (SCHEMA,):
            raise ValueError('Unsupported archive schema.')
        connection.execute('CREATE TABLE IF NOT EXISTS checkpoints (state_hash TEXT PRIMARY KEY, state_json TEXT NOT NULL, created_at TEXT NOT NULL)')
        connection.execute('CREATE TABLE IF NOT EXISTS receipts (receipt_hash TEXT PRIMARY KEY, state_hash TEXT NOT NULL REFERENCES checkpoints(state_hash), receipt_json TEXT NOT NULL)')
        connection.execute('CREATE TABLE IF NOT EXISTS current_checkpoint (singleton INTEGER PRIMARY KEY CHECK(singleton=1), state_hash TEXT NOT NULL REFERENCES checkpoints(state_hash))')
        row = connection.execute('SELECT state_hash FROM current_checkpoint WHERE singleton=1').fetchone()
        actual_head = row[0] if row else None
        if actual_head != expected_head:
            raise ValueError('Stale checkpoint: archive changed during verification. Nothing committed.')
        existing = connection.execute('SELECT state_json FROM checkpoints WHERE state_hash=?', (state_hash,)).fetchone()
        if existing:
            stored = json.loads(existing[0]); verify_state(stored)
            if stored['contentHash'] != state_hash or canonical_bytes(stored['payload']) != canonical_bytes(state['payload']):
                raise ValueError('Stored checkpoint failed integrity verification.')
            stored_receipts = connection.execute('SELECT receipt_hash, receipt_json FROM receipts WHERE state_hash=?', (state_hash,)).fetchall()
            if not stored_receipts:
                raise ValueError('Stored checkpoint lacks verification receipts.')
            for stored_hash, raw_receipt in stored_receipts:
                stored_receipt = json.loads(raw_receipt)
                validate_receipt(stored_receipt, stored)
                if stored_receipt['contentHash'] != stored_hash:
                    raise ValueError('Stored receipt hash mismatch.')
        else:
            connection.execute('INSERT INTO checkpoints VALUES (?, ?, ?)',
                               (state_hash, json.dumps(state, allow_nan=False), datetime.now(timezone.utc).isoformat()))
        # Keep the first envelope for a content ID; later timestamps do not create
        # a new checkpoint. Fresh verification receipts are retained separately.
        connection.execute('INSERT OR IGNORE INTO receipts VALUES (?, ?, ?)',
                           (receipt['contentHash'], state_hash, json.dumps(receipt, allow_nan=False)))
        connection.execute('INSERT OR IGNORE INTO current_checkpoint VALUES (1, ?)', (state_hash,))
        connection.execute('COMMIT')
        return {'status': 'checkpoint-reused' if existing else 'checkpoint-archived',
                'stateHash': state_hash, 'archive': str(database),
                'sessionCountChanged': False, 'evolutionHistoryAdvanced': False,
                'sourceByteMismatchPreserved': True}
    except BaseException:
        if connection.in_transaction:
            connection.execute('ROLLBACK')
        raise
    finally:
        connection.close()


def inspect_archive(database):
    head = read_head(database)
    if head is None:
        raise ValueError('Archive has no checkpoint.')
    with sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True) as connection:
        states = {}
        for key, raw in connection.execute('SELECT state_hash, state_json FROM checkpoints'):
            state = json.loads(raw); verify_state(state)
            if state['contentHash'] != key:
                raise ValueError('Stored state hash mismatch.')
            states[key] = state
        if head not in states:
            raise ValueError('Current checkpoint missing.')
        receipts = 0
        covered = set()
        for key, state_key, raw in connection.execute('SELECT receipt_hash, state_hash, receipt_json FROM receipts'):
            receipt = json.loads(raw)
            validate_receipt(receipt, states[state_key])
            if receipt['contentHash'] != key:
                raise ValueError('Stored receipt hash mismatch.')
            receipts += 1; covered.add(state_key)
        if set(states) != covered:
            raise ValueError('Checkpoint lacks reconciliation receipt.')
    return {'schema': SCHEMA, 'currentCheckpoint': head, 'checkpointCount': len(states),
            'verificationReceiptCount': receipts, 'storedContentHashesVerified': True,
            'mediaRecheckedDuringInspection': False, 'evolutionHistoryAdvanced': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', action='store_true', help='Read and verify stored records without selecting media')
    parser.add_argument('--current', type=Path)
    parser.add_argument('--sample-report', type=Path, default=Path('runtime/audio-sample-check-001/sample-comparison.json'))
    parser.add_argument('--state', type=Path, default=Path('runtime/audio-state-draft-001/audio-state.json'))
    parser.add_argument('--features', type=Path, default=Path('runtime/matched-features-002/features.json'))
    parser.add_argument('--summary', type=Path)
    parser.add_argument('--comparison', type=Path, default=Path('runtime/rate-comparison-001/comparison.json'))
    parser.add_argument('--archive', type=Path, default=Path('runtime/local-draft-checkpoints/checkpoints.sqlite3'))
    args = parser.parse_args()
    try:
        if args.inspect:
            print(json.dumps(inspect_archive(args.archive), indent=2))
            return
        expected = read_head(args.archive)
        current = args.current or choose('Select current WAV to verify and archive the draft checkpoint')
        if not current:
            raise ValueError('Selection cancelled.')
        receipt = reconcile(current, args.sample_report, args.state, args.features,
                            args.summary or args.features.with_name('summary.json'), args.comparison)
        raw = args.state.read_bytes()
        if hashlib.sha256(raw).hexdigest() != receipt['reconciliation']['inputs']['state']['sha256']:
            raise ValueError('State bytes changed after reconciliation.')
        state = json.loads(raw)
        result = archive(args.archive, state, receipt, expected)
        print(json.dumps(result, indent=2))
        print('Local draft archive only. No session, carry, state permissions or original evidence changed.')
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, sqlite3.Error, LineageError) as error:
        parser.exit(1, f'Checkpoint stopped: {error}\n')


if __name__ == '__main__':
    main()
