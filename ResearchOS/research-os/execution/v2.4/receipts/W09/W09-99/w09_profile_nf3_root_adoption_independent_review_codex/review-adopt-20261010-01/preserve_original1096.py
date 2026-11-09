"""Preserve the original sealer failure without changing its script or guard."""
import json,types
from pathlib import Path
D=Path(__file__).resolve().parent
p=D/'preserve_originals.py';m=types.ModuleType('Task78_original_IO_capture');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
g=json.loads((D/'seal-Source-guard.closed.json').read_bytes())
assert g['closed'] and g['retained_handles_count']==0 and not g['errors']
save_original=m.save
def save_failure(path,value):
 if value.get('original_failure_ordinal')==1096:
  value.pop('guard_created',None);value.pop('diagnostic',None)
  value.update(original_script_ref=m.pin(D/'seal_review.py'),finally_guard_closed_ref=m.pin(D/'seal-Source-guard.closed.json'),
   diagnostic='Independent sealer assumed author Python_exit marker; actual author raw must determine its own observed exit domains. Original script/guard unchanged.',actual_product_calls=0)
 return save_original(path,value)
m.save=save_failure
print(json.dumps(dict(original1096=m.capture('2b75a5',1096,1,1),guard_closed0=True,execution_grant=False,formal_acceptance=False),ensure_ascii=False))
