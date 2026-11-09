import json
from pathlib import Path
Q=Path(__file__).resolve().parent
sections=json.loads((Q/'actual-contract-excerpts.json').read_text(encoding='utf-8'))
for family,selected in [('profile',{'_independent','_global','_review_execution_cutoff','verify_owner','_root_original','_capture_registry','_independent_roles'}),('bridge',{'assemble','capture','check','derive'})]:
    for item in sections[family]:
        if item.get('function')in selected:
            print(family+' '+item['function']+':'+str(item['line']))
            print(item['source'])
print('ROOT_PYTHON_EXIT=0')
