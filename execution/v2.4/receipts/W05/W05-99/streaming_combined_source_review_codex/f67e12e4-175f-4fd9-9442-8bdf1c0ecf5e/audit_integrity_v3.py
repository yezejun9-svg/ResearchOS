import json,pathlib,hashlib,subprocess,concurrent.futures,datetime,re,os
MAIN=pathlib.Path("D:/作品集/ResearchOS/research-os")
WT=MAIN/".local/worktrees/codex-w0599-model-stream"
OUT=pathlib.Path(__file__).parent
C="0bbcef5347ed9bd3a1174c7d3df9dfd8a270e837"
PREFIX="execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/"
D=WT/PREFIX/"candidate-b8938f84655849b9847611dbf3440442"
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v): (OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def git(*a): return subprocess.check_output(["git",*a],cwd=WT)
hand=json.loads((D/"handoff.json").read_bytes()); sm=json.loads((D/"source_manifest.json").read_bytes()); man=json.loads((D/"manifest.json").read_bytes())
changed=git("diff-tree","--no-commit-id","--name-only","-r",C).decode().splitlines()
assert len(changed)==444 and len(sm["changed_owned_source"])==18
allowed={r["path"] for r in sm["changed_owned_source"]}
assert all(x in allowed or x.startswith(PREFIX) for x in changed)
refs={}
def walk(v):
 if isinstance(v,dict):
  if "path" in v and "sha256" in v: refs[v["path"]]=v["sha256"]
  for z in v.values():walk(z)
 elif isinstance(v,list):
  for z in v:walk(z)
for obj in (hand,sm,man):walk(obj)
fail=[]
for rel,expected in refs.items():
 p=WT/rel
 if not p.is_file() or h(p)!=expected:fail.append({"ref":rel,"expected":expected,"actual":h(p) if p.is_file() else None})
blobraw=git("cat-file","--batch") if False else None
proc=subprocess.run(["git","cat-file","--batch"],input="".join(C+":"+p+"\n" for p in changed).encode(),cwd=WT,stdout=subprocess.PIPE,check=True)
pos=0; blobrows=[]
for rel in changed:
 end=proc.stdout.index(b"\n",pos); header=proc.stdout[pos:end].split(); n=int(header[2]); raw=proc.stdout[end+1:end+1+n];pos=end+1+n+1
 assert header[1]==b"blob"
 digest=hashlib.sha256(raw).hexdigest()
 blobrows.append({"path":rel,"sha256":digest,"bytes":n})
 if digest!=h(WT/rel):fail.append({"blob_drift":rel})
write("commit_blobs.json",blobrows)
for row in sm["changed_owned_source"]:
 assert row["after_sha256"]==h(WT/row["path"])
 if row["before_sha256"] is not None:
  assert hashlib.sha256(git("show",C+"^:"+row["path"])).hexdigest()==row["before_sha256"]
for row in sm["protected_unchanged"]:
 assert row["sha256"]==h(WT/row["path"])
 assert hashlib.sha256(git("show",C+"^:"+row["path"])).hexdigest()==row["sha256"]
v1=json.loads((WT/hand["final_runs"][0]["source_before_ref"]["path"]).read_bytes())
for run in hand["final_runs"]:
 for key in ["source_before_ref","source_after_ref"]:
  assert json.loads((WT/run[key]["path"]).read_bytes())==v1
def locate(k):
 scope,rel=k.split(":",1)
 p= WT/rel if scope=="repo" else MAIN/rel if scope=="main" else pathlib.Path(rel) if scope=="absolute" else None
 if p is None: raise ValueError(k)
 low=str(p).replace("\\","/").lower()
 assert "/.local/resources/" not in low and (not low.endswith((".sqlite",".db",".sqlite3")) or k in ["repo:execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/test-53a6e07436494837878a09393994fdce/failed-fixture.sqlite","repo:execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/test-f4a65b87734641c8a39d7060dd8b24fb/actual-fixtures/TestCLIModelStreamInterruptedPrefix/fixture.sqlite"]) and "/vault/" not in low
 return p
# Input prefix spelling is inspected from declared snapshot, no private path fallback.
prefixes=sorted(set(k.split(":",1)[0] for k in v1))
write("vector_prefixes.json",prefixes)
def verify(item):
 k,w=item;p=locate(k)
 return None if p.is_file() and h(p)==w else {"path":k,"expected":w,"actual":h(p) if p.is_file() else None}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex: drift=[v for v in ex.map(verify,v1.items()) if v]
counts=[]
for run in hand["final_runs"]:
 raw=(WT/run["stdout_ref"]["path"]).read_text(encoding="utf8")
 inc={s:len(re.findall(r"^\s*--- "+s+r":",raw,re.M)) for s in ["PASS","FAIL","SKIP"]}
 top={s:len(re.findall(r"^--- "+s+r":",raw,re.M)) for s in ["PASS","FAIL","SKIP"]}
 inv=json.loads((WT/run["invocation_ref"]["path"]).read_bytes())
 assert inc==run["counts"]["inclusive"] and top==run["counts"]["top_level"] and inv["exit"]==0
 counts.append({"directory":run["directory"],"inclusive":inc,"top_level":top,"exit":inv["exit"]})
write("integrity_audit.json",{"candidate":C,"head":git("rev-parse","HEAD").decode().strip(),"status":git("status","--porcelain").decode(),"commit_blobs":len(blobrows),"owned_source":len(allowed),"receipt_blobs":len(changed)-len(allowed),"manifest_files":len(man["files"]),"all_refs":len(refs),"ref_failures":fail,"source_vector_count":len(v1),"source_vector_drift":drift,"source_vector_prefixes":prefixes,"final_actual_counts":counts,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(json.dumps({"refs":len(refs),"ref_failures":len(fail),"blobs":len(changed),"vector":len(v1),"drift":len(drift),"counts":counts}))

