"""Finite receipt closeout after original end-of-review summary failure.

Does not repeat production read_inputs, historical controls or compiler input pins.
"""
from pathlib import Path
import ast,hashlib,json,sys,types
N=Path(__file__).resolve().parent
ns={'__name__':'definitions_only','__file__':str(N/'review.py')}
exec(compile((N/'review.py').read_bytes(),ns['__file__'],'exec'),ns)
pin,read,save,inert=ns['pin'],ns['read'],ns['save'],ns['inert']
S,OLD,PR,ACTOR,SESSION=ns['S'],ns['OLD'],ns['PR'],ns['ACTOR'],ns['SESSION']
audit=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
limit=audit.stat().st_size;calls={};captured={}
targets=['9c0bf7','68bba7','bc71b6','a3fee4','422c54','051bda','8fa2d9']
with audit.open('rb') as f:
 header=f.readline();f.seek(max(len(header),limit-16*1024*1024))
 if f.tell()!=len(header):f.readline()
 offset=f.tell()
 while offset<limit:
  line=f.readline();row=json.loads(line);p=row.get('payload',{})
  if row.get('type')=='response_item' and p.get('type')=='custom_tool_call':calls[p['call_id']]=(offset,line,row)
  if row.get('type')=='response_item' and p.get('type')=='custom_tool_call_output':
   for block in p.get('output',[]):
    for text in dict.fromkeys([block.get('text',''),*block.get('text','').splitlines()]):
     try:v=json.loads(text)
     except (ValueError,TypeError):continue
     if not isinstance(v,dict) or v.get('chunk_id') not in targets or v['chunk_id'] in captured:continue
     key=v['chunk_id'];call=calls[p['call_id']];rows=[(0,header),(call[0],call[1]),(offset,line)]
     raw=N/('actual-'+key+'.raw.jsonl')
     with raw.open('xb') as out:out.write(b''.join(b for _,b in rows))
     rawref=pin(raw)
     br=save('actual-'+key+'.binding.json',dict(source_audit_path=str(audit),source_prefix_size_observed=limit,source_line_offsets=[a for a,_ in rows],source_line_bytes=[len(b) for _,b in rows],original_line_sha256=[hashlib.sha256(b).hexdigest() for _,b in rows],original_capture_ref=rawref,original_call_id=p['call_id'],tool_call_timestamp=call[2]['timestamp'],tool_result_timestamp=row['timestamp'],chunk_id=key))
     captured[key]=dict(raw_ref=rawref,binding_ref=br,result=v,call=call[2],rows=rows)
  offset+=len(line)
assert set(captured)==set(targets)
identity=json.loads(header)['payload']
assert identity['id']==SESSION and identity['source']['subagent']['thread_spawn']['agent_path']==ACTOR.removeprefix('codex:')
for launch,complete,session in [('9c0bf7','68bba7',15349),('bc71b6','a3fee4',95656),('051bda','8fa2d9',89233)]:
 assert captured[launch]['result']['session_id']==session
 assert str(session) in captured[complete]['call']['payload']['input']
 assert captured[complete]['result']['exit_code']==1 and 'FULLW09_V3_REVIEW_PYTHON_EXIT=1' in captured[complete]['result']['output']
