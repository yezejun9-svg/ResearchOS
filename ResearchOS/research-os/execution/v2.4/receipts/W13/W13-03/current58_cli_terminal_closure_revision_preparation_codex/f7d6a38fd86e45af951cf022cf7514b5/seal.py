import ast
import hashlib
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def ref(p):
    raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,x):
    with (OUT/n).open('xb') as f:
        f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
inputs=json.loads((OUT/'inputs.before.json').read_bytes())
assert all(ref(Path(r['path']))==r for r in inputs)
for p in OUT.glob('*.py'):
    ast.parse(p.read_bytes())
save('handoff.json',{'schema':'researchos.current58-root-terminal-closure-source-revision.v1','author':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_STOPPED','selected_ref':ref(OUT/'close-root-launch.current58.v2.proposed.py'),'review_request_ref':inputs[5],'old_source_ref':inputs[0],'inverse_ref':ref(OUT/'two-hunk.inverse.json'),'audit_ref':ref(OUT/'static-audit.json'),'contract_ref':ref(OUT/'contract.json'),'tool_observations_ref':ref(OUT/'tool-observations.json'),'fixed_findings':['C58-CLOSE-R01','C58-CLOSE-R02'],'exact_hunks':2,'input_drift_count':0,'unchanged_original_definitions':9,'completion_publication_tail_unchanged':True,'candidate_imports':0,'candidate_calls':0,'current_E_L_export_caller_reads':0,'new_failure_origins':[],'source_acceptance':False,'case_qualification':False,'formal_increment':0,'OPEN':['Non-author narrow source review','Root actual immutable request and once metadata invocation','Separate W05 actual current58 two-case qualification']})
rows=[ref(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'schema':'researchos.source-preparation-manifest.v1','members':rows,'count':len(rows),'excluded_only_self':True})
print(json.dumps({'handoff_ref':ref(OUT/'handoff.json'),'manifest_ref':ref(OUT/'manifest.json'),'selected_ref':ref(OUT/'close-root-launch.current58.v2.proposed.py'),'members':len(rows)},ensure_ascii=False))
