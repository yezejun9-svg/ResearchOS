"""Root-only r324 metadata generator. Preparation is not a registration or grant."""
import ast
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

MODE = 'seal'
ROOT = Path('D:/作品集/ResearchOS/research-os')
NS = ROOT / 'execution/v2.4/receipts/W05/W05-99'
OUT = Path(__file__).absolute().parent
PRIOR = NS / 'integration_codex/cli-exact8-source-integration-r323'
EXPECTED_OUT = NS / 'integration_codex/cli43-post-integration-r324'
EXECUTOR = NS / 'cli_exact8_integration_executor_codex/9f85939ef58d497895485094712d3672'
LAUNCHER = NS / 'cli_exact8_integration_root_launcher_codex/2ad2a87d8f3b4051b9931e69b30b8726'
BASE = 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
TARGET = 'a510dbef4a7e08fb5c428df44c39b133f3ffa856'
CANDIDATE = 'b98738ac093ea55bb8700cfa724ddd9e6b2a1251'
CANON = [ROOT / 'execution/v2.4' / (n + '.json') for n in ['checkpoint', 'path_ownership', 'step_state', 'commands']]
STATUS_SHA = 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
LOCK_SHA = '0958d3f313e8d09d471521787a2b8b9480a17a91d6e4aa722393741dcbd8e663'
READS = {}
EXTERNAL = {}
GIT_CALLS = 0


def parse(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            assert key not in result, 'duplicate JSON key'
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def path(value):
    p = Path(value)
    p = p if p.is_absolute() else ROOT / p
    assert '..' not in p.parts and p.absolute() == p.resolve()
    assert p.is_relative_to(ROOT) or p in EXTERNAL, 'not an exact sealed public runtime resource'
    for item in [p, *p.parents]:
        if item == ROOT.parent:
            break
        assert item.exists() and not item.is_symlink() and not (getattr(item.lstat(), 'st_file_attributes', 0) & 0x400)
    return p


def ref(value, expected=None):
    p = path(value)
    raw = p.read_bytes()
    result = {'path': p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    if not p.is_relative_to(ROOT):
        assert result['sha256'] == EXTERNAL[p]['sha256'] and result['bytes'] == EXTERNAL[p]['bytes']
    assert expected is None or result['sha256'] == expected
    if p in READS:
        assert result == READS[p], 'input changed: ' + str(p)
    READS[p] = result
    return result


def verify(item):
    actual = ref(item['path'], item['sha256'])
    assert actual['bytes'] == item['bytes']
    return actual


def same(a, b):
    return verify(a) == verify(b)


def doc(item):
    verify(item)
    return parse(path(item['path']).read_bytes())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def save_raw(name, raw):
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return ref(OUT / name)


def save(name, value):
    return save_raw(name, encoded(value))


def manifest(item, required=()):
    value = doc(item)
    entries = value['entries']
    assert 'count' not in value or value['count'] == len(entries)
    parent = path(item['path']).parent
    found = {}
    for member in entries:
        p = path(member['path'])
        assert p.is_relative_to(parent) and p not in found
        verify(member)
        found[p] = member
    for member in required:
        assert path(member['path']) in found and same(member, found[path(member['path'])])
    return found


def contained(value, wanted):
    if isinstance(value, dict):
        if {'path', 'sha256', 'bytes'} <= value.keys():
            candidate = Path(value['path'])
            candidate = candidate if candidate.is_absolute() else ROOT / candidate
            target = Path(wanted['path'])
            target = target if target.is_absolute() else ROOT / target
            if candidate.absolute() == target.absolute() and value['sha256'] == wanted['sha256'] and value['bytes'] == wanted['bytes']:
                return True
        return any(contained(x, wanted) for x in value.values())
    return isinstance(value, list) and any(contained(x, wanted) for x in value)


def tool_lock():
    assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize
    assert Path.cwd().resolve() == ROOT and OUT == EXPECTED_OUT
    # Only the exact 184 public Python/Git/OS resources already sealed by the
    # actual import are readable outside ROOT. No external output is possible.
    before_ref = ref(EXECUTOR / 'immutable-inputs.before.json', 'bcfb9da7720cc517a8b51a4d82dd7878022f01b4c4c18377131367af6bd16ed7')
    after_ref = ref(EXECUTOR / 'immutable-inputs.after.json', '3f1e4c7d553149ba5094a123a32bd64bb170cd277150bd0740b5ca0200fbebd1')
    groups = []
    for item in [before_ref, after_ref]:
        group = {}
        for row in doc(item):
            p = Path(row['path'])
            p = p if p.is_absolute() else ROOT / p
            if not p.is_relative_to(ROOT):
                assert p.is_absolute() and '..' not in p.parts and p not in group
                group[p] = (row['sha256'], row['bytes'])
        groups.append(group)
    assert len(groups[0]) == 184 and groups[0] == groups[1]
    EXTERNAL.update({p: {'sha256': value[0], 'bytes': value[1]} for p, value in groups[0].items()})
    lock = doc(ref(ROOT / 'execution/toolchains/locked.json', LOCK_SHA))['tools']
    assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
    for name in ['python', 'git']:
        assert hashlib.sha256(Path(lock[name]['path']).read_bytes()).hexdigest() == lock[name]['sha256']
    return lock


def git_read(lock, label, args):
    global GIT_CALLS
    GIT_CALLS += 1
    assert GIT_CALLS <= 24
    assert args[0] in {'rev-parse', 'status', 'diff', 'ls-tree', 'rev-list'}
    argv = [lock['git']['path'], '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false', *args]
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='nul', GIT_TERMINAL_PROMPT='0')
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = None
    error = None
    try:
        result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=30)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        stdout = save_raw(label + '.stdout.raw', result.stdout if result is not None else b'')
        stderr = save_raw(label + '.stderr.raw', result.stderr if result is not None else b'')
        save(label + '.invocation.json', {'argv': argv, 'cwd': str(ROOT), 'started_at': started,
            'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actual_native_exit': result.returncode if result is not None else None,
            'wrapper_error': error, 'stdout_ref': stdout, 'stderr_ref': stderr, 'automatic_retry': False, 'operation': 'READONLY_GIT'})
    assert result.returncode == 0
    return result.stdout


