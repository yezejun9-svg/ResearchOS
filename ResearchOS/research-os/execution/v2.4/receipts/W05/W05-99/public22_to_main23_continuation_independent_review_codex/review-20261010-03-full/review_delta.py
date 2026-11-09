"""Independent Source03 delta review; no SQLite connection or Root execution."""
from pathlib import Path
import ast, copy, hashlib, json, types

R = Path(r'D:\作品集\ResearchOS\research-os')
B = R / 'execution/v2.4/receipts/W05/W05-99'; W = R / 'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
N = B / 'public22_to_main23_continuation_caller_source_codex/continue-20261010-03'
OLD = N.parent / 'continue-20261010-02'
PRIOR = B / 'public22_to_main23_continuation_independent_review_codex/review-20261010-02-full'
HELPER = W / 'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s = types.ModuleType('receipt_support'); s.__file__ = str(HELPER)
exec(compile(HELPER.read_bytes(), str(HELPER), 'exec'), s.__dict__); s.D = D
href = dict(path=str(N / 'HDF.json'), sha256='6b35f9035b3b8e59971d7afbd32e672e981337b7b4608b8daeed2bd4e3c8bb48', bytes=8487)
mfref = dict(path=str(N / 'MF.json'), sha256='30840d853defc51994e6365a943f6e3f3d58c0e312dbfa0809d38ffe5f7e664d', bytes=7493)
author_audit = dict(path=str(W / 'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.public22-main23-continuation-source03.actual-audit.root.json'),
    sha256='25e8b76ae84c58273c2e9251606bc6c7091510ce4c035881b8eb1c70132ae5ef', bytes=1138)
def read(path): return json.loads(Path(path).read_bytes())
h, mf = read(href['path']), read(mfref['path'])
inverse = read(h['revision_inverse_ref']['path']); i = read(h['source_inputs_ref']['path'])
prior_h = read(PRIOR / 'HDF.json'); prior_decision = read(prior_h['source_decision_ref']['path'])
probe = read(h['working22_difference_probe_ref']['path']); author = read(author_audit['path'])
held = [s.pin(__file__), s.pin(HELPER), href, mfref, *mf['members'],
        *inverse['prior_namespace_protected_refs'], s.pin(PRIOR / 'HDF.json'), prior_h['manifest_ref'],
        prior_h['source_decision_ref'], prior_h['runtime_closure_evidence_ref'], i['leaf_runner_ref'],
        i['runtime_resources_ref'], author_audit, author['original_capture_ref'],
        probe['case_closed_ref'], probe['retained_state_ref'], probe['backup_manifest_ref']]
held = list({ref['path']:ref for ref in held}.values())
g = s.guard(); checks = []; observations = {}; failure = None
def check(name, ok, detail=None):
    checks.append(dict(name=name, passed=bool(ok), detail=detail))
    if not ok: raise ValueError(name)
def rejection(name, operation, expected):
    got = None
    try: operation()
    except ValueError as exc: got = str(exc)
    check(name, got == expected, dict(observed=got, expected=expected, Source_fixture_only=True))
