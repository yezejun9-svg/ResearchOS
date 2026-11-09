import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'session-list-closedcopy-exact1-r312'
RECEIPTS = ROOT / 'execution/v2.4/receipts/W05/W05-99'
PREP = RECEIPTS / 'provider_g2_finite_replay_preparation_codex/3ed3a3da52c3471d9ddc524897100842'
REPLAY = RECEIPTS / 'provider_g2_independent_replay_codex/3ed3a3da52c3471d9ddc524897100842'
AUDIT = OUT.parent / 'root-g2-prepare-launch-r310'
CANON = [ROOT / 'execution/v2.4' / (name + '.json') for name in ['checkpoint', 'path_ownership', 'step_state', 'commands']]
READS = {}


def read(path):
    path = Path(path).resolve()
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def pin(path, expected=None):
    path = Path(path).resolve()
    raw = read(path)
    result = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or result['sha256'] == expected
    return result


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return pin(OUT / name)


def script(path, source):
    ast.parse(source)
    with path.open('xb') as stream:
        stream.write(source.encode('utf-8'))
    return pin(path)


cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [312, 140, 386]
lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = lock['git']['path']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
pins = {}
for key, path, expected in [
    ('previous_handoff', PREVIOUS / 'handoff-r312-running.json', 'e5320a3589723a79c60336dae3079ac0af1e763c82db2464724e9ba4313d029c'),
    ('g2_prepared', REPLAY / 'prepared.json', 'fe01bef395b10c5308d28ce006bc42fca6a7465d6847ddc1711586f449ab60ec'),
    ('g2_preparation_audit', AUDIT / 'preparation-audit.json', 'db3ef414e4c15b1d83b1141b4b8940671cb4030c66cf92c5f8bdbe647ea84098'),
    ('g2_preparation_manifest', AUDIT / 'manifest.json', '6c1cc8369b27d8366ab4196eb12db63bd87b10118c0521b1d9216b4f947cb6f0'),
    ('g2_spec', PREP / 'execution_spec.json', '2c871df7ffa78c52470ed08f031be5831ceeab3098947c512d6485c06df8ca0b'),
    ('g2_runner', OUT.parent / 'complete-public-graph-and-g2-r310/g2_replay.v4.py', 'e687bd35560d4c34b4e939609b617a5d4770b4a45d51c3b132fca60a4bfa39f5'),
    ('review_failure', RECEIPTS / 'root_registration_r312_readonly_review_codex/8dd6209672094799b709571783fb353a/failure_origins.json', '72dab3741b140be0479c7573d6be3d9796705f9c9248da123af7e66570d40393'),
    ('desktop_failure', ROOT / '.local/worktrees/codex-w1303-desktop-http-r311/execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/98552188a0014da3a6d73be7cdb3f9bd/failure-origin-e32c12.json', '500518a9f2fca3ab158139a6f5d56057de0e0ae3d609cae3d57810e01495ba21')]:
    pins[key] = pin(path, expected)
spec = json.loads(read(PREP / 'execution_spec.json'))
prepared = json.loads(read(REPLAY / 'prepared.json'))
assert prepared['status'] == 'COMPILED_NOT_EXECUTED' and len(prepared['inputs']) == 41958
assert prepared['source_commit'] == spec['candidate'] == '8d0921b7c42ecd40300c58192d54af1064947aed'
assert not (REPLAY / 'execute').exists()
pins['g2_completed'] = pin(REPLAY / 'prepare/completed.json')
assert json.loads(read(REPLAY / 'prepare/completed.json'))['status'] == 'COMPLETED_NOT_ACCEPTED'
pins['g2_exe'] = pin(prepared['exe']['path'], 'e01e21ccb8e27bfd1fe88b66a8a63adfed28e5d46f45dc12337001696916689d')
assert pins['g2_exe']['bytes'] == 40873472
review_row = json.loads(read(ROOT / pins['review_failure']['path']))[0]
desktop = json.loads(read(ROOT / pins['desktop_failure']['path']))
origins = [{**{k: review_row[k] for k in ['origin_key', 'actor', 'actual_outer_exit', 'actual_native_exit', 'product_test_failures', 'cause']},
    'evidence_ref': pins['review_failure'], 'original_payload': review_row, 'json_pointer': '/0', 'raw_file_available': False},
    {'origin_key': desktop['id'], 'actor': 'codex:/root/sources_parent_impl', 'actual_outer_exit': desktop['actual_outer_wrapper_exit'],
     'actual_native_exit': desktop['actual_native_exit'], 'product_test_failures': 0, 'product_compile_failures': 1,
     'cause': desktop['cause'], 'evidence_ref': pins['desktop_failure'], 'original_payload': desktop}]
