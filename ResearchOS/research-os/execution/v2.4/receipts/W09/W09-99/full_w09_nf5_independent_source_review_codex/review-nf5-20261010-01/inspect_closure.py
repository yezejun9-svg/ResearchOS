"""Task100 read finite already bound resource shapes, without product execution."""
import json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def main():
    x=json.loads((Q/'input-shapes.json').read_bytes())
    n=json.loads(Path(x['producer_hdf_ref']['path']).read_bytes())
    s=json.loads(Path(x['registrar_hdf_ref']['path']).read_bytes())
    ch=json.loads(Path(n['source_choice_ref']['path']).read_bytes())
    bp=json.loads(Path(n['compiler_blueprint_ref']['path']).read_bytes())
    pi=json.loads(Path(s['input_pins_ref']['path']).read_bytes())
    lock=json.loads(Path(ch['common']['toolchain_ref']['path']).read_bytes())
    result=dict(blueprint_executable_refs=[r for r in bp['stable_input_refs'] if Path(r['path']).suffix.lower() in ('.exe','.dll')],
        blueprint_source21_matches=[r for r in bp['stable_input_refs'] if r in ch['common']['source21']],
        lock_keys=list(lock),lock_tools=lock.get('tools'),baseline=pi['baseline'],
        producer_source_guard_keys=list(json.loads(Path(n['source_guard_ref']['path']).read_bytes())),
        selectors=ch['selectors'],
        producer_source_delta=json.loads(Path(n['source_delta_ref']['path']).read_bytes()),
        registrar_source_delta=json.loads(Path(s['source_delta_ref']['path']).read_bytes()))
    with (Q/'closure-shapes.json').open('xb')as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps({k:v for k,v in result.items() if 'source_delta' not in k},ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
