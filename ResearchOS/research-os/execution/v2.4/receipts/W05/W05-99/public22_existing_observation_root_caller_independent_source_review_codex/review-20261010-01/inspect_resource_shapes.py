import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
import traceback
Q=Path(__file__).resolve().parent
def main():
    basis=json.loads((Q/'verified-source-basis.index.json').read_text(encoding='utf-8'))
    members={Path(x['path']).name:x for x in basis['members']}
    names=('source-inputs.json','runtime-resources.complete.json','runtime-closure-control.json','source-controls.json','identity-and-scope-controls.json','source-final-guard.closed.json')
    result={}
    for name in names:
        value=json.loads(Path(members[name]['path']).read_text(encoding='utf-8'))
        result[name]={'keys':list(value)}
        if name=='source-inputs.json':
            result[name].update(source_resource_count=len(value['source_resource_refs']),source_resource_names=[Path(x['path']).name for x in value['source_resource_refs']],refs={k:v for k,v in value.items() if k not in ('source_resource_refs','evidence')})
        if name=='runtime-resources.complete.json':result[name].update(resource_count=len(value['resource_refs']),explicit_added_resource_refs=value.get('explicit_added_resource_refs'),python_ref=value['python_ref'],sqlite_extension_ref=value['sqlite_extension_ref'])
        if name=='runtime-closure-control.json':result[name].update(status=value['status'],verified_resource_count=len(value['verified_resource_refs']))
        if name.endswith('controls.json'):result[name].update(status=value['status'],controls_count=len(value['controls']))
        if name=='source-final-guard.closed.json':result[name]['closure_fields']={k:v for k,v in value.items() if not isinstance(v,list)}
    with (Q/'resource-shapes.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
