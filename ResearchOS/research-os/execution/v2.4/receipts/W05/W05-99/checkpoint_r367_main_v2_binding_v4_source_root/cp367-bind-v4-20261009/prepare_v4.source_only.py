import sys
sys.dont_write_bytecode=True
import copy,hashlib,json,types
from datetime import datetime,timezone
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
W=R/'execution/v2.4/receipts/W09/W09-99'
OLD=B/'checkpoint_r367_scope_namespace_v3_source_root/cp367-scope-v3-20261009'
N=Path(__file__).resolve().parent
SN=W/'integration_codex/root-main-v2-scope-20261009'
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(ref):
 assert set(ref)=={'path','sha256','bytes'} and pin(ref['path'])==ref
 return Path(ref['path']).read_bytes()
def enc(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def write(name,raw):
 with (N/name).open('xb') as f:f.write(raw)
 return pin(N/name)
def save(name,value):return write(name,enc(value))
def replace_refs(value,replacements):
 if type(value) is dict:
  for before,after in replacements:
   if value==before:return copy.deepcopy(after)
  return {k:replace_refs(v,replacements) for k,v in value.items()}
 if type(value) is list:return [replace_refs(v,replacements) for v in value]
 return copy.deepcopy(value)
def differences(a,b,path=''):
 if type(a) is dict and type(b) is dict and set(a)==set(b):
  return [v for k in a for v in differences(a[k],b[k],path+'/'+k)]
 if type(a) is list and type(b) is list and len(a)==len(b):
  return [v for i,(x,y) in enumerate(zip(a,b)) for v in differences(x,y,path+'/'+str(i))]
 return [] if a==b and type(a)==type(b) else [dict(pointer=path,before=a,after=b)]
def main():
 assert len(sys.argv)==4
 input_ref=dict(path=sys.argv[1],sha256=sys.argv[2],bytes=int(sys.argv[3]));inp=json.loads(read(input_ref))
 assert set(inp)=={'schema','main_source_handoff_ref','main_source_manifest_ref','main_review_handoff_ref','main_review_manifest_ref','main_review_decision_ref'} and inp['schema']=='researchos.root-cp367-v4-source-inputs.v1'
 h=json.loads(read(inp['main_source_handoff_ref']));assert h['manifest_ref']==inp['main_source_manifest_ref']
 review=json.loads(read(inp['main_review_handoff_ref']));decision=json.loads(read(inp['main_review_decision_ref']))
 assert review['manifest_ref']==inp['main_review_manifest_ref'] and review['source_decision_ref']==inp['main_review_decision_ref']
 assert decision['decision']=='SOURCE_ACCEPTED_FOR_ROOT_SEVEN_TARGET_ADOPTION' and decision['actor_role']=='INDEPENDENT_NON_AUTHOR' and decision['actor_id'] not in ('codex:/root','codex:/root/command_queue_impl')
 old_ref=pin(OLD/'checkpoint.execution.facts.json');old_raw=read(old_ref);old=json.loads(old_raw);assert old_ref['sha256']=='1bb6a750cc232eed22b05a37758439ad8a4801d772974ad30fd46132e3cd6f2f' and enc(old)==old_raw
 scope=json.loads(read(old['scope_ref']));contract_ref=h['root_calling_contract_ref'];contract=json.loads(read(contract_ref))
 for field in ('caller_ref','change_set_ref'):
  assert decision[field]==h[field];scope[field]=h[field]
 scope.update(source_handoff_ref=inp['main_source_handoff_ref'],source_manifest_ref=inp['main_source_manifest_ref'],source_review_handoff_ref=inp['main_review_handoff_ref'],source_review_manifest_ref=inp['main_review_manifest_ref'],source_review_decision_ref=inp['main_review_decision_ref'],journal_root=contract['runtime_journal_root'])
 assert scope['exact_targets']==contract['exact_targets']==decision['exact_targets'] and set(scope)==set(contract['scope_required_fields'])
 SN.mkdir(exist_ok=False)
 with (SN/'main-seven-target.scope-registration.root.json').open('xb') as f:f.write(enc(scope))
 scope_ref=pin(SN/'main-seven-target.scope-registration.root.json');assert Path(scope_ref['path']).is_relative_to(W/'integration_codex')
 replacements=[(old['scope_ref'],scope_ref),(old['calling_contract_ref'],contract_ref),(old['reviews'][0]['handoff_ref'],inp['main_source_handoff_ref']),(old['reviews'][0]['manifest_ref'],inp['main_source_manifest_ref']),(old['reviews'][1]['handoff_ref'],inp['main_review_handoff_ref']),(old['reviews'][1]['manifest_ref'],inp['main_review_manifest_ref'])]
 facts=replace_refs(old,replacements)
 def diagnostic(ordinal,p,sha,size,outer,python,description):
  ref=pin(p);assert ref['sha256']==sha and ref['bytes']==size
  return dict(ordinal=ordinal,origin_ref=ref,actual_outer_exit=outer,actual_python_exit=python,actual_native_exit=None,description=description,origin_selector='One original invocation; original IO or explicit Root ordinal registration links original IO.',exit_qualification='Source/Python marker only where explicitly printed; no inferred outer or product Native/model exit. Original sealed NULL ordinal preserved, Root maps once.')
 new_diags=[diagnostic(948,B/'restored21_session_runtime_caller_source_codex/r21v2caller-20261009-02/original-failure.948.json','87066617f8c62ebfc76cc542f4f57196321dd309fbdf2f3d2b1aa050cef6cb50',1244,None,None,'A21 v2 Source apply_patch expected context not found; original tool IO preserved; all numeric exits NULL.'),diagnostic(949,B/'checkpoint_r367_main_registration_v2_independent_review_codex/cp367v2r-01a11fad/failure-read.original-tool-io.json','4ef8f7c8ed41bf734b8df8f9c3c3c302df866ff94f957f0c14d6601c38136d2d',22413,1,None,'CP367 v2 independent Source readonly query b7b538 appended nonexistent filename; observed outer1, Python/Native/model NULL; Root single mapping949 separate, original ordinalNULL unchanged.'),diagnostic(950,B/'restored21_session_runtime_caller_v3_source_codex/r21v3caller-20261009-01/original-failure.950.json','5e0e22a6f5ea1444e48c9f44ca3aac0840a3240bd77ca15fb04563c2539c6941',2811,None,1,'A21 v3 pure Source checker assertion expected uppercase error prefix but real in-memory output was lowercase; explicit SourcePythonExit1, outer envelope numeric NULL, product Native/model NULL; corrected control retained first failure.')]
 assert facts['diagnostics']==old['diagnostics']
 facts['diagnostics'].extend(new_diags);facts.update(highest_observed_ordinal=950,next_failure_ordinal=951,registered_after=948)
 facts['checkpoint_note']='CP367/OW171 registers independently reviewed Root Main7 v2 source/registry adoption. Source-cut950 diagnostics937..950 appended once; old934 immutable. v7 component consumers qualified; Main/formal not yet accepted. W05 A21v3 development caller Source qualified only, outer scope registration and actual13 tests pending; Native/full programme/20to24/parent/formal remain OPEN.'
 wip=facts['work_in_progress'];wip['status']='ROOT_MAIN7_V2_SOURCE_REVIEWED_PENDING_ACTUAL_ADOPTION';wip['W09_remaining'].insert(1,'Main-root native packet with Main absolute owned/raw refs and independent mode review')
 wip['W05_A21_v2_caller_correction']='V3_SOURCE_ACCEPTED_DEVELOPMENT_TESTS_ONLY_PENDING_ROOT_SCOPE_AND_ACTUAL'
 a21s=pin(B/'restored21_session_runtime_caller_v3_source_codex/r21v3caller-20261009-01/HDF.json');a21sm=pin(Path(a21s['path']).parent/'MF.json')
 a21r=pin(B/'restored21_runtime_v3_caller_independent_review_codex/review-1a11fa1/HDF.json');a21rm=pin(Path(a21r['path']).parent/'MF.json')
 assert a21s['sha256']=='72df2851c4c8fe5f8db37c283dad9cfcaba0921554606f4b3d0b51f0c6e856fd' and a21r['sha256']=='64f3bd714e1bb1811961f12eba2ecf9c238558e5efafd1a51ce8892aba590550'
 assert json.loads(read(a21r))['status']=='SOURCE_ACCEPTED_FOR_ROOT_DEVELOPMENT_TESTS_ONLY'
 for pair in (dict(handoff_ref=a21s,manifest_ref=a21sm),dict(handoff_ref=a21r,manifest_ref=a21rm)):
  facts['reviews'].append(pair);wip['source_and_review_pairs'].append(copy.deepcopy(pair))
 mapping949=pin(B/'checkpoint_r367_main_registration_v2_source_root/cp367-main-v2-20261009/root-postseal-live-950-20261009/failure-origin.949.registration.root.json')
 assert mapping949['sha256']=='55208752514b4ebd9da4ce7ba336dafbc03fd880822755dd3c9cd77ea701bbf2'
 facts['actual_refs'].append(mapping949)
 facts_ref=save('checkpoint.execution.facts.json',facts);changes=differences(old,facts)
 inverse=copy.deepcopy(facts)
 def set_pointer(doc,p,value):
  keys=p[1:].split('/');parent=doc
  for key in keys[:-1]:parent=parent[int(key)] if type(parent) is list else parent[key]
  key=keys[-1];parent[int(key) if type(parent) is list else key]=copy.deepcopy(value)
 for change in reversed(changes):set_pointer(inverse,change['pointer'],change['before'])
 assert inverse==old and enc(inverse)==old_raw
 inverse_ref=save('complete-facts-byte-inverse.json',dict(before_ref=old_ref,after_ref=facts_ref,changed_pointers=changes,complete_utf8_byte_inverse=True,complete_semantic_inverse=True))
 writer_ref=write('register_cp367.v2.source.py',read(pin(OLD/'register_cp367.v2.source.py')));assert writer_ref['sha256']=='40879ec125e975d0f9dddfc046976cedba744a022aa6c4cfba06ebedd2469e79'
 m=types.ModuleType('cp367_v4_source');m.__file__=writer_ref['path'];sys.modules[m.__name__]=m;exec(compile(read(writer_ref),writer_ref['path'],'exec'),m.__dict__)
 live=dict(schema='researchos.root-postseal-live-diagnostic-context.v1',issued_by='codex:/root',created_utc='SOURCE_PREVIEW_ONLY_FRESH_ACTUAL_CONTEXT_AFTER_REVIEW_REQUIRED',source_cutoff=dict(highest_ordinal=950,next_failure_ordinal=951),next_original_failure_ordinal=951,pending=[])
 live_ref=save('live-context.preview-only.json',live)
 refs=[pin(__file__),input_ref,old_ref,facts_ref,inverse_ref,writer_ref,scope_ref,contract_ref,live_ref,*facts['canonical_refs'],*facts['actual_refs'],pin(OLD/'HDF.json'),pin(OLD/'MF.json')]
 for pair in facts['reviews']:
  refs.extend(pair.values());members=json.loads(read(pair['manifest_ref']))['members'];members=list(members.values()) if type(members) is dict else members
  refs.extend(dict(path=str(Path(v['path']).resolve(strict=True)),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes']) for v in members)
 refs.extend(x['origin_ref'] for x in facts['diagnostics'])
 gp=dict(path=str(m.GP.resolve()),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404);refs.append(gp)
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
  assert len(c['failure_counters'])==948 and c['failure_counters'][:934]==before[0]['failure_counters'] and c['work_in_progress']['root_next_failure_ordinal_live']==951
  cr=save('checkpoint.proposed.source.json',c);orr=save('ownership.proposed.source.json',o)
  cm=types.ModuleType('main_v2_for_cp367_v4_source');cm.__file__=h['caller_ref']['path'];sys.modules[cm.__name__]=cm;exec(compile(read(h['caller_ref']),cm.__file__,'exec'),cm.__dict__)
  source_h,source_refs=cm.manifest_refs(inp['main_source_handoff_ref'],inp['main_source_manifest_ref']);change=json.loads(read(h['change_set_ref']));cm.validate_change_set(change)
  future_raw=[enc(c),enc(o)];future_refs=[cm.raw_pin(cm.CANON[i],raw) for i,raw in enumerate(future_raw)]+facts['canonical_refs'][2:]
  vector_ref=save('canonical-vector.proposed.source.json',dict(schema='researchos.w09-main-c19-adoption-canonical-vector.v1',checkpoint_revision=367,ownership_revision=171,refs=future_refs))
  original_read=cm.read_ref
  def future_read(ref):
   for i,wanted in enumerate(future_refs[:2]):
    if ref==wanted:return future_raw[i]
   return original_read(ref)
  cm.read_ref=future_read
  cm.validate_scope(scope,scope_ref,change,h['change_set_ref'],h['caller_ref'],inp['main_source_handoff_ref'],inp['main_source_manifest_ref'],source_refs,vector_ref)
  cm.read_ref=original_read
  proof=save('source-preview-proof.json',dict(status='PURE_V4_BINDING_COUNTERS_AND_REAL_CROSS_CALLER_VERIFIED',facts_ref=facts_ref,writer_ref=writer_ref,scope_ref=scope_ref,complete_inverse_ref=inverse_ref,writer_bytes_identical_to_reviewed_v2=True,old934_unchanged=True,new_ordinals=list(range(937,951)),source_next_at_cutoff=951,preview_live_next=951,source_scope_namespace_satisfied=True,main_v2_full_validate_scope_pass=True,future_CP_OW_are_explicit_in_memory_Source_simulation_only=True,real_main_source_and_independent_review_bound=True,proposed_checkpoint_ref=cr,proposed_ownership_ref=orr,input_refs=len(unique),canonical_Main_written=False,formal_delta=0,fresh_post_v4_review_live_context_required=True))
 finally:
  cleanup=guard.close();cleanup_ref=save('source-guard.cleanup.actual.json',cleanup);assert cleanup['closed'] and cleanup['errors']==[] and cleanup['retained_handles_count']==0
 mf=save('MF.json',dict(schema='researchos.root-cp367-main-registration-v4-source-manifest.v1',members=[pin(__file__),input_ref,writer_ref,facts_ref,inverse_ref,live_ref,cr,orr,vector_ref,proof,cleanup_ref]))
 hdf=save('HDF.json',dict(schema='researchos.root-cp367-main-registration-v4-source-handoff.v1',actor_id='codex:/root',status='SOURCE_V4_PREPARED_PENDING_INDEPENDENT_REVIEW_NO_ACTUAL',manifest_ref=mf,facts_ref=facts_ref,writer_ref=writer_ref,scope_ref=scope_ref,source_preview_ref=proof,source_guard_cleanup_ref=cleanup_ref,old_source_handoff_ref=pin(OLD/'HDF.json'),source_next_at_cutoff=951,preview_live_next=951,writer_bytes_identical_to_reviewed_v2=True,Main_caller_scope_namespace_satisfied=True,Main_v2_full_validate_scope_pure_pass=True,actual_live_context_required=True,Main_Canon_written=False,formal_acceptance=False))
 print(json.dumps(dict(handoff_ref=hdf,manifest_ref=mf,facts_ref=facts_ref,writer_ref=writer_ref,scope_ref=scope_ref,proof_ref=proof,guard_cleanup_ref=cleanup_ref,Canon_Main_written=False)),flush=True)
if __name__=='__main__':main()
