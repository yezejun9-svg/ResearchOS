import json, runpy, sys, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HARNESS=ROOT/'fixture_e2e_r2.py'
field=sys.argv[1]
assert field in ('native_exit_code','native_wait_result')
changes=[]
def profile(frame,event,arg):
    if event=='call' and frame.f_code.co_name=='write_json' and Path(frame.f_code.co_filename)==HARNESS:
        p=frame.f_locals.get('path'); v=frame.f_locals.get('value')
        if p.name in ('worker_native_exit.json','verifier_native_exit.json'):
            assert field in v
            changes.append({'path':str(p),'field':field,'removed_value':v.pop(field)})
sys.setprofile(profile)
try:
    result=runpy.run_path(str(HARNESS),run_name='__main__')
finally:
    sys.setprofile(None)
    (ROOT/('negative-'+field+'-mutation.json')).write_text(json.dumps(changes,indent=2),encoding='utf-8')
case=Path(result['CASE'])
r=json.loads((case/'case-result.json').read_text())
observation={'field_deleted':field,'changes':changes,'case':str(case),'result':r['result'],'unsafe_acceptance_reproduced':r['result']['state']=='STOPPED_LEASE_VERIFIED' and r['result']['native']['terminate_calls']==1,'synthetic_only':True,'source_modified':False}
(ROOT/('negative-'+field+'-result.json')).write_text(json.dumps(observation,indent=2),encoding='utf-8')
print(json.dumps(observation))