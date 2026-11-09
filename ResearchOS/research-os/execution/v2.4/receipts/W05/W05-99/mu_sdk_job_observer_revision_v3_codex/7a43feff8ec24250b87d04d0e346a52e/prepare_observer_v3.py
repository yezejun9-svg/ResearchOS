"""Author-only observer v3 Source preparation. Never imports or executes candidates."""
from pathlib import Path
import ast, copy, difflib, hashlib, json
O=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os")
P=R/"execution/v2.4/receipts/W05/W05-99"
OLD=P/"mu_sdk_job_observer_revision_v2_codex/099b315944fa42e393af8d9190e7c14e"
V9=P/"mu_model_sdk_real_trial_v9_source_codex/8c135404809b41a5a795574699bd0249"
def meta(p,raw=None):
 if raw is None:raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def put(n,value):(O/n).write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
def literal(tree,name):
 values=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id==name]
 assert len(values)==1,name
 return values[0]
oldmf=meta(OLD/"manifest.json")
assert (oldmf["sha256"],oldmf["bytes"])==("906dd48813bdf0f6014b7453f8d10c8311cd272592173c5cb7b3477d674980de",3030)
for ref in json.loads((OLD/"manifest.json").read_bytes())["members"]:
 current=meta(Path(ref["path"]));assert current["sha256"]==ref["sha256"] and current["bytes"]==ref["bytes"]
oldraw=(OLD/"mu_sdk_job_observer.v2.proposed.py").read_bytes()
assert hashlib.sha256(oldraw).hexdigest()=="7077b2b70098f64f6b0a4aa5d993c59fb6cb3ffa4f08e66eb73cdb00cecc7dc0" and len(oldraw)==31072
oldtree=ast.parse(oldraw);oldpin=literal(oldtree,"RUNNER_REF")
newrunner=V9/"mu_sdk_trial.v9.proposed.py";newpin=meta(newrunner)
assert (newpin["sha256"],newpin["bytes"])==("cbfa40e8376ad284df6521b43d64380488017ee41c7411a339dae853ed77a98f",90096)
assert newpin["bytes"]==oldpin["bytes"]
# Exact two byte replacements within the RUNNER_REF value only; bytes field stays90096.
assert oldraw.count(oldpin["path"].encode())==oldraw.count(oldpin["sha256"].encode())==1
newraw=oldraw.replace(oldpin["path"].encode(),newpin["path"].encode()).replace(oldpin["sha256"].encode(),newpin["sha256"].encode())
newfile=O/"mu_sdk_job_observer.v3.proposed.py";newfile.write_bytes(newraw)
newtree=ast.parse(newraw);assert literal(newtree,"RUNNER_REF")==newpin
a,b=copy.deepcopy(oldtree),copy.deepcopy(newtree)
for tree in (a,b):
 for node in tree.body:
  if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=="RUNNER_REF":
   node.value=ast.Constant(value=None)
assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
# Stronger exact-byte check: reverse only those new literal values and recover original.
assert newraw.replace(newpin["path"].encode(),oldpin["path"].encode()).replace(newpin["sha256"].encode(),oldpin["sha256"].encode())==oldraw
oldtext,newtext=oldraw.decode("utf-8"),newraw.decode("utf-8")
for n,before,after,fromfile,tofile in [
 ("forward.v2-to-v3.diff",oldtext,newtext,"a/mu_sdk_job_observer.v2.proposed.py","b/mu_sdk_job_observer.v3.proposed.py"),
 ("inverse.v3-to-v2.diff",newtext,oldtext,"b/mu_sdk_job_observer.v3.proposed.py","a/mu_sdk_job_observer.v2.proposed.py")]:
 (O/n).write_text("".join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=fromfile,tofile=tofile)),encoding="utf-8",newline="")
