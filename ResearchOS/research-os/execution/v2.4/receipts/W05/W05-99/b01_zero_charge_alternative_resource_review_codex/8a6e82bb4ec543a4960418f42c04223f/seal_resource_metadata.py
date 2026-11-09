from pathlib import Path
import hashlib,json,sys
BASE=Path(sys.argv[1]).resolve()
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,obj):
 p=BASE/name
 if p.exists():raise RuntimeError('OWN_FILE_EXISTS:'+name)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return ref(p)
d=json.loads((BASE/'report.json').read_text(encoding='utf-8'))
refs=[d['basis_ref'],d['historical_metadata']['ref'],d['pinned_public_source']['ref'],d['frozen_case_compatibility']['tasks_ref'],d['frozen_case_compatibility']['acceptance_ref']]
checks=[]
for row in refs:
 a=ref(Path(row['path']));checks.append({'ref':row,'actual':a,'match':a['sha256']==row['sha256'] and a['bytes']==row['bytes']})
if not all(x['match'] for x in checks):raise RuntimeError('PIN_DRIFT')
v=write('readonly-refs.verified.json',{'schema':'researchos.b01-resource-readonly-ref-check.v1','checks':checks,'drift':0})
h=write('handoff.json',{'schema':'researchos.b01-zero-charge-alternative-resource-handoff.v1','decision':d['decision'],'report_ref':ref(BASE/'report.json'),'human_report_ref':ref(BASE/'REPORT.md'),'verification_ref':v,'original_tool_observations_ref':ref(BASE/'original-tool-observations.json'),'new_failure_origins':[ref(BASE/d['failure_origin_name'])],'new_origin_count':1,'old_origin_recount':0,'strict_per_request_usd_upper':None,'model_provider_calls':0,'canonical_mutations':0,'formal_accepted_delta':0,'qualification':False,'next_owner_action':'Root seeks exact all-inclusive free deployment contract; preserve B01 LIVE block and continue FIXTURE; no speculative model call','namespace_state':'STOPPED_AFTER_SEAL'})
members=[ref(p) for p in sorted(BASE.iterdir()) if p.is_file() and p.name!='manifest.json']
m=write('manifest.json',{'schema':'researchos.resource-independent-review-manifest.v1','members_count':len(members),'members':members,'self_excluded':True,'excluded_annex_names':['postseal.original-tool-annex.json']})
print(json.dumps({'report':ref(BASE/'report.json'),'handoff':h,'manifest':m,'failure_origin':ref(BASE/d['failure_origin_name']),'members_count':len(members),'drift':0,'new_failure_count':1,'model_calls':0},ensure_ascii=False))

