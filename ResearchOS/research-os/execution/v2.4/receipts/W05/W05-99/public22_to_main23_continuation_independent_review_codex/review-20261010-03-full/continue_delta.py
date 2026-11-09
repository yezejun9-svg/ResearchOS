"""Complete only Source03 tail not reached by the retained original review call."""
from pathlib import Path
import ast, copy, hashlib, json, sys, types

R = Path(r'D:\作品集\ResearchOS\research-os')
B = R / 'execution/v2.4/receipts/W05/W05-99'; W = R / 'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
N = B / 'public22_to_main23_continuation_caller_source_codex/continue-20261010-03'
PRIOR = B / 'public22_to_main23_continuation_independent_review_codex/review-20261010-02-full'
HELPER = W / 'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s = types.ModuleType('receipt_support'); s.__file__ = str(HELPER)
exec(compile(HELPER.read_bytes(), str(HELPER), 'exec'), s.__dict__); s.D = D
def read(path): return json.loads(Path(path).read_bytes())
original_ordinal = int(sys.argv[1])
origin = s.capture('a06175', 1, 1, original_ordinal)
s.write('original-review-failure.origin.json', dict(original_ordinal=original_ordinal,
    original_io=origin, original_script_ref=s.pin(D/'review_delta.py'),
    actual_outer_exit=1, actual_Python_exit=1, actual_Native_exit=None, actual_Go_exit=None,
    actual_SQL_exit=None, actual_TP_exit=None, actual_dispatcher_exit=None, actual_model_exit=None,
    reason='Reviewer pure function extraction omitted Leaf BoundaryError class; original script and successful prefix retained.',
    product_failure=False, original_guard_ref=s.pin(D/'source-guard.closed.json'),
    no_successful_control_replay=True))
prefix = read(D/'independent-delta-result.json')
h = read(N/'HDF.json'); i = read(h['source_inputs_ref']['path'])
probe = read(h['working22_difference_probe_ref']['path'])
prior_h = read(PRIOR/'HDF.json'); prior_decision = read(prior_h['source_decision_ref']['path'])
inverse = read(h['revision_inverse_ref']['path'])
def pref(path):
    # Reuse exact pins already verified by the full closed Guard; no full inventory replay.
    return next(ref for ref in prefix['held_refs'] if Path(ref['path']) == Path(path))
refs = [s.pin(__file__), s.pin(HELPER), s.pin(D/'independent-delta-result.json'), prefix['source_guard_ref'],
    pref(N/'HDF.json'), h['caller_ref'], i['leaf_runner_ref'], h['working22_difference_probe_ref'],
    probe['case_closed_ref'], probe['retained_state_ref'], probe['backup_manifest_ref'],
    pref(PRIOR/'HDF.json'), prior_h['source_decision_ref'], inverse['base_caller_ref']]
g = s.guard(); checks=[]; failure=None; observations={}
def check(name,ok,detail=None):
    checks.append(dict(name=name,passed=bool(ok),detail=detail))
    if not ok:raise ValueError(name)
