from pathlib import Path
import json
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
d=json.loads((O/'inspection.json').read_bytes());e=d['evidence_refs']
def read(r):
 p=Path(r['path']);return json.loads((p if p.is_absolute() else R/p).read_bytes())
s=read(e['scope_ref']);rt=read(e['root_completion_ref']);request=read(rt['closure_request_ref'])
for c in d['case_details']:
 print(json.dumps({'case':c['fact']['case_id'],'fact_keys':list(c['fact']),'invocation_keys':list(c['invocation']),'request_keys':list(c['invocation']['request']),'result_keys':list(c['invocation']['result']),'verified_shape':c['verified_shape']},ensure_ascii=False))
for key in ['executor_manifest_ref','launcher_manifest_ref']:
 m=read(e[key]);print(json.dumps({'manifest':key,'keys':list(m),'rows':[r for r in m['files'] if key=='launcher_manifest_ref' or Path(r['path']).name.startswith('case-')]},ensure_ascii=False))
print(json.dumps({'runner':s['runner_ref'],'launcher':s['launcher_ref'],'rootkeys':list(rt),'root_request':request,'caller':read(request['caller_invocation_ref']),'root_completed':read(e['launcher_completed_ref'])},ensure_ascii=False))
