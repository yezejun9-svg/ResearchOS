from pathlib import Path
import hashlib,json,sys
BASE=Path(sys.argv[1]).resolve()
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,obj):
 p=BASE/name
 if p.exists():raise RuntimeError('OWN_FILE_ALREADY_EXISTS:'+name)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return ref(p)
r=json.loads((BASE/'review.json').read_text(encoding='utf-8'))
source_manifest=json.loads(Path(r['source_manifest_ref']['path']).read_text(encoding='utf-8'))
checks=[]
for row in source_manifest['members']:
 a=ref(Path(row['path']));checks.append({'ref':row,'actual':a,'match':a['sha256']==row['sha256'] and a['bytes']==row['bytes']})
author_report_path=Path(r['source_preparation_ref']['path']).parent/'report.json'
author_report=json.loads(author_report_path.read_text(encoding='utf-8'))
for row in author_report['source_refs']:
 a=ref(Path(row['path']));checks.append({'ref':row,'actual':a,'match':a['sha256']==row['sha256'] and a['bytes']==row['bytes']})
for row in r['frozen_contracts']+[r['source_manifest_ref']]:
 a=ref(Path(row['path']));checks.append({'ref':row,'actual':a,'match':a['sha256']==row['sha256'] and a['bytes']==row['bytes']})
if not all(x['match'] for x in checks):raise RuntimeError('FROZEN_REF_CHANGED')
verification=write('frozen-refs.verified.json',{'schema':'researchos.w09-readonly-ref-verification.v1','checks':checks,'drift':0,'candidate_executions':0,'native_product_executions':0})
obs=json.loads((BASE/'original-tool-observations.json').read_text(encoding='utf-8'))
h=write('handoff.json',{'schema':'researchos.w09-formal-binding-independent-source-handoff.v1','decision':r['decision'],'reviewer_id':r['reviewer_id'],'review_ref':ref(BASE/'review.json'),'report_ref':ref(BASE/'REPORT.md'),'verified_refs_ref':verification,'original_tool_observations_ref':ref(BASE/'original-tool-observations.json'),'producer_source_manifest_ref':r['source_manifest_ref'],'requested_changes':[x['id'] for x in r['findings']],'actual_metadata_status':'READONLY_SOURCE_REVIEW_COMPLETE','new_metadata_failure_origins':0,'inherited_origin_recount':0,'candidate_execution':0,'source_acceptance':False,'formal_case_accepted_delta':0,'canonical_mutations':0,'namespace_final_state':'STOPPED_AFTER_SEAL','execution_authority':'NONE','next_root_action':'NEW_IMMUTABLE_SOURCE_REVISION_AND_INDEPENDENT_REVIEW; ROOT_OWNED_BINDING_AND_ACTUAL_EVIDENCE_REQUIRED'})
members=[ref(p) for p in sorted(BASE.iterdir()) if p.is_file() and p.name!='manifest.json']
m=write('manifest.json',{'schema':'researchos.independent-source-review-manifest.v1','stage':'SOURCE_ONLY_NON_AUTHOR_REVIEW','self_excluded':True,'members_count':len(members),'members':members,'excluded_annex_names':['postseal.original-tool-annex.json']})
print(json.dumps({'namespace':str(BASE),'review':ref(BASE/'review.json'),'handoff':h,'manifest':m,'report':ref(BASE/'REPORT.md'),'members_count':len(members),'frozen_refs_checks':len(checks),'frozen_refs_drift':0,'new_metadata_origins':0,'namespace_state':'STOPPED_AFTER_SEAL'},ensure_ascii=False))

