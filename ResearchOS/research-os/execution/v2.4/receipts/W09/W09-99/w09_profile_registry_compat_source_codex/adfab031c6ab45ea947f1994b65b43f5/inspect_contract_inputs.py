import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
import traceback

Q=Path(__file__).resolve().parent
def refs(value,pointer=''):
    rows=[]
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:
            rows.append({'pointer':pointer,'ref':value})
        for key,child in value.items():
            rows.extend(refs(child,pointer+'/'+str(key)))
    elif isinstance(value,list):
        for index,child in enumerate(value):
            rows.extend(refs(child,pointer+'/'+str(index)))
    return rows
def main():
    cm=json.loads((Q/'inputs/commands.CM39.before.json').read_text(encoding='utf-8'))
    decision=json.loads((Q/'inputs/C19_reusable_actual_decision.json').read_text(encoding='utf-8'))
    gap=json.loads((Q/'inputs/Source-gap-report.json').read_text(encoding='utf-8'))
    mode=json.loads((Q/'inputs/C19_actual_mode_actor_evidence.json').read_text(encoding='utf-8'))
    print(json.dumps({'CM_top_keys':sorted(cm),'revision':cm.get('revision'),'commands':{key:cm['commands'][key] for key in ('test.retrieval','test.research.fixture','test.security')},'decision_top_keys':sorted(decision),'decision_refs':refs(decision),'mode':mode,'gap_gaps':gap['gaps'],'gap_route_matrix':gap['route_matrix'],'gap_next_source_tasks':gap['next_source_tasks']},ensure_ascii=False))
code=0
try:
    main()
except Exception:
    traceback.print_exc();code=1
print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)
