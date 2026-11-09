from pathlib import Path
import json,hashlib,sys
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
Q=B/'integration_codex/official-test2json-resource-build-root-3e9129c5f7c9461e'
def pin(p):
 b=p.read_bytes(); return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
if sys.argv[1]=='initial':
 print('\n'.join(str(p) for p in Q.rglob('*') if p.is_file()))
 p=Q/'resource-build.closed.json'; print(json.dumps(pin(p))); print(p.read_text(encoding='utf-8'))
elif sys.argv[1]=='read':
 for name in sys.argv[2:]:
  p=Path(name); print('\nFILE '+str(p)); print(p.read_text(encoding='utf-8'))
elif sys.argv[1]=='details':
 for p in [Q/'build_official_test2json.actual_owned.py',*Q.glob('*.invocation.json'),*Q.glob('*.cleanup.actual.json')]:
  print('\nFILE '+str(p)); print(p.read_text(encoding='utf-8'))
 inventory=json.loads((Q/'selected-official-compiler-inputs.json').read_text(encoding='utf-8'))
 print('INVENTORY_SHAPE '+str([(k,type(v).__name__,len(v) if isinstance(v,(list,dict,str)) else v) for k,v in inventory.items()]))
 print(json.dumps({k:v[:2] if isinstance(v,list) else v for k,v in inventory.items()},ensure_ascii=False)[:15000])
elif sys.argv[1]=='compact':
 for p in Q.glob('*.cleanup.actual.json'):
  o=json.loads(p.read_text(encoding='utf-8')); print(p.name,json.dumps({k:len(v) if k=='entries' else v for k,v in o.items()},ensure_ascii=False))
 p=Q/'original-tool-io.json'; print('ORIGINAL_IO',p.read_text(encoding='utf-8'))
 p=B/'integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py'
 for n,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
  if any(x in line for x in ['def run_owned','CreateProcess','AssignProcess','ResumeThread','QueryInformationJobObject','SetInformationJobObject','WaitForSingleObject','GetExitCodeProcess','active_processes','CloseHandle','env_block','environment']):print(f'owned-helper:{n}: {line}')
elif sys.argv[1]=='pathcheck':
 c=json.loads((Q/'resource-build.closed.json').read_text(encoding='utf-8')); inv=json.loads((Q/'selected-official-compiler-inputs.json').read_text(encoding='utf-8'))
 for ref in [c['binary_ref'],c['base_input_refs'][0],inv['GoRef']]:
  print(json.dumps({'path':ref['path'],'exists':Path(ref['path']).exists(),'repr':repr(ref['path'])},ensure_ascii=False))
