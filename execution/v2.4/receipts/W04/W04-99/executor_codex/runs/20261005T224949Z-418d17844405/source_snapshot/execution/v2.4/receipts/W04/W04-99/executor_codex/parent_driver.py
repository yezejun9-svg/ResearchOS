"""W04 exact-selector evidence reader; fresh collection is explicitly enabled later."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from evidence_module import assertion_records, digest, enrolled_sources, exact_assertions, strict_json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
EXPECTED = HERE / 'expected.json'


def read(path: Path):
    return strict_json(path.read_bytes())


def verified_ref(ref: dict) -> Path:
    if not isinstance(ref, dict) or not isinstance(ref.get('path'), str):
        raise ValueError('invalid evidence reference')
    relative = Path(ref['path'])
    target = (ROOT / relative).resolve()
    if relative.is_absolute() or relative.drive or '..' in relative.parts or not target.is_relative_to(ROOT):
        raise ValueError('evidence reference escapes repository')
    if not target.is_file() or digest(target) != ref.get('sha256'):
        raise ValueError('evidence reference missing or changed: ' + ref['path'])
    return target


def selector(key: str, task: str, check: str, case: str, expected: dict) -> tuple[str, list[str]]:
    if task != 'W04' or bool(check) == bool(case):
        raise ValueError('one exact W04 check or case required')
    if case:
        if {'command_key': key, 'case_id': case} not in expected['case_entries']:
            raise ValueError('wrong case command binding')
        return case, expected['cases'][case]
    if {'command_key': key, 'check_id': check} not in expected['gate_entries']:
        raise ValueError('wrong parent gate command binding')
    return check, [check]


def verified_proof(expected: dict) -> tuple[dict, list[dict], dict]:
    pointer = read(HERE / 'current_proof.json')
    proof_ref = pointer['proof_ref']
    proof_path = verified_ref(proof_ref)
    proof = read(proof_path)
    if proof.get('schema') != 'researchos.w04.observed-proof.v1' or proof.get('status') != 'PASS':
        raise ValueError('current proof has not passed')
    if proof.get('mode') != 'FIXTURE' or proof.get('owner_step') != 'W04-99':
        raise ValueError('current proof owner/mode mismatch')
    vector = read(verified_ref(proof['version_vector_ref']))
    for group in ('spec_files', 'source_files', 'input_files', 'lock_files', 'tool_files'):
        if not isinstance(vector.get(group), list) or not vector[group]:
            raise ValueError('incomplete version vector: ' + group)
        for ref in vector[group]:
            verified_ref(ref)
    actual_sources=[p.relative_to(ROOT).as_posix() for p in enrolled_sources(ROOT,HERE)]
    if actual_sources!=[ref['path'] for ref in vector['source_files']]:
        raise ValueError('source inventory changed, including added or removed files')
    for ref in vector['tool_files']:
        identity=read(verified_ref(ref))
        verified_ref(identity['locked_ref'])
        for tool in identity['tools']:
            if digest(Path(tool['path']))!=tool['sha256']:
                raise ValueError('tool identity changed')
    invocation = read(verified_ref(proof['go_invocation_ref']))
    if invocation.get('exit_code') != 0 or invocation.get('mode') != 'FIXTURE':
        raise ValueError('observed Go invocation did not pass')
    # The binary is external to the evidence directory; bind it independently.
    binary = Path(invocation['actual_argv'][0])
    if not binary.is_absolute() or digest(binary) != invocation.get('executable_sha256'):
        raise ValueError('observed Go tool changed')
    raw = verified_ref(invocation['stdout'])
    verified_ref(invocation['stderr'])
    records, passed = assertion_records(ROOT, raw)
    rosters = expected.get('go_test_rosters')
    if not isinstance(rosters, dict) or not rosters:
        raise ValueError('registered current test roster absent')
    if proof.get('go_test_rosters') != rosters:
        raise ValueError('observed test roster differs from current driver')
    observed = []
    for test, ids in rosters.items():
        if test not in passed:
            raise ValueError('required Go test did not pass: ' + test)
        if ids:
            observed.extend(exact_assertions(records, ids, test))
    package_invocation = read(verified_ref(proof['package_invocation_ref']))
    if package_invocation.get('exit_code') != 0 or package_invocation.get('mode') != 'FIXTURE':
        raise ValueError('package validation did not pass')
    python = Path(package_invocation['actual_argv'][0])
    if digest(python) != package_invocation['executable_sha256']:
        raise ValueError('locked Python changed')
    package_raw = verified_ref(package_invocation['stdout'])
    verified_ref(package_invocation['stderr'])
    package_result = read(package_raw)
    expected_package = {'status': 'PASS', 'scope': 'SPECIFICATION_PACKAGE_ONLY', 'product_tests': 'NOT_RUN'}
    if any(package_result.get(k) != v for k, v in expected_package.items()):
        raise ValueError('package validator boundary changed')
    observed.append({'assertion_id': 'A01-03', 'status': 'PASS', 'expected': expected_package,
                     'actual': {k: package_result[k] for k in expected_package}, 'evidence': package_result,
                     'raw_evidence_refs': [{**package_invocation['stdout'], 'locator': {'json_pointer': '/status'}}]})
    return proof, observed, proof_ref


def report(key: str, task: str, check: str, case: str) -> dict:
    expected = read(EXPECTED)
    selected, ids = selector(key, task, check, case, expected)
    proof, rows, proof_ref = verified_proof(expected)
    needed = expected['cases'][case] if case else expected['gate_requirements'][check]
    found = [row for row in rows if row['assertion_id'] in needed]
    if sorted(row['assertion_id'] for row in found) != sorted(needed):
        raise ValueError('required exact evidence absent or duplicated')
    return {'schema': 'researchos.w04.exact-result.v1', 'task_id': task,
            'step_id': 'W04-99', 'command_key': key, 'check_id': check or None,
            'case_id': case or None, 'mode': 'FIXTURE', 'status': 'PASS',
            'assertion_ids': ids, 'assertions': len(ids), 'run_id': proof['run_id'],
            'evidence_reuse': 'READ_ONLY_EXACT_CURRENT_OBSERVED_PROOF',
            'proof_ref': proof_ref, 'assertion_results': found,
            'authority': 'EXECUTION_EVIDENCE_NOT_INDEPENDENT_ACCEPTANCE'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command_key', choices=['test.context', 'test.domain', 'package.validate'])
    args = parser.parse_args()
    try:
        result = report(args.command_key, os.environ.get('RESEARCHOS_TASK_ID', ''),
                        os.environ.get('RESEARCHOS_CHECK_ID', ''), os.environ.get('RESEARCHOS_CASE_ID', ''))
        code = 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {'task_id': os.environ.get('RESEARCHOS_TASK_ID'),
                  'case_id': os.environ.get('RESEARCHOS_CASE_ID') or None,
                  'check_id': os.environ.get('RESEARCHOS_CHECK_ID') or None,
                  'command_key': args.command_key, 'mode': 'FIXTURE', 'status': 'FAIL',
                  'assertion_ids': [], 'assertions': 0, 'error': str(error)}
        code = 1
    print(json.dumps(result, ensure_ascii=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
