import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent


def ref(path, expected=None):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    raw = path.read_bytes()
    item = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected, str(path)
    return item


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


def once(source, old, new):
    assert source.count(old) == 1, (old, source.count(old))
    return source.replace(old, new, 1)


assert sys.flags.isolated and sys.flags.no_site == 1 and sys.flags.utf8_mode and not sys.flags.optimize
assert len(sys.argv) == 1
previous_runner_ref = ref(OUT / 'root_finite14_replay.v2.py', '32af67288b42f4865f021ff9b5a7d8adeabe0249a82c4734c89a3a6caeaf18f9')
previous_scope_ref = ref(OUT / 'root_finite14_scope.v2.json', '1f67e7dece77b444b53a555ed193f3402b566e7960cf8cdef68b38e37d80d0ef')
scope = json.loads((OUT / 'root_finite14_scope.v2.json').read_bytes())
old_source = (OUT / 'root_finite14_replay.v2.py').read_text(encoding='utf-8', errors='strict')
source = once(old_source, "DRAFT / 'root_finite14_scope.v2.json'", "DRAFT / 'root_finite14_scope.v3.json'")
source = once(source, 'ROOT = Path.cwd().resolve()', 'assert sys.flags.isolated and sys.flags.no_site == 1 and sys.flags.utf8_mode\nROOT = Path.cwd().resolve()')
run_id = uuid.uuid4().hex
assert source.count(scope['run_uuid']) == 2
source = source.replace(scope['run_uuid'], run_id)
ast.parse(source)
hex_pattern = r'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])'
assert re.findall(hex_pattern, source) == re.findall(hex_pattern, old_source)
with (OUT / 'root_finite14_replay.v3.py').open('xb') as stream:
    stream.write(source.encode('utf-8'))
failure_ref = ref(OUT / 'failure_origin.launch7783ca.json')
raw_failure_ref = ref(ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_root_replay_authorization_codex/a452e0211f5846db95514697db075e61/failure.origin.json')
failure = json.loads((ROOT / failure_ref['path']).read_bytes())
assert failure['actual_outer_exit'] == 1 and failure['actual_inner_exit'] is None and failure['product_cases_run'] == 0
scope.update(state='DRAFT_V3_NOT_REGISTERED_NOT_AUTHORIZED_NOT_EXECUTED', uuid=run_id, run_uuid=run_id,
    runner_ref=ref(OUT / 'root_finite14_replay.v3.py'),
    launcher_ref=ref(OUT / 'launch.v3.py', '63a8092df805a858c943cfb3b01661a541abeea56e876d634364a3cc94aa0be0'),
    authorization_gate_ref=ref(OUT / 'authorization_gate.v3.py', 'a12d165daf93687531e26a4652dcc338127f61fae63d40821d779128cbb09ba7'),
    previous_runner_draft_ref=previous_runner_ref, previous_scope_draft_ref=previous_scope_ref,
    v2_actual_prelaunch_failure_ref=failure_ref, v2_original_launcher_failure_ref=raw_failure_ref,
    python_flags=['-I', '-S', '-X', 'utf8'],
    new_output_root='execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_root_replay_codex/' + run_id,
    new_export_root='.local/independent-session-list-closedcopy-root-' + run_id,
    new_authorization_root='execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_root_replay_authorization_codex/' + run_id,
    registration_namespace='execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-root-r319',
    expected_registration=[319, 147, 413],
    authority_rule='Draft alone grants nothing. Exact actual sealed Root319 registration, original source review and v3 runner independent review, four actual canonical raw copies and one unique prelaunch grant are mandatory before native calls. Both Python processes must use -I -S -X utf8 and verify no_site. Root318 failed prelaunch is preserved; no old authorization leaf reuse.',
    bootstrap_runtime_policy='Use only the unchanged approved public1211 runtime catalog; disable system site initialization rather than approve editable/private SDK startup. Unpinned actual loaded resource still stops first. Never trim runtime guards.',
    failure_transition='Root319 preserves all410 registered rows and appends three actual original causes, for413; old Root318 execution snapshot and all source/author/harness failures remain immutable.')
assert not (ROOT / scope['new_authorization_root']).exists()
assert (ROOT / scope['new_authorization_root']).parent.is_dir()
scope_ref = save('root_finite14_scope.v3.json', scope)
audit = save('runner_revision.v3.audit.json', {'previous_runner_ref': previous_runner_ref, 'previous_scope_ref': previous_scope_ref,
    'runner_ref': scope['runner_ref'], 'scope_ref': scope_ref, 'gate_ref': scope['authorization_gate_ref'],
    'launcher_ref': scope['launcher_ref'], 'unchanged_runtime_inventory_ref': scope['runtime_resources_ref'],
    'original_failure_ref': failure_ref, 'original_launcher_failure_ref': raw_failure_ref,
    'all_original64hex_literals_exact_unchanged': True, 'R14_02_and_03_guards_retained': True,
    'fresh_unique_roots_and_non_site_bootstrap': True, 'new_product_export_compile_SQL_HTTP_MODEL': 0,
    'automatic_same_input_retry': False, 'counter_reset': False,
    'state': 'DRAFT_STATIC_REVIEW_REQUIRED', 'source_acceptance': False, 'formal_increment': 0})
print(json.dumps({'runner': scope['runner_ref'], 'scope': scope_ref, 'gate': scope['authorization_gate_ref'],
    'launcher': scope['launcher_ref'], 'audit': audit, 'actual_export_compile_tests': 0}, ensure_ascii=True))
