import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
RP = Path('execution/v2.4/receipts/W05/W05-99')
HP = RP / 'host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec'
HANDLER = ROOT / '.local/worktrees/codex-w0599-host-configuration-handler'
G1 = ROOT / RP / 'provider_whole9_g1_root_executor_codex/093a934167674f6ca02e0a09dc5d5010'
CANON = [BASE / n for n in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]

def ref(path, expected=None):
    path = Path(path)
    if not path.is_absolute(): path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    assert expected is None or sha == expected, str(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha, 'bytes': len(data)}

def save(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    return ref(OUT / name)

before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert (cp['revision'], ow['revision'], len(cp['failure_counters'])) == (297, 125, 302)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert len(status.splitlines()) == 13 and sum(r[:2] == b' D' for r in status.splitlines()) == 11

g1_refs = [ref(p) for p in sorted(G1.iterdir()) if p.is_file()]
outer_dir = ROOT / RP / 'integration_codex/provider-g1-and-f08-review-r297'
outer_ref = ref(outer_dir / 'g1.outer.invocation.json')
outer = json.loads((outer_dir / 'g1.outer.invocation.json').read_bytes())
assert outer['actor'] == 'codex:/root' and outer['actual_exit'] == 1 and not outer['automatic_retry']
for kind in ['stdout', 'stderr']:
    g1_refs.append(ref(outer_dir / ('g1.outer.' + kind + '.raw'), outer[kind + '_sha256']))
g1_refs.append(outer_ref)
alias_ref = ref(G1 / 'node-resolve-alias.invocation.json')
alias = json.loads((G1 / 'node-resolve-alias.invocation.json').read_bytes())
assert alias['actual_exit'] == 1 and alias['forced_stop'] is None
assert alias['actualargv'][1:3] == ['--input-type=module', '-e']
assert 'createRequire' in alias['actualargv'][3] and '.resolve(n)' in alias['actualargv'][3]
for kind in ['stdout', 'stderr']:
    ref(G1 / ('node-resolve-alias.' + kind + '.raw'), alias[kind + '_sha256'])
assert b'ERR_PACKAGE_PATH_NOT_EXPORTED' in (G1 / 'node-resolve-alias.stderr.raw').read_bytes()
first = json.loads((G1 / 'inputs.before.json').read_bytes())
last = json.loads((G1 / 'inputs.failure.current.json').read_bytes())
assert first == last and len(first) == 47300
failure_ref = ref(G1 / 'failure.origin.json', 'b1c8179a05d5af8d830e519a235d5d0453ea96bfeb4f8097f4a38f37c26f290f')
failure = json.loads((G1 / 'failure.origin.json').read_bytes())
assert 'node-resolve-alias failed' in failure['error'] and not failure['counter_reset']
for path, expected in failure['candidate9_current'].items():
    actual = ref(path, expected['sha256']); assert actual['bytes'] == expected['bytes']
assert len(failure['candidate9_current']) == 9
sdk_ref = ref(ROOT / 'third_party/mu/node_modules/@earendil-works/pi-ai/package.json')
sdk = json.loads((ROOT / sdk_ref['path']).read_bytes())
assert sdk['version'] == '0.87.1' and sdk['exports']['.']['import'] == './dist/index.js'
assert 'require' not in sdk['exports']['.'] and 'default' not in sdk['exports']['.']
g1_audit_ref = save('g1.original-failure.audit.json', {
    'actor': 'codex:/root', 'decision': 'PREPARATION_ALIAS_CJS_CONDITION_FAILED_NOT_PRODUCT_TEST_FAILURE',
    'actual_outer_exit': 1, 'actual_child_exit': 1, 'count_once_per_attempt': True,
    'failure_ref': failure_ref, 'outer_invocation_ref': outer_ref, 'child_invocation_ref': alias_ref,
    'input_count': 47300, 'input_drift': False, 'source9_hashes_verified': True, 'all_refs': g1_refs,
    'actual_SDK_exports_ref': sdk_ref, 'cause': 'createRequire.resolve uses require conditions while pinned SDK exports only import.',
    'bundle_builds': 0, 'Go_compiles': 0, 'Go_tests': 0, 'JS_tests': 0,
    'external_paid_private_model_calls': 0, 'whole9_source_acceptance': False,
    'next': 'Read-only precise ESM probe repair proposal and Root review before one new bounded attempt; retain original runner and failed directories.',
    'formal_increment': 0})

supplement_path = HP / 'cli-first-cohort-failures-b5c03eb15d494ebfbb52eddbc36b010a/failure_origins.json'
supplement_ref = ref(HANDLER / supplement_path, '9467528fefec731e4c2563954997a87b9fa8621a4e2acbe2a93326b90a0d767a')
supplement = json.loads((HANDLER / supplement_path).read_bytes())
copies = []
def copy_refs(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value and str(value['path']).startswith(HP.as_posix() + '/'):
            relative = Path(value['path']); assert relative.is_relative_to(HP)
            source = HANDLER / relative; actual = ref(source, value['sha256'])
            data = source.read_bytes(); target = ROOT / relative; target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists(): assert target.read_bytes() == data
            else:
                with target.open('xb') as stream: stream.write(data)
            copies.append({'source': actual, 'copy': ref(target, actual['sha256'])})
        else:
            for child in value.values(): copy_refs(child)
    elif isinstance(value, list):
        for child in value: copy_refs(child)
copy_refs({'path': supplement_path.as_posix(), 'sha256': supplement_ref['sha256']})
copy_refs(supplement)
supplement_ref = ref(ROOT / supplement_path)
assert len(supplement['runs']) == 2 and len(supplement['new_tool_origins']) == 3
cohorts = []
for cohort in supplement['runs']:
    refs = cohort['refs']
    result_ref = next(r for r in refs if r['path'].endswith('/result.json'))
    invocation_ref = next(r for r in refs if r['path'].endswith('/command.invocation.json'))
    result = json.loads((ROOT / result_ref['path']).read_bytes())
    invocation = json.loads((ROOT / invocation_ref['path']).read_bytes())
    assert result['exit'] == invocation['exit'] == 1 and not result['source_drift']
    a = next(r for r in refs if r['path'].endswith('/source.before.json'))
    b = next(r for r in refs if r['path'].endswith('/source.after.json'))
    assert a['sha256'] == b['sha256'] and result['input_count'] == 39071
    cohorts.append({'origin': cohort['origin'], 'result_ref': result_ref, 'actual_exit': 1,
        'input_count': 39071, 'source_drift': False, 'events': result.get('test_events'), 'kind': result['kind']})
report = supplement['contract_actual_report']
assert report['status'] == 'FAIL' and len(report['failures']) == 29 and not report['not_verified']
handler_audit_ref = save('handler.original-failures.audit.json', {
    'supplement_ref': supplement_ref, 'cohorts': cohorts, 'copies': copies,
    'original_contract_pass': 69, 'original_contract_fail': 29, 'original_contract_not_verified': 0,
    'old_nonconfiguration_failures': 'Actual first new contract run failures retained; unchanged is source scope, not a separately executed baseline comparison.',
    'no_combined_pass_total': True, 'source38_acceptance': False, 'formal_increment': 0})

old_failures = copy.deepcopy(cp['failure_counters'])
def append_failure(key, evidence, detail):
    assert key not in {x.get('origin_key') for x in cp['failure_counters']}
    cp['failure_counters'].append({'origin_key': key, 'evidence_ref': evidence, 'detail': detail,
        'attempts': 1, 'retries_used': 0, 'count_once': True, 'counter_reset': False,
        'status': 'ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
append_failure('W05-99/provider-whole9-g1/093a934167674f6ca02e0a09dc5d5010', g1_audit_ref,
    {'actual_outer_exit': 1, 'actual_child_exit': 1, 'cause': 'ESM-only package exports rejected by CJS alias probe', 'same_attempt_parent_child_not_double_counted': True})
for row in cohorts:
    append_failure('W05-99/handler-cli-first/' + row['origin'], supplement_ref, row)
for row in supplement['new_tool_origins']:
    assert row['outer_exit'] == 1
    append_failure('W05-99/handler-cli-first/tool-' + row['chunk'], supplement_ref, row)
prelim = ROOT / RP / 'handler38_cli_preliminary_review_codex/acf3406cef3a4fe8b20e0ee340bafc55'
prelim_manifest_ref = ref(prelim / 'manifest.json', 'dcbf50ea41cf11d1945ad4f0986400e0ac4486ffcb1f76c1d48e9f55ebd04d51')
prelim_manifest = json.loads((prelim / 'manifest.json').read_bytes())
assert len(prelim_manifest['files']) == 72
for entry in prelim_manifest['files']:
    path = Path(entry['path'])
    if not path.is_absolute(): path = ROOT / path if path.parts[0] == 'execution' else prelim / path
    actual = ref(path, entry['sha256'])
    assert 'bytes' not in entry or actual['bytes'] == entry['bytes']
prelim_review_ref = ref(prelim / 'review.json', '1ffe82710a12218cec54cc6afdf9cf910b1c1074eaaf74d406248732ef28aa43')
prelim_handoff_ref = ref(prelim / 'handoff.json', '8c8090c75644bf1c114b056d0cdbf4f87144e25f68c059b37c1d4aa0566376d1')
prelim_failure_ref = ref(prelim / 'failure_origins.json')
prelim_review = json.loads((prelim / 'review.json').read_bytes())
assert prelim_review['decision'] == 'PRELIMINARY_NEEDS_FIX_NOT_SOURCE_READY'
prelim_failure = json.loads((prelim / 'failure_origins.json').read_bytes())
assert len(prelim_failure['tooling']) == 1 and prelim_failure['tooling'][0]['outer_exit'] == 1
append_failure('W05-99/handler38-cli-preliminary/tool-7f01c3', prelim_failure_ref, prelim_failure['tooling'][0])
previous = ROOT / RP / 'integration_codex/cli-and-g1-original-failures-r298'
failed_inv_ref = ref(previous / 'invocation.json')
failed_inv = json.loads((previous / 'invocation.json').read_bytes())
assert failed_inv['actual_exit'] == 1
failed_stdout_ref = ref(previous / 'stdout.raw', failed_inv['stdout_sha256'])
failed_stderr_ref = ref(previous / 'stderr.raw', failed_inv['stderr_sha256'])
assert b"KeyError: 'test_events'" in (previous / 'stderr.raw').read_bytes()
root_diag_ref = save('root-original-registration-diagnostics.json', {
    'first_registration': {'native_chunk': '933bc6', 'actual_exit': 1, 'child_invocation_ref': failed_inv_ref,
        'stdout_ref': failed_stdout_ref, 'stderr_ref': failed_stderr_ref,
        'cause': 'Incorrectly assumed contract batch result has Go test_events key.',
        'secondary_wrapper_diagnostic': 'UTF-8 decoding of original Windows stderr failed after invocation was sealed.',
        'same_batch_count_once': True, 'canonical_mutations': 0},
    'readonly_display': {'native_chunk': '32f688', 'actual_exit': 1,
        'cause': 'Printing replacement Unicode character into GBK console raised UnicodeEncodeError.',
        'original_raw_locator': 'functions.exec result chunk32f688', 'no_original_native_raw_file_fabricated': True},
    'new_fix': 'New immutable script uses absent test_events as null, records contract kind/report separately; diagnostic display JSON escapes Unicode. Original failed scripts/raw unchanged.',
    'counter_reset': False})
append_failure('W05-99/root-failure-registration/tool-933bc6', root_diag_ref,
    {'actual_exit': 1, 'cause': 'contract result missing Go-only test_events; same wrapper/child batch counted once'})
append_failure('W05-99/root-failure-registration/tool-32f688', root_diag_ref,
    {'actual_exit': 1, 'cause': 'GBK readonly diagnostic print failed on replacement Unicode'})
assert cp['failure_counters'][:302] == old_failures and len(cp['failure_counters']) == 311
cp['failure_chains']['W05-99/provider-whole9-g1-alias-preparation'] = {
    'actual_failed_invocations': 1, 'failure_ref': g1_audit_ref,
    'same_cause_failures': 1, 'counter_reset': False, 'automatic_retry': False,
    'state': 'FIRST_FAILED_PREPARATION_STOPPED_PRECISE_REPAIR_REVIEW_PENDING'}
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
for path, data in before.items():
    with (OUT / (path.stem + '.original.json')).open('xb') as stream: stream.write(data)
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
subtasks['provider_whole9_g1_independent'].update(state='FIRST_NATIVE_ATTEMPT_FAILED_CJS_ALIAS_PREPARATION', original_failure_audit_ref=g1_audit_ref, source_ready=False)
cp['work_in_progress'].update(provider_whole9_g1_original_failure_ref=g1_audit_ref,
    configuration_handler_cli_first_failures_ref=handler_audit_ref, handler38_cli_preliminary_review_ref=prelim_review_ref,
    pending_actual_failure_imports=['Author exact38 corrected current CLI cohort and final matrix, if nonzero.'],
    next_action='Author narrows raw numeric/configuration status fixes within38 then freezes final candidate/full matrix. Root reviews precise ESM preparation repair before second bounded G1 attempt. F08 v5 readonly correction pending; no SQL24 lease.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'CLI_AND_G1_ORIGINAL_FAILURES_PRESERVED',
    'G1_audit_ref': g1_audit_ref, 'handler_audit_ref': handler_audit_ref,
    'failure_origins_before': 302, 'failure_origins_after': 311, 'counter_reset': False,
    'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=298, expected_previous_revision=297, updated_at=now, updated_by='codex:/root')
ow.update(revision=126, amended_at=now, amended_by='codex:/root')
for row in [g1_audit_ref, handler_audit_ref, supplement_ref, prelim_manifest_ref, prelim_review_ref, prelim_handoff_ref, root_diag_ref]:
    if row['path'] not in cp['evidence_index']: cp['evidence_index'].append(row['path'])
record_ref = save('record.json', {'checkpoint': [297, 298], 'ownership': [125, 126],
    'failures': [302, 311], 'G1_audit_ref': g1_audit_ref, 'handler_audit_ref': handler_audit_ref,
    'Main_product_source_writes': 0, 'formal_increment': 0})
assert all(p.read_bytes() == data for p, data in before.items())
assert subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
for p, v in zip(CANON[:2], [cp, ow]):
    temp = p.with_name(p.name + '.root298.tmp')
    with temp.open('x', encoding='utf-8') as stream:
        json.dump(v, stream, ensure_ascii=False, indent=2, allow_nan=False); stream.write('\n')
    assert p.read_bytes() == before[p]; os.replace(temp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
handoff_ref = save('handoff-r298-running.json', {
    'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE', 'actor': 'codex:/root', 'project_id': cp['project_id'],
    'Main_head': head, 'Main_source_head': '1b3cda2ee974916f864b9a0af988076d01ca65bd',
    'checkpoint': ref(CANON[0]), 'ownership': ref(CANON[1]), 'step_state': ref(CANON[2]), 'commands': ref(CANON[3]),
    'revision': 298, 'failure_origins': 311, 'counter_reset': False, 'record_ref': record_ref,
    'next_card': 'W05-99', 'protected_old_unstaged_deletions': 11,
    'G1': g1_audit_ref, 'CLI38': handler_audit_ref,
    'handler_next': 'Actual CLI response raw numeric and status revision corrections followed by exact38 freeze/full matrix and NONAUTHOR review.',
    'provider_next': 'First CJS probe failure closed, precise ESM repair pending independent Root authorization; no Go/JS test or freshbundle yet.',
    'F08': 'Whole20 v4 REQUEST_CHANGES2; readonly v5 correct refs multiset and current-epoch proof; no source SQL24 lease.',
    'formal_current': cp['current_effective_formal_status'], 'all22_and42_effective_acceptances_required': True,
    'paid_calls_this_registration': 0, 'formal_increment': 0})
print(json.dumps({'checkpoint': 298, 'ownership': 126, 'failure_origins': 311, 'handoff_ref': handoff_ref}, ensure_ascii=True))
