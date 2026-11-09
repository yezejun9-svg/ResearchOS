import ast,hashlib,json,re,sys,difflib
from pathlib import Path
O=Path(__file__).resolve().parent
B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_job_observer_revision_v2_codex/099b315944fa42e393af8d9190e7c14e")
V1=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_job_observer_source_codex/8cf71287160941f3b841945dc02be134")
PREV=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_observer_independent_source_review_codex/da1388ae95d14653a26a1f167574d251")
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py")
RUNNER=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v8_source_codex/8251b1ed21754f7cbd6c2f8e7ff574eb/mu_sdk_trial.v8.proposed.py")
WORKER=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_revision_v2_codex/6a02e12c83da4d4c80fc3f322fe8d397/phase_worker.py")
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
for n,s,z in [("handoff.json","3fbdffd14588ddc654512952a2373f1a25cee9620100ef5f96e46ec4b86c6b6f",1576),("manifest.json","906dd48813bdf0f6014b7453f8d10c8311cd272592173c5cb7b3477d674980de",3030),("mu_sdk_job_observer.v2.proposed.py","7077b2b70098f64f6b0a4aa5d993c59fb6cb3ffa4f08e66eb73cdb00cecc7dc0",31072)]:
 r=pin(B/n);assert r["sha256"]==s and r["bytes"]==z
assert pin(V1/"manifest.json")["sha256"]=="b55317c49d092422b07854c8ee43d10fd9fd9c4b7bde40d600e03e3fa23e3de6"
assert pin(PREV/"manifest.json")["sha256"]=="dd43148f0ae2b7cf000003dfa59732378bc1fcd564e760cb41b055aa63858025"
refs=[pin(B/"handoff.json"),pin(B/"manifest.json")]+json.loads((B/"manifest.json").read_bytes())["members"]
refs += [pin(V1/"handoff.json"),pin(V1/"manifest.json")]+json.loads((V1/"manifest.json").read_bytes())["members"]
prior=json.loads((PREV/"manifest.json").read_bytes())
refs += [pin(PREV/"manifest.json")]+[next(r for r in prior["members"] if Path(r["path"]).name==n) for n in ["independent_observer_controls.py","observer-controls.json","independent-source-review.json"]]
refs += [pin(BASE),pin(RUNNER),pin(WORKER),pin(Path(sys.executable))]
assert pin(BASE)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
assert pin(RUNNER)["sha256"]=="5b112a0824ab3bbbabb228416a9c2d0aa0be70ac2a45f29720138de350507fde"
assert pin(WORKER)["sha256"]=="173bbb8186f5c71967c2c345645774f2c9c760c647e73cbbdad277cf1cfceab8"
rows=[]
for ref in refs:
 p=Path(ref["path"]);assert pin(p)==ref;raw=p.read_bytes();snap=O/(ref["sha256"]+".raw")
 if not snap.exists():snap.write_bytes(raw)
 assert snap.read_bytes()==raw;rows.append({"source_ref":ref,"snapshot_ref":pin(snap)})
old=(V1/"mu_sdk_job_observer.proposed.py").read_bytes();new=(B/"mu_sdk_job_observer.v2.proposed.py").read_bytes()
assert hashlib.sha256(old).hexdigest()=="b062be8b68d1b31b658ba79a20c890ce895009fc135c80ae8d33ed5b78d01fd0"
def apply(raw,patch):
 src=raw.decode().splitlines(keepends=True);lines=patch.decode().splitlines(keepends=True);out=[];cursor=0;i=2
 while i<len(lines):
  m=re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n?",lines[i]);assert m,repr(lines[i])
  a,ac,b,bc=m.groups();start=int(a)-1 if int(a) else 0;out.extend(src[cursor:start]);cursor=start;i+=1;co=cn=0
  while i<len(lines) and not lines[i].startswith("@@"):
   line=lines[i];i+=1
   if line.startswith("\\ No newline"):continue
   assert line[0] in " +-"
   if line[0] in " -":assert src[cursor]==line[1:];cursor+=1;co+=1
   if line[0] in " +":out.append(line[1:]);cn+=1
  assert co==int(ac or 1) and cn==int(bc or 1)
 out.extend(src[cursor:]);return "".join(out).encode()
assert apply(old,(B/"v1-to-v2.diff").read_bytes())==new
inverse="".join(difflib.unified_diff(new.decode().splitlines(keepends=True),old.decode().splitlines(keepends=True),fromfile="v2/observer.py",tofile="v1/observer.py")).encode()
assert apply(new,inverse)==old
(O/"independent-v2-to-v1.diff").write_bytes(inverse)
ot,nt=ast.parse(old),ast.parse(new)
funcs=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.FunctionDef)}
of,nf=funcs(ot),funcs(nt);changed=sorted(k for k in of.keys()&nf.keys() if of[k]!=nf[k]);added=sorted(nf.keys()-of.keys())
assert changed==["observe_assigned_before_resume","observe_callback_frame","phase_projection","validate_context","validate_source_review"]
assert added==["validate_callback_launch","validate_launch_inputs","validate_public_environment"]
unchanged=sorted(k for k in of.keys()&nf.keys() if of[k]==nf[k])
oldtop=[ast.dump(n,include_attributes=False) for n in ot.body if not isinstance(n,ast.FunctionDef)]
newtop=[ast.dump(n,include_attributes=False) for n in nt.body if not isinstance(n,ast.FunctionDef) and not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="PUBLIC_ENVIRONMENT_KEYS" for t in n.targets))]
assert oldtop==newtop
for r in rows:assert pin(Path(r["source_ref"]["path"]))==r["source_ref"]
result={"rows":rows,"inputs":len(rows),"input_drift":0,"forward_inverse_byte_exact":True,"changed_functions":changed,"new_functions":added,"unchanged_functions":unchanged,"only_new_top_level_assignment":"PUBLIC_ENVIRONMENT_KEYS","candidate_executed":False}
(O/"intake.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False))