def source_guard(lock, prefix):
    for name in ['python', 'git']:
        assert hashlib.sha256(Path(lock[name]['path']).read_bytes()).hexdigest() == lock[name]['sha256']
    assert git_read(lock, prefix + '-head', ['rev-parse', 'HEAD']).decode().strip() == TARGET
    status = git_read(lock, prefix + '-status', ['status', '--porcelain=v1', '--untracked-files=no'])
    assert hashlib.sha256(status).hexdigest() == STATUS_SHA and len(status.splitlines()) == 13
    assert sum(row[:2] == b' D' for row in status.splitlines()) == 11
    assert git_read(lock, prefix + '-index', ['diff', '--cached', '--name-only']) == b''
    return status


def job_ok(value):
    assert value['actual_exit'] == 0 and value['timed_out'] is False and value['error'] is None
    assert value['owned_child_pid'] > 0 and value['creation_time_100ns'] > 0 and value['resumed'] is True
    clean = value['job_cleanup']
    for key in ['unnamed_exclusive_job', 'kill_on_job_close_configured', 'assigned_before_resume', 'job_idle_confirmed', 'primary_exit_confirmed', 'handles_closed']:
        assert clean[key] is True
    assert clean['active_processes_last_observed'] == 0 and clean['errors'] == []


def tree(raw):
    result = {}
    for row in raw.split(b'\0'):
        if not row:
            continue
        attrs, filename = row.split(b'\t', 1)
        mode, kind, blob = attrs.decode('ascii').split(' ')
        name = filename.decode('utf-8')
        assert name not in result
        result[name] = {'mode': mode, 'kind': kind, 'blob': blob}
    return result


def metadata(before, pins, origins, stamp):
    oldcp, oldow = [parse(raw) for raw in before[:2]]
    assert [oldcp['revision'], oldow['revision'], len(oldcp['failure_counters'])] == [323, 151, 425]
    assert oldcp['head'] == BASE and len(origins) == 5
    assert len({row['evidence_ref']['sha256'] for row in origins}) == 5
    for row in origins:
        assert not contained(oldcp['failure_counters'], row['evidence_ref'])
    cp, ow = copy.deepcopy(oldcp), copy.deepcopy(oldow)
    cp['failure_counters'].extend(copy.deepcopy(origins))
    assert cp['failure_counters'][:425] == oldcp['failure_counters']
    additions = {
        'cli_exact8_source_integration_state': 'CLI_EXACT8_SOURCE_COMMIT_CLOSED_PENDING_FRESH43_VALIDATION',
        'cli_exact8_source_integration_completed_ref': pins['cli_completed'],
        'cli_exact8_source_integration_manifest_ref': pins['cli_manifest'],
        'cli_exact8_source_integration_grant_ref': pins['cli_grant'],
        'cli_exact8_source_integration_pre_registration_review_ref': pins['cli_pre_registration_review'],
        'cli_exact8_actual43_head': TARGET, 'cli_exact8_actual_combined_source_paths': 43,
        'cli_exact8_fresh43_validation_authorized': False,
        'r324_registered_postcut_origin_refs': [x['evidence_ref'] for x in origins],
        'r323_cut_pending_actual_tool_origins_state': 'REGISTERED_ONCE_IN_R324_ORIGINAL_R323_FIELDS_RETAINED',
        'r324_observed_actual_tool_origin_lower_bound': 430,
        'r324_postcut_pending_actual_tool_origin_refs': [pins['aftercut_pending_origin']],
        'observed_actual_tool_origin_lower_bound_after_r324_cut': 431,
        'desktop15_actual_integration_authorized': False}
    cp['work_in_progress'].update(additions)
    cp['head'] = TARGET
    cp.update(revision=324, expected_previous_revision=323, updated_at=stamp, updated_by='codex:/root')
    cp['next_command'] = 'Source-only CLI43 import closed; wait for independent r324 registration review/CAS/seal and future separately authorized fresh43 validation. No Desktop/compile/product execution grant.'
    cp['integrity_events'].append({'event': 'ROOT_R324_CLI43_FORWARD_HEAD_REGISTRATION', 'actor': 'codex:/root', 'at': stamp,
        'before': [323, 151, 425], 'after': [324, 152, 430], 'head_before': BASE, 'head_after': TARGET,
        'completed_ref': pins['cli_completed'], 'origin_refs': [x['evidence_ref'] for x in origins], 'counter_reset': False, 'formal_increment': 0})
    for item in pins.values():
        if isinstance(item, dict) and 'path' in item and item['path'] not in cp['evidence_index']:
            cp['evidence_index'].append(item['path'])
    sub = ow['card_path_bindings']['W05-99']['subtasks']['cli_exact8_source_integration']
    assert sub['owner'] == sub['current_source_writer'] == 'codex:/root' and len(sub['source_paths']) == 8
    sub.update(current_source_writer=None, state='CLI_EXACT8_SOURCE_COMMIT_CLOSED_PENDING_FRESH43_VALIDATION',
        actual_head=TARGET, actual_unique_source_paths=43, completed_ref=pins['cli_completed'], manifest_ref=pins['cli_manifest'],
        grant_ref=pins['cli_grant'], source_acceptance=False, formal_increment=0, compile_test_SQL_HTTP_model_authorized=False)
    ow.update(revision=152, amended_at=stamp, amended_by='codex:/root')
    comparison = copy.deepcopy(ow)
    comparison['card_path_bindings']['W05-99']['subtasks']['cli_exact8_source_integration'] = oldow['card_path_bindings']['W05-99']['subtasks']['cli_exact8_source_integration']
    for key in ['revision', 'amended_at', 'amended_by']:
        if key in oldow:
            comparison[key] = oldow[key]
        else:
            comparison.pop(key, None)
    assert comparison == oldow
    allowed = {'head', 'revision', 'expected_previous_revision', 'updated_at', 'updated_by', 'failure_counters', 'work_in_progress', 'next_command', 'integrity_events', 'evidence_index'}
    assert {k: v for k, v in cp.items() if k not in allowed} == {k: v for k, v in oldcp.items() if k not in allowed}
    assert {k: v for k, v in cp['work_in_progress'].items() if k not in additions} == {k: v for k, v in oldcp['work_in_progress'].items() if k not in additions}
    assert cp['current_effective_formal_status'] == oldcp['current_effective_formal_status']
    return [encoded(cp), encoded(ow), before[2], before[3]]


