import sys
sys.dont_write_bytecode=True
import copy,hashlib,json,types,ctypes
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
OLD=B/'checkpoint_r367_main_v2_binding_v4_source_root/cp367-bind-v4-20261009';N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(ref):
 assert set(ref)=={'path','sha256','bytes'} and pin(ref['path'])==ref
 return Path(ref['path']).read_bytes()
def enc(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def write(name,raw):
 with (N/name).open('xb') as f:f.write(raw)
 return pin(N/name)
def save(name,v):return write(name,enc(v))
old_writer_ref=pin(OLD/'register_cp367.v2.source.py');assert old_writer_ref['sha256']=='40879ec125e975d0f9dddfc046976cedba744a022aa6c4cfba06ebedd2469e79'
before=read(old_writer_ref);a=b",N,'register')";b=b",N,'activate')";assert before.count(a)==1
after=before.replace(a,b);assert after.count(b)==1 and after.replace(b,a)==before
writer_ref=write('register_cp367.v5.source.py',after)
old_facts_ref=pin(OLD/'checkpoint.execution.facts.json');assert old_facts_ref['sha256']=='f0e358383f6a8c9702a2ffe1770b8d2a76ce1390764383fd02102836014d333d'
old=json.loads(read(old_facts_ref));facts=copy.deepcopy(old)
origin=pin(OLD/'failure-origin.951.original-tool-io.root.json');assert origin['sha256']=='59b52d67108293c70259327a4a39cb4c71bc282e9f56ed35a1e2da7044bc8de8' and origin['bytes']==2538
facts['diagnostics'].append(dict(ordinal=951,origin_ref=origin,actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,description='Root first CP367 v4 administrative invocation524e08 failed before canonical locks/writes: trusted transaction helper accepts activate/close, caller passed register. Original full tool args/result retained; input guard closed0; no product Native/model.',origin_selector='Root one original tools.exec_command invocation524e08; no automatic replay or counter reset.',exit_qualification='Observed outer1 and explicit ROOT_SOURCE_PYTHON_EXIT=1; product Native/model NULL.'))
facts.update(highest_observed_ordinal=951,next_failure_ordinal=952,registered_after=949)
facts['checkpoint_note']=old['checkpoint_note'].replace('Source-cut950 diagnostics937..950','Source-cut951 diagnostics937..951')
cleanup_before_ref=pin(OLD/'source_guard.cleanup.actual.json');cleanup_before=json.loads(read(cleanup_before_ref));assert cleanup_before['closed'] and cleanup_before['errors']==[] and cleanup_before['retained_handles_count']==0
facts['actual_refs'].append(cleanup_before_ref)
facts_ref=save('checkpoint.execution.facts.json',facts)
inverse=copy.deepcopy(facts);inverse['diagnostics'].pop();inverse['actual_refs'].pop()
for key in ('highest_observed_ordinal','next_failure_ordinal','registered_after','checkpoint_note'):inverse[key]=old[key]
assert inverse==old and enc(inverse)==read(old_facts_ref)
inverse_ref=save('complete-source-and-facts-inverse.json',dict(writer_before_ref=old_writer_ref,writer_after_ref=writer_ref,writer_before_span=a.decode(),writer_after_span=b.decode(),complete_writer_byte_inverse=True,facts_before_ref=old_facts_ref,facts_after_ref=facts_ref,complete_facts_byte_inverse=True,complete_facts_semantic_inverse=True,scope_and_all_Source_review_bindings_unchanged=True))
m=types.ModuleType('cp367_v5_source');m.__file__=writer_ref['path'];sys.modules[m.__name__]=m;exec(compile(after,writer_ref['path'],'exec'),m.__dict__)
tp=dict(path=str(m.TP.resolve()),sha256='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9',bytes=6877)
tm=m.module(m.TP,read(tp));old_dll=ctypes.WinDLL;events=[]
class BoundaryReached(Exception):pass
def stop_before_WinAPI(name,*args,**kwargs):
 events.append(name);raise BoundaryReached('PURE_MEMORY_STOP_BEFORE_WINAPI_NO_CANONICAL_LOCK_OR_WRITE')
try:
 ctypes.WinDLL=stop_before_WinAPI
 try:tm.update_pair(facts['canonical_refs'][:2],lambda *x:x,N,'register')
 except RuntimeError as exc:assert str(exc)=='unknown canonical transaction'
 else:raise AssertionError('OLD_REGISTER_MUST_REJECT')
 assert events==[]
 try:tm.update_pair(facts['canonical_refs'][:2],lambda *x:x,N,'activate')
 except BoundaryReached:pass
 else:raise AssertionError('LEGAL_ACTIVATE_MUST_REACH_BOUNDARY')
 assert events==['kernel32']
finally:ctypes.WinDLL=old_dll
live=dict(schema='researchos.root-postseal-live-diagnostic-context.v1',issued_by='codex:/root',created_utc='SOURCE_PREVIEW_ONLY_FRESH_POST_REVIEW_ACTUAL_CONTEXT_REQUIRED',source_cutoff=dict(highest_ordinal=951,next_failure_ordinal=952),next_original_failure_ordinal=952,pending=[])
live_ref=save('live-context.preview-only.json',live)
refs=[pin(__file__),writer_ref,facts_ref,inverse_ref,old_writer_ref,old_facts_ref,tp,live_ref,*facts['canonical_refs'],facts['scope_ref'],facts['calling_contract_ref'],*facts['actual_refs'],pin(OLD/'HDF.json'),pin(OLD/'MF.json')]
for pair in facts['reviews']:
 refs.extend(pair.values());members=json.loads(read(pair['manifest_ref']))['members'];members=list(members.values()) if type(members) is dict else members
 refs.extend(dict(path=str(Path(v['path']).resolve(strict=True)),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes']) for v in members)
refs.extend(x['origin_ref'] for x in facts['diagnostics'])
gp=dict(path=str(m.GP.resolve()),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404);refs.append(gp)
unique={}
for ref in refs:
 read(ref);key=ref['path'].casefold();assert key not in unique or unique[key]==ref;unique[key]=ref
gm=m.module(m.GP,read(gp));guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(unique.values()))
try:
 _,owner,worker=m.facts_scope(facts);old_docs=[json.loads(guard.get_buffer(ref['path'])) for ref in facts['canonical_refs'][:2]]
 c,o=m.transform(copy.deepcopy(old_docs[0]),copy.deepcopy(old_docs[1]),facts,facts_ref,old_docs[0],old_docs[1],owner,worker,'SOURCE_PREVIEW_ONLY',live)
 assert len(c['failure_counters'])==949 and c['failure_counters'][:934]==old_docs[0]['failure_counters']
 cr=save('checkpoint.proposed.source.json',c);orr=save('ownership.proposed.source.json',o)
 proof=save('source-preview-proof.json',dict(status='PURE_V5_TRANSACTION_OPERATION_FIX_VERIFIED',facts_ref=facts_ref,writer_ref=writer_ref,scope_ref=facts['scope_ref'],complete_inverse_ref=inverse_ref,operation='activate',old_register_rejected_before_WinAPI=True,legal_activate_reaches_stubbed_WinAPI_boundary=True,WinAPI_actually_called=False,canonical_Main_written=False,canonical_automatic_inverse=False,failed_partial_requires_explicit_Root_reconciliation=True,old934_unchanged=True,new_ordinals=list(range(937,952)),source_next_at_cutoff=952,preview_live_next=952,proposed_checkpoint_ref=cr,proposed_ownership_ref=orr,input_refs=len(unique),formal_delta=0,fresh_post_review_live_context_required=True))
finally:
 cleanup=guard.close();cleanup_ref=save('source-guard.cleanup.actual.json',cleanup);assert cleanup['closed'] and cleanup['errors']==[] and cleanup['retained_handles_count']==0
mf=save('MF.json',dict(schema='researchos.root-cp367-main-registration-v5-source-manifest.v1',members=[pin(__file__),writer_ref,facts_ref,inverse_ref,live_ref,cr,orr,proof,cleanup_ref]))
hdf=save('HDF.json',dict(schema='researchos.root-cp367-main-registration-v5-source-handoff.v1',actor_id='codex:/root',status='SOURCE_V5_PREPARED_PENDING_INDEPENDENT_REVIEW_NO_ACTUAL',manifest_ref=mf,facts_ref=facts_ref,writer_ref=writer_ref,scope_ref=facts['scope_ref'],source_preview_ref=proof,source_guard_cleanup_ref=cleanup_ref,old_source_handoff_ref=pin(OLD/'HDF.json'),transaction_helper_operation='activate',source_next_at_cutoff=952,preview_live_next=952,actual_live_context_required=True,Main_Canon_written=False,formal_acceptance=False))
print(json.dumps(dict(handoff_ref=hdf,manifest_ref=mf,facts_ref=facts_ref,writer_ref=writer_ref,scope_ref=facts['scope_ref'],proof_ref=proof,guard_cleanup_ref=cleanup_ref,Canon_Main_written=False)),flush=True)
