from pathlib import Path
import hashlib,json,os,subprocess,sys,uuid,datetime
root=Path(r"D:/作品集/ResearchOS/research-os")
wt=Path(__file__).resolve().parents[6]
# receipts/W05/W05-99/executor_codex -> repository is six parents above script.
if not (wt/"go.mod").is_file(): raise SystemExit("candidate root check failed")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
locked=json.loads((root/"execution/toolchains/locked.json").read_text(encoding="utf-8"))
tool=locked["tools"]["go"]
if sha(Path(tool["path"])) != tool["sha256"]: raise SystemExit("Go binary hash mismatch")
selector=sys.argv[1] if len(sys.argv)>1 else "^(TestW05CLI|TestW14CLI)"
run=Path(__file__).parent/"runs"/(datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:10])
run.mkdir(parents=True)
paths=subprocess.check_output(["git","ls-files","apps/cli","internal","adapters","migrations","spec/v2.0/contracts","go.mod","go.sum"],cwd=wt,text=True).splitlines()
paths=sorted(set(p for p in paths if Path(p).suffix in (".go",".json",".sql",".mod",".sum"))|{"apps/cli/cli_stream.go","apps/cli/cli_stream_test.go"})
inputs=[{"path":p,"sha256":sha(wt/p)} for p in paths]
for entry in inputs:
 if entry["path"].startswith("apps/cli/"):
  dest=run/"source_snapshot"/entry["path"];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((wt/entry["path"]).read_bytes())
env=dict(os.environ);env.update({"GOTOOLCHAIN":"local","GOENV":"off","GOPATH":str(root/".local/gopath"),"GOCACHE":str(root/".local/gocache")})
args=[tool["path"],"test","-json","-count=1","./apps/cli","-run",selector,"-timeout","120s"]
manifest={"schema":"researchos.w05.cli-test-input.v1","mode":"FIXTURE_AND_REAL_LOCAL_HTTP_SQLITE_NOT_LIVE_MODEL","argv":args,"cwd":str(wt),"head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=wt,text=True).strip(),"git_status":subprocess.check_output(["git","status","--short"],cwd=wt,text=True).splitlines(),"tool":tool,"source_inputs":inputs,"runner_sha256":sha(Path(__file__)),"environment_names":sorted(env),"fixed_environment":{k:env[k] for k in ("GOTOOLCHAIN","GOENV","GOPATH","GOCACHE")},"started_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"provider_calls":0}
(run/"inputs.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
with (run/"stdout.jsonl").open("wb") as out,(run/"stderr.txt").open("wb") as err:
 try:
  proc=subprocess.run(args,cwd=wt,env=env,stdout=out,stderr=err,timeout=150);exit_code=proc.returncode
 except subprocess.TimeoutExpired: exit_code=124
changed=[p["path"] for p in inputs if sha(wt/p["path"])!=p["sha256"]]
rows=[]
for line in (run/"stdout.jsonl").read_text(encoding="utf-8",errors="replace").splitlines():
 try: rows.append(json.loads(line))
 except json.JSONDecodeError: pass
result={"schema":"researchos.w05.cli-test-result.v1","mode":manifest["mode"],"started_at":manifest["started_at"],"ended_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"exit_code":exit_code,"inputs_sha256":sha(run/"inputs.json"),"stdout_sha256":sha(run/"stdout.jsonl"),"stderr_sha256":sha(run/"stderr.txt"),"source_changed_during_run":changed,"test_pass":[r.get("Test") for r in rows if r.get("Action")=="pass" and r.get("Test")],"test_fail":[r.get("Test") for r in rows if r.get("Action")=="fail" and r.get("Test")],"test_skip":[r.get("Test") for r in rows if r.get("Action")=="skip" and r.get("Test")],"package_pass":any(r.get("Action")=="pass" and not r.get("Test") for r in rows),"provider_calls":0,"formal_case_count_delta":0}
(run/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"run":str(run),"result_sha256":sha(run/"result.json"),"exit_code":exit_code,"pass":len(result["test_pass"]),"fail":result["test_fail"],"source_changed":changed},ensure_ascii=True))
if exit_code or result["test_fail"]:
 print((run/"stderr.txt").read_text(encoding="utf-8",errors="replace")[-4000:])
 print("\n".join(r.get("Output","").strip() for r in rows if "Output" in r)[-6500:])
sys.exit(exit_code)