oldtemplate=json.loads((OLD/"independent-source-review.v2.template.json").read_bytes())
template=copy.deepcopy(oldtemplate);template["observer_source_ref"]=meta(newfile);template["runner_source_ref"]=newpin
assert template["schema"]=="researchos.mu-sdk-controller-observer-independent-source-review.v2"
assert template["actor_id"] is template["decision"] is None
assert all(template[k]==oldtemplate[k] for k in template if k not in {"observer_source_ref","runner_source_ref"})
put("independent-source-review.v3.template.json",template)
inputs=[]
for p in [OLD/"mu_sdk_job_observer.v2.proposed.py",OLD/"manifest.json",OLD/"handoff.json",OLD/"independent-source-review.v2.template.json",newrunner,V9/"manifest.json",V9/"handoff.json"]:
 raw=p.read_bytes();ref=meta(p,raw)
 relative=p.relative_to(P);dest=O/"input-snapshots"/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 ref["snapshot"]=str(dest.relative_to(O));inputs.append(ref)
put("source-preparation.v3.json",dict(schema="researchos.observer-v3-author-source-preparation.v1",decision="SOURCE_PREPARATION_ONLY_NOT_INDEPENDENT_REVIEW",source_author=literal(newtree,"AUTHOR"),old_source_ref=meta(OLD/"mu_sdk_job_observer.v2.proposed.py"),source_ref=meta(newfile),runner_ref=newpin,inputs=inputs,changes=["RUNNER_REF.path","RUNNER_REF.sha256"],checks=dict(old_manifest_members_pin_match=True,source_ast_parse=True,runner_v9_literal_pin_exact=True,all_other_AST_nodes_unchanged=True,reverse_literal_replacement_exact_original=True,source_schema_v2_unchanged=True,six_ref_template_contract_unchanged=True,all_functions_constants_except_RUNNER_REF_unchanged=True,source_execution=False,real_winapi_calls=0,native_jobs=0,provider_requests=0,main_or_canonical_writes=0,formal_acceptance_delta=0)))
handoff=f"""# Observer v3 Source handoff

Status: SOURCE_PREPARATION_ONLY / NOT_INDEPENDENTLY_REVIEWED / NOT_EXECUTED.
Author: codex:/root/w05_merge_review (same as v2; provenance unchanged).

Only RUNNER_REF.path and RUNNER_REF.sha256 changed, now binding the frozen v9 runner.
Observer Source: {meta(newfile)['sha256']} / {meta(newfile)['bytes']} bytes.
Runner: {newpin['path']}
Runner SHA-256: {newpin['sha256']} / {newpin['bytes']} bytes.

All other Source bytes recover exactly by reversing these two literal replacements. Every function, actor, source commit, limit, schema.v2, six-ref independent review binding, actual argv/cwd/Python/worker checks and callback checks remains unchanged. AST comparison confirms no other semantic node changed. The new input template updates only observer/runner refs; actor and decision remain null and no grant is issued.

Old immutable v2 Source remains {meta(OLD/'mu_sdk_job_observer.v2.proposed.py')['sha256']} /31072 bytes. Its manifest and all9 listed members rehash unchanged. The prior fixed v8 runner reference cannot authorize this v9 tuple; Root must issue fresh six-ref independent review for controller C4 + observer v3 + hooks + runner v9 + worker + Python after a non-author review.

Author checks here are AST, literal data, exact raw-byte reversal and generated forward/inverse diffs only. No candidate imports or execution, no WinAPI, Job, Host, provider, Main or canonical writes. This handoff is not READY_SOURCE_ONLY, runtime admission, real cleanup evidence or formal acceptance.

Known execution gates remain Root-owned: SourceReadGuard repaired-module independent review and real Windows probe, complete guarded tuple/lifetime spanning all consumers and Job cleanup, actual suspended frame callback observations, no-provider lifecycle proof, real Host qualification and bounded provider reconciliation. This narrow revision does not fix or self-certify those components.

Files: source-preparation.v3.json, forward.v2-to-v3.diff, inverse.v3-to-v2.diff, independent-source-review.v3.template.json, input-snapshots/.
After manifest sealing the author stops all Source writes. command_queue performs the independent C4+O3 tuple review.
"""
(O/"HANDOFF.md").write_text(handoff,encoding="utf-8")
print(json.dumps(dict(status="SOURCE_ONLY_CONTROLS_PASS_NOT_INDEPENDENT_REVIEW",source=meta(newfile),handoff=meta(O/"HANDOFF.md"),runner=newpin)))

