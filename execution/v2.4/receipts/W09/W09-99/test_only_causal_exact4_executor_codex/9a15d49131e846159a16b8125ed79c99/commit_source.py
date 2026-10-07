from pathlib import Path
import json,hashlib,subprocess,datetime
OUT=Path(__file__).resolve().parent
WT=Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0999-causal-controls-r320-9a15d49131e8")
S=json.loads((OUT/"root-w09_source_scope.json").read_text(encoding="utf-8"))
AUDIT=json.loads((OUT/"protected-source-audit.json").read_text(encoding="utf-8"))
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,d):
 with (OUT/n).open("x",encoding="utf-8") as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write("\n")
def git(n,args):
 argv=["git","-c","core.quotepath=false",*args]
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(argv,cwd=WT,capture_output=True,timeout=60)
 for suffix,b in [("stdout.raw",p.stdout),("stderr.raw",p.stderr)]:
  with (OUT/("commit-"+n+"."+suffix)).open("xb") as f:f.write(b)
 save("commit-"+n+".invocation.json",{"actualargv":argv,"cwd":str(WT),"actual_native_exit":p.returncode,"started_at":start,"ended_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"stdout_ref":ref(OUT/("commit-"+n+".stdout.raw")),"stderr_ref":ref(OUT/("commit-"+n+".stderr.raw"))})
 if p.returncode:raise SystemExit(p.returncode)
 return p.stdout
for row in AUDIT["rows"]:assert ref(WT/row["path"])["sha256"]==row["current_ref"]["sha256"]
assert not git("index-pre",["diff","--cached","--name-only"])
assert git("head-pre",["rev-parse","HEAD"]).decode().strip()==S["base_commit"]
git("add",["add","--",*S["source_paths"]])
assert set(git("index-exact",["diff","--cached","--name-only"]).decode().splitlines())==set(S["source_paths"])
git("source",["commit","-m","test(w09): add bounded causal source controls"])
head=git("head-post",["rev-parse","HEAD"]).decode().strip()
assert git("parent-post",["rev-parse","HEAD^"]).decode().strip()==S["base_commit"]
assert set(git("paths-post",["diff-tree","--no-commit-id","--name-only","-r","HEAD"]).decode().splitlines())==set(S["source_paths"])
blobs=[]
for i,path in enumerate(S["source_paths"]):
 b=git("blob-"+str(i),["show",head+":"+path]);assert b==(WT/path).read_bytes()
 blobs.append({"path":path,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b),"git_blob":git("oid-"+str(i),["rev-parse",head+":"+path]).decode().strip()})
assert not git("tracked-post",["diff","--name-only"])
save("source-commit.json",{"commit":head,"parent":S["base_commit"],"exact_source_count":4,"source_blobs":blobs,"source_writer":"STOPPED","tests":"NOT_RUN","self_acceptance":False})
print(json.dumps({"source_commit":head,"sources":blobs,"writer":"STOPPED"},ensure_ascii=False))
