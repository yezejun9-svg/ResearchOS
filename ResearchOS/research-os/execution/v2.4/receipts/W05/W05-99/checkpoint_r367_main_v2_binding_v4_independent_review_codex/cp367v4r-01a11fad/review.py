import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent;B=N.parents[1]
C=B/'checkpoint_r367_main_v2_binding_v4_source_root/cp367-bind-v4-20261009'
pins={};checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):
 r=dict(path=str(Path(r['path']).resolve(strict=True)),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes']);assert pin(r['path'])==r
 assert r['path'] not in pins or pins[r['path']]==r
 pins[r['path']]=r;return Path(r['path']).read_bytes()
def load(r):return json.loads(read(r))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ck(n,v):
 assert v,n
 checks.append(n)
h=load(dict(path=str(C/'HDF.json'),sha256='2864d5989c0b82c54bc1b81465e27656c68ff2ec8581b4b39096ae2543eeb467',bytes=2715))
mf=load(h['manifest_ref'])
for r in mf['members']:read(r)
f=load(h['facts_ref']);sc=load(h['scope_ref']);proof=load(h['source_preview_ref']);inv=load(proof['complete_inverse_ref'])
oldraw=read(inv['before_ref']);oldfacts=json.loads(oldraw)
rollback=copy.deepcopy(f)
for row in inv['changed_pointers']:
 parts=[p.replace('~1','/').replace('~0','~') for p in row['pointer'].split('/')[1:]];at=rollback
 for part in parts[:-1]:at=at[part]
 assert at[parts[-1]]==row['after'];at[parts[-1]]=copy.deepcopy(row['before'])
ck('facts_complete_semantic_inverse',rollback==oldfacts)
ck('facts_complete_UTF8_byte_inverse',(json.dumps(rollback,ensure_ascii=False,indent=2)+'\n').encode()==oldraw)
allowed={'calling_contract_ref','scope_ref','reviews','diagnostics','highest_observed_ordinal','next_failure_ordinal','registered_after','actual_refs','work_in_progress','checkpoint_note'}
ck('facts_only_authorized_metadata_roots',all(row['pointer'].split('/')[1] in allowed for row in inv['changed_pointers']))
oldsc=load(oldfacts['scope_ref']);scope_changed={k for k in sc if sc[k]!=oldsc[k]}
ck('scope_only_source_binding_metadata_changed',scope_changed=={'caller_ref','change_set_ref','source_handoff_ref','source_manifest_ref','source_review_handoff_ref','source_review_manifest_ref','source_review_decision_ref','journal_root'})
contract=load(f['calling_contract_ref']);mainh=load(sc['source_handoff_ref']);maincaller=read(sc['caller_ref']);change=load(sc['change_set_ref'])
for pair in f['reviews']:
 load(pair['handoff_ref']);m=load(pair['manifest_ref']);members=m['members'];members=list(members.values()) if isinstance(members,dict) else members
 for r in members:read(r)
for r in f['actual_refs']:read(r)
origins=[load(v['origin_ref']) for v in f['diagnostics']]
ck('old11_diagnostics_exact',f['diagnostics'][:11]==oldfacts['diagnostics'])
ck('new14_ordinals_exact937to950',[v['ordinal'] for v in f['diagnostics']]==list(range(937,951)))
ck('new_three_numeric_qualifications',[(v['actual_outer_exit'],v['actual_python_exit'],v['actual_native_exit']) for v in f['diagnostics'][-3:]]==[(None,None,None),(1,None,None),(None,1,None)])
o948,o949,o950=origins[-3:]
ck('948_original_all_numeric_null',o948['ordinal']==948 and all(o948[k] is None for k in ('outer_exit','python_exit','native_exit','model_exit')) and o948['count_once'] is True)
ck('949_original_outer1_only',o949['result']['chunk_id']=='b7b538' and o949['result']['exit_code']==1)
mapping_refs=[r for r in f['actual_refs'] if Path(r['path']).name=='failure-origin.949.registration.root.json']
ck('949_root_single_mapping_in_facts',len(mapping_refs)==1)
mapping=load(mapping_refs[0]);ck('949_single_mapping_exact',mapping['ordinal']==949 and mapping['origin_ref']==f['diagnostics'][-2]['origin_ref'] and mapping['original_calls']==1 and mapping['replay'] is False and mapping['sealed_origin_ordinal_NULL_preserved'] is True)
ck('950_explicit_source_Python1_outerNULL',o950['ordinal_assigned_by_root']==950 and o950['tools_exec_command_result']['exit_code'] is None and o950['source_python_exit']==1 and 'SOURCE_PYTHON_EXIT=1' in o950['tools_exec_command_result']['output'] and o950['product_native_exit'] is None and o950['count_once'] is True)
raw=[read(r) for r in f['canonical_refs']];oldcp,oldow=[json.loads(b) for b in raw[:2]]
ck('canonical_before_exact366_170',oldcp['revision']==366 and oldow['revision']==170 and f['canonical_refs']==oldfacts['canonical_refs'])
live=load(next(r for r in mf['members'] if Path(r['path']).name=='live-context.preview-only.json'))
writer=read(h['writer_ref']);ck('writer_exact_reviewed_v2',hashlib.sha256(writer).hexdigest()=='40879ec125e975d0f9dddfc046976cedba744a022aa6c4cfba06ebedd2469e79' and len(writer)==17931)
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
graw=read(dict(path=str(gp),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404))
gm=types.ModuleType('cp367v4reviewguard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(graw,str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(pins.values()))
try:
 ns=dict(Path=Path,copy=copy,hashlib=hashlib,json=json,TARGETS=sc['exact_targets'],KEY='c19_main_source_registry_adoption',SLICE='C19_MAIN_SOURCE_REGISTRY_ADOPTION')
 names={'require','pin','read','load','facts_scope','validate_live_context','transform'}
 exec(compile(ast.Module(body=[v for v in ast.parse(writer).body if isinstance(v,ast.FunctionDef) and v.name in names],type_ignores=[]),'<pure-Root-v4-functions>','exec'),ns)
 _,owner,worker=ns['facts_scope'](f)
 nc,no=ns['transform'](copy.deepcopy(oldcp),copy.deepcopy(oldow),f,h['facts_ref'],oldcp,oldow,owner,worker,'INDEPENDENT',live)
 ck('old934_semantic_exact',len(oldcp['failure_counters'])==934 and nc['failure_counters'][:934]==oldcp['failure_counters'])
 ck('registered948_cut950_next951',len(nc['failure_counters'])==948 and nc['work_in_progress']['r367_highest_observed_diagnostic_ordinal_at_cutoff']==950 and nc['work_in_progress']['r367_next_failure_ordinal_at_cutoff']==951)
 ck('new14_single_origin_keys',len({v['origin_key'] for v in nc['failure_counters'][934:]})==14 and all(v['counted_once'] is True and v['counter_reset'] is False for v in nc['failure_counters'][934:]))
 ck('new14_payloads_exact',all(row['original_payload']['immutable_origin_ref']==item['origin_ref'] and row['original_payload']['actual_outer_exit']==item['actual_outer_exit'] and row['original_payload']['actual_python_exit']==item['actual_python_exit'] and row['original_payload']['actual_native_exit'] is None for row,item in zip(nc['failure_counters'][934:],f['diagnostics'])))
 ck('only_one_W09_worker_added',nc['workers']==oldcp['workers']+[worker] and worker['step_id']=='W09-99' and worker['scope_ref']==h['scope_ref'])
 ic,io=copy.deepcopy(nc),copy.deepcopy(no)
 for k in ('failure_counters','workers','work_in_progress','expected_previous_revision','revision','updated_at','updated_by','note'):ic[k]=copy.deepcopy(oldcp[k])
 del io['card_path_bindings']['W09-99']['subtasks'][ns['KEY']]
 for k in ('revision','updated_at','updated_by'):io[k]=oldow[k]
 ck('complete_canonical_inverse_no_W05_authority_expansion',ic==oldcp and io==oldow)
 pcraw=read(proof['proposed_checkpoint_ref']);poraw=read(proof['proposed_ownership_ref']);pc,po=json.loads(pcraw),json.loads(poraw)
 for d in (nc,no,pc,po):d.pop('updated_at',None)
 ck('independent_transform_matches_sealed_preview',nc==pc and no==po)
 def arr(b):
  t=b.decode();s=t.index('[',t.index('"failure_counters":'));_,n=json.JSONDecoder().raw_decode(t[s:]);return t[s:s+n]
 ck('old934_raw_prefix_unchanged',arr(pcraw).startswith(arr(raw[0]).rstrip()[:-1].rstrip()+','))
 main=types.ModuleType('pure_Main_v2_for_actual_v4_scope');main.__file__=sc['caller_ref']['path'];exec(compile(maincaller,main.__file__,'exec'),main.__dict__)
 _,source_refs=main.manifest_refs(sc['source_handoff_ref'],sc['source_manifest_ref'])
 vector_ref=next(r for r in mf['members'] if Path(r['path']).name=='canonical-vector.proposed.source.json')
 realread=main.read_ref;memory={str(main.CANON[0]):pcraw,str(main.CANON[1]):poraw}
 def virtual_read(r):
  if r['path'] not in memory:return realread(r)
  b=memory[r['path']];assert main.raw_pin(Path(r['path']),b)==r;return b
 main.read_ref=virtual_read
 try:
  _,vec=main.validate_scope(sc,h['scope_ref'],change,sc['change_set_ref'],sc['caller_ref'],sc['source_handoff_ref'],sc['source_manifest_ref'],source_refs,vector_ref)
 finally:main.read_ref=realread
 ck('full_Main_v2_validate_scope_real_source_review_pass',vec['checkpoint_revision']==367 and vec['ownership_revision']==171)
 ck('Scope_namespace_pass',Path(h['scope_ref']['path']).is_relative_to(main.W/'integration_codex'))
 ck('WIP_not_actual_formal_or_parent_grant',f['work_in_progress']['Main_adopted'] is False and f['work_in_progress']['formal_current_count']==0 and f['work_in_progress']['parents_accepted']==6 and 'PENDING_ROOT_SCOPE_AND_ACTUAL' in f['work_in_progress']['W05_A21_v2_caller_correction'])
 ck('four_current_canonical_unchanged',[Path(r['path']).read_bytes() for r in f['canonical_refs']]==raw)
finally:
 cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup);assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
ck('all_pins_unchanged',all(pin(r['path'])==r for r in pins.values()))
save('input-pins.json',list(pins.values()));save('checks.json',checks)
save('diagnostic-audit.json',dict(ordinals=list(range(937,951)),original11_identical=True,append948_outer_python_native=[None,None,None],append949_outer_python_native=[1,None,None],append950_outer_python_native=[None,1,None],mapping949_ref=mapping_refs[0],origin_refs=[v['origin_ref'] for v in f['diagnostics']],registered_before=934,registered_after=948,cut950_next951=True))
save('result.json',dict(status='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_LIVE_CONTEXT_VALIDATION',checks=len(checks),pins=len(pins),actual_registration_qualified_now=False,condition='After this review Root issues a new exact live context bound to source cut950/next951; live951 pending[] only if no new original failure; independently validate freshness and complete pending interval before one actual registration',new_original_failures=[],actual_Main_Canon_written=False,Go_SQL_API_model_executed=False,formal_case_accepted_delta=0))
print(json.dumps(dict(status='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_LIVE_CONTEXT_VALIDATION',checks=len(checks),pins=len(pins),new_failures=0)))
