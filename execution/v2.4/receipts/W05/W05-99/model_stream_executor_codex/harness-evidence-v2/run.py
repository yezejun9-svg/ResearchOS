import os,sys,json,uuid,subprocess,datetime,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[7];main=Path("D:/作品集/ResearchOS/research-os")
# Root derived from exact receipt path, never another worktree.
assert (root/"go.mod").is_file(),root
ns=root/"execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex";out=ns/("test-"+uuid.uuid4().hex);out.mkdir()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():
 paths=set()
 for name in ["internal","adapters","apps","tests","spec/v2.0/contracts","ops"]:
  for p in (root/name).rglob("*"):
   if p.is_file() and p.suffix in [".go",".mjs",".json",".sql"]:paths.add(p)
 for name in ["go.mod","go.sum"]:paths.add(root/name)
 return {str(p.relative_to(root)).replace(chr(92),"/"):h(p) for p in sorted(paths)}
before=sources();(out/"source_before.json").write_text(json.dumps(before,indent=2))
go=main/".local/tools/go1.27.1/go";node=Path("C:/nvm4w/nodejs/node.exe")
env=os.environ.copy();env.update(GOROOT=str(go),GOTOOLCHAIN="local",GOENV="off",GOPATH=str(main/".local/gopath"),GOCACHE=str(main/".local/gocache"),GOPROXY="off",GOSUMDB="off",RESEARCHOS_NODE=str(node),RESEARCHOS_MU_BUNDLE=str(root/".local/model-stream/mu-worker.mjs"))
env["RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR"]=str(out/"actual-fixtures")
argv=[str(go/"bin/go.exe"),*sys.argv[1:]]
if sys.argv[1]=="node":argv=[str(node),*sys.argv[2:]]
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out/"stdout.raw").open("wb") as stdout,(out/"stderr.raw").open("wb") as stderr:r=subprocess.run(argv,cwd=root,env=env,stdout=stdout,stderr=stderr)
after=sources();(out/"source_after.json").write_text(json.dumps(after,indent=2))
record={"actualargv":argv,"cwd":str(root),"exit":r.returncode,"started_at":start,"ended_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"measurement_mode":"FIXTURE","source_drift":before!=after,"tool_sha256":h(Path(argv[0])),"environment":{k:env[k] for k in ["GOROOT","GOTOOLCHAIN","GOENV","GOPATH","GOCACHE","GOPROXY","GOSUMDB","RESEARCHOS_NODE","RESEARCHOS_MU_BUNDLE"]},"bundle_sha256":h(Path(env["RESEARCHOS_MU_BUNDLE"])) if Path(env["RESEARCHOS_MU_BUNDLE"]).is_file() else None}
(out/"invocation.json").write_text(json.dumps(record,indent=2));print(out);print(json.dumps(record));print((out/"stdout.raw").read_text(errors="replace")[-24000:]);print((out/"stderr.raw").read_text(errors="replace")[-16000:]);sys.exit(r.returncode)
