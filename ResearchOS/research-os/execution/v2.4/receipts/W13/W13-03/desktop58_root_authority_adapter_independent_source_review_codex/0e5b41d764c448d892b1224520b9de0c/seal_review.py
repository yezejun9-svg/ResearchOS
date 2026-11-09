import pathlib,json,hashlib
N=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_root_authority_adapter_independent_source_review_codex/0e5b41d764c448d892b1224520b9de0c')
def ref(p):
 b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
r=ref(N/'review.json');o=ref(N/'failure-origin.communication-thread-limit.json')
h={'schema':'researchos.independent-source-review-handoff.v1','owner':'codex:/root/f08_whole_scope_review','decision':'REQUEST_CHANGES','review_ref':r,'manifest_path':(N/'manifest.json').as_posix(),'manifest_self_excluded':True,'new_failure_origin_refs':[o],'new_metadata_nonzero_count':0,'new_nullable_tool_failure_count':1,'failed_input_retries':0,'canonical_writes':0,'candidate_calls':0,'source_acceptance':False,'execution_authorized':False,'formal_increment':0,'frozen_cut_532_untouched':True,'external_postseal_annex':{'path':(N/'external-tool-annex.json').as_posix(),'excluded_from_manifest':True,'reason':'Actual own metadata sealer and final verification tool responses are explicit postseal annex; avoids hash cycle.'},'status':'STOPPED'}
(N/'handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
es=[ref(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ['manifest.json','external-tool-annex.json']]
m={'schema':'researchos.independent-review-manifest.v1','entries':es,'count':len(es),'self_excluded':True,'explicit_external_annex':(N/'external-tool-annex.json').as_posix()}
(N/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'review_ref':r,'handoff_ref':ref(N/'handoff.json'),'manifest_ref':ref(N/'manifest.json'),'manifest_members':len(es),'failure_origin_ref':o,'decision':'REQUEST_CHANGES','new_metadata_nonzero_count':0,'new_nullable_tool_failure_count':1,'status':'STOPPED'},ensure_ascii=False))