def origin_rows():
    pending_ref = ref(PRIOR / 'postcut.pending-origins.v2.json', '0f35456dd9ba3dba9df918c6b1553256a0fc00cb22d986fba0ff7da4bcb071a9')
    pending = doc(pending_ref)
    assert pending['registration_cut_after'] == [323, 151, 425] and pending['observed_lower_bound'] == 427
    assert len(pending['origin_refs']) == len(pending['origins']) == 2
    result = copy.deepcopy(pending['origins'])
    for index, row in enumerate(result):
        original = doc(pending['origin_refs'][index])
        assert same(row['evidence_ref'], pending['origin_refs'][index]) and row['original_payload'] == original
        assert row['actual_outer_exit'] == 1 and row['actual_native_exit'] == [None, 1][index]
        assert row['actual_native_product_exit'] is None and row['product_cases_run'] == 0
    specs = [
        (NS / 'cli43_source_execution_independent_review_codex/64a5eacda0874c5eb320f85254391541/failure_origin.json', 'b2722178bc7acd1c1c7ccf8130cfd838b964d4211538c0672becd9d9385e6b45', 'w05-cli43-readonly-audit-fdd482-session49811-07a507', 1),
        (NS / 'cli43_r324_generator_preparation_codex/f8ec2179d36d4bd3a1c83ed0c4e894a8/failure-origin.windows206.json', '513cdfab9bc4c6547740b6f23991384d18c980712d71ea9ec8dfea177e7b04f2', 'r324-generator-write-windows206', None),
        (OUT / 'failure-origin.99b072.json', '6ebe965fc483aee035d4cf672edd3a1ace9dc53ef6f9e37609f9046933e9bd20', 'root-readonly-mu-path-search-99b072', 1)]
    for index, (p, sha, key, outer) in enumerate(specs):
        evidence = ref(p, sha)
        original = doc(evidence)
        if index == 0:
            assert original['observed_outer_exit'] == 1 and original['independently_captured_native_exit'] is None
            assert original['product_execution'] == original['Git_calls_before_failure'] == original['source_or_canonical_writes'] == 0
        elif index == 1:
            assert original['actual_outer_exit'] is None and original['actual_native_exit'] is None and original['native_process_started'] is False
            assert original['generator_executions'] == original['canonical_source_index_writes'] == original['product_cases_run'] == 0
        else:
            assert original['actual_outer_exit'] == 1 and original['actual_native_exit'] is None
            assert original['source_canonical_index_writes'] == original['product_calls'] == 0
        result.append({'origin_key': key, 'actor': original['actor'], 'actual_outer_exit': outer,
            'actual_native_exit': None, 'actual_native_product_exit': None, 'product_cases_run': 0,
            'evidence_ref': evidence, 'original_payload': original})
    for row in result:
        row.update(attempts=1, retries_used=0, count_once=True, counter_reset=False,
            status='ACTUAL_TOOL_EVENT_PRESERVED_NO_PRODUCT_FAILURE_INFERENCE', formal_increment=0)
    assert len(result) == 5
    return pending_ref, result


