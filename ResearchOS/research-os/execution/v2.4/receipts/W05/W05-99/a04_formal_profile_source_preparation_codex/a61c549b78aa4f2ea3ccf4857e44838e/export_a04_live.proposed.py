"""Proposed A04 producer-only GLOBAL_EVIDENCE_V1 exporter.

This consumes a Root-sealed LIVE capture after the native children are closed.
It writes four producer parts and current context. The fifth part is a later
independent acceptance review; this exporter cannot create or impersonate it.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

from runtime_w05_live import REPO, BOUNDARY, IDS, GATES, SCENARIOS, \
    pin_raw, read_ref, require, strict_json, verify_bundle


def pin(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(REPO).as_posix(),
            'sha256': hashlib.sha256(raw).hexdigest()}


def put(path, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True,
                      indent=2, allow_nan=False) + '\n').encode('utf-8')
    with path.open('xb') as out:
        out.write(raw)
    return pin(path)


def export(bundle, output):
    require(os.name == 'nt', 'LIVE_WINDOWS_REQUIRED')
    require(output.is_absolute() and not output.exists() and
            output.parent.resolve(strict=True).is_relative_to(
                BOUNDARY.resolve(strict=True)) and
            not output.parent.is_symlink() and not output.parent.is_junction(),
            'FRESH_OUTPUT_SCOPE_REQUIRED')
    verify_bundle(bundle, 'A04')
    registration, _ = read_ref(bundle['root_registration_ref'])
    grant, _ = read_ref(bundle['root_grant_ref'])
    require(registration.get('schema') == 'researchos.w05.a04-root-registration.v1' and
            registration.get('actor_id') == 'codex:/root' and
            registration.get('run_id') == grant.get('run_id') == bundle['run_id'] and
            registration.get('source_commit') == bundle.get('source_commit') and
            registration.get('selected_executor') == bundle.get('executor_id') and
            registration.get('selected_runtime') == bundle.get('selected_runtime') and
            registration.get('fixed_model') == bundle.get('fixed_model') and
            grant.get('registration_ref') == bundle['root_registration_ref'],
            'ROOT_ORIGINAL_REGISTRATION_GRANT_MISMATCH')
    vector = bundle.get('version_vector')
    require(type(vector) is dict and vector.get('schema') ==
            'researchos.w05.version-vector.v1', 'CURRENT_VERSION_VECTOR_MISSING')
    required = ('source_coverage', 'accepted_baseline_ref', 'registered_argv',
                'worktree', 'executor_id', 'verifier_id', 'selected_runtime',
                'fixed_model', 'product_original_refs')
    require(all(key in bundle for key in required), 'CURRENT_CONTEXT_INPUT_MISSING')
    require(bundle['accounting']['status'] in ('UNKNOWN', 'RECORDED'),
            'COST_ACCOUNTING_MISSING')
    require(bundle['verifier_id'] != bundle['executor_id'] and
            bundle['verifier_id'] != 'codex:/root', 'INDEPENDENT_REVIEWER_NOT_RESERVED')
    invocations = []
    for row in bundle['invocations']:
        original, _ = read_ref(row['invocation_ref'])
        require(original.get('schema') == 'researchos.w05.live-invocation.v1' and
                original.get('root_grant_ref') == bundle['root_grant_ref'] and
                original.get('run_id') == bundle['run_id'] and
                original.get('lane') == row['lane'] and
                original.get('cwd') == bundle['worktree'] and
                type(original.get('native_exit')) is int and
                type(original.get('argv')) is list and original['argv'] and
                type(original.get('env_names')) is list,
                'ORIGINAL_INVOCATION_INCOMPLETE')
        pin_raw(original['stdout_ref'])
        pin_raw(original['stderr_ref'])
        invocations.append(original)
    started = min(row['started_at'] for row in invocations)
    ended = max(row['ended_at'] for row in invocations)
    require(started <= ended, 'LIVE_INTERVAL_INVALID')
    output.mkdir(mode=0o700)
    vector_ref = put(output / 'version-vector.json', vector)
    run_ref = put(output / 'run-receipt.json', {
        'schema': 'researchos.w05.run-receipt.v1', 'case_id': 'A04',
        'run_id': bundle['run_id'], 'environment_mode': 'LIVE_WINDOWS',
        **vector['environment'], 'started_at': started, 'ended_at': ended,
        'executor_id': bundle['executor_id'],
        # Reserved identity is later checked against an actual independent message.
        'verifier_id': bundle['verifier_id']})
    version_ref = put(output / 'version-manifest.json', {
        'schema': 'researchos.w05.version-manifest.v1', 'case_id': 'A04',
        'run_id': bundle['run_id'], 'package_version': '2.4.0',
        'code_revision': registration['source_commit'],
        'dirty': registration['dirty'], 'version_vector_ref': vector_ref})
    command_ref = put(output / 'command-receipt.json', {
        'schema': 'researchos.w05.command-receipt.v1', 'case_id': 'A04',
        'run_id': bundle['run_id'], 'command_key': 'test.runtime',
        'registered_argv': bundle['registered_argv'],
        'invocations': bundle['invocations']})
    assertion_ref = put(output / 'assertion-results.json', {
        'schema': 'researchos.w05.assertion-results.v1', 'case_id': 'A04',
        'run_id': bundle['run_id'], 'assertions': bundle['assertions']})
    context_ref = put(output / 'current-context.json', {
        'schema': 'researchos.w05.current-context.v1', 'task_id': 'W05',
        'step_id': 'W05-99', 'case_id': 'A04', 'mode': 'LIVE_WINDOWS',
        'run_id': bundle['run_id'], 'executor_id': bundle['executor_id'],
        'selected_runtime': bundle['selected_runtime'],
        'fixed_model': bundle['fixed_model'],
        'worktree': bundle['worktree'], 'registered_argv': bundle['registered_argv'],
        'created_at': datetime.now(timezone.utc).isoformat(),
        'root_grant_ref': bundle['root_grant_ref'],
        'acceptance_baseline_ref': bundle['accepted_baseline_ref'],
        'product_original_refs': bundle['product_original_refs'],
        'accounting': bundle['accounting'],
        'version_vector': vector, 'source_coverage': bundle['source_coverage'],
        'global_evidence_refs': {'run_receipt': run_ref,
                                 'version_manifest': version_ref,
                                 'command_receipt': command_ref,
                                 'assertion_results': assertion_ref}})
    return {'schema': 'researchos.w05.a04-producer-export.v1',
            'context_ref': context_ref, 'run_receipt_ref': run_ref,
            'version_manifest_ref': version_ref,
            'command_receipt_ref': command_ref,
            'assertion_results_ref': assertion_ref,
            'acceptance_receipt_ref': None,
            'independent_review_status': 'NOT_RUN',
            'cost_status': bundle['accounting']['status'],
            'cost_amount_usd': bundle['accounting']['amount_usd'],
            'formal_accepted_count': 0}


def main():
    source = os.environ.get('RESEARCHOS_W05_LIVE_BUNDLE_PATH')
    digest = os.environ.get('RESEARCHOS_W05_LIVE_BUNDLE_SHA256')
    target = os.environ.get('RESEARCHOS_W05_EXPORT_DIR')
    require(source and digest and target and len(digest) == 64,
            'ROOT_BUNDLE_AND_FRESH_EXPORT_REQUIRED')
    path = Path(source)
    require(path.is_absolute() and path.resolve(strict=True).is_relative_to(
            BOUNDARY.resolve(strict=True)), 'ROOT_BUNDLE_PATH')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'ROOT_BUNDLE_CHANGED')
    result = export(strict_json(raw), Path(target))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'NOT_RUN', 'reason': type(exc).__name__ + ':' + str(exc),
                          'formal_accepted_count': 0}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(3)
