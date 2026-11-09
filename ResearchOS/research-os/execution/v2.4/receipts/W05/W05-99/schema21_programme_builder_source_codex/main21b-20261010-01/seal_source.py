"""Seal Source evidence; no runtime builder entry or child process."""
import hashlib,json,sys,types
from pathlib import Path
N=Path(__file__).resolve().parent
LOG=Path(r'C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-49-27-01a11e22-ecb2-7720-80d2-af63727d414d.jsonl')
G=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py')
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
    p=Path(p);b=p.read_bytes();return dict(path=p.as_posix(),sha256=sha(b),bytes=len(b))
def save(name,x):
    p=N/name
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
    return ref(p)
chunks=['0b2778','3b67a3','8735c6','c6c11b','247ec7','60f075','11f268','706c24','85b368','2ba88c','ef38a3','aa7bad','9b3c5e']
size=LOG.stat().st_size
with LOG.open('rb') as f:
    first=f.readline();start=max(len(first),size-16000000);f.seek(start)
    if start>len(first):f.readline()
    offset=f.tell();tail=f.read(size-offset)
calls={};pairs={}
for line in tail.splitlines(keepends=True):
    try:item=json.loads(line)
    except (ValueError,UnicodeDecodeError):offset+=len(line);continue
    p=item.get('payload',{});kind=p.get('type');cid=p.get('call_id')
    if kind in ('function_call','custom_tool_call') and cid:calls[cid]=(offset,line,item)
    if kind in ('function_call_output','custom_tool_call_output') and cid in calls:
        for chunk in chunks:
            if chunk in str(p.get('output','')) and chunk not in pairs:pairs[chunk]=(calls[cid],(offset,line,item))
    offset+=len(line)
assert set(pairs)==set(chunks),{'missing':sorted(set(chunks)-set(pairs))}
captures=[]
for chunk in chunks:
    call,result=pairs[chunk];p=N/f'actual-source-{chunk}.raw.jsonl'
    with p.open('xb') as f:f.write(first+call[1]+result[1])
    b=save(f'actual-source-{chunk}.binding.json',dict(source_audit_path=LOG.as_posix(),source_prefix_size_observed=size,source_line_offsets=[0,call[0],result[0]],source_line_lengths=[len(first),len(call[1]),len(result[1])],source_line_sha256=[sha(first),sha(call[1]),sha(result[1])],original_capture_ref=ref(p),original_call_id=call[2]['payload']['call_id'],chunk_id=chunk))
    captures.append({'chunk_id':chunk,'raw_ref':ref(p),'binding_ref':b})
save('actual-source-tool-index.json',{'captures':captures,'source_preparation':{'start_chunk':'706c24','session_id':30760,'completion_chunk':'ef38a3','outer_exit':0,'Python_exit':0},'pure_controls':{'chunk':'aa7bad','outer_exit':0,'Python_exit':0},'causality_clarification':{'chunk':'9b3c5e','outer_exit':0,'Python_exit':0},'original_failures':[],'Go_exit':None,'Native_product_exit':None,'SQL_exit':None,'subprocess_calls':0,'runtime_branch_called':False,'truncated_read_outputs_preserved_as_returned':True})
raw=G.read_bytes();assert sha(raw)=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85' and len(raw)==11404
gm=types.ModuleType('old21_seal_guard');exec(compile(raw,str(G),'exec'),gm.__dict__)
members=[ref(p) for p in sorted(N.rglob('*')) if p.is_file()]
g=gm.SourceReadGuard();primary=None
try:
    g.acquire(members)
    c=json.loads(g.get_buffer(str(N/'contract.v2.json')))
    checks=json.loads(g.get_buffer(str(N/'source-controls.json')))
    causal=json.loads(g.get_buffer(str(N/'causality-clarification.json')))
    manifest=json.loads(g.get_buffer(str(N/'input-manifest.json')))
    assert checks['passed']==75 and checks['failed']==0 and causal['passed']==8 and causal['failed']==0
    assert ref(N/'old21_builder.py')==c['builder_ref']
    closed=[]
    for p in N.glob('*.guard.closed.json'):
        a=json.loads(g.get_buffer(str(p)));assert a['verification']=='PASSED' and a['closed'] is True and a['retained_handles_count']==0 and a['errors']==[];closed.append(ref(p))
    assert len(closed)==7