def prepare():
    lock = tool_lock()
    assert len(sys.argv) == 1, 'All currently sealed evidence refs are fixed; no guessed future arguments.'
    output_names = ['register.py', 'run.py', 'seal.py', 'audit.json', 'prepared_refs.json', 'source43.before-registration.json', 'registration-input-closure-manifest.json']
    output_names += [p.stem + suffix for p in CANON for suffix in ['.original.json', '.desired.json']]
    assert all(not (OUT / name).exists() for name in output_names), 'exclusive preparation only; no retry/overwrite'
    scope_ref = ref(PRIOR / 'scope_registration.json', '52d8f686f07a606afaeb64eccca26f53edb2872bf93fa595132fd6afc067da71')
    scope = doc(scope_ref)
    assert scope['base'] == BASE and scope['candidate'] == CANDIDATE
    assert scope['expected_registration'] == [323, 151, 425] and scope['exact_paths'] == 8 and scope['union_paths'] == 43
    review_root = NS / 'cli43_source_execution_independent_review_codex/a8c41f3ed8da4bc998e2392ff9648c9d'
    review_ref = ref(review_root / 'review.v2.json', '596ae49ce21948db66418639af8cff267bd140af9c66914a7cf15fdee9b458aa')
    review_mf = ref(review_root / 'manifest.v2.json', '19c04daffd6baf7a291829bebb63eeef9e326d2b1b1346077cdff65cccd551a1')
    review_handoff = ref(review_root / 'handoff.v2.json', '4c5bf6bf660057463c1f1ec1930f5c821a155daeaaad1c6a468b9dfc93663a7c')
    review = doc(review_ref)
    assert review['schema'] == 'researchos.cli43-source-import-pre-registration-review.v1'
    assert review['reviewer'] == 'codex:/root/w05_merge_review' and review['requested_changes'] == []
    assert review['decision'] == 'EXACT8_SOURCE_IMPORT_EVIDENCE_CLOSED_PENDING_HEAD_REGISTRATION_AND_FRESH43_VALIDATION'
    assert review['post_registration_audit_ref'] is None and review['actual_product_execution_by_reviewer'] is False
    manifest(review_mf, [review_ref])  # Handoff is explicitly later than this immutable manifest.
    rh = doc(review_handoff)
    assert same(rh['review_ref'], review_ref) and same(rh['manifest_ref'], review_mf)
    closure_ref = save('registration-input-closure-manifest.json', {'schema': 'researchos.registration-input-closure-manifest.v1',
        'entries': [review_ref, review_mf, review_handoff], 'count': 3, 'original_manifest_unchanged': True,
        'handoff_written_after_original_manifest': True, 'authority_expanded': False})
    completed_ref = review['completed_ref']  # Preserve actual MF ABS spelling for the future Desktop contract.
    completed = doc(completed_ref)
    emref = review['manifest_ref']
    assert path(completed_ref['path']) == EXECUTOR / 'completed.json' and path(emref['path']) == EXECUTOR / 'manifest.json'
    assert completed_ref['sha256'] == '7eeebf9ae9502ed59afa94a58c79702b62839237e32a7ed3424f11074e6babc3'
    assert emref['sha256'] == 'ef2eefaf0240c672b68e9e4c98fdc1e4b4aeb7c68188683f7492f82adf74dbca'
    members = manifest(emref, [completed_ref])
    assert len(members) == 105 and members[path(completed_ref['path'])] == completed_ref
    assert completed['status'] == 'CLI_EXACT8_SOURCE_COMMIT_CLOSED_PENDING_FRESH43_VALIDATION'
    assert completed['actor'] == 'codex:/root' and completed['parent'] == BASE and completed['actual_new_commit'] == TARGET and completed['source_candidate'] == CANDIDATE
    assert completed['apply_attempts'] == completed['commit_attempts'] == 1 and completed['Git_steps'] == 32
    assert completed['unique_combined_paths'] == 43 and completed['canonical_writes'] == completed['compile_SQL_HTTP_models'] == completed['formal_increment'] == 0
    assert same(completed['scope_ref'], scope_ref)
    calls = [p for p in members if p.name.endswith('.invocation.json')]
    assert len(calls) == 32
    for p in calls:
        call = doc(members[p])
        assert call['actual_native_exit'] == 0 and call['wrapper_error'] is None and call['automatic_retry'] is False
        job_ok(call['process_observation'])
        stem = p.name.removesuffix('.invocation.json')
        assert p.with_name(stem + '.stdout.raw') in members and p.with_name(stem + '.stderr.raw') in members
    lmref = review['launcher_manifest_ref']
    assert path(lmref['path']) == LAUNCHER / 'manifest.json'
    lm = manifest(lmref)
    lc = doc(lm[LAUNCHER / 'completed.json'])
    assert lc['actual_controller_native_exit'] == 0 and lc['Go_compile_test_SQL_HTTP_models'] == 0
    assert same(lc['scope_ref'], scope_ref) and same(lc['grant_ref'], completed['grant_ref'])
    for label in ['grant-preflight', 'source-only-integration']:
        actual = doc(lm[LAUNCHER / (label + '.owned-result.json')])
        assert actual['wrapper_error'] is None and actual['actual_native_exit'] == 0
        job_ok(actual['result'])
        for suffix in ['.invocation.json', '.stdout.raw', '.stderr.raw']:
            assert LAUNCHER / (label + suffix) in lm
    grant_ref = completed['grant_ref']
    grant = doc(grant_ref)
    assert grant['actor'] == 'codex:/root' and grant['status'] == 'ROOT_REGISTERED_EXECUTION_AUTHORIZED'
    assert grant['actual_registration_completed'] is True and grant['automatic_retry'] is False and same(grant['scope_ref'], scope_ref)
    assert grant['base'] == BASE and grant['candidate'] == CANDIDATE and grant['operation_uuid'] == scope['operation_uuid']
    assert same(grant['controller_review_ref'], review['integration_controller_review_ref'])
    manifest(review['grant_manifest_ref'], [grant_ref])
    prior_handoff = ref(PRIOR / 'handoff-r323-running.json', 'f0d6ae986711a38dc670b9d8664d7fdeb5592545d86230bfd3d4069bd3d3c9d1')
    prior_mf = ref(PRIOR / 'manifest.json', 'e61b3d4da841220a6f3fb62806a702c85e415403b2ecb264bc6e186ba70c4075')
    manifest(prior_mf, [prior_handoff, scope_ref, review['registration323_audit_ref']])
    before = [p.read_bytes() for p in CANON]
    cp, ow = [parse(raw) for raw in before[:2]]
    assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [323, 151, 425] and cp['head'] == BASE
    assert len(grant['canonical_copies']) == 4
    for p, raw, row, prior_pin in zip(CANON, before, grant['canonical_copies'], doc(prior_handoff)['canonical_refs']):
        assert path(row['canonical_path']) == p and same(ref(p), prior_pin)
        assert path(row['ref']['path']).read_bytes() == raw
        verify(row['ref'])
        previous = PRIOR / (p.stem + ('.desired.json' if p in CANON[:2] else '.original.json'))
        assert previous.read_bytes() == raw
        ref(previous)
    assert same(cp['work_in_progress']['cli_exact8_source_integration_scope_ref'], scope_ref)
    assert same(cp['work_in_progress']['cli_exact8_source_integration_controller_review_ref'], review['integration_controller_review_ref'])
    for registration_ref in grant['registration_refs'].values():
        if isinstance(registration_ref, dict) and {'path', 'sha256', 'bytes'} <= registration_ref.keys():
            verify(registration_ref)
    outer_ref = ref(OUT / 'outer-completion.json', 'de347277754507f5686f4a9918d29fba41387725ec8d100a1089d13192249f91')
    outer = doc(outer_ref)
    assert outer['actual_tool_outer_exit'] == 0 and outer['separately_measured_outer_python_native_exit'] is None
    assert outer['actual_invocation_count'] == 1 and outer['actual_registered_before'] == [323, 151, 425]
    known_ref = ref(OUT / 'tool-completion.13b080.known-fields.json', '156b63eaa744989763c847a09a25706a38b30692180f3527cf547885e26483f6')
    known = doc(known_ref)
    assert known['not_native_raw_stream'] is True and known['not_complete_original_tool_payload'] is True
    pins = {'scope': scope_ref, 'cli_completed': completed_ref, 'cli_manifest': emref, 'cli_grant': grant_ref,
        'cli_launcher_manifest': lmref, 'cli_grant_manifest': review['grant_manifest_ref'],
        'cli_pre_registration_review': review_ref, 'cli_pre_registration_review_manifest': review_mf,
        'cli_pre_registration_review_handoff': review_handoff, 'review_input_closure': closure_ref,
        'previous_handoff': prior_handoff, 'previous_manifest': prior_mf, 'outer_completion': outer_ref,
        'outer_known_fields_transcription': known_ref,
        'public_resource_observation': ref(OUT / 'public-model-resource-recheck.json', '3ef22662fa911d86396c74533ea10e04a81369fcd56f4424f23ed3788c110843')}
    pins['aftercut_pending_origin'] = ref(NS / 'cli43_fresh_compiler_preparation_codex/7bf10c8e8cc54412ba7bb89b53f5a622/failure-origin.e1bbac.json', '31476b8568f1e2e7b8e9b80200f7ec3c81e3e91e7d13d2c8c9060fb23b67ba34')
    for key in ['main38_completed_ref', 'main38_manifest_ref', 'main38_post_registration_audit_ref', 'main38_execution_review_ref']:
        pins[key.removesuffix('_ref')] = scope[key]
        verify(scope[key])
    manifest(scope['main38_manifest_ref'], [scope['main38_completed_ref']])
    assert doc(scope['main38_post_registration_audit_ref'])['registered_head'] == BASE
    assert doc(scope['main38_execution_review_ref'])['decision'] == 'EXACT38_MAIN_SOURCE_INTEGRATION_EVIDENCE_CLOSED'
    protected = doc(scope['protected_source_vector_ref'])
    planned = doc(scope['protected_source_paths_ref'])
    assert len(protected) == len(planned) == 6839
    assert sorted(path(x['path']).relative_to(ROOT).as_posix() for x in protected) == planned
    for item in protected:
        verify(item)
    assert any(x['sha256'] == '2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441' for x in protected)
    pins['protected_source_vector'] = scope['protected_source_vector_ref']
    inputs = []
    for name, count in [('immutable-inputs.before.json', 7266), ('immutable-inputs.after.json', 7271)]:
        rows = doc(members[EXECUTOR / name])
        assert len(rows) == count and len({path(x['path']) for x in rows}) == count
        inputs.append({path(x['path']): verify(x) for x in rows})
    assert all(inputs[1].get(k) == v for k, v in inputs[0].items())
    status = source_guard(lock, 'prepare')
    current = tree(git_read(lock, 'prepare-tree', ['ls-tree', '-rz', TARGET]))
    recorded = tree(path(members[EXECUTOR / 'tree-after.stdout.raw']['path']).read_bytes())
    assert current == recorded
    base_tree = tree(path(members[EXECUTOR / 'tree-base.stdout.raw']['path']).read_bytes())
    expected = dict(base_tree)
    exact = doc(scope['exact8_ref'])
    assert len(exact) == 8 and [x['path'] for x in exact] == completed['source_paths']
    for row in exact:
        assert expected[row['path']] == row['a5_preimage'] and current[row['path']] == row['after_git']
        expected[row['path']] = row['after_git']
        actual = ref(ROOT / row['path'], row['after_sha256'])
        assert actual['bytes'] == row['after_bytes']
    assert current == expected
    assert git_read(lock, 'prepare-parent', ['rev-list', '--parents', '-n', '1', TARGET]).decode().split() == [TARGET, BASE]
    union = git_read(lock, 'prepare-union', ['diff', '--name-only', '-z', '2cdb0d43d5a600eef13c8f1735946a9adf52d079', TARGET]).decode('utf-8').rstrip('\0').split('\0')
    assert len(union) == len(set(union)) == 43 and sorted(union) == sorted(review['input_closure']['source43_paths'])
    current_sources = []
    for name in union:
        p = ROOT / name
        raw = p.read_bytes()
        assert current[name]['mode'] == '100644' and current[name]['kind'] == 'blob'
        assert hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest() == current[name]['blob']
        current_sources.append({'source_ref': ref(p), 'git_entry': current[name]})
    pins['source43_vector'] = save('source43.before-registration.json', {'base': '2cdb0d43d5a600eef13c8f1735946a9adf52d079', 'head': TARGET, 'count': 43, 'entries': current_sources})
    pending_ref, origins = origin_rows()
    pins['original_r323_pending_bundle'] = pending_ref
    for index, row in enumerate(origins):
        pins['origin_' + str(index + 1)] = row['evidence_ref']
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    desired = metadata(before, pins, origins, stamp)
    originals = [save_raw(p.stem + '.original.json', raw) for p, raw in zip(CANON, before)]
    desired_refs = [save_raw(p.stem + '.desired.json', raw) for p, raw in zip(CANON, desired)]
    save_raw('git-status.original.raw', status)
    own_source = Path(__file__).read_text(encoding='utf-8')
    marker = chr(10) + 'MODE = ' + repr('prepare') + chr(10)
    assert own_source.count(marker) == 1
    scripts = {}
    for mode in ['register', 'run', 'seal']:
        text = own_source.replace(marker, chr(10) + 'MODE = ' + repr(mode) + chr(10), 1)
        ast.parse(text, filename=mode + '.py')
        scripts[mode] = save_raw(mode + '.py', text.encode('utf-8'))
    audit = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1', 'actor': 'codex:/root',
        'state': 'DRAFT_PENDING_NONAUTHOR_REGISTRATION_REVIEW', 'expected_before': [323, 151, 425], 'expected_after': [324, 152, 430],
        'actual_head': TARGET, 'prior_canonical_head': BASE, 'pins': pins, 'source_import_executions_in_preparation': 0,
        'old425_prefix_unchanged': True, 'new_origin_refs': [x['evidence_ref'] for x in origins],
        'postcut_pending_origin_refs': [pins['aftercut_pending_origin']], 'observed_lower_bound': 431,
        'source_acceptance': False, 'formal_increment': 0, 'fresh43_or_desktop_execution_authorized': False})
    prepared = save('prepared_refs.json', {'canonical_before': [ref(p) for p in CANON], 'original_refs': originals,
        'desired_refs': desired_refs, 'head': TARGET, 'canonical_head_before': BASE, 'git_status_sha256': STATUS_SHA,
        'pins': pins, 'origins': origins, 'timestamp': stamp, 'scripts': scripts, 'audit_ref': audit,
        'verified_refs': [v for p, v in sorted(READS.items(), key=lambda row: str(row[0])) if p not in CANON],
        'actual_registration_executed': False, 'source_edits_compile_test_SQL_HTTP_models': 0})
    for p, v in list(READS.items()):
        verify(v)
    assert all(p.read_bytes() == raw for p, raw in zip(CANON, before))
    print(json.dumps({'prepared_ref': prepared, 'audit_ref': audit, 'scripts': scripts, 'actual_registration_executed': False}, ensure_ascii=True))


