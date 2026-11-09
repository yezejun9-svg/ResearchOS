"""Seal independent Source decision, exact original IO and closed guard proof."""
import hashlib,json,os,types
from datetime import datetime,timezone
from pathlib import Path
D=Path(__file__).resolve().parent;W=D.parent.parent;S=W/'schema21_programme_builder_source_codex/main21b-20261010-01'
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T23-50-03-01a1215b-7210-7613-b033-756b9d553b83.jsonl')
ACTOR='codex:/root/full_w09_source_review';ROOT='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=p.as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
def module(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def capture(chunks,documents):
 limit=AUDIT.stat().st_size;start=max(0,limit-64*1024*1024);calls={};found={};out=[]
 with AUDIT.open('rb') as f:
  header=f.readline();f.seek(start)
  if start:f.readline()
  while f.tell()<limit:
   off=f.tell();line=f.readline();v=json.loads(line);p=v.get('payload')
   if v.get('type')!='response_item' or type(p) is not dict:continue
   if p.get('type') in ('custom_tool_call','function_call'):calls[p['call_id']]=(off,line,v)
   elif p.get('type') in ('custom_tool_call_output','function_call_output'):
    hosts={x['chunk_id']:x for x in documents(p.get('output')) if type(x) is dict and x.get('chunk_id') in chunks and type(x.get('output')) is str}
    for chunk,result in hosts.items():
     assert chunk not in found;found[chunk]=(calls[p['call_id']],(off,line,v),result)
 assert set(found)==set(chunks),(list(found),chunks)
 identity=json.loads(header)['payload'];assert identity['id']==os.environ['CODEX_THREAD_ID']=='01a1215b-7210-7613-b033-756b9d553b83' and identity['agent_path']==ACTOR.removeprefix('codex:') and identity['parent_thread_id']==ROOT
 for chunk in chunks:
  call,last,result=found[chunk];rows=[(0,header),(call[0],call[1]),(last[0],last[1])]
  with AUDIT.open('rb') as f:
   for off,line in rows:f.seek(off);assert f.read(len(line))==line
  name='actual-review-'+chunk
  with (D/(name+'.raw.jsonl')).open('xb') as f:f.write(b''.join(line for off,line in rows))
  raw=pin(D/(name+'.raw.jsonl'));py=0 if 'python_exit=0' in result['output'].casefold() else 1 if 'python_exit=1' in result['output'].casefold() else None
  ordinal=1074 if chunk=='3bdd95' else 1075 if chunk=='709401' else None
  binding=save(name+'.binding.json',dict(schema='researchos.old21-builder-independent-actual-review-host-binding.v1',review_author=ACTOR,reviewer_thread_id=identity['id'],parent_root_thread_id=ROOT,source_audit_path=AUDIT.as_posix(),source_prefix_size_observed=limit,source_line_offsets=[off for off,line in rows],source_line_bytes=[len(line) for off,line in rows],original_line_sha256=[hashlib.sha256(line).hexdigest() for off,line in rows],original_capture_ref=raw,original_call_id=call[2]['payload']['call_id'],tool_call_timestamp=call[2]['timestamp'],tool_result_timestamp=last[2]['timestamp'],actual_chunk_id=chunk,actual_outer_exit=result.get('exit_code'),actual_python_exit=py,Native_exit=None,Go_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None,Root_assigned_original_ordinal=ordinal,original_semantic_checks_failed=2 if ordinal==1074 else None,reset=False))
  out.append(dict(chunk_id=chunk,raw_ref=raw,binding_ref=binding,outer_exit=result.get('exit_code'),Python_exit=py,ordinal=ordinal))
 return out
def main():
 r=module(D/'review_source.py','review_definitions_no_main');resolved=read(D/'finitechecks.resolved.json');original=read(D/'finitechecks.json');h=read(S/'HDF.json');c=read(h['contract_ref']['path'])
 assert resolved['status']=='ACCEPTED_SOURCE_ONLY' and not resolved['unresolved_findings'] and resolved['prior_846_passes_reused'] is True
 pairs=capture(['86c0d2','469221','23bfa3','3bdd95','eee94a','709401','53677c'],r.documents)
 failed=[p for p in pairs if p['ordinal'] is not None]
 assert [(p['ordinal'],p['outer_exit'],p['Python_exit']) for p in failed]==[(1074,0,0),(1075,1,None)]
 failure_ref=save('original-review-failures.full-IO.json',dict(schema='researchos.old21-independent-review-original-failures.v1',originals=failed,original1074_script_ref=pin(D/'review_source.py'),original1074_finitechecks_ref=pin(D/'finitechecks.json'),original1074_closed_guard_ref=original['Source_guard_ref'],original1075_guard_created=False,product_processes=0,original_unique_invocations=2,Root_assigned_ordinals=True,reset=False))
 index=save('actual-independent-review-IO-index.json',dict(review_author=ACTOR,reviewer_thread_id=os.environ['CODEX_THREAD_ID'],actual_pairs=pairs,original_failures_ref=failure_ref,execution_grant=False,formal_acceptance=False))
 checked=846+len(resolved['continuation_checks']);when=datetime.now(timezone.utc).isoformat()
 bindings=dict(author_hdf_ref=pin(S/'HDF.json'),author_mf_ref=h['manifest_ref'],author_builder_ref=h['builder_ref'],author_contract_ref=h['contract_ref'],author_input_manifest_ref=h['input_manifest_ref'])
 decision=save('decision.json',dict(schema='researchos.old21-independent-source-decision.v1',status='ACCEPTED_SOURCE_ONLY',verdict='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION',review_author=ACTOR,source_author=h['source_author'],root_thread_id=ROOT,reviewer_thread_id=os.environ['CODEX_THREAD_ID'],reviewed_utc=when,independent_non_author=True,**bindings,author_frozen_source_manifest_ref=h['frozen_source_manifest_ref'],finitechecks_ref=pin(D/'finitechecks.resolved.json'),original_finitechecks_ref=pin(D/'finitechecks.json'),Source_guard_ref=resolved['Source_guard_ref'],original_Source_guard_ref=original['Source_guard_ref'],actual_review_IO_index_ref=index,original_failures_ref=failure_ref,blocking_findings=[],original_1074_1075_preserved=True,original846_passes_reused_without_rerun=True,unchanged14098_resource_items_reused_from_exact_independent_review=True,actual_Source_author_peer_raw_ref=resolved['author_actual_peer_raw_ref'],actual_Source_author_peer_binding_ref=resolved['author_actual_peer_binding_ref'],actual_Source_author_peer_ordinal=62007,old21_Git_commit=c['source_commit'],old21_Git_tree=c['source_tree'],frozen_source_files=272,exact_runtime_source_inputs=24,numbered_SQL=list(range(1,22)),original_session_addon=True,dual_control_backup_Go_process_plan=9,Source_controls=dict(author_builder=75,author_causality=8,author_total=83,independent_effective_passed=checked,independent_unresolved=0),formal_programme_qualification=False,candidate_program_ref=None,qualification_ref=None,formal_acceptance=False,parent_acceptance=False,execution_grant=False,runtime_branch_called=False,Go_Native_product_SQL_subprocess_calls=0,Scope_qualification_Root_grant_created=False,current_build_complete_pair_required_at_entry=False,actual_offline_compiler_qualification='OPEN_ROOT_NEXT_STAGE',caller_integration_qualification='OPEN_FUTURE_CALLER_SOURCE_AND_ACTUAL_ROOT_GATE',contract_causal_rule='PRIOR_COMPLETED_ROOT_OBSERVATION_AT_ENTRY_THEN_EXTERNAL_ACTUAL_BUILD_PAIR_AFTER_RETURN',Root_required_next=['Actual Source review FINAL captured as three original Root records then real Root witness','Separate caller Source with actual owner/lease/current4 and matching nonauthor runtime resource qualification','Real old21 offline declared/export/build/inspect under Owned Job with exact input closure','Postreturn full actual Root call/output and independent candidate programme review'],all_Source_guards_closed=True,retained_handles_count=0,live_CP_OW_held=False,STOP=True))
 local=[pin(p) for p in sorted(D.iterdir()) if p.is_file() and p.name not in ('MF.json','HDF.json')]
 mf=save('MF.json',dict(schema='researchos.old21-independent-source-manifest.v1',review_author=ACTOR,source_author=h['source_author'],members=local,excluded=['HDF.json','MF.json','postpublication guard/interface proofs and actual seal output'],execution_grant=False,formal_acceptance=False))
 hr=save('HDF.json',dict(schema='researchos.old21-independent-source-handoff.v1',status='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION',review_author=ACTOR,source_author=h['source_author'],root_thread_id=ROOT,reviewer_thread_id=os.environ['CODEX_THREAD_ID'],independent_non_author=True,reviewed_utc=when,**bindings,decision_ref=decision,manifest_ref=mf,finitechecks_ref=pin(D/'finitechecks.resolved.json'),Source_guard_ref=resolved['Source_guard_ref'],actual_review_IO_index_ref=index,original_failures_ref=failure_ref,Source_controls_pass=checked,Source_controls_unresolved=0,Source_only=True,formal_programme_qualification=False,candidate_program_ref=None,qualification_ref=None,formal_acceptance=False,parent_acceptance=False,execution_grant=False,all_Source_guards_closed=True,retained_handles_count=0,actual_runtime_qualification_created=False,Go_Native_product_SQL_subprocess_calls=0,STOP=True))
 source_members=read(h['manifest_ref']['path'])['members'];refs=r.unique([hr,mf,decision,pin(S/'HDF.json'),h['manifest_ref'],*source_members,*local]);gm=module(c['source_guard_ref']['path'],'sealed_source_review_guard');guard=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 try:
  guard.acquire(refs);rh=read(hr['path']);rd=read(decision['path']);rm=read(mf['path'])
  assert rh['status']==rd['verdict']=='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION' and rh['review_author']==rd['review_author']==ACTOR and rh['source_author']==rd['source_author']==h['source_author'] and rd['independent_non_author'] is True
  assert rh['decision_ref']==decision and rh['manifest_ref']==mf and any(r.key(v)==r.key(decision) for v in rm['members'])
  for k,v in bindings.items():assert rh[k]==rd[k]==v
  assert h['manifest_ref']==bindings['author_mf_ref'] and h['builder_ref']==bindings['author_builder_ref'] and h['contract_ref']==bindings['author_contract_ref'] and h['input_manifest_ref']==bindings['author_input_manifest_ref']
  for k in ('builder_ref','contract_ref','input_manifest_ref'):assert any(r.key(h[k])==r.key(v) for v in source_members)
  assert c['builder_ref']==h['builder_ref'] and c['input_manifest_ref']==h['input_manifest_ref'] and c['schema_version']==21
  assert all(r.key(pin(v['path']))==r.key(v) for v in refs)
  assert all(rd[k] is False for k in ('formal_programme_qualification','formal_acceptance','parent_acceptance','execution_grant')) and rd['candidate_program_ref'] is None and rd['qualification_ref'] is None
 finally:closed=guard.close();gr=save('published-Source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
 contract_ref=save('published-builder-chain-check.json',dict(actual_published_HDF_MF_decision_bindings_checked=True,M4_builder_chain_field_contract_compatible=True,schema21_future_caller_gate_not_yet_implemented=True,review_refs=[hr,mf,decision],Source_guard_ref=gr,retained_handles_count=0,qualification_or_Root_witness_not_synthesized=True,execution_grant=False,formal_acceptance=False))
 seal=save('complete-independent-Source-review-seal.json',dict(status='ACCEPTED_SOURCE_ONLY',review_refs=[hr,mf,decision],published_contract_check_ref=contract_ref,Source_guard_ref=gr,actual_review_IO_index_ref=index,original_failures_ref=failure_ref,effective_checks=checked,all_Source_guards_closed=True,retained_handles_count=0,Root_witness_grant=False,actual_programme_qualification=False,execution_grant=False,formal_acceptance=False,STOP=True))
 print(json.dumps(dict(status='ACCEPTED_SOURCE_ONLY',review_refs=[hr,mf,decision],original_failures_ref=failure_ref,seal_ref=seal,published_contract_check_ref=contract_ref,guard_ref=gr,checks=checked,retained_handles_count=0,STOP=True),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
