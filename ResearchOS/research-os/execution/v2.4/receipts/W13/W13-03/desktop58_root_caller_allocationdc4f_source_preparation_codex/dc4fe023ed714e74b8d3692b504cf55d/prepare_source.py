from pathlib import Path
import ast
import difflib
import hashlib
import json

ACTOR = 'codex:/root/f08_whole_scope_review'
BASE = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_root_caller_allocationdc4f_source_preparation_codex/dc4fe023ed714e74b8d3692b504cf55d")
SEED = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_root_caller_allocation72ff_source_preparation_codex/7c863730e8d444ada5196d332e70cbc8/root-launch-once.desktop58.allocated72ff.proposed.py')
NEW_UID = 'dc4fe023ed714e74b8d3692b504cf55d'
ROOT_ALLOCATED_OUT = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_root_terminal_closure_codex/baaf93516e9d42e2b583972e5a30df91')
REG = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r336-dc4fe023ed714e74b8d3692b504cf55d')
SEED_SHA = 'f56365f65ba5fec5d92ea262383deabd30f4e1aa3cb107cc2eeb1f7d4f4f110d'
SEED_BYTES = 7250

def pin(path):
    raw = path.read_bytes()
    return {'path': path.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def write_bytes(name, raw):
    with (BASE / name).open('xb') as stream:
        stream.write(raw)
    return pin(BASE / name)

def write_json(name, value):
    return write_bytes(name, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

raw = SEED.read_bytes()
assert len(raw) == SEED_BYTES and hashlib.sha256(raw).hexdigest() == SEED_SHA, 'Seed exact byte pin'
edits = [
    (
        b"REGISTRATION = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-72ff32d0d24a42c4a8effd849d54f882'",
        b"REGISTRATION = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r336-dc4fe023ed714e74b8d3692b504cf55d'",
    ),
    (
        b"AUTH_ROOT = DESKTOP_RECEIPTS / 'desktop58_finite_authorization_codex/72ff32d0d24a42c4a8effd849d54f882'",
        b"AUTH_ROOT = DESKTOP_RECEIPTS / 'desktop58_finite_authorization_codex/dc4fe023ed714e74b8d3692b504cf55d'",
    ),
    (b"RUN_UUID = '72ff32d0d24a42c4a8effd849d54f882'", b"RUN_UUID = 'dc4fe023ed714e74b8d3692b504cf55d'"),
    (
        b"OUT = Path(sys.argv[3])\n",
        b"OUT = Path(sys.argv[3])\nneed(OUT == DESKTOP_RECEIPTS / 'desktop58_root_terminal_closure_codex/baaf93516e9d42e2b583972e5a30df91', 'Fixed Root allocated caller output')\n",
    ),
]
candidate = raw
for before, after in edits:
    assert candidate.count(before) == 1, 'Exact edit single occurrence'
    candidate = candidate.replace(before, after, 1)
restored = candidate
for before, after in reversed(edits):
    assert restored.count(after) == 1, 'Exact inverse single occurrence'
    restored = restored.replace(after, before, 1)
assert restored == raw, 'Whole-file byte inverse'
old_ast = ast.parse(raw.decode('utf-8'))
new_ast = ast.parse(candidate.decode('utf-8'))
old_defs = {node.name: node for node in old_ast.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
new_defs = {node.name: node for node in new_ast.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
definition_checks = []
old_lines = raw.decode('utf-8').splitlines(keepends=True)
new_lines = candidate.decode('utf-8').splitlines(keepends=True)
for name, old_node in old_defs.items():
    new_node = new_defs[name]
    old_block = ''.join(old_lines[old_node.lineno - 1:old_node.end_lineno]).encode('utf-8')
    new_block = ''.join(new_lines[new_node.lineno - 1:new_node.end_lineno]).encode('utf-8')
    definition_checks.append({
        'name': name, 'byte_equal': old_block == new_block,
        'ast_equal': ast.dump(old_node, include_attributes=False) == ast.dump(new_node, include_attributes=False),
        'old_line': old_node.lineno, 'new_line': new_node.lineno,
    })
assert set(old_defs) == set(new_defs) and all(x['byte_equal'] and x['ast_equal'] for x in definition_checks)
# Unmodified launch and receipt tail is a direct byte identity, not an executed test.
tail = b"scope_path = REGISTRATION / 'scope_registration.json' "
assert raw[raw.index(tail):] == candidate[candidate.index(tail):], 'Scope/read/launch/raw/first-cause tail unchanged'
checks = {
    'seed_exact_pin': True,
    'whole_file_inverse': restored == raw,
    'logical_edit_count_is_four': len(edits) == 4,
    'all_three_definitions_byte_ast_unchanged': len(definition_checks) == 3 and all(x['byte_equal'] and x['ast_equal'] for x in definition_checks),
    'all_scope_launch_receipt_tail_bytes_unchanged': raw[raw.index(tail):] == candidate[candidate.index(tail):],
    'old_run_uid_absent': b'72ff32d0d24a42c4a8effd849d54f882' not in candidate,
    'new_run_uid_three_occurrences': candidate.count(NEW_UID.encode('ascii')) == 3,
    'fixed_future_out_one_occurrence': candidate.count(b'baaf93516e9d42e2b583972e5a30df91') == 1,
    'three_root_runtime_arguments_preserved': b'need(len(sys.argv) == 4,' in candidate and b'SCOPE_SHA, GRANT_SHA = sys.argv[1:3]' in candidate,
    'future_scope_and_grant_hash_null_preserved': b'SCOPE_SHA = None\nGRANT_SHA = None' in candidate,
    'pinned_python_flags_unchanged': b"[PYTHON, '-I', '-S', '-X', 'utf8', launcher['path']" in candidate,
    'once_intent_exclusive_write_unchanged': b".open('xb')" in candidate and b"save('root-launch.intent.json'" in candidate,
    'root_separately_allocated_empty_out_guard_unchanged': b"need(OUT.is_dir() and not any(OUT.iterdir()), 'Root must separately allocate a new empty caller directory')" in candidate,
    'current58_source_guard_unchanged': b"e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7" in candidate,
    'fixed_budget_and_native_timeout_unchanged': all(x in candidate for x in [b"scope['inner_seconds'] == 7200", b"scope['outer_seconds'] == 7500", b"scope['cleanup_seconds'] == 5", b"scope['controller_evidence_reserve_seconds'] == 60", b"scope['launcher_evidence_reserve_seconds'] == 60", b'timeout=7800, check=False']),
    'public_five_environment_allowlist_unchanged': b"{'SystemRoot', 'WINDIR', 'ComSpec', 'PATH', 'PATHEXT'}" in candidate,
    'caller_lifecycle_false_all_occurrences_unchanged': candidate.count(b"'caller_OS_lifecycle_qualification': False") == raw.count(b"'caller_OS_lifecycle_qualification': False") == 2,
    'original_actual_outer_exit_null_preserved': b"'actual_outer_tool_exit': None" in candidate,
    'no_retry_or_counter_reset_preserved': candidate.count(b"'automatic_retry': False") == raw.count(b"'automatic_retry': False") and candidate.count(b"'counter_reset': False") == raw.count(b"'counter_reset': False"),
    'no_added_imports': [ast.dump(n, include_attributes=False) for n in old_ast.body if isinstance(n, (ast.Import, ast.ImportFrom))] == [ast.dump(n, include_attributes=False) for n in new_ast.body if isinstance(n, (ast.Import, ast.ImportFrom))],
    'launcher_sha_unchanged': b'a4b5d968cc1829971ada48f55743bb7f6cc790967f76c179ceca1cac978b2bf7' in candidate,
    'python_sha_unchanged': b'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b' in candidate,
}
assert all(checks.values()), 'Static preservation checks'
selected = write_bytes('root-launch-once.desktop58.allocateddc4f.proposed.py', candidate)
patch = ''.join(difflib.unified_diff(raw.decode('utf-8').splitlines(keepends=True), candidate.decode('utf-8').splitlines(keepends=True), fromfile=SEED.as_posix(), tofile=selected['path']))
patch_ref = write_bytes('source.patch', patch.encode('utf-8'))
inverse = write_json('inverse.json', {
    'schema': 'researchos.desktop58-root-caller-source-inverse.v1',
    'seed_ref': pin(SEED), 'selected_ref': selected,
    'edits': [{'before': before.decode('utf-8'), 'after': after.decode('utf-8'), 'count': 1} for before, after in edits],
    'whole_byte_inverse': True, 'definition_checks': definition_checks,
    'unchanged_tail_starts_at': "scope_path = REGISTRATION / 'scope_registration.json' ",
    'unchanged_tail_byte_count': len(raw[raw.index(tail):]), 'candidate_imported': False, 'candidate_executed': False,
})
audit = write_json('static-audit.json', {
    'schema': 'researchos.desktop58-root-caller-allocation-static-audit.v1',
    'checks': checks, 'check_count': len(checks),
    'definition_checks': definition_checks, 'diff_hunk_count': patch.count('\n@@ '),
    'no_product_or_candidate_execution': True, 'no_root_future_directory_created': True,
    'root_future_directories_were_not_read_or_probed': True,
    'old_seed_ref_after': pin(SEED),
})
assert pin(SEED)['sha256'] == SEED_SHA and pin(SEED)['bytes'] == SEED_BYTES
report = write_json('report.json', {
    'schema': 'researchos.desktop58-root-caller-source-proposal.v1',
    'actor': ACTOR, 'role': 'AUTHOR',
    'decision': 'SOURCE_PROPOSAL_READY_FOR_NONAUTHOR_REVIEW',
    'selected_ref': selected, 'seed_ref': pin(SEED), 'inverse_ref': inverse, 'static_audit_ref': audit,
    'registration_namespace': REG.as_posix(),
    'run_uuid': NEW_UID, 'root_allocated_future_caller_output': ROOT_ALLOCATED_OUT.as_posix(),
    'runtime_arguments': ['actual_scope_sha256', 'actual_grant_sha256', 'root_allocated_empty_output'],
    'runtime_scope_sha256': None, 'runtime_grant_sha256': None,
    'changes': ['New r336 registration namespace', 'New authorization root UID', 'New run UUID', 'Only the Root-allocated baaf caller output is accepted'],
    'preserved': ['3 original helper definitions byte/AST', 'All scope read / launcher / raw / first-cause / NULL receipt tail bytes', 'Exclusive intent and raw files', 'Pinned Python flags, launcher and Python digests', '7200/7500/5/60/60 budgets and 7800 subprocess timeout', 'Public environment allowlist', 'caller_OS_lifecycle_qualification=False'],
    'legal_positive_compose': 'Root must independently review this Source, register the matching r336/dc4f current58 scope, seal its actual unique grant, and later allocate the exact canonical baaf empty OUT. Passing actual two hashes plus that OUT reaches the unchanged caller path subject to all retained gates; no actual authority is supplied here.',
    'negative_boundaries': ['Other/alias/noncanonical/relative OUT rejected', 'Old 72ff registration/authorization/run scope rejected', 'NULL or nonhex scope/grant hashes rejected', 'Reused/nonempty OUT rejected', 'Foreign scope/grant/launcher/Python/resource digest rejected', 'Any raw/invocation error remains first-cause/secondary and fails'],
    'next_independent_review': {'status': 'PENDING', 'review_actor': None, 'must_be_non_author': True, 'input_refs': [selected, inverse, audit, patch_ref], 'scope': 'SOURCE_ONLY_ALLOCATION_AND_FULL_BYTE_PRESERVATION'},
    'actual_root_scope': None, 'actual_grant': None, 'actual_caller_launch': None,
    'source_acceptance': False, 'formal_increment': 0, 'business_increment': 0,
    'candidate_imports': 0, 'product_executions': 0, 'canonical_writes': 0,
    'new_failure_origins': [], 'new_failure_count': 0, 'historical_failures_recounted': 0,
})
print(json.dumps({'selected_ref': selected, 'inverse_ref': inverse, 'audit_ref': audit, 'report_ref': report, 'static_checks': len(checks), 'diff_hunks': patch.count('\n@@ '), 'candidate_executions': 0, 'new_origins': 0}, ensure_ascii=False))
