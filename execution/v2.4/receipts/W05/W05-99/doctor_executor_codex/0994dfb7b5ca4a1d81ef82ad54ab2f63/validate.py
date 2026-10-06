import pathlib,uuid,json,hashlib,subprocess,os,datetime,sys
root=pathlib.Path(__file__).resolve().parents[7]
dest=pathlib.Path(__file__).resolve().parent
main=pathlib.Path("D:/作品集/ResearchOS/research-os")
go=main/".local/tools/go1.27.1/go/bin/go.exe"
env=dict(os.environ,GOROOT=str(go.parent.parent),GOTOOLCHAIN="local",GOENV="off",GOPATH=str(main/".local/gopath"),GOCACHE=str(main/".local/gocache"),RESEARCHOS_GO=str(go),RESEARCHOS_WRITER_LEASE_TTL="60s")
env.update(RESEARCHOS_NODE="C:/nvm4w/nodejs/node.exe", RESEARCHOS_MU_BUNDLE=str(main/".local/w0599-queue-integration/mu-worker.mjs"), GOPROXY="off", GOSUMDB="off")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,args):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(args,cwd=root,env=env,capture_output=True);(dest/(name+".stdout")).write_bytes(r.stdout);(dest/(name+".stderr")).write_bytes(r.stderr)
 row=dict(actualargv=args,cwd=str(root),exit=r.returncode,started_at=start,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(dest/(name+".stdout")),stderr_sha256=sha(dest/(name+".stderr")),mode="FIXTURE")
 (dest/(name+".invocation.json")).write_text(json.dumps(row,indent=2),encoding="utf-8");print(name,r.returncode,flush=True);return r
if __name__=="__main__":
 assert sha(pathlib.Path(env["RESEARCHOS_MU_BUNDLE"]))=="adfe7f456975bd986e58845f23a865a8f6eec5c45973fa2f14d298795aae8a38"
 assert sha(pathlib.Path(env["RESEARCHOS_NODE"]))=="5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6"
 (dest/"fixed-environment.json").write_text(json.dumps({k:env[k] for k in ["GOROOT","GOTOOLCHAIN","GOENV","GOPATH","GOCACHE","GOPROXY","GOSUMDB","RESEARCHOS_NODE","RESEARCHOS_MU_BUNDLE"]},indent=2),encoding="utf-8")
 run("go-env",[str(go),"env","GOROOT","GOTOOLCHAIN","GOENV","GOPATH","GOCACHE","GOMODCACHE","GOVERSION"])
 run("git-before",["git","status","--porcelain=v1"])
 r=run("go-list",[str(go),"list","-deps","-test","-json","./apps/cli"])
 text=r.stdout.decode(); dec=json.JSONDecoder(); paths=set()
 while text.strip():
  obj,n=dec.raw_decode(text.lstrip());text=text.lstrip()[n:];d=pathlib.Path(obj.get("Dir",""))
  if d.is_dir():
   paths.update(p for p in d.glob("*.go") if p.is_file())
   for field in ["EmbedFiles","SFiles","CFiles","CXXFiles","MFiles","HFiles","FFiles","SysoFiles","SwigFiles","SwigCXXFiles"]:
    for f in obj.get(field,[]):paths.add(d/f)
 paths.update([pathlib.Path(env["RESEARCHOS_NODE"]),pathlib.Path(env["RESEARCHOS_MU_BUNDLE"])])
 paths.update(root/p for p in ["go.mod","go.sum","apps/cli/main.go","apps/cli/cli_doctor.go","apps/cli/cli_doctor_test.go","tests/runtime/cli_contract/v2verbs.go","apps/cli/cli_stream_test.go"])
 before={str(p):sha(p) for p in sorted(paths) if p.is_file()};(dest/"source-before.json").write_text(json.dumps(before,indent=2),encoding="utf-8")
 exe=dest/"researchos-doctor.exe"
 b=run("build",[str(go),"build","-o",str(exe),"./apps/cli"])
 if b.returncode==0:
  env["RESEARCHOS_DOCTOR_TEST_BINARY"]=str(exe)
  
  run("full-cli",[str(go),"test","-count=1","-v","./apps/cli"])

 after={str(p):sha(p) for p in sorted(paths) if p.is_file()};(dest/"source-after.json").write_text(json.dumps(after,indent=2),encoding="utf-8")
 (dest/"summary.json").write_text(json.dumps(dict(source_drift=before!=after,source_count=len(before),tool_sha256=sha(go),binary_sha256=sha(exe) if exe.exists() else None),indent=2),encoding="utf-8")