assert captured['422c54']['result']['exit_code']==1
third=captured['8fa2d9']['result']['output']
assert "KeyError: 'closed'" in third and 'line 130, in run' in third
snapshot=N/'original-guard-wrapper-error.review.py'
assert snapshot.read_bytes()==(N/'review.py').read_bytes()
assert "g=read(r);check('prior source guard clean '" in snapshot.read_text(encoding='utf-8').splitlines()[129]
h,mf,c,contract=[read(S/n) for n in ('HDF.json','MF.json','source.choice.json','root-calling-contract.json')]
m=inert(S/'full_w09_runtime.source.py','finite_fullw09_v3_closeout')
gm=m.module(c['common']['guard_ref'])
href,mref=pin(S/'HDF.json'),pin(S/'MF.json')
priorh,priorm,priord=[pin(PR/n) for n in ('HDF.json','MF.json','source-review-decision.json')]
pd=read(priord)
author_binding=pin(N/'actual-v3-author-Root-peer.binding.json');author_raw=pin(N/'actual-v3-author-Root-peer.raw.jsonl')
refs=[pin(__file__),pin(N/'review.py'),pin(snapshot),pin(N/'original-source21-count-error.review.py'),pin(N/'original-historical-count-error.review.py'),href,mref,*mf['members'],priorh,priorm,priord,author_binding,author_raw,c['common']['guard_ref'],read(priorh)['final_guard_ref']]
refs += [x[k] for x in captured.values() for k in ('raw_ref','binding_ref')]
refs=m.unique(refs)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=512*1024*1024)
try:
 guard.acquire(refs)
 # Correct only the summary's wrapper access; do not rerun passed interfaces.
 author_guard=read(h['source_guard_ref'])
 assert author_guard['schema']=='researchos.fullw09-v3-source-guard-closure.v1'
 for observed in (author_guard['cleanup'],read(read(priorh)['final_guard_ref'])):
  assert observed['closed'] is True and observed['retained_handles_count']==0 and observed['errors']==[] and observed['verification']=='PASSED'
 for cap in captured.values():
  with audit.open('rb') as stream:
   for offset,line in cap['rows']:stream.seek(offset);assert stream.read(len(line))==line
 assert all(pin(r['path'])==r for r in refs)
