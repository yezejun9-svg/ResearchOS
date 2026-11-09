import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent
P=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/native_python_broker_temp_env_revision_codex/7bc2467624af477a8d55e0595ec4a7c2')
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
d=json.loads((O/'source-check.json').read_bytes());g=json.loads((O/'guard-closure.json').read_bytes());s=json.loads((O/'semantic-review.json').read_bytes())
assert len(d['checks'])==87 and all(x['passed'] for x in d['checks']) and s['decision']=='SOURCE_ONLY_ACCEPTED_WITH_EXPLICIT_LIMITATIONS'
assert g['closed'] and g['verification']=='PASSED' and g['retained_handles_count']==0 and not g['errors']
pins={r['path']:r for r in json.loads((O/'input-pins.json').read_bytes())}
for n,dest in [('original-tool-io.json','source-author-original-tool-io.json'),('postseal-tool-io.json','source-author-postseal-tool-io.json')]:
 p=P/n;assert pin(p)==pins[str(p)]
 with (O/dest).open('xb') as f:f.write(p.read_bytes())
h={'schema':'researchos.independent-broker-temp-env-source-handoff.v1','decision':'SOURCE_ACCEPTED_PENDING_ROOT_BOUNDARY_ACTUAL','authority':'NONE','formal_acceptance':False,'namespace':str(O),'source_packet':str(P),'checks_passed':87,'checks_total':87,'guarded_public_inputs':46,'all_guards_closed':True,'semantic_review_model':'gpt-6-astra','semantic_review_reasoning_effort':'high','boundary_actual':'NOT_RUN','Root_native_actual':'NOT_RUN','native_positive_Owner_nine_original_business_formal_accepted':False,'canonical_Source_Main_Tstar_writes':False,'new_mechanical_errors':0,'history_reset':False,'global_provider_requests':None,'formal_progress':'0/42','stop':True}
for n in ['report.md','source-check.json','semantic-review.json','guard-closure.json','input-pins.json','canonical-short-pins.json','original-tool-io.json','source-author-original-tool-io.json','source-author-postseal-tool-io.json','recovered-base.py']:h[n.replace('.','_')+'_ref']=pin(O/n)
save('HDF.json',h)
files=sorted(p for p in O.iterdir() if p.is_file() and p.name not in ['MF.json','postseal-tool-io.json'])
save('MF.json',{'schema':'researchos.independent-broker-temp-env-source-manifest.v1','authority':'NONE','formal_acceptance':False,'members':[{'relative_path':p.name,**pin(p)} for p in files],'exclusions_exact_relative_paths':['MF.json','postseal-tool-io.json']})
print(json.dumps({'HDF':pin(O/'HDF.json'),'MF':pin(O/'MF.json'),'member_count':len(files)},ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0')

