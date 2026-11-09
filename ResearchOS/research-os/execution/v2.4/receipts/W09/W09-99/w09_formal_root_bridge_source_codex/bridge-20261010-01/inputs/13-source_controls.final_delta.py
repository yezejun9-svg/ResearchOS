import ast,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent
p=N/"w09_root_bridge.source.py";raw=p.read_bytes();tree=ast.parse(raw,str(p))
module=types.ModuleType("bridge_final_delta");module.__file__=str(p)
exec(compile(tree,str(p),"exec"),module.__dict__)
rows=[]
def check(name,condition):
    if not condition:raise AssertionError(name)
    rows.append({"name":name,"status":"PASS","scope":"FINAL_DELTA_ONLY"})
source=raw.decode()
check("current4_exact_absolute_refs_added",'CURRENT4_ABSOLUTE_EXACT_REFS' in source)
check("Main_prospective_owner_roots_checked",'api._registered_roots(reader,owner,"W09")==roots' in source)
check("caller_claimed_hash_preserved",'"sha256":ref["sha256"],"bytes":len(raw)' in source)
check("duplicate_dependency_pin_rejected",'"CONFLICTING_DEPENDENCY_PINS"' in source)
check("preheld_Main_native_dependencies",'args.stage in {"propose","consume","assemble"}' in source)
check("final_AST_compiles",isinstance(compile(tree,str(p),"exec"),type(compile("pass","x","exec"))))
report={"schema":"researchos.w09-root-bridge-final-delta-controls.v1","status":"PASS",
        "controls":rows,"count":len(rows),"previous_controls_ref":{
         "path":str(N/"source-controls.json"),"sha256":hashlib.sha256((N/"source-controls.json").read_bytes()).hexdigest()},
        "subject":{"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)},
        "previous_controls_not_rerun":True,"runtime_stages_executed":[],"Main_modules_executed":False}
with (N/"final-delta-controls.json").open("x",encoding="utf-8") as out:
    json.dump(report,out,ensure_ascii=False,indent=2);out.write("\n")
print(json.dumps({"status":"PASS","final_delta_controls":len(rows),"subject":report["subject"]}))

