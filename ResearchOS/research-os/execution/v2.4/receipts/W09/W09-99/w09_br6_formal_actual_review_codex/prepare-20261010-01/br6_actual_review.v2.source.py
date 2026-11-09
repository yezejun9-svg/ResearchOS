"""Future Backup review entry. Publication requires a later actual-review task.

This file launches no processes and changes no Root/Canon/Scope file. It never
creates Root issuance, a Root capture, an owner AcceptanceReceipt or a grant.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
PLAN = ROOT.parent / 'ResearchOS_Implementation_Package_v2.4/contracts/execution.plan.json'
REVIEWER = '/root/backup_regression_resources'
EXECUTOR = 'codex:/root'
SHA = re.compile(r'[0-9a-f]{64}')
ROUTES = (
    ('test.retrieval', 'W09-G01', ''),
    ('test.retrieval', 'W09-G02', ''),
    ('test.research.fixture', '', 'C19'),
    ('test.retrieval', '', 'C19'),
    ('test.retrieval', '', 'A06'),
    ('test.security', '', 'A06'),
)
GLOBAL_TYPES = {'run_receipt', 'version_manifest', 'command_receipt', 'assertion_results'}
GUARD = ROOT / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
GUARD_SHA = 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
BASIS_SHA = '9a9a22ba57f4a3c36be5479ac2887b55f6ba1eeaa2cd4a44e41e5cdcfb3b4776'

def absolute_ref(ref):
    path = Path(ref['path'])
    return dict(ref, path=str(path if path.is_absolute() else ROOT / path))

def same_ref(left, right, canonical):
    return (canonical(absolute_ref(left)['path']) == canonical(absolute_ref(right)['path'])
            and left['sha256'] == right['sha256'] and left['bytes'] == right['bytes'])

def need(condition, label):
    if not condition:
        raise ValueError(label)

def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('NONFINITE_JSON')))

def shape_ref(ref, fields):
    need(type(ref) is dict and set(ref) == set(fields), 'EXACT_REFERENCE_FIELDS')
    need(type(ref['path']) is str and ref['path'] and '\x00' not in ref['path'], 'REFERENCE_PATH')
    need(type(ref['sha256']) is str and SHA.fullmatch(ref['sha256']) is not None, 'REFERENCE_HASH')
    if 'bytes' in fields:
        need(type(ref['bytes']) is int and ref['bytes'] >= 0, 'REFERENCE_BYTES')
    return ref

def context_ref(ref):
    shape_ref(ref, ('path', 'sha256'))
    value = ref['path']
    need('\\' not in value and ':' not in value and not PurePosixPath(value).is_absolute()
         and not PureWindowsPath(value).drive
         and all(part not in ('', '.', '..') for part in value.split('/'))
         and value.startswith('execution/v2.4/receipts/W09/W09-99/'), 'CONTEXT_REPO_POSIX2')
    return ref

def route(row):
    return tuple(row[key] for key in ('command_key', 'check_id', 'case_id'))

def utc():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def pin(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(path, value):
    with Path(path).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)

def load_verified_module(ref, name):
    shape_ref(ref, ('path', 'sha256', 'bytes'))
    raw = Path(ref['path']).read_bytes()
    need(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'MODULE_PIN')
    spec = importlib.util.spec_from_file_location(name, ref['path'])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(raw, ref['path'], 'exec'), module.__dict__)
    return module

def consumer_closure(document, context):
    need(document.get('schema') == 'researchos.w09-bridge-consumers.v1'
         and document.get('formal_acceptance') is False
         and document.get('producer_rerun') is False
         and document.get('c19_policy') == 'RUN_CURRENT_CM40', 'CONSUMER_RESULT_IDENTITY')
    need(document.get('registered_commands') == context['registered_commands'], 'SAME_SIX_CONSUMERS')
    executed = document.get('executed_consumer_routes')
    need(type(executed) is list and len(executed) == 6
         and {tuple(item) for item in executed} == set(ROUTES), 'SIX_CURRENT_ROUTES')
    records = document.get('processes')
    need(type(records) is list and len(records) == 6
         and {tuple(item['route']) for item in records} == set(ROUTES), 'SIX_PROCESS_OBSERVATIONS')
    for record in records:
        observation = record.get('observation')
        need(type(observation) is dict and type(record.get('actual_exit')) is int
             and type(observation.get('actual_exit')) is int
             and record['actual_exit'] == observation.get('actual_exit') == 0
             and observation.get('timed_out') is False and observation.get('error') is None,
             'ACTUAL_CONSUMER_EXIT')
        cleanup = observation.get('job_cleanup', {})
        need(cleanup.get('job_idle_confirmed') is True
             and type(cleanup.get('active_processes_last_observed')) is int
             and cleanup['active_processes_last_observed'] == 0
             and cleanup.get('handles_closed') is True
             and cleanup.get('primary_exit_confirmed') is True
             and cleanup.get('assigned_before_resume') is True and cleanup.get('errors') == [],
             'CONSUMER_OWNED_JOB_CLOSED')
        for key in ('stdout_ref', 'stderr_ref'):
            shape_ref(record[key], ('path', 'sha256', 'bytes'))
    return records

def validate_bundle(bundle):
    need(type(bundle) is dict and set(bundle) == {
        'schema', 'context_ref', 'consumer_result_ref', 'root_publication_refs',
        'current4_refs', 'resource_refs', 'native_mode_qualification_ref'}, 'BUNDLE_FIELDS')
    need(bundle['schema'] == 'researchos.w09-br6-formal-actual-review-input.v1', 'BUNDLE_SCHEMA')
    context_ref(bundle['context_ref'])
    shape_ref(bundle['consumer_result_ref'], ('path', 'sha256', 'bytes'))
    shape_ref(bundle['native_mode_qualification_ref'], ('path', 'sha256', 'bytes'))
    pubs = bundle['root_publication_refs']
    need(type(pubs) is dict and set(pubs) == {'scope', 'owner', 'roles', 'actual_root_captures'}, 'ROOT_PUBLICATION_FIELDS')
    for key in ('scope', 'owner', 'roles'):
        shape_ref(pubs[key], ('path', 'sha256', 'bytes'))
    need(type(pubs['actual_root_captures']) is list and pubs['actual_root_captures'], 'ACTUAL_ROOT_CAPTURE_OPEN')
    for ref in pubs['actual_root_captures']:
        shape_ref(ref, ('path', 'sha256', 'bytes'))
    need(type(bundle['current4_refs']) is list and len(bundle['current4_refs']) == 4, 'CURRENT4_REQUIRED')
    for ref in bundle['current4_refs']:
        shape_ref(ref, ('path', 'sha256', 'bytes'))
    need(type(bundle['resource_refs']) is list and bundle['resource_refs'], 'RESOURCE_MANIFEST_REQUIRED')
    for ref in bundle['resource_refs']:
        shape_ref(ref, ('path', 'sha256', 'bytes'))
    return bundle

def review_actual(input_ref, output_root):
    """Call only after Root's six current-CM40 consumers and assemble close.

    Root captures the actual Backup FINAL after return. Its capture/index,
    issuance and prospective owner remain later Root-only obligations.
    """
    shape_ref(input_ref, ('path', 'sha256', 'bytes'))
    observed_input = pin(input_ref['path'])
    need(observed_input['sha256'] == input_ref['sha256'] and observed_input['bytes'] == input_ref['bytes'], 'INPUT_PIN')
    bundle = validate_bundle(strict(Path(input_ref['path']).read_bytes()))
    out = Path(output_root)
    need(out.is_absolute() and out.parent.resolve(strict=True) == HERE and not out.exists(), 'NEW_REVIEW_OUTPUT')
    out.mkdir()
    guard_module = load_verified_module({'path': str(GUARD), 'sha256': GUARD_SHA, 'bytes': 11404}, 'br6_actual_guard')
    guard = guard_module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    primary = None
    draft = None
    reader = None
    try:
        resources = bundle['resource_refs']
        required = [input_ref, bundle['consumer_result_ref'], bundle['native_mode_qualification_ref'],
                    *bundle['current4_refs'], *bundle['root_publication_refs']['actual_root_captures'],
                    *[bundle['root_publication_refs'][key] for key in ('scope', 'owner', 'roles')]]
        authorized = {guard_module._canonical(ref['path']): ref for ref in resources}
        need(len(authorized) == len(resources), 'RESOURCE_DUPLICATE_PATH')
        for ref in required:
            held = authorized.get(guard_module._canonical(absolute_ref(ref)['path']))
            need(held is not None and same_ref(held, ref, guard_module._canonical), 'INPUT_NOT_HELD')
        context_path = ROOT / bundle['context_ref']['path']
        held_context = authorized.get(guard_module._canonical(str(context_path)))
        need(held_context is not None and held_context['sha256'] == bundle['context_ref']['sha256'], 'CONTEXT_NOT_HELD')
        basis_ref = {'path': str(HERE / 'basis.json'), 'sha256': BASIS_SHA, 'bytes': 31811}
        held_basis = authorized.get(guard_module._canonical(basis_ref['path']))
        need(held_basis is not None and same_ref(held_basis, basis_ref, guard_module._canonical), 'BASIS_NOT_HELD')
        need(pin(basis_ref['path']) == basis_ref, 'BASIS_PIN')
        basis = strict((HERE / 'basis.json').read_bytes())
        original_qualification = next(ref for ref in basis['source_refs'] if Path(ref['path']).name == 'decision.json')
        need(same_ref(bundle['native_mode_qualification_ref'], original_qualification, guard_module._canonical),
             'EXACT_EXISTING_NF6_QUALIFICATION')
        canon_names = ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']
        for name, ref in zip(canon_names, bundle['current4_refs']):
            need(guard_module._canonical(absolute_ref(ref)['path']) ==
                 guard_module._canonical(str(ROOT / 'execution/v2.4' / name)), 'EXACT_DYNAMIC_CURRENT4')
        source = {Path(ref['path']).name: ref for ref in basis['source_refs']
                  if Path(ref['path']).name in ('formal_case_index.py', 'formal_profile_w09.py')}
        for ref in source.values():
            held_source = authorized.get(guard_module._canonical(ref['path']))
            need(held_source is not None and same_ref(held_source, ref, guard_module._canonical), 'MAIN_SOURCE_NOT_HELD')
        guard.acquire(resources)
        api = load_verified_module(source['formal_case_index.py'], 'br6_formal_api')
        profile = load_verified_module(source['formal_profile_w09.py'], 'br6_formal_profile')
        shim = api._profile_api()
        reader = api.Reader(ROOT)
        reader.w09_audit_ranges, reader.w09_owned_inventories = [], []
        context = reader.document(bundle['context_ref'])
        api.require(context.get('schema') == profile.SCHEMAS['context']
                    and context.get('task_id') == 'W09' and context.get('step_id') == 'W09-99'
                    and context.get('executor_id') == EXECUTOR, 'SCHEMA', 'current Root W09 context')
        consumer = strict(guard.get_buffer(bundle['consumer_result_ref']['path']))
        consumer_closure(consumer, context)
        qualification = strict(guard.get_buffer(bundle['native_mode_qualification_ref']['path']))
        api.require(qualification.get('schema') == 'researchos.w09-nf6-actual-independent-review-decision.v1'
                    and qualification.get('decision') == 'QUALIFIED_CURRENT_NF6_NATIVE_AND_SIX_MODES_COMPONENT_ONLY',
                    'NATIVE_COMPONENT_QUALIFICATION', 'six Modes do not replace formal consumers')
        baseline = reader.ref(context['acceptance_baseline_ref'])
        api.require(baseline.name == 'acceptance.json'
                    and context['acceptance_baseline_ref']['sha256'] == api.FROZEN_HASHES['acceptance.json'],
                    'FROZEN_BASELINE', 'W09')
        pinned = profile._vector(shim, reader, context)
        for row in context['registered_commands']:
            process = next(item for item in consumer['processes'] if tuple(item['route']) == route(row))
            raw_ref = process['stdout_ref']
            raw = guard.get_buffer(absolute_ref(raw_ref)['path'])
            lines = raw.splitlines()
            api.require(len(lines) == 1, 'DISPATCH_SUMMARY', str(route(row)))
            summary = strict(lines[0])
            receipt_path = reader.ref(row['receipt_ref'], 'execution/invocations/')
            summary_path = Path(summary['receipt'])
            if not summary_path.is_absolute():
                summary_path = ROOT / summary_path
            api.require(summary_path.resolve(strict=True) == receipt_path, 'PROCESS_RECEIPT_LINK', str(route(row)))
            receipt = reader.read(receipt_path)
            api.require(receipt.get('registered_command_revision') ==
                        pinned[reader.path('execution/v2.4/commands.json')],
                        'RUN_CURRENT_CM40', 'all six consumers use this context registry')
        registry = profile._role_registry(shim, reader, context)
        api.require(registry['roles']['verifier'] == REVIEWER
                    and registry['roles']['executor'] == EXECUTOR
                    and registry['roles']['assembler'] == EXECUTOR, 'INDEPENDENT_ACTOR', REVIEWER)
        role_ref = context['role_policy']['registry_ref']
        api.require(same_ref(role_ref, bundle['root_publication_refs']['roles'], guard_module._canonical),
                    'ROLE_PUBLICATION_BINDING', 'Root actual roles')
        assembly = next(proof for proof in registry['provenance'] if proof['role'] == 'EVIDENCE_ASSEMBLER')
        owner_raw = assembly['raw_ref']
        owner_path = reader.ref({key: owner_raw[key] for key in ('path', 'sha256')})
        owner_ref = bundle['root_publication_refs']['owner']
        api.require(same_ref(pin(owner_path), owner_ref, guard_module._canonical), 'OWNER_PUBLICATION_BINDING', 'actual assembler')
        assembly_owner = reader.read(owner_path)
        api.require(same_ref(assembly_owner['scope_ref'], bundle['root_publication_refs']['scope'], guard_module._canonical),
                    'SCOPE_PUBLICATION_BINDING', 'actual assembly Scope')
        role_path = reader.ref({key: role_ref[key] for key in ('path', 'sha256')})
        api.require(pinned.get(role_path) == role_ref['sha256'], 'ROLE_POLICY_UNPINNED', 'vector')
        plan = reader.read(PLAN.resolve(strict=True))
        step = next(row for row in plan['steps'] if row['id'] == 'W09-99')
        state = reader.read(reader.path('execution/v2.4/step_state.json'))
        statuses = {row['id']: row['status'] for row in state['steps']}
        api.require(all(statuses.get(dep) == 'ACCEPTED' for dep in step['dependencies']), 'DEPENDENCY', 'W09 parent')
        closure = profile._trusted_closure(shim, reader, pinned)
        router = profile._router_contract(shim, reader, pinned)
        producer_sources = profile._producer_sources(shim, reader, pinned)
        outputs, facts = profile._dispatches(shim, reader, context, pinned, closure, router, plan, producer_sources, registry)
        global_rows = profile._global(shim, reader, context, outputs, facts, {'reviewer_id': REVIEWER})
        global_runs = {case: reader.document(context['global_evidence_refs'][case]['run_receipt']) for case in ('C19', 'A06')}
        issued_at = utc()
        profile._review_execution_cutoff(shim, outputs, global_runs, context['created_at'], issued_at)
        verdicts = [copy.deepcopy(global_rows[ident]) for ident in (*profile.IDS['C19'], *profile.IDS['A06'])]
        for ident in ('W09-G01', 'W09-G02'):
            item = next(value for key, value in outputs.items() if key[1] == ident)
            raw = dict(item['report'], locator={'json_pointer': '/assertion_results'})
            actual = profile._raw(shim, reader, raw)
            verdicts.append({'id': ident, 'status': 'PASS', 'mode': item['mode'], 'run_id': item['run_id'],
                             'actual': actual, 'raw_evidence_refs': [raw]})
        for inventory in reader.w09_owned_inventories:
            api.require(api._owned_inventory(reader, inventory['directory'], inventory['members']) == inventory,
                        'OWNED_INVENTORY_CHANGED', inventory['directory'])
        reader.finish()
        for path, digest in reader.read_hashes.items():
            ref = authorized.get(guard_module._canonical(str(path)))
            need(ref is not None and ref['sha256'] == digest, 'READER_INPUT_NOT_HELD')
        draft = {'schema': 'researchos.w09.independent-review.v1', 'task_id': 'W09', 'step_id': 'W09-99',
                 'run_id': context['run_id'], 'reviewer_id': REVIEWER, 'issuer_id': REVIEWER,
                 'executor_id': context['executor_id'], 'context_ref': bundle['context_ref'],
                 'issued_at': issued_at, 'decision': 'ACCEPTED', 'missing': [], 'failed': [], 'verdicts': verdicts,
                 **{key: copy.deepcopy(context[key]) for key in
                    ('acceptance_baseline_ref', 'version_vector', 'registered_commands', 'global_evidence_refs')}}
    except BaseException as exc:
        primary = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        cleanup = guard.close()
        cleanup_ref = save(out / 'SourceGuard.closed.json', cleanup)
        if primary is not None:
            save(out / 'review.failure.json', {'primary_error': primary, 'SourceGuard_ref': cleanup_ref,
                                              'review_ref': None, 'Root_issuance_ref': None})
    need(primary is None, 'ACTUAL_REVIEW_FAILED:' + repr(primary))
    need(cleanup['closed'] and cleanup['retained_handles_count'] == 0 and cleanup['errors'] == [], 'GUARD_NOT_CLOSED')
    need(draft is not None, 'NO_VERIFIED_REVIEW')
    review_ref = save(out / 'independent-review.json', draft)
    return {'schema': 'researchos.w09-br6-independent-review-delivery.v1', 'review_ref': review_ref,
            'context_ref': bundle['context_ref'], 'reviewer_id': REVIEWER, 'SourceGuard_ref': cleanup_ref,
            'Root_issuance_ref': None, 'Root_capture_ref': None, 'formal_acceptance_written': False,
            'Root_check_and_derive': 'PENDING_TRUE_FINAL_CAPTURE_AND_ROOT_ONLY_ISSUANCE'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--input-sha256', required=True)
    parser.add_argument('--input-bytes', required=True, type=int)
    parser.add_argument('--output-root', required=True)
    args = parser.parse_args()
    result = review_actual({'path': args.input, 'sha256': args.input_sha256, 'bytes': args.input_bytes}, args.output_root)
    print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
    return 0

if __name__ == '__main__':
    code = main()
    print('ROOT_PYTHON_EXIT=' + str(code))
    sys.exit(code)
