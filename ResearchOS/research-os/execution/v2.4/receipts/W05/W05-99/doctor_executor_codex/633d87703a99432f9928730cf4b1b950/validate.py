import pathlib,uuid,json,hashlib,subprocess,os,datetime,sys
root=pathlib.Path(__file__).resolve().parents[7]
dest=pathlib.Path(__file__).resolve().parent
main=pathlib.Path("D:/作品集/ResearchOS/research-os")
go=main/".local/tools/go1.27.1/go/bin/go.exe"
env=dict(os.environ,GOROOT=str(go.parent.parent),GOTOOLCHAIN="local",GOENV="off",GOPATH=str(main/".local/gopath"),GOCACHE=str(main/".local/gocache"),RESEARCHOS_GO=str(go),RESEARCHOS_WRITER_LEASE_TTL="60s")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,args):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(args,cwd=root,env=env,capture_output=True);(dest/(name+".stdout")).write_bytes(r.stdout);(dest/(name+".stderr")).write_bytes(r.stderr)
 row=dict(actualargv=args,cwd=str(root),exit=r.returncode,started_at=start,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(dest/(name+".stdout")),stderr_sha256=sha(dest/(name+".stderr")),mode="FIXTURE")
 (dest/(name+".invocation.json")).write_text(json.dumps(row,indent=2),encoding="utf-8");print(name,r.returncode,flush=True);return r
if __name__=="__main__":
 run("go-env",[str(go),"env","GOROOT","GOTOOLCHAIN","GOENV","GOPATH","GOCACHE","GOMODCACHE","GOVERSION"])
 run("git-before",["git","status","--porcelain=v1"])
 r=run("go-list",[str(go),"list","-deps","-json","./apps/cli"])
 text=r.stdout.decode(); dec=json.JSONDecoder(); paths=set()
 while text.strip():
  obj,n=dec.raw_decode(text.lstrip());text=text.lstrip()[n:];d=pathlib.Path(obj.get("Dir",""))
  if d.is_dir():
   paths.update(p for p in d.glob("*.go") if p.is_file())
   for f in obj.get("EmbedFiles",[]):paths.add(d/f)
 paths.update(root/p for p in ["go.mod","go.sum","apps/cli/main.go","apps/cli/cli_doctor.go","apps/cli/cli_doctor_test.go","tests/runtime/cli_contract/v2verbs.go","apps/cli/cli_stream_test.go"])
 before={str(p):sha(p) for p in sorted(paths) if p.is_file()};(dest/"source-before.json").write_text(json.dumps(before,indent=2),encoding="utf-8")
 exe=dest/"researchos-doctor.exe"
 b=run("build",[str(go),"build","-o",str(exe),"./apps/cli"])
 if b.returncode==0:
  env["RESEARCHOS_DOCTOR_TEST_BINARY"]=str(exe)
  run("focused",[str(go),"test","-count=1","-v","./apps/cli","-run","^TestW05Doctor"])
 after={str(p):sha(p) for p in sorted(paths) if p.is_file()};(dest/"source-after.json").write_text(json.dumps(after,indent=2),encoding="utf-8")
 (dest/"summary.json").write_text(json.dumps(dict(source_drift=before!=after,source_count=len(before),tool_sha256=sha(go),binary_sha256=sha(exe) if exe.exists() else None),indent=2),encoding="utf-8")