def prepared_inputs():
    prepared = doc(ref(OUT / 'prepared_refs.json'))
    assert prepared['head'] == TARGET and prepared['canonical_head_before'] == BASE
    assert prepared['actual_registration_executed'] is False and len(prepared['origins']) == 5
    for item in prepared['verified_refs']:
        verify(item)
    for mode, item in prepared['scripts'].items():
        assert path(item['path']) == OUT / (mode + '.py')
        verify(item)
    before = [path(item['path']).read_bytes() for item in prepared['original_refs']]
    desired = [path(item['path']).read_bytes() for item in prepared['desired_refs']]
    assert len(before) == len(desired) == 4
    assert desired == metadata(before, prepared['pins'], prepared['origins'], prepared['timestamp'])
    return prepared, before, desired


def immutable_guard(prepared):
    for item in prepared['verified_refs']:
        assert path(item['path']) not in CANON
        verify(item)


def register():
    lock = tool_lock()
    assert len(sys.argv) == 1
    prepared, before, desired = prepared_inputs()
    for p, raw, pin in zip(CANON, before, prepared['canonical_before']):
        assert path(pin['path']) == p and p.read_bytes() == raw and same(ref(p), pin)
    status = source_guard(lock, 'register-before')
    assert status == (OUT / 'git-status.original.raw').read_bytes()
    intent = save('canonical-write.intent.json', {'actor': 'codex:/root', 'Main_head': TARGET,
        'transition': {'checkpoint': [323, 324], 'ownership': [151, 152], 'failures': [425, 430]},
        'register_ref': ref(Path(__file__)), 'prepared_ref': ref(OUT / 'prepared_refs.json'),
        'metadata': [{'path': p.relative_to(ROOT).as_posix(), 'original_ref': a, 'desired_ref': b,
            'write_required': index < 2} for index, (p, a, b) in enumerate(zip(CANON, prepared['original_refs'], prepared['desired_refs']))],
        'recovery': 'Forward-only exact own original/desired prefix; stop on failure; no reset, rollback, automatic retry or source execution.',
        'source_acceptance': False, 'formal_increment': 0})
    for p, raw in zip(CANON[:2], desired[:2]):
        with p.with_name(p.name + '.root324.tmp').open('xb') as stream:
            stream.write(raw)
    expected = list(before)
    phase = 'EXCLUSIVE_DESIRED_TEMP_FILES_WRITTEN'
    try:
        for index, p in enumerate(CANON[:2]):
            assert all(q.read_bytes() == b for q, b in zip(CANON, expected))
            immutable_guard(prepared)
            source_guard(lock, 'register-pre-replace-' + str(index))
            os.replace(p.with_name(p.name + '.root324.tmp'), p)
            expected[index] = desired[index]
            READS.pop(p, None)
            assert p.read_bytes() == desired[index]
            phase = p.name + '_REPLACED_AND_VERIFIED'
            save('canonical-write.' + p.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(desired[index]).hexdigest()})
        assert expected == desired and all(p.read_bytes() == raw for p, raw in zip(CANON, desired))
        immutable_guard(prepared)
        source_guard(lock, 'register-after')
        cp, ow = [parse(raw) for raw in desired[:2]]
        assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [324, 152, 430]
        assert cp['failure_counters'][:425] == parse(before[0])['failure_counters'] and cp['head'] == TARGET
        save('canonical-write.verified.json', {'checkpoint': 324, 'ownership': 152, 'failure_origins': 430,
            'intent_ref': intent, 'registered_head': TARGET, 'old425_prefix_unchanged': True,
            'five_origins_registered_once': True, 'step_state_commands_unchanged': True, 'formal_increment': 0})
    except BaseException as exc:
        save('canonical-write.exception.json', {'phase': phase, 'error': repr(exc), 'intent_ref': intent,
            'current_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in CANON},
            'automatic_retry': False, 'rollback_or_external_overwrite': False})
        raise
    handoff = save('handoff-r324-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE', 'actor': 'codex:/root',
        'Main_head': TARGET, 'canonical_refs': [ref(p) for p in CANON], 'revision': 324, 'ownership_revision': 152,
        'failure_origins': 430, 'registered_origin_refs': [x['evidence_ref'] for x in prepared['origins']],
        'postcut_pending_origin_refs': [prepared['pins']['aftercut_pending_origin']], 'pending_origin_count': 1, 'observed_lower_bound': 431,
        'counter_reset': False, 'completed_ref': prepared['pins']['cli_completed'], 'manifest_ref': prepared['pins']['cli_manifest'],
        'grant_ref': prepared['pins']['cli_grant'], 'pre_registration_review_ref': prepared['pins']['cli_pre_registration_review'],
        'previous_handoff_ref': prepared['pins']['previous_handoff'], 'source_writer': None,
        'actual_unique_source_paths': 43, 'fresh43_validation_authorized': False, 'Desktop_integration_authorized': False,
        'source_acceptance': False, 'formal_increment': 0, 'next': cp['next_command']})
    print(json.dumps({'current': [324, 152, 430], 'handoff_ref': handoff}, ensure_ascii=True))


