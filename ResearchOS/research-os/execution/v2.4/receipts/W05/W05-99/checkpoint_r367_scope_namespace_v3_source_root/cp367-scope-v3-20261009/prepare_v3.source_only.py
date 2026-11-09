import sys
sys.dont_write_bytecode=True
import copy,hashlib,json,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
W=R/'execution/v2.4/receipts/W09/W09-99'
OLD=B/'checkpoint_r367_main_registration_v2_source_root/cp367-main-v2-20261009'
N=Path(__file__).resolve().parent
SN=W/'integration_codex/root-main-seven-target-scope-20261009'
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(ref):
 assert set(ref)=={'path','sha256','bytes'} and pin(ref['path'])==ref
 return Path(ref['path']).read_bytes()
def write(name,raw):
 with (N/name).open('xb') as f:f.write(raw)
 return pin(N/name)
def save(name,value):return write(name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def main():
 original_facts_ref=pin(OLD/'checkpoint.execution.facts.json')
 assert original_facts_ref['sha256']=='d598f46123d1cacea1e86c055bfb6464ba72bf23cdd83c724a8ea602bfe80376' and original_facts_ref['bytes']==26285
 original_writer_ref=pin(OLD/'register_cp367.v2.source.py')
 assert original_writer_ref['sha256']=='40879ec125e975d0f9dddfc046976cedba744a022aa6c4cfba06ebedd2469e79' and original_writer_ref['bytes']==17931
 old_raw=read(original_facts_ref);old_facts=json.loads(old_raw);old_scope=old_facts['scope_ref'];scope_raw=read(old_scope)
 assert old_scope['sha256']=='5e120cd9658109ed98d04bc2230e1e747424297e88a0cfedeb917d4e9eeb1ae8' and old_scope['bytes']==4355
 assert not Path(old_scope['path']).is_relative_to(W/'integration_codex')
 SN.mkdir(exist_ok=False)
 scope_path=SN/'main-seven-target.scope-registration.root.json'
 with scope_path.open('xb') as f:f.write(scope_raw)
 scope_ref=pin(scope_path)
 assert read(scope_ref)==scope_raw and Path(scope_ref['path']).is_relative_to(W/'integration_codex')
 before_token=json.dumps(old_scope['path'],ensure_ascii=False).encode('utf-8');after_token=json.dumps(scope_ref['path'],ensure_ascii=False).encode('utf-8')
 assert old_raw.count(before_token)==1
 facts_raw=old_raw.replace(before_token,after_token)
 assert facts_raw.count(after_token)==1 and facts_raw.replace(after_token,before_token)==old_raw
 facts=json.loads(facts_raw);inverse=copy.deepcopy(facts);inverse['scope_ref']=old_scope
 assert inverse==old_facts and facts['scope_ref']==scope_ref
 writer_ref=write('register_cp367.v2.source.py',read(original_writer_ref));assert writer_ref['sha256']==original_writer_ref['sha256'] and writer_ref['bytes']==original_writer_ref['bytes']
 facts_ref=write('checkpoint.execution.facts.json',facts_raw)
 inverse_ref=save('complete-facts-byte-inverse.json',{'before_ref':original_facts_ref,'after_ref':facts_ref,'exact_changed_pointer':'/scope_ref/path','before_token':before_token.decode('utf-8'),'after_token':after_token.decode('utf-8'),'complete_utf8_byte_inverse':True,'complete_semantic_inverse':True,'scope_before_ref':old_scope,'scope_after_ref':scope_ref,'scope_content_identical':True,'writer_before_ref':original_writer_ref,'writer_after_ref':writer_ref,'writer_bytes_identical':True,'Main_caller_scope_namespace_satisfied':True})
 live_ref=pin(OLD/'root-postseal-live-950-20261009/live-context.actual.root.json');live=json.loads(read(live_ref))
 assert live['next_original_failure_ordinal']==950 and [v['ordinal'] for v in live['pending']]==[948,949]
 m=types.ModuleType('cp367_v3_scope_source');m.__file__=writer_ref['path'];sys.modules[m.__name__]=m;exec(compile(read(writer_ref),writer_ref['path'],'exec'),m.__dict__)
 refs=[pin(__file__),writer_ref,facts_ref,inverse_ref,original_facts_ref,original_writer_ref,old_scope,scope_ref,live_ref,*facts['canonical_refs'],facts['calling_contract_ref'],*facts['actual_refs'],pin(OLD/'HDF.json'),pin(OLD/'MF.json')]
 for item in facts['reviews']:
  refs.extend([item['handoff_ref'],item['manifest_ref']]);members=json.loads(read(item['manifest_ref']))['members'];members=list(members.values()) if isinstance(members,dict) else members
  refs.extend(dict(path=str(Path(v['path']).resolve(strict=True)),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes']) for v in members)
 refs.extend(item['origin_ref'] for item in facts['diagnostics']);refs.extend(item['origin_ref'] for item in live['pending'])
 refs.extend(pin(OLD/name) for name in ('source-preview-proof.json','complete-source-inverse.json','source-guard.cleanup.actual.json'))
 gp=dict(path=str(m.GP.resolve()),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404)
 refs.append(gp)
 for mod in tuple(sys.modules.values()):
  for field in ('__file__','__cached__'):
   p=getattr(mod,field,None)
   if p and Path(p).is_file():refs.append(pin(p))
 unique={}
 for ref in refs:
  read(ref);key=ref['path'].casefold();assert key not in unique or unique[key]==ref;unique[key]=ref
 gm=m.module(m.GP,read(gp));guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(unique.values()))
 try:
  _,owner,worker=m.facts_scope(facts);before=[json.loads(guard.get_buffer(ref['path'])) for ref in facts['canonical_refs'][:2]]
  c,o=m.transform(copy.deepcopy(before[0]),copy.deepcopy(before[1]),facts,facts_ref,before[0],before[1],owner,worker,'SOURCE_PREVIEW_ONLY',live)
  assert len(c['failure_counters'])==945 and c['work_in_progress']['root_next_failure_ordinal_live']==950 and c['work_in_progress']['later_diagnostics_observed_after_cutoff']==live['pending']
  assert owner['scope_ref']==worker['scope_ref']==scope_ref and Path(scope_ref['path']).is_relative_to(W/'integration_codex')
  cr=save('checkpoint.proposed.source.json',c);orr=save('ownership.proposed.source.json',o)
  proof=save('source-preview-proof.json',{'status':'PURE_V3_SCOPE_NAMESPACE_REBIND_VERIFIED','facts_ref':facts_ref,'writer_ref':writer_ref,'scope_ref':scope_ref,'complete_inverse_ref':inverse_ref,'writer_bytes_identical_to_reviewed_v2':True,'old934_unchanged':True,'new_ordinals':list(range(937,948)),'source_next_at_cutoff':948,'preview_live_next':950,'preview_pending_ordinals':[948,949],'source_scope_namespace_required_by_actual_caller':'W09/W09-99/integration_codex','source_scope_namespace_satisfied':True,'proposed_checkpoint_ref':cr,'proposed_ownership_ref':orr,'input_refs':len(unique),'canonical_Main_written':False,'formal_delta':0,'fresh_post_v3_review_live_context_required':True})
 finally:
  cleanup=guard.close();cleanup_ref=save('source-guard.cleanup.actual.json',cleanup);assert cleanup['closed'] and cleanup['errors']==[] and cleanup['retained_handles_count']==0
 mf=save('MF.json',{'schema':'researchos.root-cp367-main-registration-v3-source-manifest.v1','members':[pin(__file__),writer_ref,facts_ref,inverse_ref,scope_ref,cr,orr,proof,cleanup_ref]})
 hdf=save('HDF.json',{'schema':'researchos.root-cp367-main-registration-v3-source-handoff.v1','actor_id':'codex:/root','status':'SOURCE_V3_SCOPE_NAMESPACE_PREPARED_PENDING_INDEPENDENT_REVIEW_NO_ACTUAL','manifest_ref':mf,'facts_ref':facts_ref,'writer_ref':writer_ref,'scope_ref':scope_ref,'source_preview_ref':proof,'source_guard_cleanup_ref':cleanup_ref,'old_source_handoff_ref':pin(OLD/'HDF.json'),'old_source_manifest_ref':pin(OLD/'MF.json'),'source_next_at_cutoff':948,'preview_live_next':950,'writer_bytes_identical_to_reviewed_v2':True,'facts_single_pointer_path_rebind_only':True,'Main_caller_scope_namespace_satisfied':True,'actual_live_context_required':True,'Main_Canon_written':False,'formal_acceptance':False})
 print(json.dumps(dict(handoff_ref=hdf,manifest_ref=mf,facts_ref=facts_ref,writer_ref=writer_ref,scope_ref=scope_ref,proof_ref=proof,guard_cleanup_ref=cleanup_ref,Canon_Main_written=False)),flush=True)
if __name__=='__main__':main()
