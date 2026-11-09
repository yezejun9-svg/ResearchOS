from pathlib import Path
import json,hashlib,difflib,re
own=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_fence_semantics_independent_source_review_codex/9dbd54518abc4d18ba53261413b8cba5')
src=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_fence_semantics_revision_preparation_codex/65c17a2368284d90beec9526fba58a44')
own.mkdir(parents=True,exist_ok=True)
def meta(p):
 b=p.read_bytes();return {"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def check(ref):
 a=meta(Path(ref["path"]))
 if (a["sha256"],a["bytes"])!=(ref["sha256"],ref["bytes"]):raise ValueError("frozen SHA/bytes mismatch "+ref["path"])
 return a
h=json.loads((src/"handoff.json").read_text(encoding="utf-8"))
m=json.loads((src/"manifest.json").read_text(encoding="utf-8"))
expected={"handoff.json":("9990f6421a34fdd79b28f38fee52fb7d75e5d1d03fb3f25486f769319d648b40",8251),"manifest.json":("c78b7e5d6c2eecc15d80ebba725dab8a3e2c89d218785fcebab744bde3ee683d",7872)}
for name,exp in expected.items():
 a=meta(src/name)
 if (a["sha256"],a["bytes"])!=exp:raise ValueError("parent fixed input differs")
members=[]
for r in m["files"]:
 check(r);p=Path(r["path"]);dest=own/"inputs"/p.relative_to(src);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());members.append(r)
(own/"inputs/manifest.json").write_bytes((src/"manifest.json").read_bytes())
external=[]
def walk(x):
 if isinstance(x,dict):
  if {"path","sha256","bytes"}<=set(x):
   a=check(x)
   if not Path(x["path"]).is_relative_to(src):external.append(a)
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(h)
before=json.loads(Path(h["input_before_ref"]["path"]).read_text(encoding="utf-8"))
after=json.loads(Path(h["input_after_ref"]["path"]).read_text(encoding="utf-8"))
bv={r["path"]:(r["sha256"],r["bytes"]) for r in before["files"]};av={r["path"]:(r["sha256"],r["bytes"]) for r in after["files"]}
public=[];nonreceipt_originals_unread=[]
for r in before["files"]:
 if "/execution/v2.4/receipts/" in r["path"].replace("\\","/"):public.append(check(r))
 else:nonreceipt_originals_unread.append(r)
def apply(old,patch,final):
 a=old.decode("utf-8").splitlines();p=patch.decode("utf-8").splitlines();cursor=0;out=[];i=2;hc=0
 while i<len(p):
  hit=re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*",p[i])
  if hit is None:raise ValueError("actual patch hunk header")
  start=int(hit[1])-1;oc=int(hit[2] or 1);nc=int(hit[4] or 1)
  if start<cursor:raise ValueError("patch overlap")
  out.extend(a[cursor:start]);cursor=start;i+=1;x=y=0;hc+=1
  while i<len(p) and not p[i].startswith("@@ "):
   row=p[i]
   if row=="\\ No newline at end of file":i+=1;continue
   if not row or row[0] not in " +-":raise ValueError("actual patch prefix")
   tag,content=row[0],row[1:]
   if tag in " -":
    if cursor>=len(a) or a[cursor]!=content:raise ValueError("patch OLD mismatch")
    cursor+=1;x+=1
   if tag in " +":out.append(content);y+=1
   i+=1
  if (x,y)!=(oc,nc):raise ValueError("hunk actual count mismatch")
 out.extend(a[cursor:])
 newline="\r\n" if b"\r\n" in final else "\n"
 rebuilt=(newline.join(out)+(newline if final.endswith(b"\n") else "")).encode("utf-8")
 return {"hunks":hc,"exact_final_bytes":rebuilt==final}
stats={}
for label,bk,fk,pk,ipk in [("source","base_source_ref","source_ref","source_patch_ref","source_inverse_patch_ref"),("tests","base_test_ref","test_ref","test_patch_ref","test_inverse_patch_ref")]:
 old=Path(h[bk]["path"]).read_bytes();new=Path(h[fk]["path"]).read_bytes();forward=apply(old,Path(h[pk]["path"]).read_bytes(),new);inverse=apply(new,Path(h[ipk]["path"]).read_bytes(),old)
 if not forward["exact_final_bytes"] or not inverse["exact_final_bytes"]:raise ValueError("whole-byte patch differs")
 a=old.decode("utf-8").splitlines(keepends=True);b=new.decode("utf-8").splitlines(keepends=True)
 ops=[x for x in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes() if x[0]!="equal"]
 (own/(label+".independent-full-diff.txt")).write_bytes("".join(difflib.unified_diff(a,b,fromfile=label+"-v2",tofile=label+"-v3",n=3)).encode("utf-8"))
 stats[label]={"base_lines":len(a),"final_lines":len(b),"forward":forward,"inverse":inverse,"changed_ranges":[{"kind":t,"old_start":i+1,"old_end":j,"new_start":k+1,"new_end":l} for t,i,j,k,l in ops]}
if len(bv)!=len(before["files"]) or len(av)!=len(after["files"]) or bv!=av or after["drift_count"]!=0:raise ValueError("actual101vector mismatch")
producers=[]
for r in before["files"]:
 if "/producer-evidence/" in r["path"]:
  p=Path(r["path"]);dest=own/"producer-evidence"/p.name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(p.read_bytes());producers.append(meta(dest))
record={"schema":"researchos.f08-v3-independent-input-verification.v1","author_handoff":meta(src/"handoff.json"),"author_manifest":meta(src/"manifest.json"),"member_count":len(members),"physical_with_manifest":len(members)+1,"members":members,"external_handoff_refs_verified":external,"full_source_test_bytes_loaded":True,"stats":stats,"before_count":len(before["files"]),"after_count":len(after["files"]),"public_refs_rehashed":public,"public_vectors_equal_sha_bytes":True,"public_input_drift":0,"nonreceipt_originals_unread":nonreceipt_originals_unread,"original_failed_script_9d9d3e_not_modified_or_reexecuted":True,"this_is_post_shape_fixed_receipt_subset_report":True,"producer_evidence_copies":producers,"candidate_or_native_execution":False,"GoAST_compile":False}
(own/"input-verification.json").write_bytes((json.dumps(record,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
print(json.dumps({"member_count":len(members),"physical_with_manifest":len(members)+1,"public_refs_rehashed":len(public),"vector_equal":True,"stats":stats,"producer_copy_count":len(producers)},ensure_ascii=True))