def registration_review(prepared, item):
    review = doc(item)
    parent = path(item['path']).parent
    assert parent.parent == NS / 'root_registration_r324_readonly_review_codex'
    token = parent.name.replace('-', '')
    assert len(token) == 32 and all(c in '0123456789abcdef' for c in token)
    assert review['schema'] == 'researchos.root-registration-source-review.v1'
    assert review['reviewer'] == 'codex:/root/w05_merge_review'
    assert review['decision'] == 'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION'
    assert review['requested_changes'] == [] and review['actual_registration_executed'] is False
    assert review['expected_before'] == [323, 151, 425] and review['expected_after'] == [324, 152, 430]
    for key, name in [('register_sha256', 'register.py'), ('wrapper_sha256', 'run.py'), ('prepared_refs_sha256', 'prepared_refs.json'), ('audit_sha256', 'audit.json')]:
        assert review[key] == ref(OUT / name)['sha256']
    assert len(review['canonical_before']) == len(review['copied_canonical_before_refs']) == 4
    for actual, original, copied, stored in zip(review['canonical_before'], prepared['canonical_before'], review['copied_canonical_before_refs'], prepared['original_refs']):
        assert path(actual['path']) == path(original['path']) and actual['sha256'] == original['sha256'] and actual['bytes'] == original['bytes']
        assert path(copied['path']).is_relative_to(parent)
        verify(copied)
        assert copied['sha256'] == original['sha256'] and copied['bytes'] == original['bytes']
        assert path(copied['path']).read_bytes() == path(stored['path']).read_bytes()
    return review


