import sys
sys.dont_write_bytecode=True
import copy,hashlib,json,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
OLD=B/'checkpoint_r367_main_registration_source_root/cp367-main-20261009'
N=Path(__file__).resolve().parent
def pin(path):
 path=Path(path).resolve(strict=True);raw=path.read_bytes();return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value):
 with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return pin(N/name)
def write(name,raw):
 with (N/name).open('xb') as f:f.write(raw)
 return pin(N/name)
def main():
 source=(OLD/'register_cp367.source.py').read_text(encoding='utf-8')
 original=source
 changes=[]
 def replace(a,b):
  nonlocal source
  assert source.count(a)==1,'ONE_EXACT_SOURCE_SPAN'
  source=source.replace(a,b);changes.append({'before':a,'after':b})
 live_fn="""def validate_live_context(live,facts):
 require(isinstance(live,dict) and set(live)=={'schema','issued_by','created_utc','source_cutoff','next_original_failure_ordinal','pending'},'EXACT_LIVE_CONTEXT_KEYS')
 require(live['schema']=='researchos.root-postseal-live-diagnostic-context.v1' and live['issued_by']=='codex:/root' and isinstance(live['created_utc'],str) and live['created_utc'],'ROOT_LIVE_CONTEXT')
 require(live['source_cutoff']=={'highest_ordinal':facts['highest_observed_ordinal'],'next_failure_ordinal':facts['next_failure_ordinal']},'EXACT_SOURCE_CUTOFF')
 next_live=live['next_original_failure_ordinal'];require(type(next_live) is int and next_live>=facts['next_failure_ordinal'],'NO_LIVE_RESET_TO_CUTOFF')
 pending=live['pending'];require(isinstance(pending,list) and all(isinstance(x,dict) and set(x)=={'ordinal','origin_ref','description'} and type(x['ordinal']) is int and isinstance(x['description'],str) for x in pending),'EXACT_PENDING_CONTEXT_ROWS')
 require([x['ordinal'] for x in pending]==list(range(facts['next_failure_ordinal'],next_live)),'ALL_POST_CUTOFF_ORIGINALS_EXACT_ONCE')
 for item in pending:read(item['origin_ref'])
 return live

"""
 replace("def transform(c,o,facts,fr,old_c,old_o,owner,worker,stamp):",live_fn+"def transform(c,o,facts,fr,old_c,old_o,owner,worker,stamp,live_context):")
 replace(" require(c==old_c and o==old_o and c['revision']==366 and o['revision']==170,'EXACT_BEFORE')"," validate_live_context(live_context,facts)\n require(c==old_c and o==old_o and c['revision']==366 and o['revision']==170,'EXACT_BEFORE')")
 replace("later_diagnostics_observed_after_cutoff=[],root_next_failure_ordinal_live=facts['next_failure_ordinal'])","later_diagnostics_observed_after_cutoff=copy.deepcopy(live_context['pending']),root_next_failure_ordinal_live=live_context['next_original_failure_ordinal'])")
 replace(" require(len(sys.argv)==3,'FACTS_SHA FACTS_BYTES')"," require(len(sys.argv)==6,'FACTS_SHA FACTS_BYTES LIVE_CONTEXT_ABSOLUTE_PATH LIVE_CONTEXT_SHA LIVE_CONTEXT_BYTES')")
 replace(" facts=load(fr);require(facts['schema']=='researchos.root-cp367-main-c19-registration-facts.v1' and facts['formal_acceptance'] is False,'FACTS_SCHEMA')"," facts=load(fr);require(facts['schema']=='researchos.root-cp367-main-c19-registration-facts.v1' and facts['formal_acceptance'] is False,'FACTS_SCHEMA')\n live_context_ref={'path':sys.argv[3],'sha256':sys.argv[4],'bytes':int(sys.argv[5])};live_context=load(live_context_ref)\n require(Path(live_context_ref['path']).is_relative_to(R/'execution/v2.4/receipts'),'ROOT_RECEIPT_LIVE_CONTEXT_BOUNDARY');validate_live_context(live_context,facts)")
 replace(" refs.extend(item['origin_ref'] for item in facts['diagnostics']);refs.extend(facts['actual_refs'])"," refs.extend(item['origin_ref'] for item in facts['diagnostics']);refs.extend(facts['actual_refs']);refs.append(live_context_ref);refs.extend(item['origin_ref'] for item in live_context['pending'])")
 replace("transform(c,o,facts,fr,old_c,old_o,owner,worker,datetime.now(timezone.utc).isoformat())","transform(c,o,facts,fr,old_c,old_o,owner,worker,datetime.now(timezone.utc).isoformat(),live_context)")
 replace("'next_at_cutoff':facts['next_failure_ordinal'],'formal_acceptance':False,'Main_adopted':False","'next_at_cutoff':facts['next_failure_ordinal'],'next_original_failure_ordinal_live':live_context['next_original_failure_ordinal'],'pending_after_cutoff':live_context['pending'],'live_context_ref':live_context_ref,'formal_acceptance':False,'Main_adopted':False")
 replace("'next_at_cutoff':facts['next_failure_ordinal'],'historical_parents':6","'next_at_cutoff':facts['next_failure_ordinal'],'next_original_failure_ordinal_live':live_context['next_original_failure_ordinal'],'pending_after_cutoff':live_context['pending'],'live_context_ref':live_context_ref,'historical_parents':6")
 compile(source,'register_cp367.v2.source.py','exec')
 writer_ref=write('register_cp367.v2.source.py',source.encode('utf-8'))
 inverse=source
 for change in reversed(changes):
  assert inverse.count(change['after'])==1
  inverse=inverse.replace(change['after'],change['before'])
 assert inverse==original
 inverse_ref=save('complete-source-inverse.json',{'before_ref':pin(OLD/'register_cp367.source.py'),'after_ref':writer_ref,'spans':changes,'complete_utf8_byte_inverse':True})
 facts_ref=write('checkpoint.execution.facts.json',(OLD/'checkpoint.execution.facts.json').read_bytes())
 facts=json.loads(Path(facts_ref['path']).read_bytes())
 m=types.ModuleType('cp367_v2_source');m.__file__=writer_ref['path'];sys.modules[m.__name__]=m;exec(compile(source,writer_ref['path'],'exec'),m.__dict__)
 pending_ref={'path':str((B/'restored21_session_runtime_caller_source_codex/r21v2caller-20261009-02/original-failure.948.json').resolve()),'sha256':'87066617f8c62ebfc76cc542f4f57196321dd309fbdf2f3d2b1aa050cef6cb50','bytes':1244}
 m.read(pending_ref)
 live={'schema':'researchos.root-postseal-live-diagnostic-context.v1','issued_by':'codex:/root','created_utc':'SOURCE_PREVIEW_ONLY_ACTUAL_CONTEXT_ISSUED_BY_ROOT_LATER','source_cutoff':{'highest_ordinal':947,'next_failure_ordinal':948},'next_original_failure_ordinal':949,'pending':[{'ordinal':948,'origin_ref':pending_ref,'description':'Source apply_patch expected lines validation failed; no retained numeric shell/Python/Native/model exits inferred.'}]}
 preview_live_ref=save('live-context.preview-only.json',live)
 _,owner,worker=m.facts_scope(facts);before=[m.load(x) for x in facts['canonical_refs'][:2]]
 refs=[pin(__file__),writer_ref,facts_ref,inverse_ref,preview_live_ref,pending_ref,*facts['canonical_refs'],facts['scope_ref'],facts['calling_contract_ref'],*facts['actual_refs']]
 for item in facts['reviews']:
  refs.extend([item['handoff_ref'],item['manifest_ref']]);members=m.load(item['manifest_ref'])['members'];members=list(members.values()) if isinstance(members,dict) else members
  refs.extend({'path':str(Path(v['path']).resolve(strict=True)),'sha256':v['sha256'].removeprefix('sha256:'),'bytes':v['bytes']} for v in members)
 refs.extend(item['origin_ref'] for item in facts['diagnostics'])
 unique={}
 for item in refs:
  m.read(item);key=item['path'].casefold();assert key not in unique or unique[key]==item;unique[key]=item
 gp={'path':str(m.GP.resolve()),'sha256':'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85','bytes':11404};gm=m.module(m.GP,m.read(gp));guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
 guard.acquire(list(unique.values()))
 try:
  c,o=m.transform(copy.deepcopy(before[0]),copy.deepcopy(before[1]),facts,facts_ref,before[0],before[1],owner,worker,'SOURCE_PREVIEW_TIMESTAMP',live)
  assert c['work_in_progress']['root_next_failure_ordinal_live']==949 and c['work_in_progress']['later_diagnostics_observed_after_cutoff']==live['pending']
  assert c['work_in_progress']['r367_next_failure_ordinal_at_cutoff']==948 and len(c['failure_counters'])==945
  negatives=[]
  for label,mutate in [('bool_next',lambda x:x.update(next_original_failure_ordinal=True)),('float_next',lambda x:x.update(next_original_failure_ordinal=949.0)),('next_below_cutoff',lambda x:x.update(next_original_failure_ordinal=947)),('missing_pending',lambda x:x.update(pending=[])),('duplicate_pending',lambda x:x['pending'].append(copy.deepcopy(x['pending'][0]))),('wrong_cutoff',lambda x:x['source_cutoff'].update(highest_ordinal=946)),('foreign_actor',lambda x:x.update(issued_by='other'))]:
   invalid=copy.deepcopy(live);mutate(invalid)
   try:m.validate_live_context(invalid,facts)
   except (ValueError,AssertionError,TypeError):negatives.append(label)
   else:raise ValueError('NEGATIVE_NOT_REJECTED:'+label)
  cr=save('checkpoint.proposed.source.json',c);orr=save('ownership.proposed.source.json',o)
  proof=save('source-preview-proof.json',{'status':'PURE_V2_LIVE_CONTEXT_FIX_VERIFIED','facts_ref':facts_ref,'scope_ref':facts['scope_ref'],'writer_ref':writer_ref,'complete_inverse_ref':inverse_ref,'canonical_before_refs':facts['canonical_refs'],'proposed_checkpoint_ref':cr,'proposed_ownership_ref':orr,'original_v1_request_changes_handoff_ref':{'path':str((B/'checkpoint_r367_main_registration_independent_review_codex/cp367r-01a11fad/HDF.json').resolve()),'sha256':'dd101d10a74545d660868048e6954bc2207d51fc00853bf5192e5ed959626458','bytes':3277},'old934_unchanged':True,'new_ordinals':list(range(937,948)),'source_next_at_cutoff':948,'preview_live_next':949,'preview_pending_ordinals':[948],'negative_contexts_rejected':negatives,'input_refs':len(unique),'canonical_Main_written':False,'formal_delta':0,'actual_live_context_issued':False})
 finally:
  cleanup=guard.close();cleanup_ref=save('source-guard.cleanup.actual.json',cleanup);assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
 mf=save('MF.json',{'schema':'researchos.root-cp367-main-registration-v2-source-manifest.v1','members':[pin(__file__),writer_ref,inverse_ref,facts_ref,preview_live_ref,cr,orr,proof,cleanup_ref]})
 hdf=save('HDF.json',{'schema':'researchos.root-cp367-main-registration-v2-source-handoff.v1','actor_id':'codex:/root','status':'SOURCE_V2_PREPARED_PENDING_INDEPENDENT_ADMIN_REVIEW_NO_ACTUAL','manifest_ref':mf,'facts_ref':facts_ref,'writer_ref':writer_ref,'scope_ref':facts['scope_ref'],'source_preview_ref':proof,'source_guard_cleanup_ref':cleanup_ref,'old_source_handoff_ref':pin(OLD/'HDF.json'),'source_next_at_cutoff':948,'preview_live_next':949,'future_actual_argv':['FACTS_SHA','FACTS_BYTES','LIVE_CONTEXT_ABSOLUTE_PATH','LIVE_CONTEXT_SHA','LIVE_CONTEXT_BYTES'],'actual_live_context_required':True,'Main_Canon_written':False,'formal_acceptance':False})
 print(json.dumps({'handoff_ref':hdf,'manifest_ref':mf,'facts_ref':facts_ref,'writer_ref':writer_ref,'proof_ref':proof,'guard_cleanup_ref':cleanup_ref,'Canon_Main_written':False}),flush=True)
if __name__=='__main__':main()

