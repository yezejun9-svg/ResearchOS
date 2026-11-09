import hashlib,json
from pathlib import Path
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_root_inputs_walk_revision_independent_source_review_codex/51b10509f101422298beaf11c153210b")
def raw(p):return Path(p).read_bytes()
def pin(p):
 d=raw(p);return {'path':str(Path(p).resolve()),'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)}
def verify(r):
 d=raw(r['path']);assert len(d)==r['bytes'] and hashlib.sha256(d).hexdigest()==r['sha256'];return d
def save(n,o):
 p=BASE/n;assert not p.exists();p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return pin(p)
r=json.loads(raw(BASE/'review.json'))
assert r['decision']=='READY_SOURCE_PREPARATION_ONLY' and r['new_failure_count']==0
assert not (BASE/'handoff.json').exists() and not (BASE/'manifest.json').exists()
m=json.loads(verify(r['author_manifest_ref']));assert m['count']==len(m['entries'])==5
for e in m['entries']:verify(e)
verify(r['author_handoff_ref']);verify(r['original_constructor_ref']);verify(r['inverse_ref'])
d=verify(r['constructor_ref']);p=BASE/'constructor.readonly.txt';assert not p.exists();p.write_bytes(d)
v=save('verification.json',{'schema':'researchos.source-only-static-verification.v1','facts':r['verification'],'new_failure_count':0,
 'candidate_calls':0,'canonical_writes':0})
h=save('handoff.json',{'schema':'researchos.desktop58-root-inputs-independent-source-review-handoff.v1',
 'reviewer':r['reviewer'],'author':r['author'],'independent':True,'decision':r['decision'],'status':'STOPPED',
 'review_ref':pin(BASE/'review.json'),'verification_ref':v,'constructor_ref':r['constructor_ref'],
 'original_constructor_ref':r['original_constructor_ref'],'author_handoff_ref':r['author_handoff_ref'],'author_manifest_ref':r['author_manifest_ref'],
 'prior_REQUEST_refs':r['prior_REQUEST_refs'],'closed_findings':['D58-CONSTRUCTOR-R01'],
 'preserved_author_after_cut_origin_ref':r['preserved_author_after_cut_origin_ref'],'author_origin_recounted':False,
 'new_failure_origins':[],'new_failure_count':0,'actual_Root_resource_scope_grant':'OPEN',
 'source_acceptance':False,'case_qualification':False,'formal_increment':0,'candidate_calls':0,'canonical_writes':0,
 'postseal_annex':{'path':str(BASE/'postseal-tool-observations.annex.json'),'included_in_manifest':False}})
members=[pin(p) for p in sorted(BASE.iterdir(),key=lambda p:p.name) if p.is_file()]
mf=save('manifest.json',{'schema':'researchos.independent-source-review-manifest.v1','members':members,'count':len(members),
 'self_excluded':True,'postseal_annex_excluded':True})
print(json.dumps({'review':pin(BASE/'review.json'),'handoff':h,'manifest':mf,'members':len(members),
 'new_failure_count':0,'decision':r['decision'],'status':'STOPPED'},ensure_ascii=False))
