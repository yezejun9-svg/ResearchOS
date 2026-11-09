import sys
sys.dont_write_bytecode = True
import ast, copy, difflib, hashlib, json
from pathlib import Path
ROOT=Path("D:/作品集/ResearchOS/research-os")
OUT=Path(__file__).resolve().parent
OLD=ROOT/"execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v8_source_codex/8251b1ed21754f7cbd6c2f8e7ff574eb"
frozen_paths=[ROOT/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
frozen_paths += [ROOT/p for p in ("internal/host/vault.go","internal/host/host.go","apps/control/main.go","internal/domain/runtime_qualification.go","apps/cli/cli_stream.go")]
frozen={p:p.read_bytes() for p in frozen_paths}
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(name, obj):
 p=OUT/name
 with p.open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
old_path=OLD/"mu_sdk_trial.v8.proposed.py";old=old_path.read_bytes()
assert hashlib.sha256(old).hexdigest()=="5b112a0824ab3bbbabb228416a9c2d0aa0be70ac2a45f29720138de350507fde" and len(old)==90096
anchor=b'policy.get("write_paths") == {}'
replacement=b'policy.get("write_paths") == []'
assert old.count(anchor)==1 and replacement not in old
new=old.replace(anchor,replacement,1)
assert new.replace(replacement,anchor,1)==old
path=OUT/"mu_sdk_trial.v9.proposed.py"
with path.open("xb") as f:f.write(new)
template_path=OLD/"input.v8.template.json";template=template_path.read_bytes()
assert hashlib.sha256(template).hexdigest()=="37be37e22ff19e687817b451c1a4805defb99ff22e901b1579c5f894fb7c068c"
with (OUT/"input.v9.template.json").open("xb") as f:f.write(template)
old_tree=ast.parse(old);new_tree=ast.parse(new);compile(new,str(path),"exec")
def functions(tree,raw):
 lines=raw.splitlines(keepends=True)
 return {n.name:b"".join(lines[n.lineno-1:n.end_lineno]) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
before,after=functions(old_tree,old),functions(new_tree,new)
assert set(before)==set(after) and len(before)==40
changed=[n for n in before if before[n]!=after[n]]
assert changed==["validate_input"]
target=after["validate_input"].decode()
nodes=[n for n in ast.walk(new_tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="require" and n.args and 'policy.get("write_paths")' in (ast.get_source_segment(new.decode(),n) or "")]
assert len(nodes)==1
expression=ast.Expression(body=nodes[0].args[0]);ast.fix_missing_locations(expression)
compiled=compile(expression,"<independent-policy-expression-author-control>","eval")
valid={"max_calls":1,"read_paths":["evidence.txt"],"write_paths":[],"max_read_bytes":4096,"max_write_bytes":4096}
cases=[("valid_main_array_policy",valid,True)]
for label,field,value in [("reject_object_empty_write_paths","write_paths",{}),("reject_any_write_path","write_paths",["x"]),("reject_two_tool_calls","max_calls",2),("reject_large_read","max_read_bytes",65536),("reject_large_write","max_write_bytes",65536),("reject_other_read","read_paths",["x"]),("reject_extra_read","read_paths",["evidence.txt","x"])]:
 policy=copy.deepcopy(valid);policy[field]=value;cases.append((label,policy,False))
checks=[]
for name,policy,want in cases:
 actual=eval(compiled,{"__builtins__":{}},{"policy":policy})
 assert type(actual) is bool and actual is want,name
 checks.append({"name":name,"expected":want,"actual":actual,"pass":True})
old_consts={n.targets[0].id:ast.dump(n.value) for n in old_tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
new_consts={n.targets[0].id:ast.dump(n.value) for n in new_tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
assert old_consts==new_consts
ctrl=save("source-controls.json",{"schema":"researchos.mu-sdk-v9-author-source-controls.v1","actor":"codex:/root","status":"SOURCE_CONTROLS_ONLY","old_source_ref":pin(old_path),"new_source_ref":pin(path),"ast_compile":True,"changed_functions":changed,"unchanged_function_count":39,"inverse_exact_old_bytes":True,"all_top_level_assignment_ast_unchanged":True,"pure_policy_controls":checks,"limits":{"requests":3,"qualification":1,"ordinary":2,"output_tokens_total":8192,"wall_seconds":300},"target_execution":False,"provider_requests":0,"formal_acceptance":False})
for name,a,b in [("forward.v8-to-v9.diff",old,new),("inverse.v9-to-v8.diff",new,old)]:
 with (OUT/name).open("xb") as f:f.write("".join(difflib.unified_diff(a.decode().splitlines(keepends=True),b.decode().splitlines(keepends=True),fromfile="before",tofile="after")).encode())
assert all(p.read_bytes()==b for p,b in frozen.items())
report=OUT/"review-summary.md"
with report.open("xb") as f:f.write(("# v9 Source proposal\n\nOnly validate_input's empty write_paths changes from object {} to array []; Main runtimeToolPaths consumes arrays and the revised trusted Host will emit []. Source constants, 39 unrelated functions and the input template remain exact v8 bytes. Eight pure controls accept the bounded array policy and reject incompatible object/writes/read limits. No runner entrance, Host, Windows API, provider, grant or canonical mutation ran. This is an author proposal awaiting non-author review. Old v8 independent review is preserved and covers only its exact bytes.\n").encode())
files=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file()]
manifest=save("manifest.json",{"schema":"researchos.mu-sdk-v9-source-manifest.v1","actor":"codex:/root","members":files,"excludes":["manifest.json","handoff.json"],"frozen_canonical_and_main_refs":[pin(p) for p in frozen_paths]})
hdf=save("handoff.json",{"schema":"researchos.mu-sdk-v9-source-handoff.v1","actor":"codex:/root","decision":"IMMUTABLE_SOURCE_READY_FOR_NONAUTHOR_REVIEW_ONLY","source_ref":pin(path),"input_template_ref":pin(OUT/"input.v9.template.json"),"old_source_ref":pin(old_path),"old_v8_handoff_ref":pin(OLD/"handoff.json"),"old_v8_independent_review_ref":pin(ROOT/"execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v8_independent_source_review_codex/430f8fc4d15847d48d6d185f51f839a7/review.json"),"manifest_ref":manifest,"source_controls_ref":ctrl,"changed_functions":changed,"source_commit":"adc460c2138528f163f7fdab5e8d81dde157b7fb","limits":{"requests":3,"qualification":1,"ordinary":2,"output_tokens_total":8192,"wall_seconds":300},"execution_authority_issued":False,"runtime_registration_issued":False,"provider_requests":0,"trial_executed":False,"source_acceptance":False,"formal_increment":0,"main_writes":0,"canonical_writes":0,"open":["Non-author byte-bound Source review","Controller whole Source/actual no-provider lifecycle review","Trusted Host immutable corrected Source/build/review","Actual fresh isolated scope and grant not issued"]})
assert all(p.read_bytes()==b for p,b in frozen.items())
print(json.dumps({"handoff_ref":hdf,"manifest_ref":manifest,"source_ref":pin(path),"source_controls_ref":ctrl,"status":"SOURCE_PROPOSAL_ONLY"}),flush=True)

