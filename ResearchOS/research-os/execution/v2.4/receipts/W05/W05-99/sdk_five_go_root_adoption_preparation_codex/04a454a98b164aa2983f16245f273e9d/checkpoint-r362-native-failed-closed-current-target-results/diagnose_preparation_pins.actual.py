import ast,json,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent/"prepare_checkpoint_execution_facts.actual.py"
t=ast.parse(p.read_bytes())
for node in t.body:
 if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in ("review_specs","actual_specs") for x in node.targets):
  for row in ast.literal_eval(node.value):
   d=row[0];specs=[("HDF.json",row[1],row[2]),("MF.json",row[3],row[4])] if len(row)==5 else [("",row[1],row[2])]
   for name,h,n in specs:
    f=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99")/d
    if name:f=f/name
    raw=f.read_bytes();actual=hashlib.sha256(raw).hexdigest()
    if (h,n)!=(actual,len(raw)):print(json.dumps(dict(path=str(f),expected=h,expected_bytes=n,actual=actual,actual_bytes=len(raw))))
print("ROOT_PYTHON_EXIT=0")


