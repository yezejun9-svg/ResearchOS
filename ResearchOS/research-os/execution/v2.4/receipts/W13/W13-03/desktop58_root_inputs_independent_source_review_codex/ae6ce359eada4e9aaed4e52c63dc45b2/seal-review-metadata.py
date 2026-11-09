import hashlib,json
from pathlib import Path
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_root_inputs_independent_source_review_codex/ae6ce359eada4e9aaed4e52c63dc45b2")
def raw(p):return Path(p).read_bytes()
def pin(p):
 d=raw(p);return {'path':str(Path(p).resolve()),'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)}
def verify(r):
 d=raw(r['path']);assert len(d)==r['bytes'] and hashlib.sha256(d).hexdigest()==r['sha256'];return d
def save(name,o):
 p=BASE/name;assert not p.exists()
 p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return pin(p)
r=json.loads(raw(BASE/'review.json'))
assert r['decision']=='REQUEST_CHANGES' and r['new_failure_count']==0
assert not (BASE/'handoff.json').exists() and not (BASE/'manifest.json').exists()
m=json.loads(verify(r['author_manifest_ref']))
assert len(m['entries'])==9
for e in m['entries']:verify(e)
verify(r['author_handoff_ref'])
for key,name in (('constructor_ref','constructor.readonly.txt'),('template_ref','template.readonly.json'),('source_inverse_ref','source-inverse.readonly.json')):
 d=verify(r[key]);p=BASE/name;assert not p.exists();p.write_bytes(d)
verification=save('verification.json',{'schema':'researchos.source-only-static-verification.v1',
 'verification':r['verification'],'new_failure_count':0,'candidate_calls':0,'canonical_writes':0})
h=save('handoff.json',{'schema':'researchos.desktop58-root-inputs-independent-source-review-handoff.v1',
 'reviewer':r['reviewer'],'author':r['author'],'independent':True,'decision':r['decision'],'status':'STOPPED',
 'review_ref':pin(BASE/'review.json'),'verification_ref':verification,
 'constructor_ref':r['constructor_ref'],'template_ref':r['template_ref'],
 'author_handoff_ref':r['author_handoff_ref'],'author_manifest_ref':r['author_manifest_ref'],
 'blocking_findings':['D58-CONSTRUCTOR-R01'],'new_failure_origins':[],'new_failure_count':0,
 'preserved_author_failure_origin_refs':r['preserved_author_failure_origin_refs'],
 'source_acceptance':False,'case_qualification':False,'formal_increment':0,'candidate_calls':0,'canonical_writes':0,
 'postseal_annex':{'path':str(BASE/'postseal-tool-observations.annex.json'),'included_in_manifest':False}})
members=[pin(p) for p in sorted(BASE.iterdir(),key=lambda p:p.name) if p.is_file()]
mf=save('manifest.json',{'schema':'researchos.independent-source-review-manifest.v1',
 'members':members,'count':len(members),'self_excluded':True,'postseal_annex_excluded':True})
print(json.dumps({'review':pin(BASE/'review.json'),'handoff':h,'manifest':mf,'members':len(members),
 'decision':r['decision'],'new_failure_count':0,'status':'STOPPED'},ensure_ascii=False))
