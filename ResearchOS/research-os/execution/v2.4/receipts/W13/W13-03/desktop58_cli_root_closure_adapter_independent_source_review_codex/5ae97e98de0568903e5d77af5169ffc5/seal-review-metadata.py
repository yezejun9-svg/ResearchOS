import hashlib,json
from pathlib import Path
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_cli_root_closure_adapter_independent_source_review_codex/5ae97e98de0568903e5d77af5169ffc5")
def raw(p):return Path(p).read_bytes()
def pin(p):
 d=raw(p);return {'path':str(Path(p).resolve()),'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)}
def verify(r):
 d=raw(r['path']);assert len(d)==r['bytes'] and hashlib.sha256(d).hexdigest()==r['sha256'];return d
def save(n,o):
 p=BASE/n;assert not p.exists();p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return pin(p)
r=json.loads(raw(BASE/'review.json'));assert r['decision']=='READY_SOURCE_PREPARATION_ONLY' and r['new_failure_count']==1
assert not (BASE/'handoff.json').exists() and not (BASE/'manifest.json').exists()
m=json.loads(verify(r['author_manifest_ref']));assert type(m['entries']) is dict and len(m['entries'])==18
for e in m['entries'].values():verify(e)
verify(r['author_handoff_ref']);verify(r['inverse_ref']);verify(r['provenance_diagnostic_ref'])
for e in r['new_failure_origins']:verify(e)
for k,n in (('adapter_ref','adapter.readonly.txt'),('pipeline_ref','pipeline.readonly.txt'),('builder_ref','builder.readonly.txt'),('scope_template_ref','scope.readonly.json')):
 p=BASE/n;assert not p.exists();p.write_bytes(verify(r[k]))
v=save('verification.json',{'schema':'researchos.source-only-static-verification.v1','verification':r['verification'],
 'new_failure_count':1,'candidate_calls':0,'canonical_writes':0})
h=save('handoff.json',{'schema':'researchos.cli-root-closure-adapter-independent-source-review-handoff.v1',
 'reviewer':r['reviewer'],'author':r['author'],'independent':True,'decision':r['decision'],'status':'STOPPED',
 'review_ref':pin(BASE/'review.json'),'verification_ref':v,
 'adapter_ref':r['adapter_ref'],'pipeline_ref':r['pipeline_ref'],'builder_ref':r['builder_ref'],
 'scope_template_ref':r['scope_template_ref'],'wrapper_refs':r['wrapper_refs'],
 'author_handoff_ref':r['author_handoff_ref'],'author_manifest_ref':r['author_manifest_ref'],
 'closed_findings':['W05-DIAGNOSTIC-R01'],'provenance_diagnostic_ref':r['provenance_diagnostic_ref'],
 'new_failure_origins':r['new_failure_origins'],'new_failure_count':1,
 'preserved_source_failure_origin_refs':r['preserved_source_failure_origin_refs'],'source_origin_recounted':False,
 'failed_prepare_ref':r['preserved_failed_prepare_ref'],'failed_prepare_retried':False,
 'actual_new_Root_REG_scope_CAS_grant':'OPEN','source_acceptance':False,'case_qualification':False,
 'formal_increment':0,'candidate_calls':0,'canonical_writes':0,
 'postseal_annex':{'path':str(BASE/'postseal-tool-observations.annex.json'),'included_in_manifest':False}})
members=[pin(p) for p in sorted(BASE.iterdir(),key=lambda p:p.name) if p.is_file()]
mf=save('manifest.json',{'schema':'researchos.independent-source-review-manifest.v1','members':members,'count':len(members),
 'self_excluded':True,'postseal_annex_excluded':True})
print(json.dumps({'review':pin(BASE/'review.json'),'handoff':h,'manifest':mf,'members':len(members),
 'failure_origins':r['new_failure_origins'],'new_failure_count':1,'decision':r['decision'],'status':'STOPPED'},ensure_ascii=False))
