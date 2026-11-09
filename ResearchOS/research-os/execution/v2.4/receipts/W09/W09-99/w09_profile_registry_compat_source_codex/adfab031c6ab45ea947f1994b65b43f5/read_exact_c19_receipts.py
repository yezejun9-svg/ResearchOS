import sys
sys.dont_write_bytecode=True
import importlib.util
import json
from pathlib import Path
import traceback

Q=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('w09_exact_read',Q/'read_inputs.py')
lib=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

def main():
    binding=json.loads((Q/'C19-binding-inputs.json').read_text(encoding='utf-8'))
    discovery=json.loads((Q/'input-discovery.json').read_text(encoding='utf-8'))
    guard=lib.Guard()
    finished=False
    try:
        rows=[]
        for index,consumer in enumerate(binding['summary']['value']['consumers']):
            entry={'route':consumer['route']}
            for label in ('dispatcher_receipt_ref','mode_decision_ref','dispatcher_child_stdout_ref'):
                ref=consumer[label]
                raw,actual=guard.read(ref['path'],ref)
                entry[label]={'original_ref':actual,'snapshot_ref':lib.save('inputs/C19-'+str(index)+'-'+label+'.json',raw),'value':json.loads(raw)}
            rows.append(entry)
        archive=next(x for x in binding['historical_attribution']['value']['bindings'] if x['historical_logical_ref']['path'].replace('\\','/').endswith('/commands.json'))['physical_archive_ref']
        raw,actual=guard.read(archive['path'],archive)
        archive_ref=lib.save('inputs/commands.CM39.actual-archive.json',raw)
        owner=discovery['gap_input_refs']['C19_actual_dispatcher_owner']
        raw,ownerref=guard.read(owner['path'],owner)
        ownervalue=json.loads(raw)
        owner_snapshot=lib.save('inputs/C19-dispatcher-owner.json',raw)
        result={'schema':'researchos.w09-c19-exact-receipts-discovery.v1','authority':'NONE','rows':rows,'actual_CM39_archive_original_ref':actual,'actual_CM39_archive_snapshot_ref':archive_ref,'actual_dispatcher_owner_original_ref':ownerref,'actual_dispatcher_owner_snapshot_ref':owner_snapshot,'actual_dispatcher_owner_value':ownervalue}
        result_ref=lib.savejson('C19-exact-receipts.json',result)
        closed=guard.close();finished=True
        guard_ref=lib.savejson('C19-exact-receipts-source-guard.closed.json',closed)
        print(json.dumps({'result_ref':result_ref,'guard_ref':guard_ref,'rows':[{k:v for k,v in row.items() if k!='dispatcher_child_stdout_ref'} for row in rows],'archive_ref':actual,'owner':ownervalue},ensure_ascii=False))
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
