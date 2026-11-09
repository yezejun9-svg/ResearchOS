import pathlib,json,hashlib
ROOT=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/fresh58_public_source_publication_independent_review_codex/66b4835ecfe240cca4e481900d9897a7')
def ref(p):
 b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
review=ref(ROOT/'review.json');origins=[ref(ROOT/('failure-origin.'+x+'.json')) for x in ['0cd8b6','26bc6d']]
handoff={'schema':'researchos.independent-source-metadata-publication-handoff.v1','owner':'codex:/root/f08_whole_scope_review','decision':'SOURCE_METADATA_PUBLICATION_EVIDENCE_CLOSED','review_ref':review,'manifest_path':(ROOT/'manifest.json').as_posix(),'manifest_self_excluded':True,'new_failure_origin_refs':origins,'new_metadata_nonzero_count':2,'metadata_failed_programs_rerun':0,'canonical_writes':0,'product_native_calls':0,'source_acceptance':False,'execution_authorized':False,'formal_increment':0,'future_qualification':'OPEN','external_postseal_annex':{'path':(ROOT/'external-tool-annex.json').as_posix(),'excluded_from_manifest':True,'reason':'Original sealing tool result and final verification tool observations generated after manifest closure; explicit annex avoids hash cycle.'},'status':'STOPPED'}
(ROOT/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
entries=[ref(p) for p in sorted(ROOT.iterdir()) if p.is_file() and p.name not in ['manifest.json','external-tool-annex.json']]
manifest={'schema':'researchos.independent-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True,'explicit_external_annex':(ROOT/'external-tool-annex.json').as_posix()}
(ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'review_ref':review,'handoff_ref':ref(ROOT/'handoff.json'),'manifest_ref':ref(ROOT/'manifest.json'),'manifest_members':len(entries),'new_failure_origin_refs':origins,'decision':handoff['decision'],'status':'STOPPED'},ensure_ascii=False))
