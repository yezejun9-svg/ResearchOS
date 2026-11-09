"""Actual session/header and sealed source-author call attribution. Read-only."""
import hashlib
import json
from pathlib import Path
import runpy
N=Path(__file__).resolve().parent
x=runpy.run_path(str(N/'review.py'),run_name='identity_definitions');pin,read,save=x['pin'],x['read'],x['save']
previous=x['mod'](x['R']/'execution/v2.4/receipts/W09/W09-99/cp370_actual_registration_independent_review_codex/actualr4-01a120ab/review.py');previous.N=N
authoraudit=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T17-49-39-01a12011-7d41-7991-a01c-de2d71701ff7.jsonl')
authorcap=previous.capture(authoraudit,0,'bdecc0','actual-v4-source-author')
owncap=pin(N/'review-complete.actual-host.raw.jsonl');ownbinding=pin(N/'review-complete.actual-host.binding.json')
ownrows=[json.loads(z) for z in Path(owncap['path']).read_bytes().splitlines()]
authorrows=[json.loads(z) for z in Path(authorcap['cap_ref']['path']).read_bytes().splitlines()]
own=ownrows[0]['payload'];author=authorrows[0]['payload'];h=read(N/'HDF.json');source=read(h['source_hdf_ref']['path'])
assert own['agent_path']==own['source']['subagent']['thread_spawn']['agent_path']=='/root/attach_fixture_source_review'
assert author['agent_path']==author['source']['subagent']['thread_spawn']['agent_path']=='/root/w09_formal_profile_source_impl'
assert 'codex:'+own['agent_path']==h['actor_id'] and 'codex:'+author['agent_path']==h['source_author_id']==source['author']
assert own['agent_path']!=author['agent_path'] and own['id']!=author['id']
assert own['parent_thread_id']==author['parent_thread_id']
assert authorcap['result']['exit_code']==0
published=json.loads(authorcap['result']['output'].splitlines()[0])
assert published['handoff_ref']['sha256']==h['source_hdf_ref']['sha256'] and published['handoff_ref']['bytes']==h['source_hdf_ref']['bytes']
assert published['manifest_ref']['sha256']==h['source_mf_ref']['sha256'] and published['manifest_ref']['bytes']==h['source_mf_ref']['bytes']
with (N/'reviewer-session-header.raw.jsonl').open('xb') as f:f.write(Path(owncap['path']).read_bytes().splitlines(keepends=True)[0])
with (N/'author-session-header.raw.jsonl').open('xb') as f:f.write(Path(authorcap['cap_ref']['path']).read_bytes().splitlines(keepends=True)[0])
refs=[pin(__file__),pin(N/'HDF.json'),h['source_hdf_ref'],h['source_mf_ref'],owncap,ownbinding,authorcap['cap_ref'],authorcap['binding_ref'],pin(N/'reviewer-session-header.raw.jsonl'),pin(N/'author-session-header.raw.jsonl'),pin(N/'complete-hostpair-seal.json')]
guardmod=x['mod'](x['B']/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py');guard=guardmod.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs)
try:
 for bfile in [ownbinding,authorcap['binding_ref']]:
  b=read(bfile['path']);capref=b['actual_capture_ref'];raw=Path(capref['path']).read_bytes().splitlines(keepends=True)
  with Path(b['source_audit_path']).open('rb') as f:
   for offset,line in zip(b['source_line_offsets'],raw):f.seek(offset);assert f.read(len(line))==line
 for r in refs:assert pin(r['path'])==r
finally:closed=guard.close()
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('identity-sourceguard.closed.json',closed)
def identity(v):return {k:v.get(k) for k in ('id','parent_thread_id','agent_path','agent_nickname','agent_role')}
ir=save('actual-actor-identity-chain.json',dict(decision='INDEPENDENT_NON_AUTHOR_IDENTITY_VERIFIED',reviewer=identity(own),actual_source_author=identity(author),review_actor=h['actor_id'],source_author=source['author'],different_agent_paths=True,different_session_ids=True,reviewer_header_ref=pin(N/'reviewer-session-header.raw.jsonl'),author_header_ref=pin(N/'author-session-header.raw.jsonl'),actual_review_host_capture_ref=owncap,actual_review_host_binding_ref=ownbinding,actual_source_author_host_capture_ref=authorcap['cap_ref'],actual_source_author_host_binding_ref=authorcap['binding_ref'],Source_HDF_MF_hashes_from_actual_author_output_match=True,source_output_path_display_encoding_preserved_verbatim=True,source_hdf_ref=h['source_hdf_ref'],source_mf_ref=h['source_mf_ref'],source_guard_ref=gr,Source_actor_string_not_relabelled=True,formal_acceptance=False))
seal=read(N/'complete-hostpair-seal.json')
final=save('complete-hostpair-seal.with-identity.json',dict(seal,prior_seal_ref=pin(N/'complete-hostpair-seal.json'),actual_actor_identity_chain_ref=ir,actual_reviewer_actor=h['actor_id'],actual_source_author_actor=source['author'],independent_non_author_identity_verified=True))
print(json.dumps(dict(seal=final,identity=ir,source_author_capture=authorcap['cap_ref'],source_author_binding=authorcap['binding_ref']),ensure_ascii=False),flush=True)
