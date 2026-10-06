import os,json,subprocess,pathlib,hashlib,datetime
p=pathlib.Path(__file__).parent;r=p.parents[6];w=r/".local/worktrees/codex-w0599-cli-read-interrupt"
go=r/".local/tools/go1.27.1/go/bin/go.exe"
e=os.environ.copy();e.update({"GOROOT":str(go.parents[1]),"GOPATH":str(r/".local/gopath"),"GOCACHE":str(r/".local/gocache"),"GOTOOLCHAIN":"local","GOENV":"off","GOPROXY":"off","GOSUMDB":"off"})
argv=[str(go),"test","-overlay",str(p/"overlay.json"),"./apps/cli","-run","^TestIndependentOversizeCannotBecomeSignalFailure$","-count=1","-v","-timeout=45s"]
x=subprocess.run(argv,cwd=w,env=e,capture_output=True);(p/"stdout.raw").write_bytes(x.stdout);(p/"stderr.raw").write_bytes(x.stderr)
(p/"invocation.json").write_text(json.dumps({"argv":argv,"cwd":str(w),"exit_code":x.returncode,"go_sha256":hashlib.sha256(go.read_bytes()).hexdigest(),"stdout_sha256":hashlib.sha256(x.stdout).hexdigest(),"stderr_sha256":hashlib.sha256(x.stderr).hexdigest()},indent=2),encoding="utf-8")
print(json.dumps({"exit":x.returncode,"stdout":x.stdout.decode(errors="replace"),"stderr":x.stderr.decode(errors="replace")}))