assert len(origins) == len({row['origin_key'] for row in origins}) == 2
assert not {row['origin_key'] for row in origins}.intersection({row.get('origin_key') for row in cp['failure_counters']})
pins['failure_cut'] = save('failure-origins.cut.json', {'before': 386, 'after': 388, 'origins': origins,
    'counter_reset': False, 'native_Go_compile_successes_not_test_acceptance': True,
    'desktop_actual_native1_outer0_preserved': True})
pins['scope'] = save('scope_registration.json', {'schema': 'researchos.provider-g2-root-execute29-scope.v1',
    'owner': 'codex:/root', 'status': 'AUTHORIZED_BY_CAS313_ONLY_NOT_EXECUTED', 'registration_checkpoint': 313,
    'candidate': spec['candidate'], 'spec_ref': pins['g2_spec'], 'runner_ref': pins['g2_runner'],
    'prepared_ref': pins['g2_prepared'], 'preparation_audit_ref': pins['g2_preparation_audit'],
    'compiled_exe_ref': pins['g2_exe'], 'phases': ['execute'], 'case_count': 29,
    'finite_future_roster': [row['selector'] for row in spec['roster']],
    'output_root': spec['output_root'], 'work_root': spec['work_root'], 'prepared_inputs': 41958,
    'MODEL_loopback_maximum': 4, 'external_paid_MODEL_calls': 0, 'bootstrap_HTTP': 'UNKNOWN_NOT_INSTRUMENTED',
    'actual_grant_write': 'Only after actual CAS313 and exact CP scope pin: write completed=true grant with actual fe01bef prepared SHA; no prepare phase or broad selector.',
    'input_closure': 'Prepared actual Go/SDK/Python/OS/WORK/archive/exe plus new scope/grant/controller/CP snapshot and actual phase runtime. Every case before/nativeafter/fixtureafter complete vector, late unbound resource stops.',
    'DB_limits': 'Fixture VACUUM INTO snapshots; independent typed rows/schema/integrity and unchanged snapshot bytes; original file bytes/storage types/implicit rowid are not claimed.',
    'native_timeout_seconds': 150, 'outer_timeout_seconds': 180, 'owned_job_cleanup_seconds': 5,
    'first_unexpected_stop': True, 'same_input_automatic_retry': False, 'start_index_or_resume': False,
    'source_writes': 0, 'Main_product_source_writes': 0, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0,
    'limits': 'Finite development G2 only; no heldpositive2/LIVE/billingupper/fullwhole9/Main/all22/42 acceptance.'})
