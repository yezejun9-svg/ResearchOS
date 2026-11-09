"""Rebind unsealed v2 after preserving pre-directory failure diagnostics."""
import base64
import hashlib
import json
from pathlib import Path

N=Path(__file__).resolve().parent
assert not (N/'HDF.json').exists() and not (N/'MF.json').exists()
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def raw(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
changes=[]
def replace(name,data):
    p=N/name;old=p.read_bytes()
    changes.append(dict(path=str(p),whole_before_base64=base64.b64encode(old).decode(),whole_after_base64=base64.b64encode(data).decode()))
    p.write_bytes(data)
runtime=pin(N/'main_c19_runtime.source.py');compile((N/'main_c19_runtime.source.py').read_bytes(),'runtime','exec')
contract=json.loads((N/'root-calling-contract.json').read_bytes());oldsha=contract['bound_source_refs']['runtime_ref']['sha256']
for name in ('main_c19_launcher.source.py','prepare_main_c19.actual_owned.py','run_main_c19.actual_owned.py'):
    data=(N/name).read_bytes();assert data.count(oldsha.encode())==1
    data=data.replace(oldsha.encode(),runtime['sha256'].encode());compile(data,name,'exec');replace(name,data)
contract['bound_source_refs']={k:pin(N/name) for k,name in contract['source_file_bindings'].items()}
contract['receipt_rules']['pre_directory_failure']='Emit unsaved stage diagnostics without creating a directory; exception text retains primary and secondary error classifications if output also fails.'
replace('root-calling-contract.json',raw(contract))
inverse=json.loads((N/'complete-byte-inverse.json').read_bytes())
for row in inverse['files']:
    p=N/row['relative'];row['successor_ref']=pin(p);row['whole_after_base64']=base64.b64encode(p.read_bytes()).decode()
replace('complete-byte-inverse.json',raw(inverse))
with (N/'unsealed-refinement.complete-byte-inverse.json').open('xb') as f:f.write(raw(dict(changes=changes)))
print(json.dumps(dict(status='UNSEALED_V2_BINDINGS_REFINED',runtime_ref=runtime,actual=False)))
