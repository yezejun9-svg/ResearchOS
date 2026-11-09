import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import argparse
if sys.flags.optimize != 0:
    raise RuntimeError('Optimized Python execution prohibited for this registration')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
RP = Path('execution/v2.4/receipts/W05/W05-99')
HP = RP / 'host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec'
HANDLER = ROOT / '.local/worktrees/codex-w0599-host-configuration-handler'
G1 = ROOT / RP / 'provider_whole9_g1_root_executor_codex/093a934167674f6ca02e0a09dc5d5010'
CANON = [BASE / n for n in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
READ_SNAPSHOTS = {}

def checked_bytes(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if path not in READ_SNAPSHOTS:
        READ_SNAPSHOTS[path] = path.read_bytes()
    return READ_SNAPSHOTS[path]

def load_json(path):
    return json.loads(checked_bytes(path))

def ref(path, expected=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    data = checked_bytes(path)
    sha = hashlib.sha256(data).hexdigest()
    assert expected is None or sha == expected, str(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha, 'bytes': len(data)}

def save(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    return ref(OUT / name)
parser = argparse.ArgumentParser()
parser.add_argument('--review', required=True)
parser.add_argument('--review-sha', required=True)
args = parser.parse_args()
final_review_ref = ref(args.review, args.review_sha)
final_review = load_json(args.review)
if final_review.get('decision') != 'GUARDED_REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' or final_review.get('reviewer') != 'codex:/root/w05_merge_review':
    raise RuntimeError('Missing independent final execution-guard review')
if final_review.get('register_sha256') != hashlib.sha256(Path(__file__).read_bytes()).hexdigest() or final_review.get('expected_before') != [297, 125, 302] or final_review.get('failure_origins_after') != 313:
    raise RuntimeError('Final independent review does not bind actual source bytes and counter transition')
tool_lock = load_json(ROOT / 'execution/toolchains/locked.json')['tools']
GIT = tool_lock['git']['path']
assert hashlib.sha256(Path(GIT).read_bytes()).hexdigest() == tool_lock['git']['sha256']
assert Path(sys.executable).resolve() == Path(tool_lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == tool_lock['python']['sha256']
before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert (cp['revision'], ow['revision'], len(cp['failure_counters'])) == (297, 125, 302)
head = subprocess.check_output([GIT, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([GIT, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert len(status.splitlines()) == 13 and sum((r[:2] == b' D' for r in status.splitlines())) == 11
g1_refs = [ref(p) for p in sorted(G1.iterdir()) if p.is_file()]
outer_dir = ROOT / RP / 'integration_codex/provider-g1-and-f08-review-r297'
outer_ref = ref(outer_dir / 'g1.outer.invocation.json')
outer = json.loads(checked_bytes(outer_dir / 'g1.outer.invocation.json'))
assert outer['actor'] == 'codex:/root' and outer['actual_exit'] == 1 and (not outer['automatic_retry'])
for kind in ['stdout', 'stderr']:
    g1_refs.append(ref(outer_dir / ('g1.outer.' + kind + '.raw'), outer[kind + '_sha256']))
g1_refs.append(outer_ref)
alias_ref = ref(G1 / 'node-resolve-alias.invocation.json')
alias = json.loads(checked_bytes(G1 / 'node-resolve-alias.invocation.json'))
assert alias['actual_exit'] == 1 and alias['forced_stop'] is None
assert alias['actualargv'][1:3] == ['--input-type=module', '-e']
assert 'createRequire' in alias['actualargv'][3] and '.resolve(n)' in alias['actualargv'][3]
for kind in ['stdout', 'stderr']:
    ref(G1 / ('node-resolve-alias.' + kind + '.raw'), alias[kind + '_sha256'])
assert b'ERR_PACKAGE_PATH_NOT_EXPORTED' in (G1 / 'node-resolve-alias.stderr.raw').read_bytes()
first = json.loads(checked_bytes(G1 / 'inputs.before.json'))
last = json.loads(checked_bytes(G1 / 'inputs.failure.current.json'))
assert first == last and len(first) == 47300
failure_ref = ref(G1 / 'failure.origin.json', 'b1c8179a05d5af8d830e519a235d5d0453ea96bfeb4f8097f4a38f37c26f290f')
failure = json.loads(checked_bytes(G1 / 'failure.origin.json'))
assert 'node-resolve-alias failed' in failure['error'] and (not failure['counter_reset'])
for path, expected in failure['candidate9_current'].items():
    actual = ref(path, expected['sha256'])
    assert actual['bytes'] == expected['bytes']
assert len(failure['candidate9_current']) == 9
sdk_ref = ref(ROOT / 'third_party/mu/node_modules/@earendil-works/pi-ai/package.json')
sdk = json.loads(checked_bytes(ROOT / sdk_ref['path']))
assert sdk['version'] == '0.87.1' and sdk['exports']['.']['import'] == './dist/index.js'
assert 'require' not in sdk['exports']['.'] and 'default' not in sdk['exports']['.']
g1_audit_ref = save('g1.original-failure.audit.json', {'actor': 'codex:/root', 'decision': 'PREPARATION_ALIAS_CJS_CONDITION_FAILED_NOT_PRODUCT_TEST_FAILURE', 'actual_outer_exit': 1, 'actual_child_exit': 1, 'count_once_per_attempt': True, 'failure_ref': failure_ref, 'outer_invocation_ref': outer_ref, 'child_invocation_ref': alias_ref, 'input_count': 47300, 'input_drift': False, 'source9_hashes_verified': True, 'all_refs': g1_refs, 'actual_SDK_exports_ref': sdk_ref, 'cause': 'createRequire.resolve uses require conditions while pinned SDK exports only import.', 'bundle_builds': 0, 'Go_compiles': 0, 'Go_tests': 0, 'JS_tests': 0, 'external_paid_private_model_calls': 0, 'whole9_source_acceptance': False, 'historical_stop_at_first_attempt': 'ESM probe repair was not authorized at this original failure; later Root repair scopes remain separately authoritative and are never overwritten by this diagnostic.', 'formal_increment': 0})
supplement_path = HP / 'cli-first-cohort-failures-b5c03eb15d494ebfbb52eddbc36b010a/failure_origins.json'
supplement_ref = ref(HANDLER / supplement_path, '9467528fefec731e4c2563954997a87b9fa8621a4e2acbe2a93326b90a0d767a')
supplement = json.loads(checked_bytes(HANDLER / supplement_path))
copies = []

def copy_refs(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value and str(value['path']).startswith(HP.as_posix() + '/'):
            relative = Path(value['path'])
            assert relative.is_relative_to(HP)
            source = HANDLER / relative
            actual = ref(source, value['sha256'])
            data = checked_bytes(source)
            target = ROOT / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                assert target.read_bytes() == data
            else:
                with target.open('xb') as stream:
                    stream.write(data)
            copies.append({'source': actual, 'copy': ref(target, actual['sha256'])})
        else:
            for child in value.values():
                copy_refs(child)
    elif isinstance(value, list):
        for child in value:
            copy_refs(child)
copy_refs({'path': supplement_path.as_posix(), 'sha256': supplement_ref['sha256']})
copy_refs(supplement)
supplement_ref = ref(ROOT / supplement_path)
assert len(supplement['runs']) == 2 and len(supplement['new_tool_origins']) == 3
cohorts = []
for cohort in supplement['runs']:
    refs = cohort['refs']
    result_ref = next((r for r in refs if r['path'].endswith('/result.json')))
    invocation_ref = next((r for r in refs if r['path'].endswith('/command.invocation.json')))
    result = json.loads(checked_bytes(ROOT / result_ref['path']))
    invocation = json.loads(checked_bytes(ROOT / invocation_ref['path']))
    assert result['exit'] == invocation['exit'] == 1 and (not result['source_drift'])
    a = next((r for r in refs if r['path'].endswith('/source.before.json')))
    b = next((r for r in refs if r['path'].endswith('/source.after.json')))
    assert a['sha256'] == b['sha256'] and result['input_count'] == 39071
    cohorts.append({'origin': cohort['origin'], 'result_ref': result_ref, 'actual_exit': 1, 'input_count': 39071, 'source_drift': False, 'events': result.get('test_events'), 'kind': result['kind']})
report = supplement['contract_actual_report']
assert report['status'] == 'FAIL' and report['assertions'] == len(report['assertion_ids']) == 69 and (len(report['failures']) == 26) and (not report['not_verified'])
handler_audit_ref = save('handler.original-failures.audit.json', {'supplement_ref': supplement_ref, 'cohorts': cohorts, 'copies': copies, 'original_contract_success_check_ids': 69, 'original_contract_failure_entries': 26, 'original_contract_not_verified': 0, 'old_nonconfiguration_failures': 'Actual first new contract run failures retained; unchanged is source scope, not a separately executed baseline comparison.', 'no_combined_pass_total': True, 'source38_acceptance': False, 'formal_increment': 0})
old_failures = copy.deepcopy(cp['failure_counters'])

def append_failure(key, evidence, detail):
    assert key not in {x.get('origin_key') for x in cp['failure_counters']}
    cp['failure_counters'].append({'origin_key': key, 'evidence_ref': evidence, 'detail': detail, 'attempts': 1, 'retries_used': 0, 'count_once': True, 'counter_reset': False, 'status': 'ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
append_failure('W05-99/provider-whole9-g1/093a934167674f6ca02e0a09dc5d5010', g1_audit_ref, {'actual_outer_exit': 1, 'actual_child_exit': 1, 'cause': 'ESM-only package exports rejected by CJS alias probe', 'same_attempt_parent_child_not_double_counted': True})
for row in cohorts:
    append_failure('W05-99/handler-cli-first/' + row['origin'], supplement_ref, row)
for row in supplement['new_tool_origins']:
    assert row['outer_exit'] == 1
    append_failure('W05-99/handler-cli-first/tool-' + row['chunk'], supplement_ref, row)
prelim = ROOT / RP / 'handler38_cli_preliminary_review_codex/acf3406cef3a4fe8b20e0ee340bafc55'
prelim_manifest_ref = ref(prelim / 'manifest.json', 'dcbf50ea41cf11d1945ad4f0986400e0ac4486ffcb1f76c1d48e9f55ebd04d51')
prelim_manifest = json.loads(checked_bytes(prelim / 'manifest.json'))
assert len(prelim_manifest['files']) == 72
for entry in prelim_manifest['files']:
    path = Path(entry['path'])
    if not path.is_absolute():
        path = ROOT / path if path.parts[0] == 'execution' else prelim / path
    actual = ref(path, entry['sha256'])
    assert 'bytes' not in entry or actual['bytes'] == entry['bytes']
prelim_review_ref = ref(prelim / 'review.json', '1ffe82710a12218cec54cc6afdf9cf910b1c1074eaaf74d406248732ef28aa43')
prelim_handoff_ref = ref(prelim / 'handoff.json', '8c8090c75644bf1c114b056d0cdbf4f87144e25f68c059b37c1d4aa0566376d1')
prelim_failure_ref = ref(prelim / 'failure_origins.json')
prelim_review = json.loads(checked_bytes(prelim / 'review.json'))
assert prelim_review['decision'] == 'PRELIMINARY_NEEDS_FIX_NOT_SOURCE_READY'
prelim_failure = json.loads(checked_bytes(prelim / 'failure_origins.json'))
assert len(prelim_failure['tooling']) == 1 and prelim_failure['tooling'][0]['outer_exit'] == 1
append_failure('W05-99/handler38-cli-preliminary/tool-7f01c3', prelim_failure_ref, prelim_failure['tooling'][0])
previous = ROOT / RP / 'integration_codex/cli-and-g1-original-failures-r298'
failed_inv_ref = ref(previous / 'invocation.json')
failed_inv = json.loads(checked_bytes(previous / 'invocation.json'))
assert failed_inv['actual_exit'] == 1
failed_stdout_ref = ref(previous / 'stdout.raw', failed_inv['stdout_sha256'])
failed_stderr_ref = ref(previous / 'stderr.raw', failed_inv['stderr_sha256'])
assert b"KeyError: 'test_events'" in (previous / 'stderr.raw').read_bytes()
root_diag_ref = save('root-original-registration-diagnostics.json', {'first_registration': {'native_chunk': '933bc6', 'actual_exit': 1, 'child_invocation_ref': failed_inv_ref, 'stdout_ref': failed_stdout_ref, 'stderr_ref': failed_stderr_ref, 'cause': 'Incorrectly assumed contract batch result has Go test_events key.', 'secondary_wrapper_diagnostic': 'UTF-8 decoding of original Windows stderr failed after invocation was sealed.', 'same_batch_count_once': True, 'canonical_mutations': 0}, 'readonly_display': {'native_chunk': '32f688', 'actual_exit': 1, 'cause': 'Printing replacement Unicode character into GBK console raised UnicodeEncodeError.', 'original_raw_locator': 'functions.exec result chunk32f688', 'no_original_native_raw_file_fabricated': True}, 'new_fix': 'New immutable script uses absent test_events as null, records contract kind/report separately; diagnostic display JSON escapes Unicode. Original failed scripts/raw unchanged.', 'counter_reset': False})
append_failure('W05-99/root-failure-registration/tool-933bc6', root_diag_ref, {'actual_exit': 1, 'cause': 'contract result missing Go-only test_events; same wrapper/child batch counted once'})
append_failure('W05-99/root-failure-registration/tool-32f688', root_diag_ref, {'actual_exit': 1, 'cause': 'GBK readonly diagnostic print failed on replacement Unicode'})
second_failed = ROOT / RP / 'integration_codex/cli-g1-failure-registration-corrected-r298'
second_inv_ref = ref(second_failed / 'invocation.json')
second_inv = json.loads(checked_bytes(second_failed / 'invocation.json'))
assert second_inv['actual_exit'] == 1
second_stderr_ref = ref(second_failed / 'stderr.raw', second_inv['stderr_sha256'])
assert b'AssertionError' in (second_failed / 'stderr.raw').read_bytes()
second_diag_ref = save('root-second-registration-diagnostic.json', {'actual_exit': 1, 'native_chunk': '6ec8e0', 'invocation_ref': second_inv_ref, 'stderr_ref': second_stderr_ref, 'cause': 'Assumed oral report failure29, actual immutable report failure entries26.', 'canonical_mutations': 0, 'same_registration_failed_attempts': 2, 'counter_reset': False, 'action': 'Stopped automatic repeats, requested NONAUTHOR full readonly registration review; current script is new corrected draft.'})
append_failure('W05-99/root-failure-registration/tool-6ec8e0', second_diag_ref, {'actual_exit': 1, 'cause': 'Incorrect assumed report failure count29; actual26'})
correction_path = HP / 'contract-count-correction-d344de6ea1134acb8c8dcaa56fccb510/correction.json'
correction_source_ref = ref(HANDLER / correction_path, '5dd620972f04876158108d0a29be1c9075ab4f1b39d7d03e0a44186b5443e112')
copy_refs({'path': correction_path.as_posix(), 'sha256': correction_source_ref['sha256']})
correction_ref = ref(ROOT / correction_path)
cp['failure_chains']['W05-99/root-original-failure-registration'] = {'actual_failed_invocations': 2, 'failed_origin_refs': [root_diag_ref, second_diag_ref], 'readonly_native_display_failure_counted_separately': True, 'counter_reset': False, 'state': 'TWO_FAILURES_PRESERVED_CURRENT_GUARDS_INDEPENDENTLY_REVIEWED', 'oral_report_correction_ref': correction_ref, 'final_guard_review_ref': final_review_ref}
registration_review = ROOT / RP / 'root_registration_r298_readonly_review_codex/a440882c6172440a84239e8865e25d4e'
registration_manifest_ref = ref(registration_review / 'manifest.final.json', '049f3e644dd938d328d7a10a1f6d1ab467463a9d4ce5448ef5500c5bdcc52dd1')
registration_manifest = load_json(registration_review / 'manifest.final.json')
assert len(registration_manifest['files']) == 33
for entry in registration_manifest['files']:
    p = Path(entry['path'])
    if not p.is_absolute(): p = ROOT / p if p.parts[0] == 'execution' else registration_review / p
    actual = ref(p, entry['sha256'])
    assert 'bytes' not in entry or actual['bytes'] == entry['bytes']
registration_review_ref = ref(registration_review / 'review.json', 'fea1c10d9fa3e066ac396003e405e0bbf16270bcba1d2fccfb11fac5fb0e44d5')
registration_handoff_ref = ref(registration_review / 'handoff.final.json', '7bd0dc2e1a6cdcd725660036469c2275e5e201b74a53ebc18ee9306e9d1c71d6')
registration_tool_ref = save('registration-review-tool-original.json', {
    'origin_key': 'W05-99/root-registration-readonly/tool-176c1f', 'actual_exit': 1,
    'cause': 'Reviewer attempted slicing integer report.assertions and got TypeError.',
    'original_raw_locator': 'Reviewer functions.exec native chunk176c1f',
    'review_ref': registration_review_ref, 'original_native_raw_file_fabricated': False,
    'counter_reset': False, 'product_test_failure': False})
append_failure('W05-99/root-registration-readonly/tool-176c1f', registration_tool_ref,
    {'actual_exit': 1, 'cause': 'readonly integer assertions slice TypeError'})
second_stdout_ref = ref(second_failed / 'stdout.raw', second_inv['stdout_sha256'])
assert cp['failure_counters'][:302] == old_failures and len(cp['failure_counters']) == 313
cp['failure_chains']['W05-99/provider-whole9-g1-alias-preparation'] = {'actual_failed_invocations': 1, 'failure_ref': g1_audit_ref, 'same_cause_failures': 1, 'counter_reset': False, 'automatic_retry': False, 'state': 'FIRST_FAILED_PREPARATION_STOPPED_PRECISE_REPAIR_REVIEW_PENDING'}
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
for path, data in before.items():
    with (OUT / (path.stem + '.original.json')).open('xb') as stream:
        stream.write(data)
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
subtasks['provider_whole9_g1_independent'].update(historical_first_failure_audit_ref=g1_audit_ref)
cp['work_in_progress'].update(provider_whole9_g1_original_failure_ref=g1_audit_ref, configuration_handler_cli_first_failures_ref=handler_audit_ref, handler38_cli_preliminary_review_ref=prelim_review_ref, pending_actual_failure_imports=['Author exact38 corrected current CLI cohort and final matrix, if nonzero.'])
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'CLI_AND_G1_ORIGINAL_FAILURES_PRESERVED', 'G1_audit_ref': g1_audit_ref, 'handler_audit_ref': handler_audit_ref, 'failure_origins_before': 302, 'failure_origins_after': 313, 'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=298, expected_previous_revision=297, updated_at=now, updated_by='codex:/root')
ow.update(revision=126, amended_at=now, amended_by='codex:/root')
for row in [g1_audit_ref, handler_audit_ref, supplement_ref, prelim_manifest_ref, prelim_review_ref, prelim_handoff_ref, root_diag_ref, second_diag_ref, correction_ref, registration_review_ref, registration_manifest_ref, registration_handoff_ref, registration_tool_ref, final_review_ref]:
    if row['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(row['path'])
record_ref = save('record.json', {'checkpoint': [297, 298], 'ownership': [125, 126], 'failures': [302, 313], 'G1_audit_ref': g1_audit_ref, 'handler_audit_ref': handler_audit_ref, 'Main_product_source_writes': 0, 'formal_increment': 0})
with (OUT / 'git-status.original.raw').open('xb') as stream: stream.write(status)
status_ref = ref(OUT / 'git-status.original.raw')
desired = {p: (json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8') for p, v in zip(CANON[:2], [cp, ow])}
for p, data in desired.items():
    with (OUT / (p.stem + '.desired.json')).open('xb') as stream: stream.write(data)
intent_ref = save('canonical-write.intent.json', {
    'actor': 'codex:/root', 'checkpoint': [297, 298], 'ownership': [125, 126], 'failures': [302, 313],
    'root_final_execution_guard_review': final_review_ref, 'Main_head': head, 'original_git_status_ref': status_ref,
    'register_ref': ref(Path(__file__)), 'launcher_ref': ref(OUT / 'run.py'),
    'toolchain_lock_ref': ref(ROOT / 'execution/toolchains/locked.json'),
    'actual_python': {'path': sys.executable, 'sha256': hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()},
    'locked_git': tool_lock['git'],
    'metadata': [{'path': p.relative_to(ROOT).as_posix(), 'before_sha256': hashlib.sha256(before[p]).hexdigest(),
        'desired_sha256': hashlib.sha256(desired[p]).hexdigest(), 'original_ref': ref(OUT / (p.stem + '.original.json')),
        'desired_ref': ref(OUT / (p.stem + '.desired.json'))} for p in CANON[:2]],
    'unchanged': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[p]).hexdigest()} for p in CANON[2:]],
    'recovery': 'Resume forward only when both canonical files equal own original or desired bytes, with unchanged other metadata and HEAD/status. External differences stop; no overwrite/rollback/failure reset.'})
assert all(p.read_bytes() == data for p, data in before.items())
assert subprocess.check_output([GIT, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
assert subprocess.check_output([GIT, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
for p, data in READ_SNAPSHOTS.items():
    assert p.read_bytes() == data, 'Published evidence drift before canonical write: ' + str(p)
for p, data in desired.items():
    temp = p.with_name(p.name + '.root298.guarded.tmp')
    with temp.open('xb') as stream: stream.write(data)
    assert temp.read_bytes() == data
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
expected_live = dict(before)
try:
    for p, data in desired.items():
        assert all(c.read_bytes() == expected_live[c] for c in CANON)
        assert subprocess.check_output([GIT, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([GIT, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(p.with_name(p.name + '.root298.guarded.tmp'), p)
        expected_live[p] = data
        assert p.read_bytes() == data
        phase = p.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + p.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(data).hexdigest()})
    assert all(p.read_bytes() == data for p, data in desired.items())
    assert all(p.read_bytes() == before[p] for p in CANON[2:])
    actual_cp = json.loads(CANON[0].read_bytes()); actual_ow = json.loads(CANON[1].read_bytes())
    assert [actual_cp['revision'], actual_ow['revision'], len(actual_cp['failure_counters'])] == [298, 126, 313]
    assert actual_cp['failure_counters'][:302] == old_failures
    assert actual_cp['failure_chains']['W05-99/root-original-failure-registration']['actual_failed_invocations'] == 2
    assert actual_cp['failure_chains']['W05-99/provider-whole9-g1-alias-preparation']['actual_failed_invocations'] == 1
    assert actual_cp['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([GIT, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([GIT, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'phase': 'BOTH_CANONICAL_FILES_VERIFIED', 'intent_ref': intent_ref,
        'checkpoint': 298, 'ownership': 126, 'failures': 313, 'old302_prefix_unchanged': True,
        'step_state_and_commands_unchanged': True, 'protected_old_git_deletions': 11, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in CANON},
        'no_automatic_retry': True, 'no_rollback_or_external_overwrite': True})
    raise
handoff_ref = save('handoff-r298-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE', 'actor': 'codex:/root', 'project_id': cp['project_id'], 'Main_head': head, 'Main_source_head': '1b3cda2ee974916f864b9a0af988076d01ca65bd', 'checkpoint': ref(CANON[0]), 'ownership': ref(CANON[1]), 'step_state': ref(CANON[2]), 'commands': ref(CANON[3]), 'revision': 298, 'failure_origins': 313, 'counter_reset': False, 'record_ref': record_ref, 'next_card': 'W05-99', 'protected_old_unstaged_deletions': 11, 'G1': g1_audit_ref, 'CLI38': handler_audit_ref, 'handler_next': 'Actual CLI response raw numeric and status revision corrections followed by exact38 freeze/full matrix and NONAUTHOR review.', 'provider_historical_first_failure': 'Original first attempt CJS alias probe failed before bundle/Go/JS. Historical diagnostic only; current scope/state retained below.', 'provider_current_ownership': subtasks['provider_whole9_g1_independent'], 'current_next_action_retained': cp['work_in_progress'].get('next_action'), 'F08': 'Whole20 v4 REQUEST_CHANGES2; readonly v5 correct refs multiset and current-epoch proof; no source SQL24 lease.', 'formal_current': cp['current_effective_formal_status'], 'all22_and42_effective_acceptances_required': True, 'paid_calls_this_registration': 0, 'formal_increment': 0})
print(json.dumps({'checkpoint': 298, 'ownership': 126, 'failure_origins': 313, 'handoff_ref': handoff_ref}, ensure_ascii=True))
