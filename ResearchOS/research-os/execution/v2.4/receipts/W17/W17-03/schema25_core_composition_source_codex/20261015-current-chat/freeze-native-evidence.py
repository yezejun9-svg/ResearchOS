"""Append a byte inventory for the native Host8 nested evidence."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
NATIVE=HERE/'T5-host-native-evidence'

def ref(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def save(name,value):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
        f.write('\n')

files=[{'relative_path':str(p.relative_to(NATIVE)).replace('\\','/'),**ref(p)}
       for p in sorted(NATIVE.rglob('*')) if p.is_file()]
if len(files)!=20:
    raise RuntimeError('expected 20 nested Host8 evidence files')
save('NATIVE-EVIDENCE-MANIFEST.json',{'schema':'researchos.schema25-native8-evidence-inventory/1',
     'native_test_receipt':ref(HERE/'T5-host-eight.json'),'count':len(files),
     'files':files,'formal_increment':0})
save('FINAL-ADDENDUM.json',{'schema':'researchos.schema25-source-candidate-final-addendum/1',
     'base_final':ref(HERE/'FINAL.json'),
     'nested_native_manifest':ref(HERE/'NATIVE-EVIDENCE-MANIFEST.json'),
     'clarification':'T5 Host8 nested canonical/checkpoint/bridge evidence is byte-pinned here; initial FINAL pinned the top-level test receipt and raw output.',
     'formal_increment':0})
print(json.dumps({'nested_native_files':len(files),
                  'addendum':ref(HERE/'FINAL-ADDENDUM.json')},ensure_ascii=False))
