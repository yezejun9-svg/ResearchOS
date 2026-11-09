"""Finite non-author Source review. No Native, Go, SQL, dispatcher or model calls."""
import ast
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import types
from contextlib import redirect_stdout

sys.dont_write_bytecode = True
R = Path('D:/作品集/ResearchOS/research-os')
S = R / 'execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_source_codex/fullw09-20261009-01'
D = Path(__file__).resolve().parent
SPEC = Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
ACTOR = 'codex:/root/full_w09_source_review'
PINS = {'HDF.json': ('ca8c9767daa5296c129f87f285672b9f6963c9133dd7d71c9ba1454afdeed6c6', 13725),
        'MF.json': ('5914889742cf9e2cd0bae3fabfbf3ca93ec8013f901502eba55411321c6580a8', 11860),
        'root-calling-contract.json': ('e6209dc9ea2a1aae5e216f4e6b68653151ee90f188cf055c75aa9fbdd36f7b95', 6239)}

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def load(path):
    return json.loads(Path(path).read_bytes())

def save(name, value):
    assert Path(name).name == name
    with (D / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())
    return pin(D / name)

def inert(path, name):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(Path(path).read_bytes(), str(path), 'exec'), module.__dict__)
    return module

def undo(text, patch):
    source = text.splitlines(keepends=True)
    rows = patch.splitlines(keepends=True)
    output = []
    pos = 0
    i = 2
    while i < len(rows):
        match = re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\r?\n', rows[i])
        assert match, 'PATCH_HEADER'
        start = int(match[1]) - 1
        output.extend(source[pos:start])
        pos = start
        i += 1
        while i < len(rows) and not rows[i].startswith('@@ '):
            tag, payload = rows[i][0], rows[i][1:]
            assert tag in (' ', '-', '+'), 'PATCH_TAG'
            if tag in (' ', '-'):
                assert source[pos] == payload, 'PATCH_CONTEXT'
                pos += 1
            if tag in (' ', '+'):
                output.append(payload)
            i += 1
    output.extend(source[pos:])
    return ''.join(output)

def original_capture(binding):
    ref = binding['original_capture_ref']
    assert pin(ref['path']) == ref, 'HOST_CAPTURE_PIN'
    lines = Path(ref['path']).read_bytes().splitlines(keepends=True)
    assert len(lines) == 3 and all(row.endswith(b'\n') for row in lines)
    with Path(binding['source_audit_path']).open('rb') as stream:
        for offset, digest, line in zip(binding['source_line_offsets'], binding['original_line_sha256'], lines):
            assert type(offset) is int and offset >= 0
            assert offset + len(line) <= binding['source_prefix_size_observed']
            assert hashlib.sha256(line).hexdigest() == digest
            stream.seek(offset)
            assert stream.read(len(line)) == line, 'ORIGINAL_HOST_BYTES'
    head, call, result = map(json.loads, lines)
    assert head['type'] == 'session_meta'
    first, last = call['payload'], result['payload']
    assert first['call_id'] == last['call_id'] and first['type'] in ('function_call', 'custom_tool_call')
    assert last['type'] in ('function_call_output', 'custom_tool_call_output')
    return dict(capture_ref=ref, actual_call_id=first['call_id'], tool_name=first.get('name'),
                original_source_offsets=binding['source_line_offsets'], original_line_sha256=binding['original_line_sha256'],
                actual_original_bytes_verified=True, actor_id=binding.get('source_actor', binding.get('actor_id')))

