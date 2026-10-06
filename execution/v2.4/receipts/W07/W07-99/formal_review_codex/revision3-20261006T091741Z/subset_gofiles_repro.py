from pathlib import Path
import importlib.util,json,os
p=Path(os.environ["W07_CANDIDATE_ROOT"])/"execution/v2.4/formal_profile_w07_test.py";s=importlib.util.spec_from_file_location("subset_helpers",p);m=importlib.util.module_from_spec(s);exec(compile(p.read_bytes(),str(p),"exec"),m.__dict__)
m.W07RawControls.setUpClass()
try:
 t=m.W07RawControls();name="researchos.local/research-os/internal/canonical";changed=[]
 def mutate(packages):
  for package in packages:
   for key in ("Imports","Deps"):
    if key in package:package[key]=[v for v in package[key] if v!=name]
   if package.get("ImportPath","").startswith("researchos.local/research-os/") and package.get("ImportPath")!=name:
    relative=package["ImportPath"][len("researchos.local/research-os/"):]
    original=list(package.get("GoFiles",[]));kept=[f for f in original if name.encode() not in (t.repo/relative/f).read_bytes()]
    if kept!=original:
     assert kept,relative
     package["GoFiles"]=kept;changed.append({"package":relative,"before":len(original),"after":len(kept)})
  return [p for p in packages if p.get("ImportPath")!=name]
 context,tools=t.inventory_control(mutate);reader=t.reader()
 try:m.PROFILE.product(m.API,reader,context,tools);reader.finish();result="ACCEPTED"
 except Exception as e:result="REJECTED: "+str(e)
 print(json.dumps({"classification":"FULL_PRODUCT_FUNCTION_NEGATIVE_NOT_REGISTERED_CURRENT","variant":"omit dependency package+alllinks+only its importing GoFiles; actual source bytes untouched","changed":changed,"result":result},indent=2))
finally:m.W07RawControls.tearDownClass()
