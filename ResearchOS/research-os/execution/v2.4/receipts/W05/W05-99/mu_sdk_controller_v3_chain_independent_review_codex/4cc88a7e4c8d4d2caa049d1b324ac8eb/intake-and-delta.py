import ast,hashlib,json,re
from pathlib import Path
O=Path(__file__).resolve().parent
B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_revision_v3_codex/41ee2ad00c864829b5f6926c5fac919f")
V2=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_revision_v2_codex/6a02e12c83da4d4c80fc3f322fe8d397")
OBSREVIEW=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_observer_v2_independent_source_review_codex/75b8c18a1ee84e2db9738de1ac2a1d0b")
CTRLREVIEW=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_v2_partial_independent_review_codex/c97b2628db1b4e788a3d40cb70b24491")
def pin(p):
 r=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(r).hexdigest(),"bytes":len(r)}
assert pin(B/"handoff.json")=={"path":str(B/"handoff.json"),"sha256":"902c40d889760a4c4420c13dff0f508e2cfa9a3928b66956bc8c0ff1f721cc3d","bytes":2675}
assert pin(B/"manifest.json")["sha256"]=="533087f8b20a73687028e456af4d0b4d3d56dc1f6f3da245d5229535d7f0ae28"
assert pin(OBSREVIEW/"handoff.json")["sha256"]=="c5e0c84ca39f56ea28cf2b881d6c81d56f6284c01fb9e99ba3e8e97c2c70063e"
assert pin(OBSREVIEW/"manifest.json")["sha256"]=="ddf21f9dc0cd7f59069ffcb36ca2cad9b9ef9d1dee41e6cdb8c09dd88168e2f3"
assert pin(CTRLREVIEW/"handoff.json")["sha256"]=="705361108d3aa5ed704803e9719ea63d87036e4afb4237fd85ef00ac4394619f"
assert pin(CTRLREVIEW/"manifest.json")["sha256"]=="65b97460cfe6995b3600563d3a27dea3e8594c686007e32608b3f9369e4b59e0"
refs=[pin(B/"handoff.json"),pin(B/"manifest.json")]+json.loads((B/"manifest.json").read_bytes())["members"]
for folder in (OBSREVIEW,CTRLREVIEW):
 mf=json.loads((folder/"manifest.json").read_bytes())
 refs += [pin(folder/"handoff.json"),pin(folder/"manifest.json")]
 refs += [next(r for r in mf["members"] if Path(r["path"]).name==n) for n in ["independent-review.json","review.md"]]
review=json.loads((OBSREVIEW/"independent-review.json").read_bytes())
refs += [review["source_ref"],review["controls_ref"]]
creview=json.loads((CTRLREVIEW/"independent-review.json").read_bytes())
refs += [creview["source_ref"],creview["controls_ref"]]
previous_intake=json.loads((OBSREVIEW/"intake.json").read_bytes())
refs += [next(r["source_ref"] for r in previous_intake["rows"] if Path(r["source_ref"]["path"]).name==n) for n in ["mu_sdk_trial.v8.proposed.py","windows_owned_process.py"]]
rows=[]
for ref in refs:
 p=Path(ref["path"]);assert pin(p)==ref;raw=p.read_bytes();snap=O/(ref["sha256"]+".raw")
 if not snap.exists():snap.write_bytes(raw)
 assert snap.read_bytes()==raw;rows.append({"source_ref":ref,"snapshot_ref":pin(snap)})
old=(V2/"controller.py").read_bytes();new=(B/"controller.py").read_bytes()
def apply(raw,patch):
 src=raw.decode().splitlines(keepends=True);lines=patch.decode().splitlines(keepends=True);out=[];cursor=0;i=2
 while i<len(lines):
  m=re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n?",lines[i]);assert m,repr(lines[i])
  a,ac,b,bc=m.groups();start=int(a)-1 if int(a) else 0;out.extend(src[cursor:start]);cursor=start;i+=1;co=cn=0
  while i<len(lines) and not lines[i].startswith("@@"):
   s=lines[i];i+=1
   if s.startswith("\\ No newline"):continue
   assert s[0] in " +-"
   if s[0] in " -":assert src[cursor]==s[1:];cursor+=1;co+=1
   if s[0] in " +":out.append(s[1:]);cn+=1
  assert co==int(ac or 1) and cn==int(bc or 1)
 out.extend(src[cursor:]);return "".join(out).encode()
assert apply(old,(B/"controller.forward.diff").read_bytes())==new
assert apply(new,(B/"controller.inverse.diff").read_bytes())==old
ot,nt=ast.parse(old),ast.parse(new)
funcs=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.FunctionDef)}
of,nf=funcs(ot),funcs(nt);changed=sorted(k for k in of.keys()&nf.keys() if of[k]!=nf[k])
assert changed==["activate_canonical_lease","close_canonical_lease","launch_reviewed_phase"]
for name in ["pinned","cleanup_confirmed"]:assert of[name]==nf[name]
literalrefs={}
for n in nt.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ("CANONICAL_TRANSACTION_REF","JOB_WATCHDOG_REF"):
  ref=ast.literal_eval(n.value);assert pin(Path(ref["path"]))==ref;literalrefs[n.targets[0].id]=ref
for n in ["controller.py","canonical_transactions.py","job_deadline_watchdog.py","owned_job_hooks.py","phase_worker.py","job_probe_worker.py"]:
 compile((B/n).read_bytes(),str(B/n),"exec")
for n in ["owned_job_hooks.py","phase_worker.py","job_probe_worker.py"]:assert (B/n).read_bytes()==(V2/n).read_bytes()
for r in rows:assert pin(Path(r["source_ref"]["path"]))==r["source_ref"]
result={"rows":rows,"input_count":len(rows),"drift_count":0,"forward_inverse_byte_exact":True,"changed_controller_functions":changed,"R01_guard_and_R03_pin_unchanged":True,"unchanged_three_dependencies":True,"fixed_dependency_pins":literalrefs,"six_sources_compile_only":True,"observer_39_controls_reused_not_rerun":True,"new_tool_failures":0}
(O/"intake.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in result.items() if k not in ("rows","fixed_dependency_pins")},ensure_ascii=False))

