from pathlib import Path
import json,hashlib,os,sys,types,datetime
ROOT=Path("D:/作品集/ResearchOS/research-os")
WT=ROOT/".local/worktrees/codex-w0999-causal-controls-r320-9a15d49131e8"
OUT=Path(__file__).resolve().parent
scope=json.loads((OUT/"root-w09_source_scope.json").read_text(encoding="utf-8"))
lock=json.loads((ROOT/"execution/toolchains/locked.json").read_text(encoding="utf-8"))["tools"]
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,d):
 with (OUT/n).open("x",encoding="utf-8") as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write("\n")
assert Path(sys.executable).resolve()==Path(lock["python"]["path"]).resolve()
assert ref(Path(sys.executable))["sha256"]==lock["python"]["sha256"]
h=scope["formatting"]["owned_process_helper_ref"];hp=ROOT/h["path"]
assert ref(hp)["sha256"]==h["sha256"]
g=scope["formatting"]["tool_ref"];gp=ROOT/g["path"]
assert ref(gp)["sha256"]==g["sha256"]
mod=types.ModuleType("w09_format_owned_process");mod.__file__=str(hp)
exec(compile(hp.read_bytes(),str(hp),"exec"),mod.__dict__)
paths=[WT/p for p in scope["source_paths"]]
argv=[str(gp),"-w"]+[str(p) for p in paths]
before=[ref(p) for p in paths]
save("format-01.before.json",before)
for p in paths:
 target=OUT/"format-01.before"/p.relative_to(WT);target.parent.mkdir(parents=True,exist_ok=True)
 with target.open("xb") as f:f.write(p.read_bytes())
env={k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT","WINDIR","COMSPEC","PATHEXT","NUMBER_OF_PROCESSORS","PROCESSOR_ARCHITECTURE"}}
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (OUT/"format-01.stdout.raw").open("xb") as so,(OUT/"format-01.stderr.raw").open("xb") as se:
 result=mod.run_owned(argv,str(WT),env,so,se,30)
save("format-01.invocation.json",{"actualargv":argv,"cwd":str(WT),"env":env,"started_at":start,"ended_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"result":result,"actual_native_exit":result.get("actual_exit"),"tool_ref":ref(gp),"python_ref":ref(Path(sys.executable)),"helper_ref":ref(hp),"static_format_only":True})
save("format-01.after.json",[ref(p) for p in paths])
print(json.dumps(result,ensure_ascii=False))
if result.get("actual_exit")!=0 or result.get("error") or result.get("timed_out") or (result.get("job_cleanup") or {}).get("errors"):
 raise SystemExit(1)
