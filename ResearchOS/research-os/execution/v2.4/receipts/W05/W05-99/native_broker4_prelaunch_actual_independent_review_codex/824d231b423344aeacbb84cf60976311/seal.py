import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib
O=pathlib.Path(__file__).resolve().parent;Q=O/'revision-crlf-role'
B=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
r=json.loads((Q/'review.json').read_bytes());assert r['decision']=='COMPONENT_ACCEPTED_PRELAUNCH_CONDITIONAL' and len(r['checks'])==77 and all(x['passed'] for x in r['checks'])
for p in [O/'guard-closure.json',O/'revision-rawpin-shape/guard-closure.json',Q/'guard-closure.json']:
 g=json.loads(p.read_bytes());assert g['closed'] and g['verification']=='PASSED' and g['retained_handles_count']==0 and not g['errors']
pins={x['path']:x for x in json.loads((Q/'input-pins.json').read_bytes())}
for rel,dest in [('integration_codex/python-broker4-public-units-root-1791512710000/original-root-tool-io.json','original-root-U10-tool-io.json'),('integration_codex/native-broker4-controller-config-root-1791513411000/original-root-tool-io.json','original-root-C10-tool-io.json')]:
 p=B/rel;assert pin(p)==pins[str(p)]
 with (O/dest).open('xb') as f:f.write(p.read_bytes())
h={'schema':'researchos.independent-broker4-public17-prelaunch-handoff.v1','decision':r['decision'],'authority':'NONE','formal_acceptance':False,'namespace':str(O),'checks_passed':77,'checks_total':77,'guarded_public_inputs':4560,'all_guards_closed':True,'actual_public17_component_accepted':True,'fresh_C10_fixed_callers_prelaunch_conditionally_accepted':True,'Root_may_one_fresh_precisely_approved_synthetic_positive':True,'auto_signing_authority':False,'native_positive_Owner_nine_original_business_formal_accepted':False,'global_provider_requests':None,'original_trial_provider_requests':None,'formal_progress':'0/42','new_mechanical_errors':2,'new_failure_ordinals':[889,891],'history_reset':False,'Main_canonical_Source_writes':False,'stop':True}
for n in ['report.md','original-tool-io.json','original-root-U10-tool-io.json','original-root-C10-tool-io.json','failure-origin.889.json','failure-origin.891.json','revision-crlf-role/review.json','revision-crlf-role/input-pins.json','revision-crlf-role/guard-closure.json','revision-crlf-role/actual-unit-owned-job.json','revision-crlf-role/canonical-pins.json','revision-crlf-role/unit-proof-freeze-scope.json','revision-crlf-role/builder-literal-adaptations.json','revision-crlf-role/builder-exact.diff','revision-rawpin-shape/review.json']:
 h[n.replace('/','_').replace('.','_')+'_ref']=pin(O/n)
save('HDF.json',h)
files=sorted(p for p in O.rglob('*') if p.is_file() and p.relative_to(O).as_posix() not in ['MF.json','postseal-tool-io.json'])
save('MF.json',{'schema':'researchos.independent-broker4-public17-prelaunch-manifest.v1','authority':'NONE','formal_acceptance':False,'members':[{'relative_path':p.relative_to(O).as_posix(),**pin(p)} for p in files],'exclusions_exact_relative_paths':['MF.json','postseal-tool-io.json']})
print(json.dumps({'HDF':pin(O/'HDF.json'),'MF':pin(O/'MF.json'),'member_count':len(files)},ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0')

