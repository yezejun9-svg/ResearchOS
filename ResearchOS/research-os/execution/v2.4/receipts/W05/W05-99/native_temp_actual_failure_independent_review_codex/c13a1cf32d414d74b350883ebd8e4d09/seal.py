import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
d=json.loads((O/'review.json').read_bytes());g=json.loads((O/'guard-closure.json').read_bytes())
assert d['decision']=='LIMITED_FAILED_EXECUTION_WHOLE_SQL_SPECIFIC_RELEASE_ACCEPTED' and len(d['checks'])==55 and all(x['passed'] for x in d['checks'])
assert g['closed'] and g['verification']=='PASSED' and g['retained_handles_count']==0 and not g['errors']
r=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-temp-failed-root-release-1791509915469/original-root-native-tool-io.json')
b=r.read_bytes();assert len(b)==28903 and hashlib.sha256(b).hexdigest()=='e1e34f4c272493186c01f9e496fe66ccb3db6179c68b79ccd17e90cf943880d1'
with (O/'original-root-native-tool-io.json').open('xb') as f:f.write(b)
h={'schema':'researchos.independent-native-temp-actual-failure-handoff.v1','authority':'NONE','formal_acceptance':False,'decision':d['decision'],'namespace':str(O),'checks_passed':55,'checks_total':55,'guarded_public_inputs':58,'all_guards_closed':True,'historical_failed_execution_whole_SQL_specific_release_accepted':True,'native_positive_accepted':False,'Owner_nine_original_business_formal_accepted':False,'global_provider_requests':None,'formal_progress':'0/42','new_mechanical_errors':1,'new_failure_ordinals':[869],'history_reset':False,'original_actual_failure_ordinal':868,'database_live_currently_available':False,'canonical_Source_Main_writes':False,'stop':True}
for n in ['report.md','review.json','guard-closure.json','input-pins.json','actual-owned-jobs.json','canonical-short-pins.json','historical-guard-summary.json','original-tool-io.json','original-root-native-tool-io.json','failure-origin.869.json']:h[n.replace('.','_')+'_ref']=pin(O/n)
save('HDF.json',h)
files=sorted(p for p in O.iterdir() if p.is_file() and p.name not in ['MF.json','postseal-tool-io.json'])
save('MF.json',{'schema':'researchos.independent-native-temp-actual-failure-manifest.v1','authority':'NONE','formal_acceptance':False,'members':[{'relative_path':p.name,**pin(p)} for p in files],'exclusions_exact_relative_paths':['MF.json','postseal-tool-io.json']})
print(json.dumps({'HDF':pin(O/'HDF.json'),'MF':pin(O/'MF.json'),'member_count':len(files)},ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0')