old = (PREVIOUS / 'register.py').read_text('utf-8')
header = old[:old.index("pins = prepared['pins']")].replace('[311, 139, 384]', '[312, 140, 386]')
mutation = '''pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
assert scope['registration_checkpoint'] == 313 and scope['phases'] == ['execute'] and scope['case_count'] == 29
assert scope['prepared_ref']['sha256'] == 'fe01bef395b10c5308d28ce006bc42fca6a7465d6847ddc1711586f449ab60ec'
assert not (Path(scope['output_root']) / 'execute').exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 2
for row in prepared['origins']:
    assert row['origin_key'] not in old_keys and (row['actual_outer_exit'] == 1 or row['actual_native_exit'] == 1)
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_TOOL_ORIGIN_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:386] == old_failures and len(cp['failure_counters']) == 388
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(provider_g2_execute_scope_ref=pins['scope'],
    provider_g2_independent_prepared_ref=pins['g2_prepared'], provider_g2_independent_preparation_audit_ref=pins['g2_preparation_audit'],
    provider_g2_finite_state='NONAUTHOR_PREPARE_COMPILED_41958_INPUTS_EXECUTE_EXACT29_AUTHORIZED_NOT_EXECUTED',
    desktop_http_exact15_latest_failure_ref=pins['desktop_failure'],
    desktop_http_exact15_state='SOURCE_IMPLEMENTATION_ACTIVE_VITE_MISSING_PUBLIC_TOKEN_ORIGIN_RETAINED_TARGETED_BUILDER_FIX',
    session_list_closedcopy_exact1_state='DEDICATED_WORKTREE_READY_SOURCE_IMPLEMENTATION_ACTIVE')
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
subtasks['provider_g2_independent_prepare'].update(state='ACTUAL_COMPILED_NO_CASES', prepared_ref=pins['g2_prepared'], audit_ref=pins['g2_preparation_audit'])
assert 'provider_g2_independent_execute29' not in subtasks
subtasks['provider_g2_independent_execute29'] = {'owner': 'codex:/root', 'current_source_writer': None, 'paths': [],
    'scope_ref': pins['scope'], 'candidate_source_commit': scope['candidate'], 'state': 'EXACT29_EXECUTION_AUTHORIZED_NOT_EXECUTED',
    'prepared_ref': pins['g2_prepared'], 'receipt_namespace': scope['output_root'], 'source_ready': False,
    'source_acceptance': False, 'Main_product_source_writes': 0, 'formal_increment': 0}
assert subtasks['session_list_closedcopy_exact1']['current_source_writer'] == 'codex:/root/command_queue_impl'
assert ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer'] == 'codex:/root/sources_parent_impl'
cp['failure_chains']['W05-99/r312-review-boundary-and-Desktop-development-resource'] = {
    'actual_failed_invocations': 2, 'original386_prefix_unchanged': True, 'counter_reset': False,
    'audit_ref': pins['audit'], 'failure_cut_ref': pins['failure_cut'], 'automatic_same_input_retry': False}
cp['next_command'] = 'Root finiteG2 exact29/newpreparedfe01/e01exe execution authorized; 4MODEL loopback maximum/externalpaid0/bootstrapHTTPunknown. SourceDesktop15 targeteddevelopmentresourcefix and Cmdclosedcopyexact1 implementations active in disjointworktrees. Preserve386+2=388 and all old failures; Main2cdb, source/formal acceptance HOLD.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'G2_ACTUAL_PREPARED_FINITE29_EXECUTION_SCOPE_REGISTERED',
    'scope_ref': pins['scope'], 'audit_ref': pins['audit'], 'failure_origins_before': 386,
    'failure_origins_after': 388, 'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=313, expected_previous_revision=312, updated_at=now, updated_by='codex:/root')
ow.update(revision=141, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
'''
tail = old[old.index('for path, raw in before.items():'):old.index("handoff_ref = save('handoff-r312-running.json'")]
tail = tail.replace('root312.tmp', 'root313.tmp').replace('[312, 140, 386]', '[313, 141, 388]').replace('[:384]', '[:386]').replace('old384_', 'old386_')
tail = tail.replace('[311, 312]', '[312, 313]').replace('[139, 140]', '[140, 141]').replace('[384, 386]', '[386, 388]')
tail = tail.replace("'checkpoint': 312", "'checkpoint': 313").replace("'ownership': 140", "'ownership': 141").replace("'failure_origins': 386", "'failure_origins': 388")
tail = tail.replace("'new_closedcopy_exact1_source_lease_and_CLI221_finite_record_only': True", "'new_actual_prepared_G2_finite29_execution_only': True")
handoff = '''handoff_ref = save('handoff-r313-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 313, 'failure_origins': 388, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'G2_scope_ref': pins['scope'], 'prepared_ref': pins['g2_prepared'],
    'next': 'Root exact29 G2 execute once; SourceDesktop15 and Cmdclosedcopyexact1 continue independently.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 313, 'ownership': 141, 'failure_origins': 388, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
register = script(OUT / 'register.py', header + mutation + tail + handoff)
wrapper = (PREVIOUS / 'run.py').read_text('utf-8').replace('root_registration_r312_readonly_review_codex', 'root_registration_r313_readonly_review_codex')
wrapper = wrapper.replace("review['expected_before'] == [311, 139, 384] and review['expected_after'] == [312, 140, 386]", "review['expected_before'] == [312, 140, 386] and review['expected_after'] == [313, 141, 388]")
wrapper = wrapper.replace("cp['revision'] == 311 and len(cp['failure_counters']) == 384", "cp['revision'] == 312 and len(cp['failure_counters']) == 386")
wrapped = script(OUT / 'run.py', wrapper)
launch = (AUDIT / 'launch.v2.py').read_text('utf-8')
launch = launch.replace('complete-public-graph-and-g2-r310', OUT.name).replace('prepared_refs.v2.json', 'prepared_refs.json')
launch = launch.replace("cp['revision'] == 310 and len(cp['failure_counters']) == 384", "cp['revision'] == 313 and len(cp['failure_counters']) == 388")
launch = launch.replace('g2_prepare_scope.v2.json', 'scope_registration.json').replace('provider_g2_prepare_scope_ref', 'provider_g2_execute_scope_ref')
launch = launch.replace("prepared['pins']['g2_scope']", "prepared['pins']['scope']")
launch = launch.replace("value['phases'] == ['prepare'] and value['prepare_product_test_cases'] == 0", "value['phases'] == ['execute'] and value['case_count'] == 29")
launch = launch.replace("runner = DRAFT / 'g2_replay.v4.py'", "runner = ROOT / value['runner_ref']['path']")
launch = launch.replace("assert not Path(spec['output_root']).exists() and not Path(spec['work_root']).exists()", "assert ref(ROOT / value['prepared_ref']['path']) == value['prepared_ref']\nassert value['prepared_ref']['sha256'] == 'fe01bef395b10c5308d28ce006bc42fca6a7465d6847ddc1711586f449ab60ec'\nassert not (Path(spec['output_root']) / 'execute').exists()")
launch = launch.replace("'registration_checkpoint': 310", "'registration_checkpoint': 313").replace("'phases': ['prepare']", "'phases': ['execute'], 'prepared_sha256': value['prepared_ref']['sha256']")
launch = launch.replace("'product_test_cases_authorized_now': 0", "'product_test_cases_authorized_now': 29").replace("'SDK_MODEL_external_paid_calls_authorized_now': 0", "'MODEL_loopback_maximum': 4, 'external_paid_calls_authorized_now': 0")
launch = launch.replace("'execute_requires_future_actual_prepared_SHA_and_new_immutable_grant': True", "'actual_prepared_SHA_bound': True")
launch = launch.replace('authorization.prepare.json', 'authorization.execute.json').replace("'--phase', 'prepare'", "'--phase', 'execute'")
launchout = OUT.parent / 'root-g2-execute29-launch-r313'
assert not launchout.exists()
launchout.mkdir()
launcher = script(launchout / 'launch.py', launch)
pins['launcher'] = launcher
pins['audit'] = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1', 'actor': 'codex:/root',
    'state': 'DRAFT_PENDING_NONAUTHOR_REVIEW', 'expected_before': [312, 140, 386], 'expected_after': [313, 141, 388],
    'scope_ref': pins['scope'], 'actual_prepared_ref': pins['g2_prepared'], 'launcher_ref': launcher,
    'new_origins': origins, 'old386_prefix_unchanged': True, 'desktop_native1_outer0_preserved': True,
    'maximum_active_construction_tasks': 2, 'both_source_writers_preserved': True,
    'G2_execution_source_writes': 0, 'Main_source_integration': False, 'formal_increment': 0,
    'actual_grant_write_after_CAS_only': True, 'prepare_not_granted': True})
prepared_refs = {'canonical_before': [pin(path) for path in CANON], 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins, 'origins': origins,
    'verified_refs': [pin(path) for path in READS if path not in CANON], 'actual_source_exports_compile_cases': 0}
prepared_ref = save('prepared_refs.json', prepared_refs)
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'state': 'G2_EXECUTE_DRAFT_NOT_EXECUTED', 'register': register, 'wrapper': wrapped,
    'prepared': prepared_ref, 'audit': pins['audit'], 'scope': pins['scope'], 'launcher': launcher}, ensure_ascii=True))
