"""Read-only actual CP370 audit. Historical logical Canon refs use real archive attribution.
No Source loader is monkeypatched; no registrar entrypoint or canonical transaction runs.
"""
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import types

N=Path(__file__).resolve().parent;W=N.parent.parent
S=W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v4'
ROOTDIR=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
PREV=W/'cp370_root_facts_independent_review_codex/factsr4-01a120ab'
MAINREVIEW=W/'formal_profile_v4_actual_adoption_independent_review_codex/actualr-01a12072'
checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,x):
 with (N/name).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def mod(p):
 m=types.ModuleType('actualreview_'+Path(p).stem);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def record(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:raise AssertionError(name)
def rawrefs(value):
 if type(value) is dict:
  if set(value)=={'path','sha256','bytes'}:yield value
  else:
   for v in value.values():yield from rawrefs(v)
 elif type(value) is list:
  for v in value:yield from rawrefs(v)
def capture(audit,start,chunk,name):
 audit=Path(audit);limit=audit.stat().st_size;calls={};found=[]
 with audit.open('rb') as file:
  header=file.readline();file.seek(start);offset=start
  while offset<limit:
   line=file.readline();item=json.loads(line);payload=item.get('payload',{})
   if item.get('type')=='response_item' and payload.get('type')=='custom_tool_call':calls[payload['call_id']]=(offset,line,item)
   if item.get('type')=='response_item' and payload.get('type')=='custom_tool_call_output' and isinstance(payload.get('output'),list):
    for block in payload['output']:
     try:value=json.loads(block.get('text',''))
     except (ValueError,TypeError,AttributeError):continue
     if isinstance(value,dict) and value.get('chunk_id')==chunk:
      call=calls[payload['call_id']];rows=[(0,header),(call[0],call[1]),(offset,line)]
      found.append((call[2],item,value,rows))
   offset+=len(line)
 record('unique actual audit chunk '+chunk,len(found)==1)
 call,out,result,rows=found[0]
 with (N/(name+'.actual-host.raw.jsonl')).open('xb') as file:file.write(b''.join(r[1] for r in rows))
 cap=pin(N/(name+'.actual-host.raw.jsonl'))
 br=save(name+'.actual-host.binding.json',dict(source_audit_path=str(audit),source_prefix_size_observed=limit,source_line_offsets=[r[0] for r in rows],source_line_bytes=[len(r[1]) for r in rows],original_line_sha256=[hashlib.sha256(r[1]).hexdigest() for r in rows],actual_capture_ref=cap,original_call_id=call['payload']['call_id'],tool_call_timestamp=call['timestamp'],tool_result_timestamp=out['timestamp'],chunk_id=chunk))
 return dict(call=call,output=out,result=result,rows=rows,audit=audit,cap_ref=cap,binding_ref=br)

def main():
 ar=pin(S/'registration.activate.root.json');fr=pin(ROOTDIR/'postseal-live-context.live1005.root.json')
 record('actual activation handed ref',(ar['sha256'],ar['bytes'])==('4a41818929e31b7c194c42a9b54a84980bbb2d7f92882946d501162406d642a1',1594))
 record('actual fresh context handed ref',(fr['sha256'],fr['bytes'])==('5669b965da9c4072b8a719a67dace76df3f19a9a025757a020ead27ed4801a64',21181))
 actual=read(ar['path']);fresh=read(fr['path']);h=read(S/'HDF.json');mf=read(h['manifest_ref']['path']);m=mod(h['registrar_ref']['path'])
 fref=pin(S/'registration-facts.root.json');facts=read(fref['path']);request=read(facts['build_request_ref']['path']);seed=read(facts['live_ref']['path']);scope=read(facts['scope_ref']['path']);owner=read(facts['owner_document_ref']['path']);worker=read(facts['worker_document_ref']['path'])
 witness=read(fresh['activation_witness_ref']['path']);q=read(fresh['qualification_ref']['path']);sbw=read(seed['seed_witness_ref']['path']);sq=read(seed['qualification_ref']['path']);binding=read(witness['capture_binding_ref']['path']);bio=read(ROOTDIR/'registrar-v4-activate.actual.original-tool-io.root.json')
 j=Path(actual['transaction']['transaction_journal']);ir=pin(j/'intent.json');cr=pin(j/'committed.json');intent=read(ir['path']);commit=read(cr['path'])
 oldlogical=facts['before_canonical_refs'];archives=request['historical_cp369_archives'];archive_map={r['path'].casefold():(r,a) for r,a in zip(oldlogical,archives)}
 attribution=[]
 for logical,archive in zip(oldlogical,archives):
  record('genuine CP369 archive bytes '+Path(archive['path']).name,pin(archive['path'])==archive and (archive['sha256'],archive['bytes'])==(logical['sha256'],logical['bytes']))
  attribution.append(dict(historical_logical_ref=logical,physical_archived_ref=archive,current_canonical_claim=False))
 current=[pin(p) for p in m.CANON];current_cp,current_ow=read(current[0]['path']),read(current[1]['path']);oldcp,oldow=read(archives[0]['path']),read(archives[1]['path'])
 record('current CP370 exact after ref',(current[0]['sha256'],current[0]['bytes'])==('a5429468aefaa383f587e699d90744d437d6e0b4ef70d0df656519a1aa2ec994',4489310) and current_cp['revision']==370)
 record('current OW174 exact after ref',(current[1]['sha256'],current[1]['bytes'])==('a612b51f23a5157aff5b99817caa09fb634a67c70879c56430daa4690d1da0bc',208629) and current_ow['revision']==174)
 record('SS and commands39 unchanged',current[2:]==oldlogical[2:] and read(current[3]['path'])['revision']==39)
 priorh=read(PREV/'HDF.json');priord=read(priorh['source_decision_ref']['path']);mainh=read(MAINREVIEW/'HDF.json')
 guard_ref=pin(S/'source-guard.cleanup.activate.root.json');rootguard=read(guard_ref['path'])
 nativeh=read(request['native_hdf_ref']['path']);nativehandoff=read(request['native_handoff_ref']['path'])
 sourcecallerh=read(facts['source_hdf_ref']['path']);sourcecallerm=read(facts['source_mf_ref']['path']);callerreviewh=read(facts['source_review_hdf_ref']['path']);callerreviewm=read(facts['source_review_mf_ref']['path'])
 # A fresh Root host event followed the actual receipt publication, not just its declared timestamp.
 own_audit=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
 sealcap=capture(own_audit,0,'5b858f','facts-review-seal')
 actcap=capture(binding['source_audit_path'],binding['source_line_offsets'][1],'920580','activation')
 refs=[ar,fr,fref,pin(__file__),pin(S/'HDF.json'),h['manifest_ref'],*mf['members'],ir,cr,guard_ref,pin(PREV/'HDF.json'),priorh['manifest_ref'],priorh['source_decision_ref'],pin(MAINREVIEW/'HDF.json'),mainh['manifest_ref'],mainh['actual_decision_ref'],*mainh['Main_after_refs'],pin(ROOTDIR/'registrar-v4-activate.actual.original-tool-io.root.json')]
 for value in (facts,request,seed,fresh,scope,owner,worker,q,sq,witness,sbw,binding,intent,commit,nativeh,nativehandoff,sourcecallerh,sourcecallerm,callerreviewh,callerreviewm):refs.extend(rawrefs(value))
 for cap in (sealcap,actcap):refs.extend((cap['cap_ref'],cap['binding_ref']))
 refs.extend({k:e[k] for k in ('path','sha256','bytes')} for e in rootguard['entries'])
 # Resolve only known historical logical refs to their exact physical archive. Current refs
 # are held separately. Never feed an old logical ref as a claim about a current Canon file.
 resolved=[]
 for ref in refs:
  known=archive_map.get(ref['path'].casefold())
  if known and ref==known[0]:resolved.append(known[1])
  else:resolved.append(ref)
 resolved.extend(current)
 guard,count=m.held_guard(resolved,False)
 try:
  record('TP exact before expected vector',intent['expected_refs']==oldlogical[:2] and intent['mandatory_share_mode']==0 and intent['automatic_inverse'] is False)
  for index in range(2):
   record('TP before equals independent actual archive '+str(index),Path(intent['before_refs'][index]['path']).read_bytes()==Path(archives[index]['path']).read_bytes())
   record('TP proposed after equals current bytes '+str(index),Path(intent['after_refs'][index]['path']).read_bytes()==Path(current[index]['path']).read_bytes())
  record('TP committed both under exclusive held ownership',commit['after_refs']==current[:2] and commit['written_indices']==[0,1] and commit['both_verified_while_exclusively_held'] is True)
  record('actual result and transaction after refs coincide',actual['proposed_after_refs']==current[:2] and actual['transaction']['checkpoint_ref']==current[0] and actual['transaction']['ownership_ref']==current[1])
  record('TP no failed partial journal',(j/'failed.partial.json').exists() is False)
  # Unmodified read validators accept the real sealed receipts even after Canon advanced.
  seed_qualified=m.validate_live(seed);fresh_qualified=m.validate_live(fresh,'activation')
  m.validate_activation_context(fresh,seed,facts)
  record('actual postseal Source validator gate accepted without Canon remapping',True,'No source loader was changed; no check_before_pair/build/register/main/update_pair invoked.')
  record('independent facts decision exact root facts seed pins',priord['root_facts_ref']==fref and priord['root_seed_live_ref']==facts['live_ref'] and priord['source_hdf_ref']==pin(S/'HDF.json') and priord['registrar_ref']==h['registrar_ref'])
  record('postseal exactly bound independent facts review triple',witness['registrar_review_refs']==[pin(PREV/'HDF.json'),priorh['manifest_ref'],priorh['source_decision_ref']])
  seal_lines=sealcap['result']['output'].splitlines();published=json.loads(seal_lines[0])
  record('facts seal actual host publication returned exact three refs',published['HDF']==pin(PREV/'HDF.json') and published['MF']==priorh['manifest_ref'] and published['decision']==priorh['source_decision_ref'] and seal_lines[-1]=='ROOT_SOURCE_PYTHON_EXIT=0')
  record('new physical Root postseal call after actual review publication',m.utc(binding['tool_call_timestamp'])>m.utc(sealcap['output']['timestamp']) and m.utc(binding['tool_result_timestamp'])>m.utc(sealcap['output']['timestamp']))
  record('new postseal call differs from seed',binding['original_call_id']!=read(sbw['capture_binding_ref']['path'])['original_call_id'] and witness['actual_host_capture_ref']!=sbw['actual_host_capture_ref'])
  record('actual activation later than new observation context',m.utc(actcap['call']['timestamp'])>m.utc(fresh['created_utc']))
  record('actual activation host exact saved IO',m.extract_original_result_block(actcap['output']['payload']['output'])==bio['result'] and bio['result']==actcap['result'] and bio['actual_outer_exit']==bio['actual_python_exit']==0)
  record('actual activation command exact mode facts fresh pins',json.dumps(bio['args']['cmd'],ensure_ascii=False)[1:-1] in actcap['call']['payload']['input'] and "'"+h['registrar_ref']['path']+"' activate" in bio['args']['cmd'] and fref['sha256']+' '+str(fref['bytes']) in bio['args']['cmd'] and fr['sha256']+' '+str(fr['bytes']) in bio['args']['cmd'])
  lines=bio['result']['output'].splitlines();record('actual activation returned exact result ref',len(lines)==2 and json.loads(lines[0])==ar and lines[1]=='ROOT_SOURCE_PYTHON_EXIT=0')
  record('activation observed Native dispatcher model unknown NULL',all(bio[k] is None for k in ('actual_native_exit','actual_dispatcher_exit','actual_model_exit')))
  record('actual250reader cleanup closed zero',len(rootguard['entries'])==actual['source_guard_ref_count']==250 and rootguard['verification']=='PASSED' and rootguard['closed'] is True and rootguard['retained_handles_count']==0 and rootguard['errors']==[])
  rootpaths={r['path'].casefold() for r in rootguard['entries']}
  record('actual activation guard pair excluded others held',all(r['path'].casefold() not in rootpaths for r in current[:2]) and all(r['path'].casefold() in rootpaths for r in (current[2],current[3],fref,fr,facts['scope_ref'],facts['owner_document_ref'],facts['worker_document_ref'],fresh['qualification_ref'],fresh['activation_witness_ref'])))
  caller=m.ensure_caller_source(facts['source_hdf_ref'],facts['source_mf_ref']);rh,rm,rd,decision=m.validate_review(request,caller)
  cm=mod(caller[2]['path']);cm.validate_scope(scope);cm.validate_source_review(decision,scope,*caller)
  cm.validate_canon_lease(current_cp,current_ow,scope,facts['scope_ref'],caller[0],rd,facts['owner_document_ref'],facts['worker_document_ref'],owner,worker,Path(scope['authorized_output_root'])/'independent-actual-lease-check')
  record('actual Caller6 exact scope unique OwnerWorker active lease',len([r for r in current_cp['workers'] if r.get('slice_id')==m.SLICE])==1)
  # Pure transformation of genuine archive objects is a byte comparison, not a Source run.
  generated=m.transformed_pair(copy.deepcopy(oldcp),copy.deepcopy(oldow),facts,fresh,oldcp,oldow,fref)
  record('pure archived before transform matches exact current pair',all(m.encoded(v)==Path(ref['path']).read_bytes() for v,ref in zip(generated,current[:2])))
  record('old963failure prefix all previous workers unchanged',current_cp['failure_counters'][:963]==oldcp['failure_counters'] and current_cp['workers'][:-1]==oldcp['workers'])
  added=current_cp['failure_counters'][963:]
  record('exact39appended ordinals966through1004',len(added)==39 and [r['original_payload']['observed_ordinal'] for r in added]==list(range(966,1005)))
  for row in added:
   payload=row['original_payload'];qual=fresh_qualified[payload['observed_ordinal']]
   record('actual qualified invocation '+str(payload['observed_ordinal']),payload['immutable_origin_ref']==qual['origin_ref'] and payload['origin_selector']==qual['origin_selector'] and payload['exit_qualification']==qual['exit_qualification'] and payload['capture_completeness']==qual['capture_completeness'] and all(type(payload[k]) is type(qual[k]) and payload[k]==qual[k] for k in ('actual_outer_exit','actual_python_exit','actual_native_exit','actual_dispatcher_exit','actual_model_exit')) and row['counted_once'] is True and row['counter_reset'] is False and row['automatic_retry'] is False)
  record('registered original1004 remains failure 1 with unknown consumers',added[-1]['original_payload']['actual_outer_exit']==1 and added[-1]['original_payload']['actual_python_exit']==1 and all(added[-1]['original_payload'][k] is None for k in ('actual_native_exit','actual_dispatcher_exit','actual_model_exit')))
  record('first38 immutable original qualifiers preserved',len(seed_qualified)==38 and all({k:v for k,v in fresh_qualified[n].items() if k!='exit_qualification'}=={k:v for k,v in seed_qualified[n].items() if k!='exit_qualification'} for n in seed_qualified))
  invcp=copy.deepcopy(current_cp)
  for key in ('failure_counters','workers','work_in_progress','revision','expected_previous_revision','updated_at','updated_by','note'):invcp[key]=copy.deepcopy(oldcp[key])
  invow=copy.deepcopy(current_ow);del invow['card_path_bindings']['W09-99']['subtasks'][m.KEY]
  for key in ('revision','updated_at','updated_by'):invow[key]=copy.deepcopy(oldow[key])
  record('independent whole byte inverse equals actual CP369 OW173 archives',m.encoded(invcp)==Path(archives[0]['path']).read_bytes() and m.encoded(invow)==Path(archives[1]['path']).read_bytes())
  record('CP369 four pending rows retained',current_cp['work_in_progress']['later_diagnostics_observed_after_cutoff'][:4]==oldcp['work_in_progress']['later_diagnostics_observed_after_cutoff'])
  record('next original1005 remains unreset',current_cp['work_in_progress']['root_next_failure_ordinal_live']==1005 and fresh['next_original_failure_ordinal']==1005)
  for ref in mainh['Main_after_refs']:record('accepted MainProfile bytes retained '+Path(ref['path']).name,pin(ref['path'])==ref)
  for ref in caller:record('accepted Caller6 bytes retained '+Path(ref['path']).name,pin(ref['path'])==ref)
  for key in ('native_hdf_ref','native_handoff_ref','native_historical_request_ref'):record('accepted Native bounded receipt retained '+key,pin(request[key]['path'])==request[key])
  record('zero formal parent or dispatcher actual claim',actual['formal_acceptance'] is False and actual['parent_acceptance'] is False and actual['formal_case_accepted_delta']==0 and actual['Native_rerun'] is False and actual['dispatcher_run'] is False and scope['formal_acceptance'] is False)
  for ref in resolved:record('final actual or archive pin '+Path(ref['path']).name,pin(ref['path'])==ref)
  for cap in (sealcap,actcap):
   with cap['audit'].open('rb') as file:
    for offset,raw in cap['rows']:file.seek(offset);record('final actual audit immutable range',file.read(len(raw))==raw)
  record('current four Canon unchanged during independent review',[pin(p) for p in m.CANON]==current)
 finally:
  cleanup=guard.close();gr=save('sourceguard.closed.json',cleanup)
 record('independent actual review reader closed zero',cleanup['closed'] and cleanup['retained_handles_count']==0 and cleanup['errors']==[])
 amap=save('historical-canonical-attribution.json',dict(attribution=attribution,only_physical_archives_read_for_historical_bytes=True,Source_pin_functions_monkeypatched=False))
 controls=save('actual-checks.json',dict(checks=checks,count=len(checks),guard_refs=count,registrar_entrypoints_or_TP_executed=False,Native_or_dispatcher_executed=False))
 decision=dict(schema='researchos.cp370-independent-actual-registration-decision.v1',decision='ACTUAL_REGISTRATION_VERIFIED_NONFORMAL',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',reviewed_at=datetime.now(timezone.utc).isoformat(),source_hdf_ref=pin(S/'HDF.json'),source_mf_ref=h['manifest_ref'],registrar_ref=h['registrar_ref'],root_contract_ref=h['root_contract_ref'],root_facts_ref=fref,root_seed_live_ref=facts['live_ref'],root_fresh_live_ref=fr,actual_registration_result_ref=ar,current_canonical_refs=current,transaction_intent_ref=ir,transaction_commit_ref=cr,source_guard_ref=gr,checks_ref=controls,historical_attribution_ref=amap,actual_registration_verified=True,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,Native_rerun=False,dispatcher_executed=False,Main_or_Canon_written_by_reviewer=False,new_original_failures=[],Root_next_original=1005)
 dr=save('actual-decision.json',decision)
 om=save('MF.json',dict(schema='researchos.cp370-independent-actual-registration-manifest.v1',members=[pin(__file__),controls,gr,amap,dr,*[cap[k] for cap in (sealcap,actcap) for k in ('cap_ref','binding_ref')]],current_canonical_refs=current,root_facts_ref=fref,actual_registration_result_ref=ar))
 oh=save('HDF.json',dict(schema='researchos.cp370-independent-actual-registration-handoff.v1',decision=decision['decision'],actor_id=decision['actor_id'],actor_role=decision['actor_role'],manifest_ref=om,actual_decision_ref=dr,current_canonical_refs=current,root_facts_ref=fref,root_fresh_live_ref=fr,actual_registration_result_ref=ar,guard_ref_count=count,guard_closed=True,retained_handles_count=0,checks=len(checks),formal_acceptance=False,parent_acceptance=False,Native_rerun=False,dispatcher_executed=False,Main_or_Canon_written_by_reviewer=False,STOP=True,FINAL=True))
 for ref in (oh,om,dr,*resolved):assert pin(ref['path'])==ref
 print(json.dumps(dict(HDF=oh,MF=om,decision=dr,checks=len(checks),guard_refs=count),ensure_ascii=False))

if __name__=='__main__':main()