def run():
    lock = tool_lock()
    assert len(sys.argv) == 3
    prepared, before, desired = prepared_inputs()
    review_ref = ref(sys.argv[1], sys.argv[2])
    registration_review(prepared, review_ref)
    assert all(p.read_bytes() == raw for p, raw in zip(CANON, before))
    immutable_guard(prepared)
    source_guard(lock, 'run-prelaunch')
    argv = [sys.executable, '-I', '-S', '-X', 'utf8', str(OUT / 'register.py')]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = None
    error = None
    try:
        with (OUT / 'stdout.raw').open('xb') as stdout, (OUT / 'stderr.raw').open('xb') as stderr:
            env = {k: v for k, v in os.environ.items() if k.upper() not in {'PYTHONOPTIMIZE', 'PYTHONPATH'}}
            result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=600)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        save('invocation.json', {'actor': 'codex:/root', 'argv': argv, 'cwd': str(ROOT), 'started_at': started,
            'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actual_exit': result.returncode if result is not None else None,
            'wrapper_error': error, 'review_ref': review_ref, 'runner_sha256': ref(OUT / 'register.py')['sha256'],
            'wrapper_sha256': ref(Path(__file__))['sha256'], 'stdout_sha256': ref(OUT / 'stdout.raw')['sha256'],
            'stderr_sha256': ref(OUT / 'stderr.raw')['sha256'], 'automatic_retry': False, 'counter_reset': False})
    print(json.dumps({'actual_exit': result.returncode, 'stdout_ref': ref(OUT / 'stdout.raw'), 'stderr_ref': ref(OUT / 'stderr.raw')}, ensure_ascii=True))
    sys.exit(result.returncode)


