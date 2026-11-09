import hashlib,json
from pathlib import Path
OWN=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_forward_head_revision_independent_review_codex/335dbe67cc9a4ab39d2ff274e3c6f26a').resolve()
def read_json(p): return json.loads(Path(p).read_bytes())
def digest(p):
 p=Path(p).resolve();b=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,value):
 p=(OWN/name).resolve()
 assert p.parent==OWN and not p.exists()
 p.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return digest(p)
r=read_json(OWN/'review.json');f=read_json(OWN/'facts.json')
author=read_json(r['author_handoff_ref']['path'])
mf=read_json(r['author_manifest_ref']['path'])
extra=read_json(author['static_audit_ref']['path'])
inp=read_json(Path(r['author_handoff_ref']['path']).parent/'inputs.final.json')
expected=[*mf['entries'],*inp['prior_inputs'],*inp['independent_request_refs'],*f['input_refs']]
expected += [x['expected'] for x in f['actual_compose']['direct_pin_checks']]
expected += [x['ref'] for x in f['actual_compose']['origin_facts']]
expected += [x['ref'] for x in f['new_source_pin_facts']['new_current_pin_facts']]
expected += [f['new_source_pin_facts']['tree_ref'],r['selected_engine_ref'],r['selected_builder_ref'],r['positive_composition']['actual_runtime_ref']] if 'actual_runtime_ref' in r['positive_composition'] else [f['new_source_pin_facts']['tree_ref'],r['selected_engine_ref'],r['selected_builder_ref']]
refs={}
for x in expected:
 p=str(Path(x['path']).resolve())
 assert p not in refs or (refs[p]['sha256'],refs[p]['bytes'])==(x['sha256'],x['bytes'])
 refs[p]=x
rows=[]
for p,x in sorted(refs.items()):
 actual=digest(p);rows.append({'expected':x,'actual':actual,'match':(x['sha256'],x['bytes'])==(actual['sha256'],actual['bytes'])})
assert all(x['match'] for x in rows)
pins=write('pins.after.json',{'schema':'researchos.narrow-source-review-pins.v1','expected_refs_from_actual_prior_metadata':True,'actual_hashed_unique':len(rows),'drift':[],'refs':rows,'full8986_or_full58_rehash':False,'candidate_executed':False})
review_ref=digest(OWN/'review.json');tool_ref=digest(OWN/'original-tool-io.json')
h=write('handoff.json',{'schema':'researchos.desktop58-forward-head-revision-independent-review-handoff.v1','actor':r['reviewer'],'decision':r['decision'],'status':'STOPPED','review_ref':review_ref,'readable_ref':digest(OWN/'review.md'),'facts_ref':digest(OWN/'facts.json'),'original_tool_io_ref':tool_ref,'pins_after_ref':pins,'selected_engine_ref':r['selected_engine_ref'],'selected_builder_ref':r['selected_builder_ref'],'root_request_ref':r['actual_root_request_ref'],'author_handoff_ref':r['author_handoff_ref'],'author_manifest_ref':r['author_manifest_ref'],'prior_REQUEST_refs':r['prior_independent_REQUEST_refs'],'new_failure_origins':[],'new_failure_origin_count':0,'candidate_import_or_execution':False,'actual_prepare_registration_Git_Job_CAS':0,'formal_increment':0,'source_acceptance':False,'OPEN':r['open_gates'],'external_postseal_observation_annex':'seal-tool-observation.json','external_annex_reason':'The final metadata sealer response is available only after manifest bytes are sealed; it is a separately pinned annex and is not recursively inserted into manifest.'})
entries=[digest(p) for p in sorted(OWN.iterdir()) if p.is_file() and p.name!='manifest.json']
m=write('manifest.json',{'schema':'researchos.independent-source-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True,'external_annex_excluded':'seal-tool-observation.json','formal_increment':0})
print(json.dumps({'decision':r['decision'],'review_ref':review_ref,'handoff_ref':h,'manifest_ref':m,'manifest_members':len(entries),'pins_hashed_unique':len(rows),'drift':0,'new_failure_origins':0,'candidate_executed':False,'STOPPED':True},ensure_ascii=False))
