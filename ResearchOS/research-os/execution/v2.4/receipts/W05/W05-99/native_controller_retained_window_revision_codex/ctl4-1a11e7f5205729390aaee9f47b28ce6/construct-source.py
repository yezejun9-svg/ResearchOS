import ast,json,hashlib,difflib
from pathlib import Path
N=Path(__file__).resolve().parent;B=N.parents[1]
P=B/"native_migration_controller_temp_env_revision_codex/e6a4d23ff0a84a6d9c2905181d97c2e4/root_native_migration_controller.py"
CL=B/"native_retained_cleanup_context_revision_codex/cl-1a11e7f5205729390aaee9f47b28ce6"
V=B/"native_retained_cleanup_context_independent_review_codex/clr-20261009-source-review"
def pin(p):
 p=Path(p).resolve();r=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def verify(r):
 a=pin(r["path"]);assert a["sha256"]==r["sha256"].removeprefix("sha256:") and a["bytes"]==r["bytes"];return a
def save(n,v):
 p=N/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def rawsave(n,r):
 p=N/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(r)
 return pin(p)
refs=[verify(dict(path=str(p),sha256=h,bytes=z)) for p,h,z in [
(P,"a1f53e223f47c5d8ecdb7edc5f94fec0bcc36beae9774d16ad9d0002b6ef638a",42696),
(CL/"HDF.json","def8d9e965e4a3c38fb6082c965ac59bfb199b8c4c986cde3063ac98f11bd269",4115),
(CL/"MF.json","675fd9ab068cf2403df5986ad75215ab2b73a210bf748953ee58fbcaabfe4e53",4836),
(V/"HDF.json","7e0b451fed4eeae20941c285721a8b8f982993fecd8651b4f46b41e6353ae6c6",2406),
(V/"MF.json","2f8acd3e7bb5a9df58c26add65174f55884923ee47bf2a7da912c3b7f92db387",2473)]]
for d in (CL,V):
 mf=json.loads((d/"MF.json").read_bytes())
 refs.extend(verify(r) for r in mf["members"].values())
assert json.loads((V/"HDF.json").read_bytes())["status"]=="SOURCE_ACCEPTED_PENDING_RESOURCE_PREREQUISITE_AND_ROOT_ACTUAL"
original=P.read_bytes();text=original.decode()
changes=[
('"case_deadline_seconds":1260','"case_deadline_seconds":1560'),
('argv, str(c["build"]/"internal/domain"), env, stdout, stderr, 1260,','argv, str(c["build"]/"internal/domain"), env, stdout, stderr, 1560,'),
('deadline = time.monotonic() + 1270','deadline = time.monotonic() + 1570')]
candidate=text
for old,new in changes:
 assert candidate.count(old)==1
 candidate=candidate.replace(old,new,1)
inverse=candidate
for old,new in reversed(changes):
 assert inverse.count(new)==1
 inverse=inverse.replace(new,old,1)
assert inverse.encode()==original
oldtree=ast.parse(text);newtree=ast.parse(candidate)
oldnodes=list(ast.walk(oldtree));newnodes=list(ast.walk(newtree))
assert len(oldnodes)==len(newnodes)
diff=[]
for a,b in zip(oldnodes,newnodes):
 assert type(a)==type(b)
 if isinstance(a,ast.Constant) and a.value!=b.value:
  diff.append(dict(line=a.lineno,old=a.value,new=b.value))
  b.value=a.value
assert sorted((d["old"],d["new"]) for d in diff)==[(1260,1560),(1260,1560),(1270,1570)]
assert ast.dump(oldtree,include_attributes=False)==ast.dump(newtree,include_attributes=False)
# Extract coordination facts from the candidate AST; do not import/execute it.
tree=ast.parse(candidate)
record=[v.value for d in ast.walk(tree) if isinstance(d,ast.Dict) for k,v in zip(d.keys,d.values) if isinstance(k,ast.Constant) and k.value=="case_deadline_seconds"]
owned=[n.args[5].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="run_owned_observed"]
loop=[n.value.right.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="deadline" for t in n.targets) and isinstance(n.value,ast.BinOp) and isinstance(n.value.right,ast.Constant) and n.value.right.value==1570]
assert record==[1560] and owned==[1560] and loop==[1570]
assert candidate.count('"-test.timeout=25m"')==text.count('"-test.timeout=25m"')==1
clh=json.loads((CL/"HDF.json").read_bytes());clsource=Path(clh["candidate_ref"]["path"]).read_text(encoding="utf-8")
assert "context.WithTimeout(context.Background(), 20*time.Minute)" in clsource
assert "context.WithTimeout(context.Background(), 4*time.Minute)" in clsource
assert "now.Add(4 * time.Minute)" in clsource and "TimeoutSeconds: 180" in clsource
main,cleanup,go_timeout,owned_timeout,loop_timeout,outer_timeout=1200,240,1500,owned[0],loop[0],1800
assert main+cleanup==1440 < go_timeout < owned_timeout < outer_timeout
assert owned_timeout < loop_timeout < outer_timeout
rawsave("base/root_native_migration_controller.py",original)
cref=rawsave("root_native_migration_controller.py",candidate.encode())
save("source-replacements.json",[dict(old=a,new=b) for a,b in changes])
rawsave("three-deadlines.patch","".join(difflib.unified_diff(text.splitlines(True),candidate.splitlines(True),fromfile="CTL3/root_native_migration_controller.py",tofile="CTL4/root_native_migration_controller.py")).encode())
save("deadline-coordination-controls.json",dict(source_only=True,Python_AST=True,changed_constant_nodes=diff,exact_inverse=True,all_other_AST_nodes_unchanged=True,main_seconds=main,cleanup_seconds=cleanup,main_plus_cleanup_seconds=main+cleanup,Go_test_timeout_seconds=go_timeout,owned_native_seconds=owned_timeout,loop_seconds=loop_timeout,outer_wrapper_required_seconds=outer_timeout,strict_order_1440_1500_1560_1800=True,loop1570_below_outer1800=True,private_broker180_unchanged=True,grant240_unchanged=True,native_retention_qualification=False))
refs=list({r["path"].casefold():r for r in refs}.values())
assert all(pin(r["path"])==r for r in refs)
save("sourceguard.final.json",dict(refs=refs,all_unchanged=True,method="exact Source read/hash before-after",Main_canonical_write=False))
save("prerequisites.json",dict(cleanup_handoff=pin(CL/"HDF.json"),cleanup_manifest=pin(CL/"MF.json"),cleanup_source=verify(clh["candidate_ref"]),cleanup_independent_handoff=pin(V/"HDF.json"),cleanup_independent_manifest=pin(V/"MF.json"),CTL4_must_receive_non_author_review=True,Root_fresh_Config_FrozenInputs_must_pin_new_CTL4_and_review=True,old_Config_not_reusable=True,actual_native_SQL_model_Git_Go=False))
print(json.dumps(dict(status="CTL4_SOURCE_ONLY_PREPARED",candidate=cref,changed_constants=3,input_refs=len(refs),new_native_SQL_model_Git_Go=False)))