try:
    g.acquire(held)
    before = g.get_buffer(inverse['base_caller_ref']['path'])
    after = g.get_buffer(h['caller_ref']['path'])
    restored = after
    for block in reversed(inverse['changes']):
        check('inverse_unique_block_' + str(len(checks)), restored.count(block['after'].encode()) == 1)
        restored = restored.replace(block['after'].encode(), block['before'].encode(), 1)
    check('independent_complete_Source02_byte_inverse', restored == before)
    old_tree, new_tree = ast.parse(before), ast.parse(after)
    def nodes(tree): return {x.name:x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
    old_nodes, new_nodes = nodes(old_tree), nodes(new_tree)
    changed = [key for key in old_nodes if ast.dump(old_nodes[key], include_attributes=False)
               != ast.dump(new_nodes[key], include_attributes=False)]
    check('only_execute_changed_and_validate_working22_added', changed == ['execute']
          and set(new_nodes) - set(old_nodes) == {'validate_working22'} and set(old_nodes) <= set(new_nodes), changed)
    restored_tree = ast.parse(restored)
    check('complete_module_AST_inverse_preserves_imports_constants_all_gates',
          ast.dump(restored_tree, include_attributes=False) == ast.dump(old_tree, include_attributes=False))
    check('all_other_functions_including_149_runtime_and_three_phase_oracles_unchanged',
          all(ast.dump(old_nodes[key], include_attributes=False) == ast.dump(new_nodes[key], include_attributes=False)
              for key in old_nodes if key != 'execute'))
    check('Source_inputs_same_bytes_and_foreign_ref_objects',
          g.get_buffer(h['source_inputs_ref']['path']) == g.get_buffer(inverse['prior_namespace_protected_refs'][
              next(index for index,ref in enumerate(inverse['prior_namespace_protected_refs'])
                   if Path(ref['path']).name == 'source-inputs.json')]['path']))
    check('original15_Source02_files_still_match_protected_pins',
          len(inverse['prior_namespace_protected_refs']) == 15,
          dict(all_pins_verified_by_source_guard=True, controls_rerun=False))
    # Extract call ordering without executing execute(), live(), source_chain(), or any stage.
    source_text = after.decode(); execute_text = ast.get_source_segment(source_text, new_nodes['execute'])
    a = execute_text.index('leaf.validate_ledger(sealed,22)')
    b = execute_text.index("state['observations']['working22_input']=sealed")
    c = execute_text.index("validate_working22(leaf,sealed,retained,doc(i['evidence']['backup_manifest_ref']))")
    check('ledger22_before_retained_observation_before_fallible_new_validator', a < b < c)
    check('original_source_and_workcopy_byte_guard_still_precede_new_validator',
          execute_text.index("'EXACT_RETAINED22_SOURCE'") < c
          and execute_text.index("'EXACT_WORKING_COPY'") < c)
    source03_contract = json.loads(g.get_buffer(h['calling_contract_ref']['path']))
    old_contract = json.loads(g.get_buffer(prior_h['calling_contract_ref']['path']))
    unchanged_fields = ('modes','registration_request_schema','registration_request_required_fields',
        'Source_review_schema','Source_review_required_fields','actual_request_schema','actual_request_required_fields',
        'execute_second_ref','required_root_hostpairs','required_peer_hostpairs','current4',
        'finite_lease_seconds_max','new_native_phase_limit','child_timeout_seconds','private_owner','remaining_uncovered')
    check('unchanged_calling_Scope_runtime_and_actual_review_contract_gates',
          all(source03_contract[key] == old_contract[key] for key in unchanged_fields), list(unchanged_fields))

    # Independently check sealed actual Source delivery without locking the growing Root log.
    raw = g.get_buffer(author['original_capture_ref']['path'])
    lines = raw.splitlines(keepends=True); check('actual_author_capture_three_original_LF_lines', len(lines)==3 and all(x.endswith(b'\n') for x in lines))
    head, meta, final = [json.loads(line) for line in lines]
    payload = final['payload']
    check('actual_Attach_author_delivered_Source03_to_Root',
          head['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
          and meta['type']=='inter_agent_communication_metadata' and final['type']=='response_item'
          and final['ordinal']==meta['ordinal']+1 and meta['timestamp']==final['timestamp']
          and payload['type']=='agent_message' and payload['author']=='/root/attach_restore_independent_review'
          and payload['recipient']=='/root' and final['metadata']['client_authored'] is False
          and author['binding_sha256']==href['sha256'])
    check('actual_author_capture_exact_hashes_and_offsets',
          author['original_line_sha256'] == [hashlib.sha256(line).hexdigest() for line in lines]
          and author['source_line_offsets'] == sorted(set(author['source_line_offsets']))
          and author['source_line_offsets'][0] == 0)
    with Path(author['source_audit_path']).open('rb') as stream:
        for offset,line in zip(author['source_line_offsets'],lines):
            stream.seek(offset)
            if offset+len(line)>author['source_prefix_size_observed'] or stream.read(len(line))!=line:
                raise ValueError('ACTUAL_SOURCE_AUTHOR_ROOT_OFFSET_BYTES')
    check('actual_author_original_offset_bytes_readback_without_audit_lock',True)
    m = s.inert(N / 'public22_to23_root.source.py', after)
    check('actual_author_Final_typed_full_HDF_MF_caller_refs',
          all(m.contains_ref(payload['content'], ref) for ref in [href,mfref,h['caller_ref']]))
    # Only existing pure Source digest/require functions are executed; no Leaf module import.
    leaf_raw = g.get_buffer(i['leaf_runner_ref']['path']); leaf_tree = ast.parse(leaf_raw)
    leaf_nodes = nodes(leaf_tree)
    pure = dict(hashlib=hashlib,json=json)
    exec(compile(ast.Module(body=[leaf_nodes['require'],leaf_nodes['schema_digest']],type_ignores=[]),
        '<independent-pure-schema-digest>', 'exec'), pure)
    leaf = types.SimpleNamespace(schema_digest=pure['schema_digest'])
    # This is a new lexical boundary control, not a replay of Author's twelve cases.
    comparator = next(node for node in ast.walk(new_nodes['validate_working22']) if isinstance(node,ast.ListComp))
    expression = compile(ast.Expression(body=comparator), '<sqlite-like-source-projection>', 'eval')
    names = ['sqlite','sqlite_','SQLITE_sequence','sqliteX','sqlite!x','sqlite_sequence',
             'sqlite-master','sqlit','sqlite0extra','my_sqlite_x','İsqlite_x']
    rows = [['table',name,name,'CREATE TABLE x(a)'] for name in names]
    got = eval(expression,{},dict(rows=rows))
    def legacy_name_included(name):
        # SQL LIKE is ASCII case-insensitive; underscore matches exactly one character.
        return not (len(name)>=7 and ''.join(chr(ord(char)+32) if 'A'<=char<='Z' else char
                    for char in name[:6])=='sqlite')
    check('legacy_projection_matches_SQLITE_LIKE_wildcard_and_case_boundaries_without_SQL',
          got == [row for row in rows if legacy_name_included(row[1])], dict(Source_fixture_only=True, SQL_connections=0))
    fixture_rows = sorted([
        ['index','sqlite_autoindex_domain_objects_1','domain_objects',''],
        ['table','domain_objects','domain_objects','CREATE TABLE domain_objects(id TEXT)'],
        ['table','sqlite_sequence','sqlite_sequence','CREATE TABLE sqlite_sequence(name,seq)'],
        ['table','sqliteXcustom','sqliteXcustom','CREATE TABLE sqliteXcustom(id TEXT)'],
    ], key=lambda row:(row[0],row[1]))
    full = leaf.schema_digest(fixture_rows)
    legacy_rows = [row for row in fixture_rows if legacy_name_included(row[1])]
    legacy = hashlib.sha256(json.dumps(legacy_rows,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    sealed = dict(tables={'domain_objects':dict(count=0,rows_sha256='a'*64)},
        database_ref=dict(path='Source_fixture_working22',sha256='b'*64,bytes=4096),
        versions=list(range(1,23)),schema_rows=fixture_rows,schema_sha256=full)
    retained = dict(tables=copy.deepcopy(sealed['tables']), database_ref=dict(sealed['database_ref'],path='Source_fixture_original22'),
        versions=list(range(1,23)),schema_sha256=legacy)
    manifest = dict(migrations=list(range(1,23)),schema_hash='sha256:'+full)
    snapshots = copy.deepcopy((sealed,retained,manifest))
    compatibility = m.validate_working22(leaf,sealed,retained,manifest)
    check('validator_keeps_both_projections_without_mutating_input_documents',
          (sealed,retained,manifest)==snapshots and compatibility['full_schema_sha256']==full
          and compatibility['legacy_schema_sha256']==legacy and compatibility['historical_observation_rewritten'] is False,
          dict(Source_fixture_only=True, actual_component_pass=False))
    check('compatibility_return_contains_only_hash_counts_flags_not_row_or_credential_values',
          not any(key in compatibility for key in ('tables','schema_rows','credentials','database_ref')))
    omitted = copy.deepcopy(sealed); omitted['schema_rows'] = legacy_rows
    omitted['schema_sha256'] = leaf.schema_digest(legacy_rows)
    rejection('omitted_internal_rows_preserve_legacy_but_fail_frozen_full_Native_manifest',
              lambda:m.validate_working22(leaf,omitted,retained,manifest), 'COPIED22_FULL_NATIVE_SCHEMA')
    reordered = copy.deepcopy(sealed); reordered['schema_rows'] = list(reversed(fixture_rows))
    rejection('schema_order_change_rejected_by_bound_full_digest_oracle',
              lambda:m.validate_working22(leaf,reordered,retained,manifest), 'PUBLIC_SCHEMA_ORDER_OR_DUPLICATE')
    duplicated = copy.deepcopy(sealed); duplicated['schema_rows'].append(copy.deepcopy(fixture_rows[-1]))
    rejection('schema_duplicate_rejected_by_bound_full_digest_oracle',
              lambda:m.validate_working22(leaf,duplicated,retained,manifest), 'PUBLIC_SCHEMA_ORDER_OR_DUPLICATE')

    # Reuse actual existing read-only proof; do not reopen a database or rerun a probe.
    case = json.loads(g.get_buffer(probe['case_closed_ref']['path']))
    retained_state = json.loads(g.get_buffer(probe['retained_state_ref']['path']))
    retained_actual = retained_state['observations']['sealed22']
    backup_actual = json.loads(g.get_buffer(probe['backup_manifest_ref']['path']))
    check('actual_original1201_failure_preserved_and_zero_children',
          case['status']=='STOPPED_AT_FIRST_FAILURE' and case['first_failure']['message']=='COPIED22_LOGICAL_STATE'
          and case['new_native_children_attempted']==0 and case['calls']==[])
    check('actual_probe83_tables_and_both_schema_projections_bind_retained_and_Native_manifest',
          probe['table_count']==len(retained_actual['tables'])==83 and probe['table_differences']=={}
          and probe['retained_schema_sha256']==retained_actual['schema_sha256']==probe['legacy_exclude_sqlite_compact_sha256']
          and probe['manifest_schema_hash']==backup_actual['schema_hash']=='sha256:'+probe['current_schema_sha256']
          and probe['working_copy_ref']['sha256']==retained_actual['database_ref']['sha256']
          and probe['working_copy_ref']['bytes']==retained_actual['database_ref']['bytes']
          and probe['working_bytes_unchanged'] is True)
    check('author_probe_did_not_emit_rows_or_access_private_key_or_replay_old_validation',
          probe['original_source_db_opened'] is False and probe['private_key_accessed'] is False
          and probe['raw_rows_emitted'] is False and probe['SQL_write_statements']==0
          and probe['SQL_integrity_or_foreign_key_checks_replayed']==0 and probe['sqlite_connection_closed'] is True)
    check('runtime_closure_149_144_reused_with_exact_unchanged_external_resources_and_no_new_imports',
          prior_decision['runtime_closure_reviewed'] is True
          and h['runtime_resources_ref']==prior_decision['runtime_resources_ref']==i['runtime_resources_ref']
          and ast.dump(ast.Module(body=[node for node in old_tree.body if isinstance(node,(ast.Import,ast.ImportFrom))],type_ignores=[]),include_attributes=False)
              == ast.dump(ast.Module(body=[node for node in new_tree.body if isinstance(node,(ast.Import,ast.ImportFrom))],type_ignores=[]),include_attributes=False))
    observations = dict(changed_existing_functions=changed, added_functions=['validate_working22'],
        exact_complete_inverse=True, actual_source_author_audit_ref=author_audit,
        source_author_capture_computed_line_bytes=[len(line) for line in lines],
        working_probe_ref=h['working22_difference_probe_ref'], actual_case_closed_ref=probe['case_closed_ref'],
        original1201_status=case['status'], original1201_new_children=case['new_native_children_attempted'],
        actual_original22_table_count=probe['table_count'], legacy_schema_sha256=probe['retained_schema_sha256'],
        full_Native_schema_sha256=probe['current_schema_sha256'],
        immutable_history_rewritten=False, new_SQL_connections=0,
        reused_runtime_closure_evidence_ref=prior_h['runtime_closure_evidence_ref'])
    s.write('source-delta-evidence.json',dict(
        source03_caller_ref=h['caller_ref'], base_caller_ref=inverse['base_caller_ref'],
        functions=s.code_evidence(after,h['caller_ref']['path'],['validate_working22','execute']),
        unchanged_other_functions=list(key for key in old_nodes if key!='execute'),
        all_original15_pins_preserved=inverse['prior_namespace_protected_refs'],
        observations=observations, runtime_closure_scope='Unchanged external closure inherited from actual accepted Source02; current Source03 Caller selfpin and complete manifest newly held. Future Root entry still reobserves runtime.',
        old144_149_checks_rerun=False, author12_controls_rerun=False,
        all_new_condition_controls_Source_only=True))
except BaseException as exc:
    failure = dict(type=type(exc).__name__,message=str(exc))
    raise
finally:
    closed_ref = s.write('source-guard.closed.json',g.close())
    s.write('independent-delta-result.json',dict(checks=checks,count=len(checks),passed=sum(x['passed'] for x in checks),
        failure=failure,observations=observations,source_guard_ref=closed_ref,held_refs=held,
        Source_only=True, actual_Native_Go_SQL_TP_Root_stage_model_calls=0,
        execution_grant=False, formal_acceptance=False, Root_scope_issued=False))
print(json.dumps(dict(checks=len(checks),passed=sum(x['passed'] for x in checks),failure=failure,
    source_guard_ref=closed_ref, Source_only=True, new_SQL_connections=0,
    execution_grant=False,formal_acceptance=False),ensure_ascii=False))
