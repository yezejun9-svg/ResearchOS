import hashlib,json
from pathlib import Path
OWN=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/fresh58_cli2_controller_independent_source_review_codex/931535caab7d4a72b5ab4e2e1d40355e').resolve()
def doc(p): return json.loads(Path(p).read_bytes())
def ref(p):
 p=Path(p).resolve();b=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,d):
 p=OWN/name;assert p.parent==OWN and not p.exists()
 p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));return ref(p)
r=doc(OWN/'review.json');source=Path(r['author_handoff_ref']['path']).parent
mf=doc(r['author_manifest_ref']['path'])
expected=[*mf['entries'],*doc(source/'inputs.final.json'),*doc(source/'supplemental-read-inputs.json'),r['author_manifest_ref']]
root=Path(r'D:/作品集/ResearchOS/research-os');rows={}
for x in expected:
 p=Path(x['path']);p=p if p.is_absolute() else root/p;a=ref(p);assert (a['sha256'],a['bytes'])==(x['sha256'],x['bytes'])
 rows[str(p.resolve())]={'expected':x,'actual':a}
pins=write('pins.after.json',{'unique_actual_hash_checks':len(rows),'drift':[],'rows':list(rows.values()),'candidate_executed':False})
rr=ref(OWN/'review.json')
h=write('handoff.json',{'schema':'researchos.fresh58-cli2-independent-source-review-handoff.v1','actor':r['reviewer'],'decision':r['decision'],'status':'STOPPED','review_ref':rr,'readable_ref':ref(OWN/'review.md'),'original_tool_io_ref':ref(OWN/'original-tool-io.json'),'pins_after_ref':pins,'source_handoff_ref':r['author_handoff_ref'],'source_manifest_ref':r['author_manifest_ref'],'requested_changes':r['requested_changes'],'runner_ref':r['runner_ref'],'gate_ref':r['authorization_gate_ref'],'actual_source_adoption_or_execution':False,'formal_increment':0,'source_acceptance':False,'new_failure_origins':[],'external_postseal_annex':'seal-tool-observation.json','external_annex_reason':'Final metadata sealer response exists after manifest; separately pinned without recursive self hash.'})
items=[ref(p) for p in sorted(OWN.iterdir()) if p.is_file() and p.name!='manifest.json']
m=write('manifest.json',{'schema':'researchos.independent-source-review-manifest.v1','entries':items,'count':len(items),'self_excluded':True,'external_annex_excluded':'seal-tool-observation.json','formal_increment':0})
print(json.dumps({'decision':r['decision'],'review_ref':rr,'handoff_ref':h,'manifest_ref':m,'members':len(items),'input_unique_hash_checks':len(rows),'drift':0,'new_origins':0,'candidate_executed':False,'STOPPED':True},ensure_ascii=False))