try:
    g.acquire(refs)
    # Confirm retained evidence; this does not execute the prior twenty controls.
    closed = json.loads(g.get_buffer(prefix['source_guard_ref']['path']))
    assert prefix['passed']==prefix['count']==20 and closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
    raw=g.get_buffer(h['caller_ref']['path']); m=s.inert(N/'public22_to23_root.source.py',raw)
    tree=ast.parse(g.get_buffer(i['leaf_runner_ref']['path']))
    nodes={node.name:node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    pure=dict(hashlib=hashlib,json=json)
    exec(compile(ast.Module(body=[nodes['BoundaryError'],nodes['require'],nodes['schema_digest']],type_ignores=[]),
        '<complete-pure-leaf-digest>', 'exec'),pure)
    leaf=types.SimpleNamespace(schema_digest=pure['schema_digest'])
    rows=sorted([
        ['index','sqlite_autoindex_domain_objects_1','domain_objects',''],
        ['table','domain_objects','domain_objects','CREATE TABLE domain_objects(id TEXT)'],
        ['table','sqlite_sequence','sqlite_sequence','CREATE TABLE sqlite_sequence(name,seq)'],
        ['table','sqliteXcustom','sqliteXcustom','CREATE TABLE sqliteXcustom(id TEXT)'],
    ],key=lambda row:(row[0],row[1]))
    full=leaf.schema_digest(rows)
    legacy_rows=[row for row in rows if not (len(row[1])>=7 and row[1][:6].lower()=='sqlite')]
    legacy=hashlib.sha256(json.dumps(legacy_rows,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    sealed=dict(tables={'domain_objects':dict(count=0,rows_sha256='a'*64)},
        database_ref=dict(path='Source_fixture_working22',sha256='b'*64,bytes=4096),
        versions=list(range(1,23)),schema_rows=rows,schema_sha256=full)
    retained=dict(tables=copy.deepcopy(sealed['tables']),database_ref=dict(sealed['database_ref'],path='Source_fixture_original22'),
        versions=list(range(1,23)),schema_sha256=legacy)
    manifest=dict(migrations=list(range(1,23)),schema_hash='sha256:'+full)
    def rejection(name,value):
        error=None
        try:m.validate_working22(leaf,value,retained,manifest)
        except (ValueError,pure['BoundaryError']) as exc:error=str(exc)
        check(name,error=='PUBLIC_SCHEMA_ORDER_OR_DUPLICATE',dict(observed=error,Source_fixture_only=True))
    reordered=copy.deepcopy(sealed);reordered['schema_rows']=list(reversed(rows))
    rejection('schema_order_change_rejected_by_bound_full_digest_oracle',reordered)
    duplicated=copy.deepcopy(sealed);duplicated['schema_rows'].append(copy.deepcopy(rows[-1]))
    rejection('schema_duplicate_rejected_by_bound_full_digest_oracle',duplicated)

    case=json.loads(g.get_buffer(probe['case_closed_ref']['path']))
    retained_state=json.loads(g.get_buffer(probe['retained_state_ref']['path']))
    original=retained_state['observations']['sealed22']
    backup=json.loads(g.get_buffer(probe['backup_manifest_ref']['path']))
    check('actual_original1201_failure_preserved_and_zero_children',
        case['status']=='STOPPED_AT_FIRST_FAILURE' and case['first_failure']['message']=='COPIED22_LOGICAL_STATE'
        and case['new_native_children_attempted']==0 and case['calls']==[])
    check('actual_probe83_tables_and_both_schema_projections_bind_retained_and_Native_manifest',
        probe['table_count']==len(original['tables'])==83 and probe['table_differences']=={}
        and probe['retained_schema_sha256']==original['schema_sha256']==probe['legacy_exclude_sqlite_compact_sha256']
        and probe['manifest_schema_hash']==backup['schema_hash']=='sha256:'+probe['current_schema_sha256']
        and probe['working_copy_ref']['sha256']==original['database_ref']['sha256']
        and probe['working_copy_ref']['bytes']==original['database_ref']['bytes']
        and probe['working_bytes_unchanged'] is True)
    check('author_probe_did_not_emit_rows_or_access_private_key_or_replay_old_validation',
        probe['original_source_db_opened'] is False and probe['private_key_accessed'] is False
        and probe['raw_rows_emitted'] is False and probe['SQL_write_statements']==0
        and probe['SQL_integrity_or_foreign_key_checks_replayed']==0 and probe['sqlite_connection_closed'] is True)
    old_tree=ast.parse(g.get_buffer(inverse['base_caller_ref']['path']));new_tree=ast.parse(raw)
    def imports(t):return ast.dump(ast.Module(body=[node for node in t.body if isinstance(node,(ast.Import,ast.ImportFrom))],type_ignores=[]),include_attributes=False)
    check('runtime_closure_149_144_reused_with_exact_unchanged_external_resources_and_no_new_imports',
        prior_decision['runtime_closure_reviewed'] is True
        and h['runtime_resources_ref']==prior_decision['runtime_resources_ref']==i['runtime_resources_ref']
        and imports(old_tree)==imports(new_tree))
    observations=dict(exact_complete_inverse_in_retained_prefix=True,
        actual_source_author_audit_ref=pref(W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.public22-main23-continuation-source03.actual-audit.root.json'),
        working_probe_ref=h['working22_difference_probe_ref'],actual_case_closed_ref=probe['case_closed_ref'],
        original1201_status=case['status'],original1201_new_children=case['new_native_children_attempted'],
        actual_original22_table_count=probe['table_count'],legacy_schema_sha256=probe['retained_schema_sha256'],
        full_Native_schema_sha256=probe['current_schema_sha256'],
        runtime_closure_evidence_ref=prior_h['runtime_closure_evidence_ref'],
        immutable_history_rewritten=False,SQL_connections_by_this_reviewer=0)
    s.write('source-delta-evidence.json',dict(source03_caller_ref=h['caller_ref'],base_caller_ref=inverse['base_caller_ref'],
        functions=s.code_evidence(raw,h['caller_ref']['path'],['validate_working22','execute']),
        prefix_ref=s.pin(D/'independent-delta-result.json'),tail_counts=len(checks),observations=observations,
        unchanged_other_functions_and_complete_inverse_verified_in_retained_prefix=True,
        all_original15_pins_preserved_in_closed_prefix=True,old144_149_checks_rerun=False,
        author12_controls_rerun=False,all_new_condition_controls_Source_only=True,
        runtime_closure_scope='Unchanged external closure inherited from actual accepted Source02; Source03 Caller selfpin and complete manifest newly held. Future Root entry still reobserves resources.'))
except BaseException as exc:
    failure=dict(type=type(exc).__name__,message=str(exc));raise
finally:
    guard_ref=s.write('tail-source-guard.closed.json',g.close())
    s.write('independent-tail-result.json',dict(checks=checks,count=len(checks),passed=sum(x['passed'] for x in checks),
        failure=failure,observations=observations,source_guard_ref=guard_ref,held_refs=refs,
        retained_successful_prefix_ref=s.pin(D/'independent-delta-result.json'),
        original_review_failure=origin,original_ordinal=original_ordinal,
        Source_only=True,actual_Native_Go_SQL_TP_Root_stage_model_calls=0,execution_grant=False,formal_acceptance=False))
print(json.dumps(dict(checks=len(checks),passed=sum(x['passed'] for x in checks),failure=failure,
    source_guard_ref=guard_ref,original_review_failure=origin,retained_prefix_controls=20,
    Source_only=True,new_SQL_connections=0,execution_grant=False,formal_acceptance=False),ensure_ascii=False))
