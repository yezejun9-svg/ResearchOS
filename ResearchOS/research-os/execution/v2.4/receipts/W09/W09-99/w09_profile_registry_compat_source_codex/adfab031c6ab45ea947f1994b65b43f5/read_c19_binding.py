import sys
sys.dont_write_bytecode=True
import importlib.util
import json
from pathlib import Path
import traceback

Q=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('w09_read_inputs',Q/'read_inputs.py')
lib=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

def refs(value,pointer=''):
    rows=[]
    if isinstance(value,dict):
        if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str):
            rows.append({'pointer':pointer,'ref':value})
        for key,child in value.items():
            rows.extend(refs(child,pointer+'/'+str(key)))
    elif isinstance(value,list):
        for index,child in enumerate(value):
            rows.extend(refs(child,pointer+'/'+str(index)))
    return rows

def main():
    decision=json.loads((Q/'inputs/C19_reusable_actual_decision.json').read_text(encoding='utf-8'))
    discovery=json.loads((Q/'input-discovery.json').read_text(encoding='utf-8'))
    guard=lib.Guard()
    finished=False
    try:
        docs={}
        for label in ('consumer_summary_ref','caller_closed_ref','historical_attribution_ref'):
            ref=decision[label]
            raw,actual=guard.read(ref['path'],ref)
            docs[label]={'original_ref':actual,'value':json.loads(raw)}
            if label!='caller_closed_ref':
                docs[label]['snapshot_ref']=lib.save('inputs/'+label+'.json',raw)
        linked=refs(docs['caller_closed_ref']['value'])
        selected=[x for x in linked if 'execution/invocations/' in x['ref']['path'].replace('\\','/') and x['ref']['path'].replace('\\','/').endswith('/receipt.json')]
        unique={x['ref']['path']:x for x in selected}
        receipts=[]
        for index,item in enumerate(unique.values()):
            ref=item['ref']
            path=Path(ref['path'])
            if not path.is_absolute():
                path=lib.R/path
            raw,actual=guard.read(path,ref)
            receipt=json.loads(raw)
            receipts.append({'original_ref':actual,'snapshot_ref':lib.save('inputs/C19-receipt-'+str(index)+'.json',raw),'registered_parent_pointer':item['pointer'],'value':receipt})
        closure_ref=discovery['gap_input_refs']['Main_closure']
        raw,actual=guard.read(closure_ref['path'],closure_ref)
        closure_snapshot=lib.save('inputs/Main_closure.py',raw)
        result={'schema':'researchos.w09-c19-exact-legacy-binding-input.v1','authority':'NONE','summary':docs['consumer_summary_ref'],'historical_attribution':docs['historical_attribution_ref'],'caller_closed_ref':docs['caller_closed_ref']['original_ref'],'receipts':receipts,'closure_original_ref':actual,'closure_snapshot_ref':closure_snapshot}
        result_ref=lib.savejson('C19-binding-inputs.json',result)
        closed=guard.close();finished=True
        guard_ref=lib.savejson('C19-binding-source-guard.closed.json',closed)
        print(json.dumps({'result_ref':result_ref,'guard_ref':guard_ref,'summary':docs['consumer_summary_ref']['value'],'receipt_count':len(receipts),'receipts':receipts,'historical_attribution':docs['historical_attribution_ref']['value'],'closure_ref':actual},ensure_ascii=False))
    finally:
        if not finished:
            for stream,_,_ in guard.held:
                stream.close()

code=0
try:
    main()
except Exception:
    traceback.print_exc();code=1
print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)
