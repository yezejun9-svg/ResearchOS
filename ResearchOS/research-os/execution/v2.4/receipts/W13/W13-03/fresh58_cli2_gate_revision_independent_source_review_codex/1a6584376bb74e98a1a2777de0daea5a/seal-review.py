import hashlib,json
from pathlib import Path
OWN=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/fresh58_cli2_gate_revision_independent_source_review_codex/1a6584376bb74e98a1a2777de0daea5a').resolve()
def doc(p):return json.loads(Path(p).read_bytes())
def ref(p):
 p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,d):
 p=OWN/name;assert p.parent==OWN and not p.exists();p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));return ref(p)
r=doc(OWN/'review.json');src=Path(r['author_handoff_ref']['path']).parent;mf=doc(r['author_manifest_ref']['path']);refs=[*mf['entries'],*doc(src/'inputs.final.json'),r['author_manifest_ref'],r['positive_composition']['actual_request_ref']]
seen={}
for x in refs:
 a=ref(x['path']);assert (a['sha256'],a['bytes'])==(x['sha256'],x['bytes']);seen[a['path']]={'expected':x,'actual':a}
pins=write('pins.after.json',{'unique_actual_hashes':len(seen),'drift':[],'rows':list(seen.values()),'old44_full_rehash':False,'candidate_executed':False})
rr=ref(OWN/'review.json')
h=write('handoff.json',{'schema':'researchos.fresh58-cli2-gate-revision-independent-review-handoff.v1','actor':r['reviewer'],'decision':r['decision'],'status':'STOPPED','review_ref':rr,'readable_ref':ref(OWN/'review.md'),'original_tool_io_ref':ref(OWN/'original-tool-io.json'),'pins_after_ref':pins,'gate_ref':r['selected_gate_ref'],'scope_ref':r['selected_scope_ref'],'runner_ref':r['runner_ref'],'launcher_ref':r['launcher_ref'],'author_handoff_ref':r['author_handoff_ref'],'author_manifest_ref':r['author_manifest_ref'],'prior_REQUEST_refs':r['prior_independent_REQUEST_refs'],'closed_source_findings':['F58-R01-FORWARD-TUPLE-RELATION','F58-R02-ACCEPTED-UNION-MEMBERSHIP'],'requested_changes':[],'actual_Root_execution_authority_or_source_acceptance':False,'formal_increment':0,'candidate_executed':False,'new_failure_origins':[],'OPEN':r['open_gates'],'external_postseal_annex':'seal-tool-observation.json','external_annex_reason':'Final metadata sealer response is separately pinned after immutable MF, avoiding a self-hash cycle.'})
entries=[ref(p) for p in sorted(OWN.iterdir()) if p.is_file() and p.name!='manifest.json']
m=write('manifest.json',{'schema':'researchos.independent-source-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True,'external_annex_excluded':'seal-tool-observation.json','formal_increment':0})
print(json.dumps({'decision':r['decision'],'review_ref':rr,'handoff_ref':h,'manifest_ref':m,'members':len(entries),'input_unique_hashes':len(seen),'drift':0,'new_origins':0,'candidate_executed':False,'STOPPED':True},ensure_ascii=False))
