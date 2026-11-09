import ast,json,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent
rows=json.loads((O/"intake.json").read_bytes())["rows"]
structure=[]
for row in rows:
 p=Path(row["source_ref"]["path"])
 if p.suffix!=".py":continue
 raw=Path(row["snapshot_ref"]["path"]).read_bytes();tree=ast.parse(raw)
 structure.append({"source_ref":row["source_ref"],"top_level_calls":[{"line":n.lineno,"name":ast.unparse(n.func)} for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) for n in [n.value]],"functions":[{"name":n.name,"line":n.lineno,"end_line":n.end_lineno} for n in tree.body if isinstance(n,ast.FunctionDef)],"all_called_names":sorted(set(ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)))})
(O/"source-structure.json").write_text(json.dumps(structure,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"source_files":len(structure),"candidate_executed":False}))

