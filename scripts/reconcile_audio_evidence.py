"""Link a resolved draft chain to freshly verified decoded-sample equality; never replace hashes."""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path

try:
    from scripts.compare_audio_samples import compare, digest, choose
    from scripts.resolve_state_evidence import resolve_evidence
    from scripts.review_session_transition import same_json
    from scripts.adapt_lineage import canonical_bytes, LineageError
except ModuleNotFoundError:
    from compare_audio_samples import compare, digest, choose
    from resolve_state_evidence import resolve_evidence
    from review_session_transition import same_json
    from adapt_lineage import canonical_bytes, LineageError


def reconcile(current, sample_report, state, features, summary, comparison):
    paths = dict(zip(('current', 'sampleReport', 'state', 'features', 'summary', 'comparison'),
                     map(Path, (current, sample_report, state, features, summary, comparison))))
    before = {key: digest(path) for key, path in paths.items()}
    submitted = json.loads(paths['sampleReport'].read_text(encoding='utf-8'))
    resolved = resolve_evidence(state, features, summary, comparison)
    print('Rechecking current WAV and identity-control samples...', flush=True)
    fresh = compare(current, comparison)
    if not same_json(submitted, fresh):
        raise ValueError('Saved sample comparison differs from the fresh comparison. No reconciliation produced.')
    if fresh['status'] != 'decoded-samples-identical':
        raise ValueError('Decoded samples differ; equality reconciliation refused.')
    source = json.loads(paths['state'].read_text(encoding='utf-8'))['payload']['sourceRef']['sha256']
    if fresh['declaredEarlierSourceSha256'] != source:
        raise ValueError('Sample comparison and state refer to different earlier source hashes.')
    if fresh['current']['sha256'] == source:
        raise ValueError('No source-byte mismatch exists; use the strict evidence resolver instead.')
    for key, path in paths.items():
        if digest(path) != before[key]:
            raise ValueError('Input changed while reconciling; no reconciliation produced.')
    report = {'schema': 'AUEVO-AudioEvidenceReconciliation/v0.1',
              'status': 'source-bytes-differ-decoded-control-samples-identical',
              'stateRef': resolved['resolution']['stateRef'],
              'inputs': {key: {'filename': path.name, 'sha256': before[key]} for key, path in paths.items()},
              'earlierSourceSha256': source, 'currentSourceSha256': fresh['current']['sha256'],
              'strictSourceByteMatch': False, 'decodedControlSampleMatch': True,
              'measurementChainResolution': resolved, 'freshSampleComparison': fresh,
              'historyAdvanced': False, 'authorizedForHistoryCommit': False,
              'stateFilesModified': False, 'originalHashReplaced': False,
              'limitations': ['Equality is against the hash-linked identity control; earlier original bytes are unavailable.',
                  'Container byte changes are not located or explained by this report.',
                  'Hashes and local rechecks do not authenticate authorship, capture provenance or rights.',
                  'This report does not bypass strict source-byte validation or authorize persistent history.']}
    content_hash = hashlib.sha256(canonical_bytes(report)).hexdigest()
    return {'reconciliationId': 'audio-reconciliation:sha256:'+content_hash,
            'contentHash': content_hash, 'createdAt': datetime.now(timezone.utc).isoformat(),
            'reconciliation': report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', type=Path)
    parser.add_argument('--sample-report', type=Path, default=Path('runtime/audio-sample-check-001/sample-comparison.json'))
    parser.add_argument('--state', type=Path, default=Path('runtime/audio-state-draft-001/audio-state.json'))
    parser.add_argument('--features', type=Path, default=Path('runtime/matched-features-002/features.json'))
    parser.add_argument('--summary', type=Path)
    parser.add_argument('--comparison', type=Path, default=Path('runtime/rate-comparison-001/comparison.json'))
    parser.add_argument('--output', type=Path, default=Path('runtime/audio-reconciliation-001'))
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError('Output exists; select a new --output directory.')
        current = args.current or choose('Select current aujoulevol.wav for read-only reconciliation')
        if not current:
            raise ValueError('Selection cancelled.')
        result = reconcile(current, args.sample_report, args.state, args.features,
                           args.summary or args.features.with_name('summary.json'), args.comparison)
        page = '<!doctype html><meta charset="utf-8"><title>Audio evidence reconciliation</title><h1>Audio evidence reconciliation</h1><p>Source bytes differ. Decoded samples match the verified identity control. Both hashes are preserved; history remains unchanged.</p><pre>'+html.escape(json.dumps(result, indent=2))+'</pre>'
        # All checks and serialization precede exclusive output creation.
        encoded = json.dumps(result, indent=2, allow_nan=False)+'\n'
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output/'reconciliation.json').write_text(encoded, encoding='utf-8')
        (args.output/'reconciliation.html').write_text(page, encoding='utf-8')
        print('Reconciliation recorded; strict source-byte mismatch preserved.')
        print('Open '+str(args.output/'reconciliation.html'))
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, LineageError) as error:
        parser.exit(1, f'Reconciliation stopped: {error}\n')


if __name__ == '__main__':
    main()
