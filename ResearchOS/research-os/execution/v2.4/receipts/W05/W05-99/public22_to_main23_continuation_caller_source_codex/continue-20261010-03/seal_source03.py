"""Seal existing Source03 results, preserving original diagnostics. No tests rerun."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;P=O.parent/'continue-20261010-02';R=O.parents[6]
A=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
    spelling=str(p);b=Path(p).read_bytes();return dict(path=spelling,sha256=sha(b),bytes=len(b))
def doc(p):return json.loads(Path(p).read_bytes())
def save(n,v,raw=False):
    with (O/n).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(O/n)
assert R.name=='research-os'
rows=[]
with A.open('rb') as f:
    while True:
        off=f.tell();line=f.readline()
        if not line:break
        rows.append((off,line,json.loads(line)))
captures={}
for chunk,ordinal,exitcode,label in [('eb1b66',None,0,'actual-working22-probe'),('915d57',1205,1,'original-1205'),('f46d4a',None,0,'actual-source03-controls')]:
    results=[]
    for row in rows:
        d=row[2];p=d.get('payload',{})
        if d.get('type')!='response_item' or p.get('type') not in ('custom_tool_call_output','function_call_output'):continue
        for block in p.get('output',[]):
            if type(block) is not dict:continue
            try:v=json.loads(block.get('text',''))
            except ValueError:continue
            if type(v) is dict and v.get('chunk_id')==chunk:results.append((row,v))
    assert len(results)==1,(chunk,len(results))
    result,tool=results[0];cid=result[2]['payload']['call_id'];assert tool['exit_code']==exitcode
    calls=[x for x in rows if x[2].get('type')=='response_item' and x[2].get('payload',{}).get('type') in ('custom_tool_call','function_call') and x[2]['payload'].get('call_id')==cid]
    assert len(calls)==1;call=calls[0]
    hosts=[x for x in rows if call[2]['ordinal']<x[2]['ordinal']<result[2]['ordinal'] and x[2].get('type')=='event_msg' and x[2].get('payload',{}).get('item',{}).get('type')=='CommandExecution']
    assert len(hosts)==1 and hosts[0][2]['payload']['item']['exit_code']==exitcode
    host=hosts[0];triple=[rows[0],call,result]
    raw_ref=save(label+'.raw.jsonl',b''.join(x[1] for x in triple),True);host_ref=save(label+'.host-event.jsonl',host[1],True)
    binding=save(label+'.binding.json',dict(schema='researchos.source03-actual-operation-binding.v1',
        actor_id='/root/attach_restore_independent_review',actor_thread_id=rows[0][2]['payload']['id'],source_audit_path=str(A),
        source_line_offsets=[x[0] for x in triple],original_line_sha256=[sha(x[1]) for x in triple],original_line_bytes=[len(x[1]) for x in triple],
        original_raw_ref=raw_ref,actual_call_id=cid,actual_chunk_id=chunk,host_event_ref=host_ref,
        host_event_offset=host[0],host_event_ordinal=host[2]['ordinal'],original_ordinal=ordinal,
        actual_outer_exit=exitcode,actual_python_exit=exitcode,python_exit_basis='Sole explicit Python native command in host invocation; actual host result and process output retained.',
        actual_native_exit=None,actual_go_exit=None,actual_TP_exit=None,actual_dispatcher_exit=None,
        diagnostic='PATH_SPELLING_COMPARISON_IN_AUTHOR_BUILD_SCRIPT' if ordinal else None,
        source_contract_raw_reference_equality_changed=False,successful_prefix_rerun=False,formal_acceptance=False))
    captures[label]=dict(raw_ref=raw_ref,binding_ref=binding)

S=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
completion_ref=dict(path=str(S/'w05-continuation-fe948281-execute-completed.host-pair.root.json'),sha256='4d7ed2a38c5d4630247c06e3cd2a8353a82e38e53200ffff7222f6189ace0153',bytes=1509)
original_ref=dict(path=str(S/'w05-continuation-fe948281-execute-completed.original.raw.jsonl'),sha256='f37e6436b900eaa82a241cad8b46f4f7740147d11f1a04cf76c0b5368b88ce70',bytes=72220)
for ref in [completion_ref,original_ref]:assert pin(ref['path'])==ref
probe=doc(O/'working22-difference-probe.json');assert pin(probe['case_closed_ref']['path'])==probe['case_closed_ref']
closed=doc(probe['case_closed_ref']['path']);assert closed['calls']==[] and closed['new_native_children_attempted']==0
assert closed['first_failure']['message']=='COPIED22_LOGICAL_STATE'
original1201=save('original-1201-preserved.json',dict(schema='researchos.original1201-preserved-source-input.v1',
    ordinal=1201,case_closed_ref=probe['case_closed_ref'],Root_completed_host_binding_ref=completion_ref,Root_original_three_line_ref=original_ref,
    actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,new_native_children_attempted=0,
    public_tool_stdout_platform_truncated=True,complete_state_source='Pinned case.closed.json, not a reconstructed tool output.',
    old_scope_reexecution_permitted=False,original1025_result='FAILED_RETAINED',formal_acceptance=False))
inverse=doc(O/'revision-inverse.json');assert all(pin(r['path'])==r for r in inverse['prior_namespace_protected_refs'])
controls=doc(O/'delta-source-controls.json');assert controls['passed']==controls['count']==12
i=doc(O/'source-inputs.json')
decision=dict(schema='researchos.public22-continuation-source-revision-declaration.v1',source_author='codex:/root/attach_restore_independent_review',
    status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION',revision='continue-20261010-03',
    revision_reason='Original1201 cross-version schema digest comparison used different sqlite_master projections.',
    caller_ref=pin(O/'public22_to23_root.source.py'),source_inputs_ref=pin(O/'source-inputs.json'),calling_contract_ref=pin(O/'root-calling-contract.source.json'),
    delta_controls_ref=pin(O/'delta-source-controls.json'),historical_review_prefix_ref=pin(O/'historical-review-prefix.json'),complete_inverse_ref=pin(O/'revision-inverse.json'),
    working22_difference_probe_ref=pin(O/'working22-difference-probe.json'),original1201_ref=original1201,
    original1205_ref=captures['original-1205']['binding_ref'],actual_probe_ref=captures['actual-working22-probe']['binding_ref'],actual_controls_ref=captures['actual-source03-controls']['binding_ref'],
    Source_controls_only=12,isolated_readonly_working_copy_SQL_probes=1,old_SQL_validations_replayed=0,
    Native_Go_TP_Rootstage_calls=0,MainCanonScope_writes=0,private_key_read_hash_copy=0,
    source_author_acceptance=False,self_acceptance=False,formal_acceptance=False,parent_acceptance=False,execution_grant=False,STOP=True)
# Replace this unpublished declaration only; all old generations remain byte exact.
(O/'source-decision.json').write_bytes((json.dumps(decision,ensure_ascii=False,indent=2)+'\n').encode())
report='''Source03 candidate fixes original1201 COPIED22_LOGICAL_STATE.

The only product-caller delta adds validate_working22 and replaces the incompatible schema digest comparison in execute. The current observation is retained before validation. All other function ASTs match Source02; the recorded inverse reconstructs its exact bytes. The Source02 inputs are copied byte for byte, including every original raw reference spelling.

The isolated working-copy probe found 83 tables with identical counts and row digests. The retained pre-v3 observation hashes sqlite_master after excluding names matching SQLite LIKE sqlite_%; v3 hashes every row and coalesces SQL NULL. The current complete schema hash 2f91574c52b3f6d5e5c4610bab175209cb80c9a38e6696c2bdfd7c9d423320cf equals the original Native backup manifest. Its historical projection reproduces bfc98c568af73d276aad92b26d96ec5708f3cd26da7261d3c907161ad901792b exactly. Working bytes remained unchanged. The original source database and private recovery key were not opened by this probe; credential row values were never emitted.

The new validator requires exact all-table equality, working/retained byte digest and size equality, exact ledger 1..22 in all three documents, v3 schema self-consistency and Native manifest binding, and the exact old schema projection digest. A non-internal empty SQL string is rejected because the v3 coalesced representation cannot distinguish historical NULL. No schema/table mismatch is waived. The prior original1025 and original1201 failures remain failures.

Twelve new in-memory controls passed, including changes to table digest/set, byte digest/size, ledger, claimed complete hash, manifest hash, retained old hash and internal schema rows. The tests use synthetic objects; they are not a product acceptance. The actual working-copy probe separately establishes the real discrepancy. Successful previous controls, 144/149 review prefixes and old SQL validation suites were not replayed.

Original1205 is an author build-script path-spelling assertion: a Path converted a slash-form leaf ref to backslashes. The raw I/O and host result are preserved. The successful candidate-build prefix was retained; a separate tail script compared the original ref spelling with exact SHA/bytes and executed only the still-unrun controls. Source raw-ref equality rules were unchanged.

No new Native child, Main/Canon/Scope write, Root stage, dispatcher, Go, TP or model call occurred. The consumed Source02 Scope must never execute again. This candidate requires independent Full Source review, then new Root registration, fresh current4 and a finite lease. Source author remains codex:/root/attach_restore_independent_review. Formal and parent acceptance remain false.
'''
report_ref=save('SOURCE03_REVIEW_NOTES.md',report.encode(),True)
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ['HDF.json','MF.json','postseal-tool-io.json']]
mf=save('MF.json',dict(schema='researchos.public22-continuation-source-revision-manifest.v1',members=members,exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
hdf=save('HDF.json',dict(schema='researchos.public22-to-main23-continuation-source-handoff.v1',source_author='codex:/root/attach_restore_independent_review',
    status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION',revision='continue-20261010-03',manifest_ref=mf,
    caller_ref=pin(O/'public22_to23_root.source.py'),source_inputs_ref=pin(O/'source-inputs.json'),calling_contract_ref=pin(O/'root-calling-contract.source.json'),
    source_decision_ref=pin(O/'source-decision.json'),source_controls_ref=pin(O/'delta-source-controls.json'),
    runtime_resources_ref=i['runtime_resources_ref'],main23_bound_ref=i['main23_bound_ref'],existing22_decision_ref=i['existing22_decision_ref'],
    historical_review_prefix_ref=pin(O/'historical-review-prefix.json'),revision_inverse_ref=pin(O/'revision-inverse.json'),
    working22_difference_probe_ref=pin(O/'working22-difference-probe.json'),original1201_preserved_ref=original1201,
    original1205_preserved_ref=captures['original-1205']['binding_ref'],actual_operations=captures,review_notes_ref=report_ref,
    new_native_phases=['upgrade22to23','backup23','verify23'],Source_controls_only=12,isolated_readonly_working_copy_SQL_probes=1,
    Source_author_Native_Go_TP_RootStage_calls=0,MainCanonScope_writes=0,live_Canon_handles=0,private_key_read_hash_copy=0,
    old_four_Native_children_replayed=False,old_controls_and_SQL_validations_replayed=False,
    original1025='FAILED_RETAINED',original1201='FAILED_RETAINED',original_failure_ordinals=[1201,1205],
    source02_prior_files_byte_unchanged=len(inverse['prior_namespace_protected_refs']),write_scope=str(O),
    formal_acceptance=False,parent_acceptance=False,execution_grant=False,self_acceptance=False,formal_case_accepted_delta=0,
    remaining='Independent non-author Full Source03 review, then new Root registration and Scope; old consumed Scope cannot execute again.',STOP=True))
assert all(pin(r['path'])==r for r in members)
assert all(pin(r['path'])==r for r in inverse['prior_namespace_protected_refs'])
print(json.dumps(dict(HDF_ref=hdf,MF_ref=mf,caller_ref=pin(O/'public22_to23_root.source.py'),decision_ref=pin(O/'source-decision.json'),
    original1205_ref=captures['original-1205']['binding_ref'],probe_ref=pin(O/'working22-difference-probe.json'),controls_ref=pin(O/'delta-source-controls.json'),
    member_count=len(members),formal_acceptance=False),ensure_ascii=False))
