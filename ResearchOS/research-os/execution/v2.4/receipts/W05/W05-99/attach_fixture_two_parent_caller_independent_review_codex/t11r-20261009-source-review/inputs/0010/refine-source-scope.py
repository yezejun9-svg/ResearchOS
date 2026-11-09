import ast,json,hashlib,re
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def write(p,v):
 p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
choice_path=N/"source.integration.choice.json";choice=json.loads(choice_path.read_bytes())
B=N.parents[1];R=N.parents[6]
base=json.loads(Path(choice["base_current49"]).read_bytes())
parents=set(base["exact_25_parent_names"])
for item in choice["source_components"]:
 m=json.loads(Path(item["source_manifest"]["path"]).read_bytes())["members"];values=m.values() if isinstance(m,dict) else m
 candidate=(B/item["candidate_namespace"]/"candidate-root").resolve()
 for ref in values:
  p=Path(ref["path"]).resolve()
  if p.is_relative_to(candidate) and p.name.endswith("_test.go"):parents.update(re.findall(r"^func (Test[A-Za-z0-9_]+)\(",p.read_text(encoding="utf-8"),re.MULTILINE))
assert len(parents)==54
selected=set(choice["exact_parent_names"]);assert len(selected)==2
names=["source.integration.choice.json","validate_attach_fixture_two_parent.actual_owned.py","static-preservation.json","execution-contract.json","source-replacements.json","validate.patch"]
d=N/"initial-draft";d.mkdir()
for name in names:(d/name).write_bytes((N/name).read_bytes())
choice["all_source_file_declared_parent_names"]=choice["source_preserved_parent_names"]
choice["source_preserved_parent_names"]=sorted(parents)
choice["source_preserved_parent_count"]=54
choice["source_preserved_nonselected_parent_count"]=52
write(choice_path,choice)
driverp=N/names[1];driver=driverp.read_text(encoding="utf-8")
old='assert isolation["source_overlay"] is False and isolation["Main_canonical_unchanged"] is True if "Main_canonical_unchanged" in isolation else isolation["main_canonical_unchanged"] is True'
new='assert isolation["source_overlay"] is False and isolation["main_canonical_unchanged"] is True'
assert driver.count(old)==1
driver=driver.replace(old,new)
driverp.write_bytes(driver.encode())
replp=N/"source-replacements.json";repls=json.loads(replp.read_bytes())
hits=[x for x in repls["validate"] if old in x["new"]];assert len(hits)==1
hits[0]["new"]=hits[0]["new"].replace(old,new);write(replp,repls)
inverse=driver
for pair in reversed(repls["validate"]):
 assert inverse.count(pair["new"])==1
 inverse=inverse.replace(pair["new"],pair["old"],1)
assert inverse==(N/"base/validate.py").read_text(encoding="utf-8")
import difflib
(N/"validate.patch").write_bytes("".join(difflib.unified_diff(inverse.splitlines(True),driver.splitlines(True),fromfile="base/validate",tofile="candidate/validate")).encode())
s=json.loads((N/"static-preservation.json").read_bytes());s.update(preserved_parent_count=54,nonselected_parent_count=52,all_Source_file_declared_parent_count=132,declared_names_are_not_execution_scope=True)
write(N/"static-preservation.json",s)
contract=json.loads((N/"execution-contract.json").read_bytes());contract["choice_ref"]=pin(choice_path);write(N/"execution-contract.json",contract)
# Pure Source composition preflight: copied exact definitions and Source-only statements;
# no candidate entrypoint invocation, no worktree or output namespace creation.
tree=ast.parse(driver)
scope={"Path":Path,"hashlib":hashlib,"json":json,"re":re,"R":R,"B":B,"P":R/".local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1","A":B/"integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2","choice":choice,"sources":{},"input_refs":[]}
keep=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ("pin","verify","members","unique")]
exec(compile(ast.Module(body=keep,type_ignores=[]),"<pure-functions>","exec"),scope)
start=driver.index('assert pin(A/"validation.closed.json")')
end=driver.index('\ncanonical=[',start)
exec(compile(driver[start:end],"<exact-source-composition-only>","exec"),scope)
assert len(scope["sources"])==58 and scope["new_tests"]==selected and len(scope["preserved_parent_sources"])==54
assert len(scope["preserved_parent_sources"]-selected)==52
assert all(scope["verify"](ref) for ref in scope["input_refs"])
for k in ("worktree","isolation_output","target_output","scratch"):assert not Path(contract[k]).exists()
write(N/"source-composition-preflight.json",dict(status="SOURCE_ONLY_PASS",exact_composition_block_executed=True,entrypoint_invoked=False,source_count=58,previous_scope_parent_count=54,selected_parent_count=2,nonselected_parent_sources=sorted(parents-selected),source_input_count=len(scope["input_refs"]),actual_Git_Go_SQL_native_model=False,draft_correction="Distinguish 132 declarations across whole Source files from previous targeted 54-parent scope; retain all Source, select exactly two, report other 52 as not executed. Simplify exact ready flag assertion.",initial_draft_preserved=True))
print(json.dumps(dict(status="SOURCE_PREFLIGHT_PASS",choice_ref=pin(choice_path),driver_ref=pin(driverp),source_count=58,selected=2,not_executed=52,actual_Git_Go_SQL_native_model=False)))

