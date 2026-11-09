import json,hashlib,re
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
O=Path(__file__).parent
OLD=O.parent/'5aaf107a30464fda89765e7d6228ac27'
N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-72ff32d0d24a42c4a8effd849d54f882'
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def ref(p):
 b=path(p).read_bytes();return {'path':str(path(p)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(path(p).read_bytes())
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(O/n)
C=[]
def ck(n,v):C.append({'check':n,'passed':bool(v)})
def verify(r):
 a=ref(r['path']);ck('pin '+r['path'],a['sha256']==r['sha256'] and a['bytes']==r['bytes'])
 return path(r['path']).read_bytes()
prior=read(OLD/'review.json')
ck('preserved prior sealed review',ref(OLD/'review.json')['sha256']=='6b42a8b2311ddb6336602f91909213d1deea390d0025ad7963e73936bfc0dacb')
mf=read(OLD/'manifest.json')
ck('prior manifest pin',ref(OLD/'manifest.json')['sha256']=='0ed3cf155cb3b39a44614b8ebfe35d77a714eecda22b0d074a44279208d6f2e3')
ck('prior manifest cardinality',mf['count']==len(mf['entries']) and mf['self_excluded'] is True)
for r in mf['entries']:verify(r)
a=read(prior['audit_ref']['path']);u=read(prior['compatibility_supplement_ref']['path'])
ck('main and compatibility actual passed',a['failed']==[] and u['failed']==[] and len(a['checks'])==24809 and len(u['checks'])==60)
oldguards=read(prior['final_guards_ref']['path'])
ck('only original false predicate',oldguards['failed']==[{'check':'original metadata tool status 2e7202','passed':False}])
obs=read(prior['Root_actual_prepare_tool_observation_ref']['path'])
verify(prior['Root_actual_prepare_tool_observation_ref'])
facts=[]
for row in obs['records']:
 z=row['result'];lines=re.findall(r'^ACTUAL_PYTHON_EXIT=(-?\d+)\r?$',z['output'],re.M)
 facts.append({'kind':row['kind'],'chunk_id':z['chunk_id'],'outer_exit':z.get('exit_code'),'standalone_Python_exit_markers':lines})
 ck('actual standalone status '+z['chunk_id'],z.get('exit_code') in (None,0) and (lines==['0'] if z.get('exit_code')==0 else lines==[]))
late=next(x for x in obs['records'] if x['result']['chunk_id']=='2e7202')
payload,end=json.JSONDecoder().raw_decode(late['result']['output'])
tail=late['result']['output'][end:]
ck('late reader tail precisely own bridge',tail.strip()=='ACTUAL_PYTHON_EXIT=0' and late['result']['exit_code']==0)
ck('late reader actual command bridges LASTEXITCODE',"$actualNativeExit=$LASTEXITCODE" in late['input']['cmd'] and "exit $actualNativeExit" in late['input']['cmd'])
hist=[x for x in payload if isinstance(x,dict) and x.get('object',{}).get('schema')=='researchos.tool-failure-origin.v1']
ck('two historical failures remain numeric1',len(hist)==2 and all(x['object']['actual_python_exit']==1 and x['object']['outer_tool_exit']==1 for x in hist))
p=read(N/'prepared_refs.json');b=read(N/'binding.json')
for name,key in [('register.py','register_sha256'),('run.py','wrapper_sha256'),('prepared_refs.json','prepared_refs_sha256'),('audit.json','audit_sha256')]:
 ck('unchanged candidate '+name,ref(N/name)['sha256']==prior[key])
verify(prior['binding_ref']);verify(prior['scope_ref']);verify(prior['sealer_ref']);verify(prior['grant_producer_ref'])
ck('same exact scope dictionary',p['scope_ref']==prior['scope_ref']==u['scope_ref'] and not Path(p['scope_ref']['path']).is_absolute())
s=read(p['scope_ref']['path'])
ck('same intended tuple',p['expected_before']==[334,162,532] and p['expected_after']==[335,163,580])
ck('canonical exact prepared order',prior['canonical_before']==p['canonical_before'] and len(p['canonical_before'])==4)
copies=[]
for i,(live,original,oldcopy) in enumerate(zip(p['canonical_before'],p['original_refs'],prior['copied_canonical_before_refs'])):
 lb=verify(live);ob=verify(original);cb=verify(oldcopy)
 ck('live original oldcopy exact '+str(i),lb==ob==cb)
 cp=O/('canonical-before-'+str(i)+'.json')
 with cp.open('xb') as f:f.write(lb)
 copies.append(ref(cp))
 ck('fresh owncopy exact '+str(i),cp.read_bytes()==lb and cp.parent==O)
for k in ['output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root']:
 ck('future absent '+k,not path(s[k]).exists())
ck('registration outputs absent',all(not (N/x).exists() for x in ['invocation.json','canonical-write.intent.json','registration-audit.json']))
failed=[x for x in C if not x['passed']]
correction=save('correction-and-final-guards.json',{'schema':'researchos.readonly-audit-predicate-correction.v1','checks':C,'failed':failed,'prior_review_ref':ref(OLD/'review.json'),'prior_manifest_ref':ref(OLD/'manifest.json'),'prior_handoff_ref':ref(OLD/'handoff.json'),'original_predicate':'Unanchored regex scanned serialized historical tool output and misclassified two historical Python1 markers as current tool status.','corrected_predicate':'Anchored standalone bridge line plus actual result.exit_code; separately parse the JSON prefix and preserve historical origin values.','actual_tool_facts':facts,'historical_origin_refs':[x['ref'] for x in hist],'historical_origin_count_unchanged':True,'prior_audit_tool_exit':0,'prior_sealer_tool_exit':0,'new_failure_count':0})
v=dict(prior)
v.update(decision='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' if not failed else 'REQUEST_CHANGES',requested_changes=failed,copied_canonical_before_refs=copies,final_guards_ref=correction,Root_actual_prepare_tool_facts=facts,tool_observations_ref=ref(O/'tool-observations.before-seal.json'))
v['checks']={'main_reused':24809,'compatibility_reused':60,'narrow_correction_and_final_checks':len(C),'failed':len(failed)}
v['supersedes_static_false_positive_only']={'prior_review_ref':ref(OLD/'review.json'),'prior_manifest_ref':ref(OLD/'manifest.json'),'old_bytes_unchanged':True,'does_not_reexecute_candidate':True}
v['remaining_conditions']=prior['remaining_conditions']
rv=save('review.json',v)
h=save('handoff.json',{'schema':'researchos.independent-review-handoff.v1','reviewer':v['reviewer'],'decision':v['decision'],'review_ref':rv,'correction_ref':correction,'reused_audit_ref':v['audit_ref'],'reused_compatibility_ref':v['compatibility_supplement_ref'],'new_failure_count':0,'new_failure_origins':[],'actual_registration_executed':False,'status':'STOPPED','manifest_filename':'manifest.json'})
entries=[ref(x) for x in sorted(O.iterdir()) if x.is_file() and x.name!='manifest.json']
m=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True})
print(json.dumps({'decision':v['decision'],'checks':v['checks'],'review_ref':rv,'manifest_ref':m,'handoff_ref':h,'failed':failed,'new_failure_count':0},ensure_ascii=False))

