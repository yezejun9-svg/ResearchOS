"""Static diagnosis and pure type-boundary counterexamples; no product entrypoint."""
from pathlib import Path
import ast,copy,difflib,hashlib,json,types
O=Path(__file__).resolve().parent;R=O.parents[6];W=R/'execution/v2.4/receipts/W09/W09-99'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
B=W/'w09_formal_root_bridge_source_codex/bridge-20261010-06'
Q=W/'full_w09_nf6_actual_independent_review_codex/review-actual-nf6-20261010-01'
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(Path(p).read_bytes())
def save(name,value,raw=False):
    with (O/name).open('xb') as f:f.write(value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(O/name)
def literals(p,names):
    return {n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(Path(p).read_bytes()).body
            if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in names}
profile=R/'execution/v2.4/formal_profile_w09.py';index=R/'execution/v2.4/formal_case_index.py';router_path=R/'ops/ci/w09_formal_router.py'
files=[profile,index,router_path,R/'ops/ci/retrieval.py',B/'HDF.json',B/'MF.json',B/'w09_root_bridge.source.py',
    Q/'HDF.json',Q/'MF.json',Q/'decision.json',Q/'prepare_review.py',Q/'review_partial_actual.py',Q/'review_remaining_actual.py',Q/'publish_six_modes_revision.py',
    W/'full_w09_nf5_actual_independent_review_codex/review-actual-nf5-20261010-01/review_actual_nf5.v7.py',
    S/'original1208.fixed-actual.binding.root.json',S/'original1208.fixed-actual.raw.root.jsonl']
inputs=[pin(p) for p in files]
binding=doc(files[-2]);raw=files[-1].read_bytes();parts=raw.splitlines(keepends=True)
assert binding['original_ordinal']==1208 and binding['actual_host_chunk_id']=='aeeae7'
assert binding['actual_outer_exit']==binding['actual_python_exit']==1
assert pin(files[-1])==binding['original_capture_ref'] and len(parts)==3
assert [len(x) for x in parts]==binding['source_line_bytes']
assert [hashlib.sha256(x).hexdigest() for x in parts]==binding['original_line_sha256']
with Path(binding['source_audit_path']).open('rb') as f:
    for off,part in zip(binding['source_line_offsets'],parts):f.seek(off);assert f.read(len(part))==part
original=[json.loads(x) for x in parts]
assert original[0]['payload']['id']==binding['Root_thread_id']
assert 'TYPE_ARRAY' in parts[-1].decode('utf-8') and '_native' in parts[-1].decode('utf-8')
root_failure=save('original1208-observation.json',dict(schema='researchos.original1208-static-diagnosis-observation.v1',
    original_binding_ref=pin(files[-2]),original_raw_ref=pin(files[-1]),original_three_lines_verified=True,source_ranges_match=True,
    Root_actual_propose_failure=True,actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_dispatcher_exit=None,
    own_full_propose_execution=False,formal_acceptance=False))

routes=literals(router_path,{'FORMAL','NATIVE','SELECTED'});ids=literals(profile,{'IDS'})['IDS']
route_rows=[]
for route,formal in routes['FORMAL'].items():
    route_rows.append(dict(route=list(route),formal_value_type=type(formal).__name__,formal_ids=list(formal),
        native_value_type=type(routes['NATIVE'][route]).__name__,selected_value_type=type(routes['SELECTED'][route]).__name__))
assert len(route_rows)==6 and all(x['formal_value_type']=='tuple' for x in route_rows)
source=profile.read_text('utf-8')
old='    api.exact_ids(router["FORMAL"][route], IDS[key], "router formal IDs")\n'
new='    api.require(type(router["FORMAL"][route]) in (list, tuple), "ROUTER_CONTRACT", "formal IDs sequence")\n    api.exact_ids(list(router["FORMAL"][route]), IDS[key], "router formal IDs")\n'
assert source.count(old)==1
candidate=source.replace(old,new,1)
candidate_ref=save('formal_profile_w09.candidate.py',candidate.encode('utf-8'),True)
patch=''.join(difflib.unified_diff(source.splitlines(True),candidate.splitlines(True),fromfile='a/execution/v2.4/formal_profile_w09.py',tofile='b/execution/v2.4/formal_profile_w09.py'))
patch_ref=save('candidate-main-native-boundary.patch',patch.encode(),True)
before_functions={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
after_functions={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(candidate).body if isinstance(n,ast.FunctionDef)}
assert set(before_functions)==set(after_functions)
assert [n for n in before_functions if before_functions[n]!=after_functions[n]]==['_native']
assert candidate.replace(new,old,1)==source

# The exact Main helper definitions are extracted; neither Main module nor _native runs.
tree=ast.parse(index.read_bytes());names={'InvalidEvidence','require','text','sequence','exact_ids'}
nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
assert len(nodes)==len(names)
env={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<exact-Main-type-helpers-only>','exec'),env)
api=types.SimpleNamespace(**env)
def proposed(value,expected):
    api.require(type(value) in (list,tuple),'ROUTER_CONTRACT','formal IDs sequence')
    api.exact_ids(list(value),expected,'router formal IDs')
def outcome(fn):
    try:fn()
    except env['InvalidEvidence'] as exc:return exc.code
    return 'PASS'
checks=[]
for route,value in routes['FORMAL'].items():
    expected=ids[route[2] or route[3]]
    original_code=outcome(lambda:api.exact_ids(value,expected,'router formal IDs'))
    fixed_code=outcome(lambda:proposed(value,expected))
    assert original_code=='TYPE_ARRAY' and fixed_code=='PASS'
    checks.append(dict(route=list(route),original_boundary=original_code,candidate_boundary=fixed_code))
values=[('list_remains_supported',['C19-01','C19-02','C19-03'],'PASS'),
    ('duplicate_tuple',('C19-01','C19-02','C19-03','C19-03'),'DUPLICATE_ID'),
    ('missing_id',('C19-01','C19-02'),'ID_SET'),('extra_id',('C19-01','C19-02','C19-03','C19-04'),'ID_SET'),
    ('non_text',('C19-01','C19-02',3),'TYPE_TEXT'),('empty_tuple',(),'TYPE_ARRAY'),
    ('dictionary_with_expected_keys',{'C19-01':1,'C19-02':1,'C19-03':1},'ROUTER_CONTRACT'),
    ('set_of_expected_ids',{'C19-01','C19-02','C19-03'},'ROUTER_CONTRACT'),('string','C19-01','ROUTER_CONTRACT')]
counterexamples=[]
for label,value,want in values:
    actual=outcome(lambda:proposed(value,ids['C19']));assert actual==want,(label,actual,want)
    counterexamples.append(dict(case=label,actual=actual,expected=want))
dict_bad={x:True for x in ids['C19']}
assert outcome(lambda:api.exact_ids(list(dict_bad),ids['C19'],'unguarded conversion'))=='PASS'
global_strict=outcome(lambda:api.sequence(('receipt-member',),'untrusted JSON array'))
assert global_strict=='TYPE_ARRAY'
matrix_ref=save('pure-type-boundary-diagnosis.json',dict(schema='researchos.w09-router-type-boundary-diagnosis.v1',
    actual_router_rows=route_rows,six_original_tuple_refusals_and_candidate_passes=checks,counterexamples=counterexamples,
    unconditional_list_conversion_dict_counterexample='PASS demonstrates why an explicit tuple/list guard is needed.',
    global_JSON_sequence_still_strict=global_strict,Main_module_imported=False,Main_native_called=False,
    Root_stages_run=0,Native_calls=0,SQL_calls=0,old_controls_replayed=False,formal_acceptance=False))

producer_sources=literals(R/'ops/ci/retrieval.py',{'SOURCES'})['SOURCES']
assert 'execution/v2.4/formal_profile_w09.py' not in producer_sources and 'ops/ci/w09_formal_router.py' in producer_sources
input_ref=save('input-pins.json',dict(schema='researchos.w09-type-diagnosis-input-pins.v1',refs=inputs))
criteria=[
 'Independently review this two-line Main _native boundary change against the exact prior profile pin; all other AST and strict JSON sequence helpers remain unchanged.',
 'Exercise _router_contract on the actual pinned router and confirm all six FORMAL tuples traverse the guarded normalization while missing/duplicate/non-text IDs and dict/set/string containers are rejected.',
 'Use actual sealed NF6 reports, tool-runs and six Backup Mode documents with the real Main API and Reader in the post-adoption formal flow. Direct closure.verify_mode alone does not certify _native or verify_owner.',
 'Refresh the Main profile source pin in a new context seed and all dependent request/grant/snapshot bindings. Keep original1208 as failed; do not reuse its old request as a retry.',
 'After authorized Main adoption and fresh Root authority, Root real propose must pass its six Main _native checks and close all guards before registration. This diagnosis does not execute that gate.',
 'Preserve all NF6 Source21 bytes. A profile-only change is outside producer Source21; do not rerun Native merely for this internal adapter repair. If a Source21 input changes, reassess reuse explicitly.',
 'Complete six actual CM40 consumers and subsequent Main assemble/verify_owner/derive under the applicable fresh scope and independent review before changing formal acceptance counts.'
]
decision=save('diagnosis-decision.json',dict(schema='researchos.w09-br6-propose-type-array-diagnosis.v1',actor='/root/attach_restore_independent_review',
    original_ordinal=1208,decision='MAIN_INTERNAL_TYPE_BOUNDARY_DEFECT',recommended_owner='Main formal_profile_w09.py::_native',
    root_failure_ref=root_failure,input_pins_ref=input_ref,candidate_ref=candidate_ref,static_patch_ref=patch_ref,pure_boundary_diagnosis_ref=matrix_ref,
    actual_Main_patch_applied=False,BR6_sealed_Source_modified=False,Canon_Scope_written=False,
    root_cause='ast.literal_eval preserves FORMAL tuple values; _native passes a tuple to exact_ids whose sequence helper accepts only exact list.',
    prior_NF6_review_boundary='prepare_review.py converted route table values to lists in its review data. review_group called closure.verify_native/verify_owned; publish_six_modes_revision.py called closure.verify_mode directly. Neither uses Main profile._native.',
    rejected_alternatives=[dict(change='BR6-only list adapter',reason='Main verify_owner reconstructs router tuples and calls _dispatches->_native again, so final acceptance still fails.'),
      dict(change='Relax formal_case_index.sequence globally',reason='Widens all JSON-array evidence validation and is unnecessary.'),
      dict(change='Convert router.py FORMAL literals to lists',reason='Changes a producer Source21 input and invalidates current exact source pins; larger consequences than fixing the consuming Main boundary.'),
      dict(change='Unconditional list(value)',reason='A dict with expected IDs as keys would pass; require list/tuple explicitly first.')],
    independent_completion_criteria=criteria,Native_SQL_Go_model_TP_dispatcher_calls=0,Root_stages_run=0,formal_acceptance=False,execution_grant=False))
report='''Root original1208 is a Main internal tuple/list contract mismatch.

Actual Root BR6 propose called the sealed bridge __main__ and failed at Main _native line 642. The original call/output three-line capture and source byte ranges were verified. This diagnosis does not replace that real failure with a simulated Root run.

ops/ci/w09_formal_router.py stores every NATIVE, FORMAL and SELECTED value as a tuple. Main _router_contract uses ast.literal_eval and returns these tuples unchanged. Main _native gives FORMAL[route] directly to exact_ids; formal_case_index.sequence requires type(value) is list. Every one of the six valid routes therefore fails TYPE_ARRAY before Native/Mode validation.

NF6's accepted component review does not contradict this. prepare_review.py lines 40-48 extracts router literals and explicitly converts IDs/tests to lists for its review records. Its reused review_group calls closure.verify_native/verify_owned directly; publication lines 67-76 calls closure.verify_mode with a route tuple and prepared ctx/native records. These component checks do not call formal_profile_w09._native and do not claim formal parent acceptance.

The candidate patch belongs in Main _native: accept only an exact tuple/list from the trusted router, then pass list(value) into the existing exact_ids. Do not broaden sequence globally. Do not patch only BR6: verify_owner reconstructs the router and reaches the same defect through _dispatches. Do not rewrite router literals as the minimal fix: router.py belongs to producer Source21, while formal_profile_w09.py does not.

The static patch and candidate file are stored only in this diagnosis directory. Six pure boundary examples show original TYPE_ARRAY and candidate PASS. Nine counterexamples verify list compatibility and rejection of duplicate/missing/extra/non-text/empty IDs and dict/set/string containers. A dictionary with expected keys demonstrates why unguarded list conversion is insufficient. These are pure helper checks; no Main module, _native, Root stage, Native, SQL, model, dispatcher or TP was executed. Prior successful controls were not replayed.

After separate authorization/adoption and independent review, refresh the context's Main source pin and all dependent Root authority/snapshot references, then exercise the actual Main _native path with the sealed NF6 and Mode inputs. Original1208 remains failed. Existing Native evidence can remain reusable only while its exact Source21 pins remain unchanged. Six consumers and actual final acceptance gates remain outstanding.
'''
report_ref=save('DIAGNOSIS.md',report.encode('utf-8'),True)
for ref in inputs:assert pin(ref['path'])==ref
mf=save('MF.json',dict(schema='researchos.source-diagnosis-manifest.v1',members=[pin(p) for p in sorted(O.iterdir()) if p.is_file()],formal_acceptance=False))
hdf=save('HDF.json',dict(schema='researchos.w09-br6-type-array-diagnosis-handoff.v1',status='DIAGNOSED_MAIN_FIX_CANDIDATE_ONLY',
    actor='/root/attach_restore_independent_review',manifest_ref=mf,decision_ref=decision,candidate_ref=candidate_ref,static_patch_ref=patch_ref,
    input_pins_ref=input_ref,report_ref=report_ref,pure_diagnosis_ref=matrix_ref,original1208_ref=root_failure,
    Main_BR6_Canon_Scope_modified=False,Root_stages_run=0,Native_SQL_Go_model_TP_dispatcher_calls=0,formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(HDF_ref=hdf,MF_ref=mf,decision_ref=decision,patch_ref=patch_ref,candidate_ref=candidate_ref,pure_diagnosis_ref=matrix_ref,
    original1208_ref=root_failure,all_inputs_unchanged=True),ensure_ascii=False))
