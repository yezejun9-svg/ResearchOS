"""Correct selection using the observed real message id; preserve original failed source."""
from pathlib import Path
import types,sys
N=Path(__file__).resolve().parent
old=(N/'capture_original_registration_delivery.root.py').read_text(encoding='utf-8')
needle="and 'CP369/OW173 Actual 行政独审 PASS' in flatten(v.get('content'))"
assert old.count(needle)==1
new=old.replace(needle,"and v.get('id')=='amsg_01a1203a-7d10-7ee3-8e21-467e2f4e6207' and v.get('author')=='/root/native_temp_independent_review'")
p=N/'capture_original_registration_delivery_v2.root.py'
compile(new,str(p),'exec')
with p.open('x',encoding='utf-8',newline='') as f:f.write(new)
m=types.ModuleType('root_actual_delivery_v2');m.__file__=str(p);sys.modules[m.__name__]=m
exec(compile(new,str(p),'exec'),m.__dict__)
