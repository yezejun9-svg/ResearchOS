import hashlib,json
from pathlib import Path
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_root_caller_independent_source_review_codex/b64193deb484cb647f785f114041992c")
def raw(p):return Path(p).read_bytes()
def pin(p):
 d=raw(p);return {'path':str(Path(p).resolve()),'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)}
def verify(r):
 d=raw(r['path']);assert len(d)==r['bytes'] and hashlib.sha256(d).hexdigest()==r['sha256'];return d
def save(n,o):
 p=BASE/n;assert not p.exists();p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return pin(p)
r=json.loads(raw(BASE/'review.json'))
assert r['decision']=='READY_SOURCE_PREPARATION_ONLY' and r['new_failure_count']==1
assert not (BASE/'handoff.json').exists() and not (BASE/'manifest.json').exists()
m=json.loads(verify(r['author_manifest_ref']));assert len(m['entries'])==6
for e in m['entries']:verify(e)
for k in ('author_handoff_ref','baseline_ref','launcher_ref','inverse_ref','static_audit_ref','request_template_ref'):verify(r[k])
for origin in r['new_failure_origins']:verify(origin)
dest=BASE/'caller.readonly.txt';assert not dest.exists();dest.write_bytes(verify(r['caller_ref']))
v=save('verification.json',{'schema':'researchos.source-only-static-verification.v1','verification':r['verification'],
 'source_checks':r['source_checks'],'new_failure_count':1,'candidate_calls':0,'canonical_writes':0})
h=save('handoff.json',{'schema':'researchos.desktop58-root-caller-independent-source-review-handoff.v1',
 'reviewer':r['reviewer'],'author':r['author'],'independent':True,'decision':r['decision'],'status':'STOPPED',
 'review_ref':pin(BASE/'review.json'),'verification_ref':v,
 'caller_ref':r['caller_ref'],'baseline_ref':r['baseline_ref'],'launcher_ref':r['launcher_ref'],
 'author_handoff_ref':r['author_handoff_ref'],'author_manifest_ref':r['author_manifest_ref'],
 'new_failure_origins':r['new_failure_origins'],'new_failure_count':1,'counter_reset':False,'automatic_retry':False,
 'future_scope_SHA':None,'future_grant_SHA':None,'future_caller_output':None,
 'actual_Root_scope_grant_and_launcher_qualification':'OPEN','caller_OS_lifecycle_qualification':False,
 'source_acceptance':False,'case_qualification':False,'formal_increment':0,'candidate_calls':0,'canonical_writes':0,
 'postseal_annex':{'path':str(BASE/'postseal-tool-observations.annex.json'),'included_in_manifest':False}})
members=[pin(p) for p in sorted(BASE.iterdir(),key=lambda p:p.name) if p.is_file()]
mf=save('manifest.json',{'schema':'researchos.independent-source-review-manifest.v1','members':members,'count':len(members),
 'self_excluded':True,'postseal_annex_excluded':True})
print(json.dumps({'review':pin(BASE/'review.json'),'handoff':h,'manifest':mf,'members':len(members),
 'failure_origins':r['new_failure_origins'],'new_failure_count':1,'decision':r['decision'],'status':'STOPPED'},ensure_ascii=False))
