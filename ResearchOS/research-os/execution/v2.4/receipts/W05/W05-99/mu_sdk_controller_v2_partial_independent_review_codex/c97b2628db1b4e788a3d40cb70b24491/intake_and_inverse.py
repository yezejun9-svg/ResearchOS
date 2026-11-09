import ast,difflib,hashlib,json,re
from pathlib import Path
O=Path(__file__).resolve().parent
B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_revision_v2_codex/6a02e12c83da4d4c80fc3f322fe8d397")
OLD=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_source_codex/2e716ffb2df44199b7d3d28cdbdddbed")
PREV=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_observer_independent_source_review_codex/da1388ae95d14653a26a1f167574d251")
def pin(p):
 raw=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
for name,sha,size in [("handoff.json","5d540d9c1f1dab5cfb02e9072bb22b0ebd16bfa162f9b12e023ff8d9158fb945",1131),("manifest.json","da57c749c817742e8ad3a28bccc32e5d9eed4377e358cf2f6e358a2806da8306",2516),("controller.py","9dfad55126c68bc02a3a16c45b0d487c3af363182d45914fb409850c63309487",17140)]:
 r=pin(B/name);assert r["sha256"]==sha and r["bytes"]==size
refs=[pin(B/"handoff.json"),pin(B/"manifest.json")]+json.loads((B/"manifest.json").read_bytes())["members"]
refs += [pin(OLD/n) for n in ["controller.py","owned_job_hooks.py","phase_worker.py","job_probe_worker.py"]]
refs += [pin(PREV/n) for n in ["independent-source-review.json","independent_controls.py","controls.json"]]
rows=[]
for r in refs:
 p=Path(r["path"]);assert pin(p)==r;raw=p.read_bytes();out=O/(r["sha256"]+".raw")
 if not out.exists():out.write_bytes(raw)
 assert out.read_bytes()==raw;rows.append({"source_ref":r,"snapshot_ref":pin(out)})
old=(OLD/"controller.py").read_bytes();new=(B/"controller.py").read_bytes()
def apply_unified(raw,patch):
 original=raw.decode().splitlines(keepends=True);lines=patch.decode().splitlines(keepends=True);result=[];cursor=0;i=2
 while i<len(lines):
  match=re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n?",lines[i]);assert match,lines[i]
  oldline,oldcount,newline,newcount=match.groups();start=int(oldline)-1 if int(oldline) else 0;oc=int(oldcount or 1);nc=int(newcount or 1)
  result.extend(original[cursor:start]);cursor=start;i+=1;actualold=actualnew=0
  while i<len(lines) and not lines[i].startswith("@@"):
   line=lines[i];i+=1
   if line.startswith("\\\\ No newline"):continue
   assert line[0] in " +-",repr(line)
   if line[0] in " -":assert original[cursor]==line[1:];cursor+=1;actualold+=1
   if line[0] in " +":result.append(line[1:]);actualnew+=1
  assert actualold==oc and actualnew==nc
 result.extend(original[cursor:]);return "".join(result).encode()
forward=apply_unified(old,(B/"controller.forward.diff").read_bytes());inverse=apply_unified(new,(B/"controller.inverse.diff").read_bytes())
assert forward==new and inverse==old
oldt,newt=ast.parse(old),ast.parse(new)
funcs=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.FunctionDef)}
of,nf=funcs(oldt),funcs(newt)
changes=sorted(n for n in of.keys()&nf.keys() if of[n]!=nf[n]);added=sorted(nf.keys()-of.keys());removed=sorted(of.keys()-nf.keys())
assert changes==["close_canonical_lease","launch_reviewed_phase","pinned"] and added==["cleanup_confirmed"] and removed==[]
assert [ast.dump(n,include_attributes=False) for n in oldt.body if not isinstance(n,ast.FunctionDef)]==[ast.dump(n,include_attributes=False) for n in newt.body if not isinstance(n,ast.FunctionDef)]
unchanged={n:(OLD/n).read_bytes()==(B/n).read_bytes() for n in ["owned_job_hooks.py","phase_worker.py","job_probe_worker.py"]};assert all(unchanged.values())
for row in rows:assert pin(Path(row["source_ref"]["path"]))==row["source_ref"]
report={"rows":rows,"input_drift":0,"forward_matches_new_bytes":True,"inverse_matches_old_bytes":True,"changed_functions":changes,"added_functions":added,"removed_functions":removed,"other_top_level_AST_unchanged":True,"unchanged_dependencies":unchanged,"scope":"Only R01 R03 R04 delta; previous whole source review remains unchanged"}
(O/"intake.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in report.items() if k!="rows"},ensure_ascii=False))

