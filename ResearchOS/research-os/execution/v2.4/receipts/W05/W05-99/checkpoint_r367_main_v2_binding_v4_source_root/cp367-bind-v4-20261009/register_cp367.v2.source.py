import sys
sys.dont_write_bytecode=True
import copy,hashlib,json,types
from datetime import datetime,timezone
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
N=Path(__file__).resolve().parent
CANON=[R/'execution/v2.4'/(x+'.json') for x in ('checkpoint','path_ownership','step_state','commands')]
BEFORE=[('9628b913e83364f629a38e8cc6dce8c5ebedb8566fa7e5ce43a6b0e624ccde21',4302132),('662ec1f0143b378f7888fb8b7eb4d7c814d6e61a439b55be1db56984935d7166',196505),('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),('b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129',68156)]
GP=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
IDENTITY=R/'execution/project_identity.json'
TARGETS=[str((R/x).resolve()) for x in ('internal/domain/domain_test.go','internal/domain/retrieval_test.go','ops/ci/retrieval.py','internal/domain/w09_evidence_export_test.go','ops/ci/w09_formal_router.py','ops/ci/w09_evidence_closure.py','execution/v2.4/commands.json')]
KEY='c19_main_source_registry_adoption'
SLICE='C19_MAIN_SOURCE_REGISTRY_ADOPTION'
def require(v,label):
 if not v:raise ValueError(label)
def pin(p):
 p=Path(p).resolve(strict=True);raw=p.read_bytes()
 require(len(raw)<=256*1024*1024,'PIN_SIZE')
 return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(ref):
 require(isinstance(ref,dict) and set(ref)=={'path','sha256','bytes'},'EXACT_TYPED_REF')
 require(type(ref['bytes']) is int and 0<=ref['bytes']<=256*1024*1024,'TYPED_BYTES')
 require(Path(ref['path']).is_absolute() and str(Path(ref['path']).resolve(strict=True))==ref['path'],'CANONICAL_ABSOLUTE_REF')
 require(pin(ref['path'])==ref,'EXACT_PIN')
 return Path(ref['path']).read_bytes()
def load(ref):return json.loads(read(ref))
def save(name,value):
 with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return pin(N/name)
def module(path,raw):
 m=types.ModuleType('cp367_'+path.stem);m.__file__=str(path);sys.modules[m.__name__]=m
 exec(compile(raw,str(path),'exec'),m.__dict__);return m
def facts_scope(facts):
 scope=load(facts['scope_ref']);contract=load(facts['calling_contract_ref'])
 require(set(scope)==set(contract['scope_required_fields']),'EXACT_SCOPE_KEYS')
 require(scope['schema']==contract['root_scope_schema'] and scope['status']==contract['root_scope_status'],'EXACT_SCOPE_SCHEMA_STATUS')
 require(scope['issued_by']==scope['executor']=='codex:/root','ROOT_ACTOR')
 require(scope['exact_targets']==contract['exact_targets']==TARGETS,'EXACT_SEVEN_TARGETS')
 require(scope['caller_ref']==contract['caller_ref'] and scope['change_set_ref']==contract['change_set_ref'],'CONTRACT_CALLER_CHANGESET')
 require(scope['journal_root']==contract['runtime_journal_root'],'FIXED_JOURNAL')
 for key in ('formal_dispatcher','formal_acceptance','producer_rerun','copy_native_packet','checkpoint_write','ownership_write','step_state_write'):
  require(scope[key] is False,'SCOPE_NO_'+key)
 require(type(scope['formal_case_accepted_delta']) is int and scope['formal_case_accepted_delta']==0 and type(scope['new_Go_SQL_API_model_calls']) is int and scope['new_Go_SQL_API_model_calls']==0,'SCOPE_ZERO_CALLS_FORMAL')
 reviews=facts['reviews']
 for a,b in (('source_handoff_ref','source_manifest_ref'),('source_review_handoff_ref','source_review_manifest_ref'),('component_review_handoff_ref','component_review_manifest_ref')):
  require(any(item['handoff_ref']==scope[a] and item['manifest_ref']==scope[b] for item in reviews),'FULL_REVIEW_PAIR_'+a)
 source=load(scope['source_handoff_ref'])
 require(source['manifest_ref']==scope['source_manifest_ref'],'SOURCE_MANIFEST_BINDING')
 source_members=load(scope['source_manifest_ref'])['members'];source_members=list(source_members.values()) if isinstance(source_members,dict) else source_members
 require(facts['calling_contract_ref'] in source_members,'CONTRACT_IS_SOURCE_MF_MEMBER')
 decision=load(scope['source_review_decision_ref']);review=load(scope['source_review_handoff_ref'])
 require(decision['schema']==contract['source_review_decision_schema'] and decision['decision']==contract['source_review_decision_value'],'REAL_SOURCE_ACCEPTED_DECISION')
 require(decision['actor_role']=='INDEPENDENT_NON_AUTHOR' and decision['actor_id'] not in ('codex:/root','codex:/root/command_queue_impl'),'SOURCE_NONAUTHOR')
 require(review['actor_id']==decision['actor_id'] and review['manifest_ref']==scope['source_review_manifest_ref'] and review['source_decision_ref']==scope['source_review_decision_ref'],'REVIEW_DECISION_MANIFEST_BINDING')
 for field in ('source_handoff_ref','source_manifest_ref','caller_ref','change_set_ref','exact_targets'):
  require(decision[field]==scope[field],'SOURCE_DECISION_FULL_BINDING_'+field)
 require(type(decision['formal_case_accepted_delta']) is int and decision['formal_case_accepted_delta']==0 and decision['actual_adoption_executed'] is False,'SOURCE_DECISION_NOT_ACTUAL_FORMAL')
 members=load(scope['source_review_manifest_ref'])['members'];members=list(members.values()) if isinstance(members,dict) else members
 require(scope['source_review_decision_ref'] in members,'DECISION_IS_MF_MEMBER')
 component=load(scope['component_review_handoff_ref'])
 require(scope['component_review_handoff_ref']==contract['component_review_handoff_ref'] and scope['component_review_manifest_ref']==contract['component_review_manifest_ref'],'FIXED_COMPONENT_REVIEW_PAIR')
 require(component['schema']==contract['component_actual_schema'] and component['decision']==contract['component_actual_decision'],'ACTUAL_COMPONENT_INDEPENDENT_PASS')
 require(component['consumer_closed_ref']==scope['consumer_closed_ref']==contract['original_consumer_closed_ref'],'ACTUAL_COMPONENT_CLOSED_BINDING')
 require(component['all_owned_jobs_closed'] is True and component['all_guards_closed'] is True and component['all_held_inputs_unchanged'] is True and component['formal_case_accepted_delta']==0 and component['Main_adopted'] is False,'ACTUAL_COMPONENT_BOUNDARY')
 bindings={'EXACT_ROOT_REGISTRATION_SCOPE_REF':facts['scope_ref'],'EXACT_ORDERED_SEVEN_ABSOLUTE_TARGETS':TARGETS,'THIS_SOURCE_HDF_REF':scope['source_handoff_ref'],'THIS_SOURCE_MF_REF':scope['source_manifest_ref'],'FUTURE_SOURCE_INDEPENDENT_HDF_REF':scope['source_review_handoff_ref'],'FUTURE_SOURCE_INDEPENDENT_MF_REF':scope['source_review_manifest_ref']}
 def resolve(value):return copy.deepcopy(bindings.get(value,value)) if isinstance(value,str) else copy.deepcopy(value)
 owner={k:resolve(v) for k,v in contract['owner_exact_field_bindings'].items()}
 worker={k:resolve(v) for k,v in contract['checkpoint_worker_exact_field_bindings'].items()}
 require(set(owner)=={'owner','current_source_writer','scope_ref','exact_targets','state','source_handoff_ref','source_manifest_ref','source_review_handoff_ref','source_review_manifest_ref','component_review_handoff_ref','component_review_manifest_ref','journal_root','formal_case_accepted_delta','formal_dispatcher','parent_acceptance'},'EXACT_OWNER_KEYS')
 require(set(worker)=={'step_id','slice_id','owner','state','scope_ref','exact_targets','source_review_handoff_ref','component_review_handoff_ref'},'EXACT_WORKER_KEYS')
 require(owner['state']==worker['state']=='ROOT_REGISTERED_PENDING_SOURCE_ADOPTION' and owner['scope_ref']==worker['scope_ref']==facts['scope_ref'],'OWNER_WORKER_SCOPE_STATE')
 require(owner['owner']=='codex:/root' and owner['current_source_writer'] is None and owner['exact_targets']==TARGETS and owner['formal_case_accepted_delta']==0 and owner['formal_dispatcher'] is False and owner['parent_acceptance'] is False,'OWNER_BOUNDARY')
 require(worker['owner']=='codex:/root' and worker['step_id']=='W09-99' and worker['slice_id']==SLICE and worker['exact_targets']==TARGETS,'WORKER_BOUNDARY')
 return scope,owner,worker
def validate_live_context(live,facts):
 require(isinstance(live,dict) and set(live)=={'schema','issued_by','created_utc','source_cutoff','next_original_failure_ordinal','pending'},'EXACT_LIVE_CONTEXT_KEYS')
 require(live['schema']=='researchos.root-postseal-live-diagnostic-context.v1' and live['issued_by']=='codex:/root' and isinstance(live['created_utc'],str) and live['created_utc'],'ROOT_LIVE_CONTEXT')
 require(live['source_cutoff']=={'highest_ordinal':facts['highest_observed_ordinal'],'next_failure_ordinal':facts['next_failure_ordinal']},'EXACT_SOURCE_CUTOFF')
 next_live=live['next_original_failure_ordinal'];require(type(next_live) is int and next_live>=facts['next_failure_ordinal'],'NO_LIVE_RESET_TO_CUTOFF')
 pending=live['pending'];require(isinstance(pending,list) and all(isinstance(x,dict) and set(x)=={'ordinal','origin_ref','description'} and type(x['ordinal']) is int and isinstance(x['description'],str) for x in pending),'EXACT_PENDING_CONTEXT_ROWS')
 require([x['ordinal'] for x in pending]==list(range(facts['next_failure_ordinal'],next_live)),'ALL_POST_CUTOFF_ORIGINALS_EXACT_ONCE')
 for item in pending:read(item['origin_ref'])
 return live

def transform(c,o,facts,fr,old_c,old_o,owner,worker,stamp,live_context):
 validate_live_context(live_context,facts)
 require(c==old_c and o==old_o and c['revision']==366 and o['revision']==170,'EXACT_BEFORE')
 require(len(c['failure_counters'])==934,'OLD934')
 require(c['work_in_progress']['construction_active_parents']==['W05','W09'],'TWO_PARENTS')
 require(c['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and c['head']=='adc460c2138528f163f7fdab5e8d81dde157b7fb','PROJECT_HEAD')
 require(o['active_integrator']['id']=='codex:/root' and o['shared_integrator']=='qoder-desktop:/root/platform_owner' and o['card_path_bindings']['W09-99']['owner']=='codex:/root','REAL_OWNERSHIP_STRUCTURE')
 require(KEY not in o['card_path_bindings']['W09-99']['subtasks'] and not any(x.get('slice_id')==SLICE for x in c['workers']),'NEW_UNIQUE_SUBTASK_WORKER')
 pending=facts['diagnostics'];require([v['ordinal'] for v in pending]==list(range(937,facts['highest_observed_ordinal']+1)),'EXACT_ORDINAL_CUTOFF')
 require(facts['next_failure_ordinal']==facts['highest_observed_ordinal']+1 and facts['registered_after']==934+len(pending),'COUNTS')
 seen={v.get('origin_key') for v in c['failure_counters']}
 for item in pending:
  ref=item['origin_ref'];read(ref);ordinal=item['ordinal'];key=hashlib.sha256((ref['sha256']+'#'+str(ordinal)).encode()).hexdigest()
  require(key not in seen,'UNIQUE_ORIGINAL_KEY');seen.add(key)
  c['failure_counters'].append({'origin_key':key,'evidence_ref':ref,'original_payload':{'observed_ordinal':ordinal,'immutable_origin_ref':ref,'actual_outer_exit':item['actual_outer_exit'],'actual_python_exit':item['actual_python_exit'],'actual_native_exit':item['actual_native_exit'],'diagnostic':item['description'],'origin_selector':item['origin_selector'],'exit_qualification':item['exit_qualification']},'counted_once':True,'counter_reset':False,'automatic_retry':False})
 require(c['failure_counters'][:934]==old_c['failure_counters'],'OLD_COUNTERS_UNCHANGED')
 c['workers'].append(copy.deepcopy(worker));o['card_path_bindings']['W09-99']['subtasks'][KEY]=copy.deepcopy(owner)
 wip=c['work_in_progress'];require('mu_sdk_r367' not in wip,'NEW_WIP')
 wip['mu_sdk_r367']=copy.deepcopy(facts['work_in_progress'])
 wip.update(r367_registered_failure_count=len(c['failure_counters']),r367_highest_observed_diagnostic_ordinal_at_cutoff=facts['highest_observed_ordinal'],r367_next_failure_ordinal_at_cutoff=facts['next_failure_ordinal'],mu_sdk_r367_facts_ref=fr,later_diagnostics_observed_after_cutoff=copy.deepcopy(live_context['pending']),root_next_failure_ordinal_live=live_context['next_original_failure_ordinal'])
 c.update(expected_previous_revision=366,revision=367,updated_at=stamp,updated_by='codex:/root',note=facts['checkpoint_note'])
 o.update(revision=171,updated_at=stamp,updated_by='codex:/root')
 inverse_c=copy.deepcopy(c);inverse_c['failure_counters']=copy.deepcopy(old_c['failure_counters']);inverse_c['workers']=copy.deepcopy(old_c['workers']);inverse_c['work_in_progress']=copy.deepcopy(old_c['work_in_progress'])
 for k in ('expected_previous_revision','revision','updated_at','updated_by','note'):inverse_c[k]=old_c[k]
 inverse_o=copy.deepcopy(o);del inverse_o['card_path_bindings']['W09-99']['subtasks'][KEY]
 for k in ('revision','updated_at','updated_by'):inverse_o[k]=old_o[k]
 require(inverse_c==old_c and inverse_o==old_o,'COMPLETE_CANONICAL_INVERSE')
 return c,o
def main():
 require(len(sys.argv)==6,'FACTS_SHA FACTS_BYTES LIVE_CONTEXT_ABSOLUTE_PATH LIVE_CONTEXT_SHA LIVE_CONTEXT_BYTES')
 fr={'path':str((N/'checkpoint.execution.facts.json').resolve(strict=True)),'sha256':sys.argv[1],'bytes':int(sys.argv[2])}
 facts=load(fr);require(facts['schema']=='researchos.root-cp367-main-c19-registration-facts.v1' and facts['formal_acceptance'] is False,'FACTS_SCHEMA')
 live_context_ref={'path':sys.argv[3],'sha256':sys.argv[4],'bytes':int(sys.argv[5])};live_context=load(live_context_ref)
 require(Path(live_context_ref['path']).is_relative_to(R/'execution/v2.4/receipts'),'ROOT_RECEIPT_LIVE_CONTEXT_BOUNDARY');validate_live_context(live_context,facts)
 refs_c=[{'path':str(p.resolve()),'sha256':sha,'bytes':size} for p,(sha,size) in zip(CANON,BEFORE)]
 require(facts['canonical_refs']==refs_c,'EXACT_FOUR_BEFORE')
 raw=[read(ref) for ref in refs_c];old_c,old_o=[json.loads(s) for s in raw[:2]]
 gp={'path':str(GP.resolve()),'sha256':'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85','bytes':11404}
 tp={'path':str(TP.resolve()),'sha256':'094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9','bytes':6877}
 require(pin(IDENTITY)['sha256']=='03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec' and pin(IDENTITY)['bytes']==420,'IDENTITY')
 require(pin(sys.executable)['sha256']=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b','PYTHON')
 gm=module(GP,read(gp));tm=module(TP,read(tp))
 refs=[fr,pin(__file__),pin(sys.executable),pin(IDENTITY),gp,tp,*refs_c[2:],facts['scope_ref'],facts['calling_contract_ref']]
 for item in facts['reviews']:
  refs.extend([item['handoff_ref'],item['manifest_ref']]);members=load(item['manifest_ref'])['members'];members=list(members.values()) if isinstance(members,dict) else members
  for member in members:refs.append({'path':str(Path(member['path']).resolve(strict=True)),'sha256':member['sha256'].removeprefix('sha256:'),'bytes':member['bytes']})
 refs.extend(item['origin_ref'] for item in facts['diagnostics']);refs.extend(facts['actual_refs']);refs.append(live_context_ref);refs.extend(item['origin_ref'] for item in live_context['pending'])
 for mod in list(sys.modules.values()):
  for field in ('__file__','__cached__'):
   path=getattr(mod,field,None)
   if path and Path(path).is_file():refs.append(pin(path))
 unique={};planned={str(p.resolve()).casefold() for p in CANON[:2]}
 for ref in refs:
  read(ref);key=ref['path'].casefold()
  if key in planned:continue
  require(key not in unique or unique[key]==ref,'UNIQUE_SAME_PIN');unique[key]=ref
 guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(unique.values()))
 try:
  require(guard.get_buffer(fr['path'])==read(fr),'HELD_FACTS')
  scope,owner,worker=facts_scope(facts)
  transaction=tm.update_pair(refs_c[:2],lambda c,o:transform(c,o,facts,fr,old_c,old_o,owner,worker,datetime.now(timezone.utc).isoformat(),live_context),N,'register')
  require([p.read_bytes() for p in CANON[2:]]==raw[2:],'SS_COMMANDS_UNCHANGED')
 finally:
  cleanup=guard.close();cleanup_ref=save('source_guard.cleanup.actual.json',cleanup)
  require(cleanup['closed'] is True and cleanup['errors']==[] and cleanup['retained_handles_count']==0,'GUARD_CLOSED')
 new_c=json.loads(CANON[0].read_bytes())
 def arr(data):
  text=data.decode('utf-8');start=text.index('[',text.index('"failure_counters":'));_,length=json.JSONDecoder().raw_decode(text[start:]);return text[start:start+length]
 require(arr(CANON[0].read_bytes()).startswith(arr(raw[0]).rstrip()[:-1].rstrip()+','),'OLD934_RAW_ARRAY_PREFIX')
 proof=save('canonical_pair.actual.json',{'transaction':transaction,'checkpoint_ref':pin(CANON[0]),'ownership_ref':pin(CANON[1]),'old934_semantic_equal':True,'old934_raw_array_prefix_preserved':True,'new_ordinals':[x['ordinal'] for x in facts['diagnostics']],'registered_failures':len(new_c['failure_counters']),'highest_registered_ordinal':facts['highest_observed_ordinal'],'next_at_cutoff':facts['next_failure_ordinal'],'next_original_failure_ordinal_live':live_context['next_original_failure_ordinal'],'pending_after_cutoff':live_context['pending'],'live_context_ref':live_context_ref,'formal_acceptance':False,'Main_adopted':False})
 resume=save('RESUME.r367.original.json',{'schema':'researchos.root-resume.v1','checkpoint_ref':pin(CANON[0]),'ownership_ref':pin(CANON[1]),'scope_ref':facts['scope_ref'],'registered_failures':len(new_c['failure_counters']),'next_at_cutoff':facts['next_failure_ordinal'],'next_original_failure_ordinal_live':live_context['next_original_failure_ordinal'],'pending_after_cutoff':live_context['pending'],'live_context_ref':live_context_ref,'historical_parents':6,'current_formal_accepted':0,'required_parents':22,'required_formal':42,'formal_acceptance':False,'Main_adopted':False,'counter_reset':False,'proof_ref':proof,'next_action':'Seal postregistration adoption vector/request, then Root one actual seven-target adoption after Source qualification.'})
 save('handoff.actual.json',{'status':'ADMIN_CANONICAL_SCOPE_REGISTERED_NO_PRODUCT_ACCEPTANCE','proof_ref':proof,'resume_ref':resume,'guard_cleanup_ref':cleanup_ref})
 print(json.dumps({'checkpoint_ref':pin(CANON[0]),'ownership_ref':pin(CANON[1]),'resume_ref':resume,'formal_acceptance':False,'Main_adopted':False}),flush=True)
if __name__=='__main__':main()