def seal():
    lock = tool_lock()
    assert len(sys.argv) == 1
    invocation = doc(ref(OUT / 'invocation.json'))
    assert invocation['actual_exit'] == 0 and invocation['wrapper_error'] is None and invocation['automatic_retry'] is False and invocation['counter_reset'] is False
    prepared, before, desired = prepared_inputs()
    review = registration_review(prepared, invocation['review_ref'])
    assert invocation['runner_sha256'] == review['register_sha256'] and invocation['wrapper_sha256'] == review['wrapper_sha256']
    assert invocation['stdout_sha256'] == ref(OUT / 'stdout.raw')['sha256'] and invocation['stderr_sha256'] == ref(OUT / 'stderr.raw')['sha256']
    assert all(p.read_bytes() == raw for p, raw in zip(CANON, desired))
    for p, raw in zip(CANON, before):
        old = PRIOR / (p.stem + ('.desired.json' if p in CANON[:2] else '.original.json'))
        assert old.read_bytes() == raw
    actual, actual_ow = [parse(raw) for raw in desired[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [324, 152, 430]
    assert actual['failure_counters'][:425] == parse(before[0])['failure_counters'] and actual['failure_counters'][425:] == prepared['origins']
    assert actual['head'] == TARGET and desired[2:] == before[2:]
    assert actual['current_effective_formal_status'] == parse(before[0])['current_effective_formal_status']
    assert actual_ow['card_path_bindings']['W05-99']['subtasks']['cli_exact8_source_integration']['current_source_writer'] is None
    intent_ref = ref(OUT / 'canonical-write.intent.json')
    intent = doc(intent_ref)
    verified_ref = ref(OUT / 'canonical-write.verified.json')
    verified = doc(verified_ref)
    assert same(verified['intent_ref'], intent_ref) and verified['registered_head'] == TARGET
    assert verified['checkpoint'] == 324 and verified['ownership'] == 152 and verified['failure_origins'] == 430
    assert len(intent['metadata']) == 4
    for index, (p, row) in enumerate(zip(CANON, intent['metadata'])):
        assert path(row['path']) == p and same(row['original_ref'], prepared['original_refs'][index]) and same(row['desired_ref'], prepared['desired_refs'][index])
        assert row['write_required'] == (index < 2)
        if index < 2:
            done = doc(ref(OUT / ('canonical-write.' + p.stem + '.done.json')))
            assert done['sha256'] == row['desired_ref']['sha256']
    immutable_guard(prepared)
    source_guard(lock, 'seal-current')
    audit = save('registration-audit.json', {'schema': 'researchos.cli43-post-integration-registration-audit.v1',
        'actor': 'codex:/root', 'status': 'ACTUAL_CLI43_FORWARD_HEAD_REGISTRATION_CLOSED_PENDING_INDEPENDENT_REVIEW_AND_FRESH43_VALIDATION',
        'before': [323, 151, 425], 'after': [324, 152, 430], 'actual_registration_exit': 0, 'registered_head': TARGET,
        'completed_ref': prepared['pins']['cli_completed'], 'manifest_ref': prepared['pins']['cli_manifest'], 'grant_ref': prepared['pins']['cli_grant'],
        'pre_registration_review_ref': prepared['pins']['cli_pre_registration_review'], 'registration_review_ref': invocation['review_ref'],
        'invocation_ref': ref(OUT / 'invocation.json'), 'intent_ref': intent_ref, 'verified_ref': verified_ref,
        'registered_origin_refs': [x['evidence_ref'] for x in prepared['origins']], 'old425_failure_prefix_unchanged': True,
        'postcut_pending_origin_refs': [prepared['pins']['aftercut_pending_origin']], 'pending_origin_count': 1, 'observed_lower_bound': 431,
        'step_state_commands_unchanged': True, 'old11_deletions_preserved': True, 'source_writer': None,
        'unique_source_paths': 43, 'source43_vector_ref': prepared['pins']['source43_vector'],
        'Main38_completed_ref': prepared['pins']['main38_completed'], 'Main38_manifest_ref': prepared['pins']['main38_manifest'],
        'fresh43_validation_authorized': False, 'Desktop_integration_authorized': False, 'source_acceptance': False,
        'formal_increment': 0, 'final_closed_execution_review_ref': None,
        'final_closed_review_requirement': 'A future independent review must bind this actual post-registration audit; this registration is not that review.'})
    entries = [ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    mf = save('manifest.json', {'count': len(entries), 'entries': entries, 'self_excluded': True,
        'at_seal_only': True, 'future_temporal_append_not_covered': True})
    print(json.dumps({'registration_audit': audit, 'manifest': mf, 'current': [324, 152, 430]}, ensure_ascii=True))


if __name__ == '__main__':
    {'prepare': prepare, 'register': register, 'run': run, 'seal': seal}[MODE]()
