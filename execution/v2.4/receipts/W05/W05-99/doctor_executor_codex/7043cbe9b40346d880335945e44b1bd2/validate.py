import pathlib,uuid,json,hashlib,subprocess,os,datetime,sys
root=pathlib.Path(__file__).resolve().parents[7]
dest=pathlib.Path(__file__).resolve().parent
main=pathlib.Path("D:/作品集/ResearchOS/research-os")
go=main/".local/tools/go1.27.1/go/bin/go.exe"
env=dict(os.environ,GOROOT=str(go.parent.parent),GOTOOLCHAIN="local",GOENV="off",GOPATH=str(main/".local/gopath"),GOCACHE=str(main/".local/gocache"),RESEARCHOS_GO=str(go),RESEARCHOS_WRITER_LEASE_TTL="60s")
env.update(RESEARCHOS_NODE="C:/nvm4w/nodejs/node.exe", RESEARCHOS_MU_BUNDLE=str(main/".local/w1401-mu-worker/mu-worker.mjs"), GOPROXY="off", GOSUMDB="off")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,args):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(args,cwd=root,env=env,capture_output=True);(dest/(name+".stdout")).write_bytes(r.stdout);(dest/(name+".stderr")).write_bytes(r.stderr)
 row=dict(actualargv=args,cwd=str(root),exit=r.returncode,started_at=start,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(dest/(name+".stdout")),stderr_sha256=sha(dest/(name+".stderr")),mode="FIXTURE")
 (dest/(name+".invocation.json")).write_text(json.dumps(row,indent=2),encoding="utf-8");print(name,r.returncode,flush=True);return r
if __name__=="__main__":
 env["GOFLAGS"]="-overlay="+str(dest.parent/"3ecc3ca99bd74821be8986203033e863/baseline-overlay.json")
 (dest/"fixed-environment.json").write_text(json.dumps({k:env[k] for k in ["GOROOT","GOTOOLCHAIN","GOENV","GOPATH","GOCACHE","GOPROXY","GOSUMDB","RESEARCHOS_NODE","RESEARCHOS_MU_BUNDLE","GOFLAGS"]},indent=2),encoding="utf-8")
 run("baseline-sdk",[str(go),"test","-count=1","-v","./apps/cli","-run","^TestCLIActual(MuInteractiveDurableQueue|MuInteractiveCancelUnknown|GoalCancelBeforeRun)$"])