finally:
    a=g.close();seal_guard=save('seal.guard.closed.json',a)
    assert a['verification']=='PASSED' and a['closed'] is True and a['retained_handles_count']==0 and a['errors']==[]
checks_ref=save('source-seal-checks.json',{'source_members_verified':len(members),'prior_guard_count':len(closed),'seal_guard_ref':seal_guard,'Source_controls_passed':83,'Source_controls_failed':0,'prior75_unchanged_builder_controls_reused':True,'current_final_contract_ref':ref(N/'contract.v2.json'),'original_contract_preserved_ref':ref(N/'contract.json'),'Go_Native_product_SQL_subprocess_calls':0,'execution_branch_called':False})
delivery=save('source-delivery.json',{'schema':'researchos.old21-programme-builder-source-delivery.v1','status':'SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION','source_author':c['source_author'],'builder_ref':c['builder_ref'],'contract_ref':ref(N/'contract.v2.json'),'input_manifest_ref':c['input_manifest_ref'],'frozen_source_manifest_ref':c['frozen_source_manifest_ref'],'source_controls_ref':ref(N/'source-controls.json'),'causality_clarification_ref':ref(N/'causality-clarification.json'),'actual_source_tool_index_ref':ref(N/'actual-source-tool-index.json'),'seal_checks_ref':checks_ref,'guard_refs':closed+[seal_guard],'input_counts':manifest['counts'],'input_bytes':manifest['bytes'],'source_commit':c['source_commit'],'source_tree':c['source_tree'],'RootScope_interface':c['Root_caller_interface'],'resource_binding_keys':c['resource_binding_keys'],'phases':c['phases'],'programme_result_fields':['target_results.control.program_ref','target_results.backup.program_ref','candidate_for_independent_review.program_refs.control','candidate_for_independent_review.program_refs.backup','candidate_for_independent_review.provenance_ref','candidate_for_independent_review.qualification_ref=null'],'outer_host_binding_contract':c['outer_host_binding_contract'],'actual_build_hostpair_obligation':c['actual_build_hostpair_obligation'],'actual_Root_scope_ref':None,'actual_activation_ref':None,'actual_runtime_grant_ref':None,'programme_refs':None,'programme_qualification_ref':None,'non_author_source_review':'PENDING_DIFFERENT_SOURCE_AUTHOR','Root_failure_counter_last_reported':1067,'new_original_failures':[],'Main_Canon_existing_namespace_writes':0,'Go_subprocess_SQL_Native_product_calls':0,'runtime_branch_called':False,'old22_Development13_reruns':0,'formal_acceptance':False,'STOP':True})
members=[ref(p) for p in sorted(N.rglob('*')) if p.is_file()]
mf=save('MF.json',{'schema':'researchos.old21-builder-source-manifest.v1','members':members,'source_author':c['source_author'],'no_external_cache_or_toolchain_copy':True})
hdf=save('HDF.json',{'schema':'researchos.old21-builder-source-handoff.v1','status':'SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION','source_author':c['source_author'],'manifest_ref':mf,'source_delivery_ref':delivery,'builder_ref':c['builder_ref'],'contract_ref':ref(N/'contract.v2.json'),'input_manifest_ref':c['input_manifest_ref'],'frozen_source_manifest_ref':c['frozen_source_manifest_ref'],'source_controls_pass':83,'source_controls_fail':0,'all8_Source_read_guards_closed':True,'retained_handles_count':0,'execution_branch_called':False,'Go_Native_product_SQL_subprocess_calls':0,'runtime_scope_or_grant_created':False,'programme_or_formal_qualification_created':False,'independent_source_review':'PENDING_DIFFERENT_SOURCE_AUTHOR','RootScope_interface':c['Root_caller_interface'],'resource_binding_keys':c['resource_binding_keys'],'outer_host_binding_means':'Prior completed real Root registration/qualification/activation/current4 hostpair; never current build future full return','current_build_actual_hostpair':'Root external_capture after return/failure, required before independent actual programme qualification','Root_counter_last_reported':1067,'new_original_failures':[],'STOP':True})
for r in members:assert ref(r['path'])==r
print(json.dumps({'HDF':hdf,'MF':mf,'builder':c['builder_ref'],'contract':ref(N/'contract.v2.json'),'input_manifest':c['input_manifest_ref'],'frozen_source_manifest':c['frozen_source_manifest_ref'],'sealed_members':len(members),'source_controls':83,'all_guards_closed':True,'runtime_branch_called':False},ensure_ascii=False))