def main():
    checks = []
    findings = []
    def check(name, condition, detail=None):
        if not condition:
            raise AssertionError(name)
        checks.append(dict(name=name, status='PASS_SOURCE_ONLY', detail=detail))
    def reject(name, action, code=None):
        try:
            action()
        except (ValueError, KeyError, TypeError, FileNotFoundError) as exc:
            check(name, code is None or code in str(exc), dict(exception_type=type(exc).__name__, error=str(exc)))
            return
        raise AssertionError(name + '_ACCEPTED')

    for name, (digest, size) in PINS.items():
        check('root_supplied_' + name, pin(S / name) == dict(path=str(S / name), sha256=digest, bytes=size))
    handoff, manifest, contract, choices = (load(S / name) for name in ('HDF.json', 'MF.json', 'root-calling-contract.json', 'source.choice.json'))
    common = choices['common']
    blueprint = load(common['compiler_blueprint_ref']['path'])
    check('non_author_identity', handoff['actor_id'] != ACTOR and handoff['source_thread_id'] != os.environ['CODEX_THREAD_ID'])
    guardmodule = inert(common['guard_ref']['path'], 'review_guard')
    check('guard_helper_pin', pin(common['guard_ref']['path']) == common['guard_ref'])
    spec_names = ['08_AGENT_EXECUTION_GOAL.md', 'tasks/steps/W09-99.md', 'contracts/tasks.json', 'contracts/acceptance.json', 'contracts/execution.plan.json']
    gap_path = R / 'execution/v2.4/receipts/W09/W09-99/full_w09_native_gap_source_review_codex/Source-gap-report.json'
    refs = [pin(S / 'HDF.json'), pin(S / 'MF.json'), *manifest['members'], *common['source21'], *blueprint['stable_input_refs'],
            common['guard_ref'], common['owned_job_ref'], common['toolchain_ref'], common['identity_ref'], common['spec_manifest_ref'],
            *common['tool_refs'].values(), pin(gap_path), *[pin(SPEC / name) for name in spec_names], pin(R / 'AGENTS.md')]
    reuse_refs = load(S / 'MR2-program-reuse-evaluation.json')
    refs.extend(value for value in reuse_refs.values() if type(value) is dict and set(value) == {'path', 'sha256', 'bytes'})
    refs.append(load(S / 'source-build-observation.json')['base_runtime_ref'])
    refs_by_path = {}
    for ref in refs:
        key = ref['path'].casefold()
        if key in refs_by_path and refs_by_path[key] != ref:
            raise AssertionError('CONFLICTING_INPUT_PIN_' + ref['path'])
        refs_by_path[key] = ref
    refs = list(refs_by_path.values())
    check('unique_nonconflicting_guarded_inputs', True, len(refs))
    canon = {str(R / 'execution/v2.4' / (name + '.json')).casefold() for name in ('checkpoint', 'path_ownership', 'step_state', 'commands')}
    check('no_current_Canon_in_Source_guard', not canon.intersection(refs_by_path))
    # All handles are closed in this invocation before the shell/tool boundary.
    guard = guardmodule.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    cleanup = None
    control_output = io.StringIO()
    try:
        guard.acquire(refs)
        check('all_frozen_references_current', all(pin(ref['path']) == ref for ref in refs), len(refs))
        m = inert(S / 'full_w09_runtime.source.py', 'independent_full_runtime')
        check('source_HDF_MF_binding', handoff['manifest_ref'] == pin(S / 'MF.json'))
        check('MF_exact_local_unique_members', len(manifest['members']) == len({ref['path'].casefold() for ref in manifest['members']})
              and all(Path(ref['path']).parent == S for ref in manifest['members']))
        gap = load(gap_path)
        plan = next(row for row in gap['next_source_tasks'] if row['id'] == 'SOURCE_THREE_SELECTOR_MAIN_PRODUCER')
        check('gap_pin', pin(gap_path)['sha256'] == '9b7bb0a54314560e285f5245d95d0ce44cb5c2510c31ef5bff3996f1602e93e5')
        check('Main21_gap_source_author_parity', common['source21'] == handoff['Source21'] == plan['source21'])
        check('exact_source_package', m.package_refs()[:2] == (pin(S / 'HDF.json'), pin(S / 'MF.json')))
        check('current_compiler_3905_unique_pins', len(blueprint['stable_input_refs']) == 3905
              and len({ref['path'].casefold() for ref in blueprint['stable_input_refs']}) == 3905)
        check('roster_353_is_only_upper_bound', len(blueprint['allowed_package_roster']) == 353
              and blueprint['actual_package_count'] is None and blueprint['no_prior_program_or_test_result_reuse'] is True)
        check('exact_module_go_mod_19', len(blueprint['module_go_mod_refs']) == 19
              and all(ref in blueprint['stable_input_refs'] for ref in blueprint['module_go_mod_refs']))
        m.verify_directories(blueprint)
        check('current_compile_directory_inventory', True, len(blueprint['main_directory_inventory']))
        adapter = 'researchos.local/research-os/adapters/retrieval'
        domain = 'researchos.local/research-os/internal/domain'
        six = [adapter, adapter + ' [' + adapter + '.test]', adapter + '.test', domain, domain + ' [' + domain + '.test]', domain + '.test']
        check('exact_six_two_package_variants', blueprint['required_test_packages'] == six)
        runner_tree = ast.parse((R / 'ops/ci/retrieval.py').read_bytes())
        # Inert AST literals/comprehensions establish the roster without importing/running the producer.
        roster_module = types.ModuleType('roster_only')
        for node in runner_tree.body:
            if isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) and t.id in ('TESTS', 'GROUPS', 'CASES', 'SOURCES') for t in node.targets):
                exec(compile(ast.Module(body=[node], type_ignores=[]), '<Main-roster-AST-only>', 'exec'), roster_module.__dict__)
        check('runner_Source21_inventory', roster_module.SOURCES == [Path(ref['path']).relative_to(R).as_posix() for ref in common['source21']])
        check('distinct_one_shot_run_ids', len({row['run_id'] for row in choices['selectors'].values()}) == 3)
        for job in plan['jobs']:
            key = job['selector']['check_id'] or job['selector']['case_id']
            c = m.choice(key)
            for field in ('selector', 'mode', 'native_scope', 'selected_tests', 'expected_native_ids', 'packages', 'go_test_argv_suffix'):
                check(key + '_gap_' + field, c[field] == job[field])
            check(key + '_full_Main_roster', c['selected_tests'] == (roster_module.GROUPS[key] if key.startswith('W09-') else roster_module.CASES[key]))
            check(key + '_Main_assertion_owner', c['assertion_owner'] == {aid: test for test in c['selected_tests'] for aid in roster_module.TESTS[test][1]})
            check(key + '_fixed_paths_absent', all(not Path(c[field]).exists() for field in ('receipt_root', 'scratch_root', 'output_root')))
            check(key + '_fresh_export_compilation_path', c['list_argv_suffix'] == job['go_list_argv_suffix']
                  and c['list_argv_suffix'] == ['list', '-test', '-deps', '-compiled', '-export', '-json', './adapters/retrieval', './internal/domain'])
            check(key + '_three_selector_environment', m.build_environment(c)['RESEARCHOS_CHECK_ID'] == c['selector']['check_id']
                  and m.build_environment(c)['RESEARCHOS_CASE_ID'] == c['selector']['case_id'])
        check('source_does_not_authorize_execution', contract['source_only'] is True and contract['execution_grant'] is False
              and all(handoff[field] == 0 for field in ('actual_Go_runs', 'actual_Native_runs', 'actual_dispatcher_runs', 'actual_SQL_runs', 'formal_case_accepted_delta')))
        for file in ('full_w09_runtime.source.py', 'full_w09_launcher.source.py', 'prepare_full_w09.source.py', 'run_full_w09.source.py'):
            ast.parse((S / file).read_bytes())
            check(file + '_AST_and_runtime_pin', file == 'full_w09_runtime.source.py' or pin(S / 'full_w09_runtime.source.py')['sha256'] in (S / file).read_text())
        base_ref = load(S / 'source-build-observation.json')['base_runtime_ref']
        base = Path(base_ref['path']).read_bytes().decode()
        runtime = (S / 'full_w09_runtime.source.py').read_bytes().decode()
        check('independent_inverse_exact_bytes', undo(runtime, (S / 'runtime.inverse.diff').read_bytes().decode()).encode() == base.encode())
        check('independent_forward_exact_bytes', undo(base, (S / 'runtime.forward.diff').read_bytes().decode()).encode() == runtime.encode())
        # Reproduce the author's finite functions with writes redirected only into this review namespace.
        # This reproduction is explicitly separate from our own additional adversarial checks.
        source = (S / 'source-controls.py').read_text()
        old = "m.save(N,'source-controls.json',"
        assert source.count(old) == 1
        source = source.replace(old, "review_save('reproduced-source-controls.json',")
        control = types.ModuleType('author_checks_reproduced')
        control.__file__ = str(S / 'source-controls.py')
        control.review_save = save
        with redirect_stdout(control_output):
            exec(compile(source, control.__file__, 'exec'), control.__dict__)
            control.main()
        extra = (S / 'audit-and-closure-controls.py').read_text()
        old = "p=N/'real-Root-audit.control.raw.jsonl'"
        assert extra.count(old) == 1
        extra = extra.replace(old, "p=review_destination/'reproduced-real-Root-audit.control.raw.jsonl'")
        old = "exec(compile(Path(m.__file__).read_bytes(),m.__file__,'exec'),m.__dict__)"
        assert extra.count(old) == 1
        extra = extra.replace(old, old + "\n    m.save=lambda root,name,value:review_save('reproduced-'+name,value)")
        control = types.ModuleType('author_audit_checks_reproduced')
        control.__file__ = str(S / 'audit-and-closure-controls.py')
        control.review_destination = D
        control.review_save = save
        with redirect_stdout(control_output):
            exec(compile(extra, control.__file__, 'exec'), control.__dict__)
            control.main()
        author_controls = load(S / 'source-controls.json')['controls']
        author_extra = load(S / 'audit-and-closure-controls.json')['controls']
        reproduced = load(D / 'reproduced-source-controls.json')['controls']
        reproduced_extra = load(D / 'reproduced-audit-and-closure-controls.json')['controls']
        check('author_69_reproduced_names_and_statuses', [(x['name'], x['status']) for x in reproduced] == [(x['name'], x['status']) for x in author_controls]
              and [(x['name'], x['status']) for x in reproduced_extra] == [(x['name'], x['status']) for x in author_extra]
              and len(reproduced) + len(reproduced_extra) + 1 == handoff['finite_Source_checks'] == 69)
        reject('reviewer_missing_request_before_any_directory', lambda: m.validate_authority(dict(path=str(D / 'NOT_ISSUED.json'), sha256='0' * 64, bytes=0), m.choice('A06')))
        for invalid in ('C19', 'W09-G03', '', 'A06 ', True):
            reject('independent_selector_reject_' + repr(invalid), lambda invalid=invalid: m.choice(invalid), 'THREE_SELECTORS_ONLY')
        for value in (-1, 2**32, 1.0, False):
            result = dict(owned_child_pid=value, creation_time_100ns=1, job_cleanup={})
            check('independent_invalid_PID_' + repr(value), m.job_closed(result) is False)
        good = dict(owned_child_pid=1, creation_time_100ns=2**64 - 1,
                    job_cleanup=dict(errors=[], active_processes_last_observed=0, **{key: True for key in
                    ('unnamed_exclusive_job', 'kill_on_job_close_configured', 'assigned_before_resume', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed')}))
        check('independent_max_FILETIME_exact', m.job_closed(good) and str(good['creation_time_100ns']) == '18446744073709551615')
        for key in ('unnamed_exclusive_job', 'kill_on_job_close_configured', 'assigned_before_resume', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed'):
            bad = copy.deepcopy(good)
            bad['job_cleanup'][key] = 1
            check('independent_cleanup_bool_type_' + key, m.job_closed(bad) is False)
        for value in (0, -1, 2**64, '18446744073709551615', True, 1.0):
            bad = copy.deepcopy(good)
            bad['creation_time_100ns'] = value
            check('independent_invalid_FILETIME_' + repr(value), m.job_closed(bad) is False)
        # All required test variants must be observed; no fixed 351 or 353 count may qualify them.
        c = m.choice('A06')
        originals = m.pin, m.exact_path, m.verify_directories
        cache = Path(c['scratch_root']) / 'gocache'
        generated, export = cache / 'generated.go', cache / 'compiled.a'
        by_path = {ref['path']: ref for ref in blueprint['stable_input_refs']}
        by_path[str(generated)] = dict(path=str(generated), sha256='1' * 64, bytes=1)
        by_path[str(export)] = dict(path=str(export), sha256='2' * 64, bytes=1)
        m.pin = lambda path: by_path[str(path)]
        m.exact_path = lambda path, *args: Path(path)
        m.verify_directories = lambda bp: None
        chain = None
        for ref in blueprint['module_go_mod_refs']:
            chain = dict(GoMod=ref['path'], Replace=chain)
        sample = [dict(ImportPath=name, Name='main' if name.endswith('.test') else 'retrieval', Dir=str(R),
                       Export=str(export), CompiledGoFiles=[str(generated)]) for name in six]
        sample[0]['Module'] = chain
        dump = lambda rows: '\n'.join(json.dumps(row) for row in rows)
        try:
            check('synthetic_six_graph_shape_only_NO_COMPILATION_QUALIFICATION', m.compiler_inventory(dump(sample), c, blueprint)['package_count'] == 6)
            for index, name in enumerate(six):
                reject('independent_missing_variant_' + name, lambda index=index: m.compiler_inventory(dump(sample[:index] + sample[index + 1:]), c, blueprint), 'FINITE_TWO_PACKAGE_TEST_CLOSURE')
            foreign = copy.deepcopy(sample)
            foreign[0]['CompiledGoFiles'] = [str(R / 'UNHELD_CONTROL.go')]
            by_path[str(R / 'UNHELD_CONTROL.go')] = dict(path=str(R / 'UNHELD_CONTROL.go'), sha256='3' * 64, bytes=1)
            reject('independent_unheld_go_input', lambda: m.compiler_inventory(dump(foreign), c, blueprint), 'GO_LIST_UNHELD_OR_DRIFTED_INPUT')
            outside = copy.deepcopy(sample)
            outside[0]['Export'] = str(R / 'FOREIGN_EXPORT.a')
            reject('independent_non_private_export', lambda: m.compiler_inventory(dump(outside), c, blueprint), 'EXPORT_NOT_PRIVATE_GOCACHE')
            missing = copy.deepcopy(sample)
            for row in missing:
                row['CompiledGoFiles'] = []
            reject('independent_no_actual_generated_input', lambda: m.compiler_inventory(dump(missing), c, blueprint), 'ACTUAL_EXPORT_AND_GENERATED_INPUTS_REQUIRED')
            error = copy.deepcopy(sample)
            error[0]['DepsErrors'] = [dict(Err='independent failure')]
            reject('independent_dependency_error', lambda: m.compiler_inventory(dump(error), c, blueprint), 'GO_LIST_PACKAGE_ERROR')
        finally:
            m.pin, m.exact_path, m.verify_directories = originals
        hosts = []
        for binding_path in sorted(S.glob('actual-Source-tool-*.binding.json')):
            binding = load(binding_path)
            check('actual_author_host_' + binding_path.stem, binding['source_actor'] == handoff['actor_id']
                  and binding['source_thread_id'] == handoff['source_thread_id'])
            hosts.append(dict(binding_ref=pin(binding_path), **original_capture(binding)))
        check('all_six_true_author_hostpairs', len(hosts) == 6)
        root_audit = load(S / 'real-Root-audit.control.binding.json')
        check('actual_Root_original_pair', len(m.actual_audit(pin(S / 'real-Root-audit.control.binding.json'), m.ROOT_ACTOR, root_audit['binding_sha256'])) == 2)
        hosts.append(dict(binding_ref=pin(S / 'real-Root-audit.control.binding.json'), **original_capture(root_audit)))
        save('independent-original-hostpair-audit.json', dict(status='PASS_SOURCE_ONLY', hostpairs=hosts,
             copied_Source_original_diagnostics_ref=pin(S / 'original-diagnostics.json'), preserves_original_failures=True,
             current_execution_authority=False, unknown_individual_exits=None))
        reuse = load(S / 'MR2-program-reuse-evaluation.json')
        inv = load(reuse['actual_inventory_ref']['path'])
        check('MR2_actual_inventory_pin', pin(reuse['actual_inventory_ref']['path']) == reuse['actual_inventory_ref'])
        observed = {name for name in inv['packages'] if '/adapters/retrieval' in name or '/internal/domain' in name}
        check('MR2_lacks_adapter_test_program', adapter in observed and adapter + '.test' not in observed
              and adapter + ' [' + adapter + '.test]' not in observed and reuse['retained_executable_program_refs'] == [])
        check('MR2_C19_only_no_new_selector_reuse', reuse['status'] == 'DO_NOT_REUSE_AS_TWO_PACKAGE_TEST_PROGRAM'
              and reuse['prior_results_used_as_new_selector_results'] is False and reuse['actual_native_rerun'] is False)
        check('all_inputs_remain_byte_exact', all(pin(ref['path']) == ref for ref in refs))
        check('all_future_paths_still_absent', all(not Path(c[field]).exists() for c in choices['selectors'].values()
              for field in ('receipt_root', 'scratch_root', 'output_root')))
    finally:
        cleanup = guard.close()
        save('independent-Source-guard.closed.json', cleanup)
    check('review_Source_guard_closed_zero', cleanup['closed'] is True and not cleanup['errors']
          and type(cleanup['retained_handles_count']) is int and cleanup['retained_handles_count'] == 0)
    save('reproduction.stdout.json', dict(stdout=control_output.getvalue(), actual_Python_exits_are_shell_captured=True))
    # Mechanically record source constraints for Root's later issuance; no Scope/request is created here.
    save('Root-next-stage-required-fields.json', dict(schema='researchos.w09-source-review-next-stage-contract.v1',
         source_only=True, execution_grant=False, scope_required_fields=contract['scope_required_fields'],
         request_exact_fields=contract['request_exact_fields'], request_schema=contract['request_schema'], scope_schema=contract['scope_schema'],
         canonical_registration=contract['canonical_registration'], future_argv=contract['future_argv'],
         capture_fields=['schema', 'actor_id', 'Root_thread_id', 'source_audit_path', 'source_line_offsets', 'original_line_sha256',
                         'source_prefix_size_observed', 'original_capture_ref', 'binding_sha256'],
         Root_capture_rows='session_meta + actual function/custom call + matching actual call output',
         peer_capture_rows='session_meta + actual inter_agent_communication_metadata + next host-authored agent_message',
         source_author_actor=handoff['actor_id'], source_review_actor=ACTOR,
         source_author_binding=pin(S / 'HDF.json')['sha256'], source_review_binding='sealed independent decision SHA256',
         scope_binding='fresh actual Root-issued Scope SHA256',
         canonical_vector_fields=['schema', 'checkpoint_revision', 'ownership_revision', 'refs'],
         canonical_vector_schema='researchos.w09-three-selector-native-canonical-vector.v1',
         canonical_ref_order=['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json'],
         canonical_revision_minimum_exclusive=dict(checkpoint=371, ownership=175),
         lease=dict(unique='32 lowercase hex', timezone_required=True, maximum_seconds=3600, current_at_every_execution_gate=True),
         per_selector_budget=dict(maximum_go_list_runs=1, maximum_go_test_runs=1, list_timeout_seconds=240,
                                  producer_timeout_seconds=420, inner_Go_timeout_seconds=180),
         selector_specs=choices['selectors'], source21=common['source21'], missing_actual_Root_scope_and_captures=True,
         actualprepare_request_issued=False, actualrun_request_issued=False, actual_executed=False, formal_case_accepted_delta=0))
    observation = dict(schema='researchos.w09-three-selector-independent-source-controls.v1', actor_id=ACTOR,
        source_thread_id=os.environ['CODEX_THREAD_ID'], status='ACCEPTED_SOURCE_ONLY', findings=findings,
        checks=checks, unique_guarded_input_count=len(refs), compiler_source_pin_count=len(blueprint['stable_input_refs']),
        compiler_allowed_package_upper_bound=len(blueprint['allowed_package_roster']), actual_compiled_package_count=None,
        author_controls_reproduced=69, independent_additional_controls=len(checks),
        counterexamples='FINITE_IN_MEMORY_ONLY_NOT_PRODUCT_OR_FORMAL_CASE_PASS',
        actual_Go_runs=0, actual_Native_runs=0, actual_dispatcher_runs=0, actual_SQL_runs=0, actual_model_provider_calls=0,
        Main_written=False, Canon_read=False, Canon_written=False, current_CanonicalPair_held=False,
        execution_grant=False, formal_acceptance=False, formal_case_accepted_delta=0,
        all_Source_guards_closed=True, retained_handles_count=0, automatic_retry=False,
        original_failure_ordinals_preserved=[1026, 1029], new_failure_count=0, self_assigned_Root_ordinal=False)
    result = save('independent-source-controls.json', observation)
    print(json.dumps(dict(status='ACCEPTED_SOURCE_ONLY', controls_ref=result,
                         guard_ref=pin(D / 'independent-Source-guard.closed.json'),
                         author_controls_reproduced=69, independent_checks=len(checks), unique_guarded_input_count=len(refs),
                         actual_Go_runs=0, actual_Native_runs=0, formal_case_accepted_delta=0), ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
