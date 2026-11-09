import ast,copy,difflib,hashlib,json,pathlib,sys
OWN=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(r"D:\作品集\ResearchOS\research-os")
BASE=ROOT/"execution/v2.4/receipts/W05/W05-99"
NEW=BASE/"mu_model_sdk_real_trial_v9_source_codex/8c135404809b41a5a795574699bd0249"
inputs=[]
def ref(path,raw=None):
 p=pathlib.Path(path); raw=p.read_bytes() if raw is None else raw
 return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def read(path,expected=None):
 p=pathlib.Path(path); p=p if p.is_absolute() else ROOT/p
 raw=p.read_bytes(); actual=ref(p,raw)
 if expected is not None: assert actual["sha256"]==expected["sha256"] and actual["bytes"]==expected["bytes"], str(p)
 inputs.append(actual)
 snapshot=OWN/("input-"+actual["sha256"]+".raw")
 if not snapshot.exists():snapshot.write_bytes(raw)
 return raw
def readref(r):return read(r["path"],r)
def obj(raw):return json.loads(raw)
def write(name,value):
 p=OWN/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
hraw=read(NEW/"handoff.json",{"sha256":"33696532a57d47cd8bd7f644c85dd2eee91e96dfec7c073e696f37441d44babb","bytes":3136})
h=obj(hraw);m=obj(readref(h["manifest_ref"]))
for member in m["members"]:readref(member)
new=readref(h["source_ref"]);old=readref(h["old_source_ref"])
prior=obj(readref(h["old_v8_independent_review_ref"]))
oldh=obj(readref(h["old_v8_handoff_ref"]))
prioraudit=obj(readref(prior["audit_ref"]))
prior_manifest=obj(readref(prior["source_manifest_ref"]))
oldtemplate=readref(prior["input_template_ref"]);newtemplate=readref(h["input_template_ref"])
assert prior["verification"]["independent_checks"]==47 and prior["verification"]["failed_checks"]==[]
assert prior["source_ref"]["sha256"]==h["old_source_ref"]["sha256"]
a=b'policy.get("write_paths") == {}';b=b'policy.get("write_paths") == []'
assert old.count(a)==1 and new.count(b)==1
assert old.replace(a,b)==new and new.replace(b,a)==old
ot=ast.parse(old.decode());nt=ast.parse(new.decode())
of={n.name:n for n in ot.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
nf={n.name:n for n in nt.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def seg(raw,node):
 return b"".join(raw.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
assert set(of)==set(nf) and len(nf)==40
changed=[n for n in of if seg(old,of[n])!=seg(new,nf[n])]
assert changed==["validate_input"]
assign=lambda tree:[ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.Assign,ast.AnnAssign))]
assert assign(ot)==assign(nt)
assert oldtemplate==newtemplate
forward="".join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile="before",tofile="after"))
inverse="".join(difflib.unified_diff(new.decode().splitlines(keepends=True),old.decode().splitlines(keepends=True),fromfile="before",tofile="after"))
assert forward.encode()==(NEW/"forward.v8-to-v9.diff").read_bytes()
assert inverse.encode()==(NEW/"inverse.v9-to-v8.diff").read_bytes()
(OWN/"independent-forward.diff").write_bytes(forward.encode())
(OWN/"independent-inverse.diff").write_bytes(inverse.encode())
go=ROOT/"internal/host/runtime_tools_windows.go"; goraw=read(go); gotext=goraw.decode()
golines=gotext.splitlines()
start=next(i for i,line in enumerate(golines) if line.startswith("func runtimeToolPaths("))
end=next(i for i in range(start+1,len(golines)) if golines[i]=="}")
excerpt="\n".join(golines[start:end+1])
(OWN/"main-runtimeToolPaths.txt").write_text(excerpt+"\n",encoding="utf-8")
assert "[]interface{}" in excerpt or "[]any" in excerpt
def extract_condition(tree):
 fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="validate_input")
 calls=[n for n in ast.walk(fn) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=="require" and len(n.value.args)>1 and isinstance(n.value.args[1],ast.Constant) and n.value.args[1].value=="frozen read-only workspace tool policy changed"]
 assert len(calls)==1
 expr=copy.deepcopy(calls[0].value.args[0])
 code=compile(ast.fix_missing_locations(ast.Expression(body=expr)),"<exact policy guard expression>","eval")
 return code,calls[0].lineno,calls[0].end_lineno
newcode,lineno,end_lineno=extract_condition(nt);oldcode,_,_=extract_condition(ot)
valid={"max_calls":1,"read_paths":["evidence.txt"],"write_paths":[],"max_read_bytes":4096,"max_write_bytes":4096}
cases=[("VALID_FROZEN_POLICY",{},True),("REJECT_WRITE_OBJECT",{"write_paths":{}},False),("REJECT_NONEMPTY_WRITE",{"write_paths":["evidence.txt"]},False),("REJECT_OTHER_READ_PATH",{"read_paths":["other.txt"]},False),("REJECT_SECOND_READ_PATH",{"read_paths":["evidence.txt","other.txt"]},False),("REJECT_MAX_CALLS_TWO",{"max_calls":2},False),("REJECT_READ_BYTES_4097",{"max_read_bytes":4097},False),("REJECT_WRITE_BYTES_4097",{"max_write_bytes":4097},False)]
controls=[]
for name,change,expected in cases:
 policy=copy.deepcopy(valid);policy.update(change)
 observed=eval(newcode,{"__builtins__":{}},{"policy":policy})
 controls.append({"id":name,"policy":policy,"expected":expected,"observed":observed,"matched":observed is expected})
assert all(x["matched"] for x in controls)
assert eval(oldcode,{"__builtins__":{}},{"policy":valid}) is False
oldshape=dict(valid,write_paths={})
assert eval(oldcode,{"__builtins__":{}},{"policy":oldshape}) is True
write("independent-controls.json",{"scope":"EXACT_TOOL_POLICY_REQUIRE_EXPRESSION_ONLY","candidate_module_imports":0,"candidate_entry_calls":0,"controls":controls,"matched":8,"total":8,"guard_lines":[lineno,end_lineno],"old_guard_contrast":{"empty_array":False,"empty_object":True}})
audit={"decision":"READY_SOURCE_ONLY","scope":"V9_RUNNER_SINGLE_WRITE_PATHS_LITERAL_DELTA_ONLY","source_ref":h["source_ref"],"prior_source_ref":h["old_source_ref"],"prior_review_ref":h["old_v8_independent_review_ref"],"prior_review_checks_reused":47,"prior_review_checks_rerun":0,"author_controls_executed":0,"functions_total":40,"changed_functions":changed,"other39_exact_bytes":True,"all_top_level_assignments_unchanged":True,"full_forward_exact":True,"full_inverse_exact":True,"author_diffs_independently_regenerated_exact":True,"input_template_exact":True,"main_runtime_tool_paths_ref":ref(go,goraw),"main_contract_lines":[start+1,end+1],"new_independent_controls":8,"controls_matched":8,"inputs":inputs,"input_drift":[],"no_full_validate_input_or_main":True,"native_windows_api_calls":0,"product_native_executions":0,"sql_calls":0,"provider_requests":0,"main_writes":0,"canonical_writes":0,"formal_increment":0,"runtime_registration":False,"execution_authority":False,"qualification":False,"whole_chain_ready":False}
write("audit.json",audit)
print(json.dumps({k:v for k,v in audit.items() if k!="inputs"},ensure_ascii=False,indent=2))
print("INPUT_RECORDS",len(inputs))
print("GO_EXCERPT",excerpt)