finally:closed=guard.close()
assert closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[] and closed['verification']=='PASSED'
gr=save('final-finite-Source-guard.closed.json',closed)
failures=save('original-failures-preserved.json',dict(originals=[dict(ordinal=ordinal,launch_ref=captured[launch]['raw_ref'],launch_binding_ref=captured[launch]['binding_ref'],completion_ref=captured[end]['raw_ref'],completion_binding_ref=captured[end]['binding_ref'],outer_exit=1,python_exit=1,Native_exit=None,source_snapshot_ref=pin(N/source),original_close_receipt=None,closure_evidence='finally guard.close() executed on unwinding; original return object was not persisted; process terminated. No original errors==[] assertion is inferred.') for ordinal,launch,end,source in [(1059,'9c0bf7','68bba7','original-source21-count-error.review.py'),(1060,'bc71b6','a3fee4','original-historical-count-error.review.py'),(1063,'051bda','8fa2d9','original-guard-wrapper-error.review.py')]],read_diagnostic=dict(ordinal=1061,raw_ref=captured['422c54']['raw_ref'],binding_ref=captured['422c54']['binding_ref'],outer_exit=1,python_exit=None,Native_exit=None),Root_assigned_ordinals=True,original_failures_never_rewritten=True))
evidence=save('completed-delta-evidence.json',dict(schema='researchos.fullw09-v3-completed-delta-evidence.v1',evidence_kind='ACTUAL_EXECUTION_CONTROL_FLOW_WITH_EXPLICIT_LATE_SUMMARY_FAILURE',source_snapshot_ref=pin(snapshot),actual_launch_ref=captured['051bda']['raw_ref'],actual_launch_binding_ref=captured['051bda']['binding_ref'],actual_completion_ref=captured['8fa2d9']['raw_ref'],actual_completion_binding_ref=captured['8fa2d9']['binding_ref'],completed_before_original_exception=['unchanged production package_refs accepted final exact v3 HDF/MF','unchanged actual_audit accepted real adjacent Root metadata and author FINAL','six exact unchanged Source files','choice and contract strict inverse namespace/run-id rebase only','three fresh selector UUIDs and absent exact future directories','21 Main source keys exact and all input pins under SourceReadGuard','production read_inputs verified inventory/locked tools and every returned ref held','loaded DLL runtime resources held','historical 69/112/20/98 reused from pinned original evidence only'],inference_limit='These successful assertions are supported by the captured original process reaching line 130 without earlier assertion failure. The original checks list and final SourceReadGuard.close return were not serialized. This receipt does not invent them.',original_input_final_pin_loop_executed=False,original_guard_closed_receipt=None,corrected_assertion='author source guard cleanup.closed, cleanup.retained_handles_count, cleanup.errors',corrected_author_and_prior_guards_pass=True,final_finite_guard_ref=gr,final_finite_guard_closed=True,final_finite_guard_retained_handles=0,final_finite_guard_errors=[],no_full_input_or_production_read_inputs_rerun_in_closeout=True,actual_prepare_run=False,actual_Go_runs=0,actual_Native_runs=0,actual_SQL_runs=0,actual_dispatcher_runs=0,actual_model_provider_calls=0,Main_written=False,Canon_written=False,formal_acceptance=False,execution_grant=False))
inputs=save('review-inputs-and-evidence.json',dict(final_finite_held_refs=refs,completed_delta_evidence_ref=evidence,original_failures_ref=failures,original_production_blueprint_ref=c['common']['compiler_blueprint_ref'],source21=c['common']['source21'],source_author_audit_ref=author_binding,prior_review_refs=[priorh,priorm,priord],complete_input_reverification_repeated=False))
bound={key:pin(S/name) for key,name in contract['source_file_bindings'].items()}
common=dict(actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',reviewer_thread_id=SESSION,source_handoff_ref=href,source_manifest_ref=mref,calling_contract_ref=pin(S/'root-calling-contract.json'),**bound,selectors=c['selectors'],source21=c['common']['source21'],actual_executed=False,formal_case_accepted_delta=0,formal_acceptance=False,execution_grant=False,parent_acceptance=False,Main_written=False,Canon_written=False)
decision=save('source-review-decision.json',dict(schema='researchos.w09-three-selector-producer-independent-source-decision.v1',decision='SOURCE_ACCEPTED_FOR_ROOT_THREE_SELECTOR_NATIVE',verdict='SOURCE_ACCEPTED_FOR_ROOT_THREE_SELECTOR_NATIVE',**common,source_author=m.AUTHOR,source_author_audit_ref=author_binding,prior_review_hdf_ref=priorh,prior_review_mf_ref=priorm,prior_review_decision_ref=priord,completed_delta_evidence_ref=evidence,input_evidence_ref=inputs,original_failures_ref=failures,final_Source_guard_ref=gr,final_guard_closed=True,final_guard_errors=[],final_guard_retained_handles=0,earlier_failed_process_guard_receipts_available=False,findings=[],resolved_prior_findings=[x['id'] for x in pd['findings']],current_CanonicalPair_held=False,actual_prepare_run=False,actual_Go_runs=0,actual_Native_runs=0,actual_SQL_runs=0,actual_dispatcher_runs=0,actual_model_provider_calls=0,Root_next_gate='Fresh Root scope/lease/Canon and exact real audit bindings; independently verify actual prepare/run afterwards.'))
members=[pin(N/n) for n in ('review.py','closeout.py','original-source21-count-error.review.py','original-historical-count-error.review.py','original-guard-wrapper-error.review.py')]+[author_binding,author_raw,gr,failures,evidence,inputs,decision]+[x[k] for x in captured.values() for k in ('raw_ref','binding_ref')]
manifest=save('MF.json',dict(schema='researchos.w09-three-selector-independent-source-review-manifest.v1',members=members))
handoff=save('HDF.json',dict(schema='researchos.w09-three-selector-independent-source-review-handoff.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',reviewer_thread_id=SESSION,status='SOURCE_ACCEPTED_FOR_ROOT_THREE_SELECTOR_NATIVE',manifest_ref=manifest,source_decision_ref=decision,source_handoff_ref=href,source_manifest_ref=mref,calling_contract_ref=common['calling_contract_ref'],completed_delta_evidence_ref=evidence,original_failures_ref=failures,final_Source_guard_ref=gr,actual_executed=False,formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,Main_written=False,Canon_written=False,final_guard_closed=True,earlier_failed_process_guard_receipts_available=False))
# Validate the actually published local review pair and exact caller fields.
rh,rr=m.pair(handoff,manifest)
assert decision in rr and rh['source_decision_ref']==decision and rh['actor_id']==ACTOR
d=read(decision)
assert d['schema']==contract['review_schema'] and d['decision']==contract['review_decision']
assert all(d[k]==v for k,v in dict(source_handoff_ref=href,source_manifest_ref=mref,calling_contract_ref=common['calling_contract_ref'],**bound).items())
assert d['selectors']==c['selectors'] and d['source21']==c['common']['source21']
print(json.dumps(dict(HDF=handoff,MF=manifest,decision=decision,completed_delta_evidence=evidence,original_failures=failures,final_Source_guard_ref=gr,final_finite_held_refs=len(refs),actual_prepare_run=False,formal_acceptance=False,execution_grant=False),ensure_ascii=False),flush=True)
