import pathlib,json,os,subprocess,hashlib,datetime,re,sys
# Explicit roots, not candidate depth-derived authority.
ROOT=pathlib.Path("D:/作品集/ResearchOS/research-os")
OUT=pathlib.Path(__file__).resolve().parent
WT=ROOT/".local/worktrees/codex-w0599-session-list-identity-r306"
LOCAL=WT/".local/list-identity-build";LOCAL.mkdir(parents=True,exist_ok=True)
lock=json.loads((ROOT/"execution/toolchains/locked.json").read_bytes())["tools"]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(n,d):
 with (OUT/n).open("x",encoding="utf-8") as f:json.dump(d,f,ensure_ascii=False,indent=2)
def run(n,args,cwd=WT,timeout=300):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (OUT/(n+".stdout.raw")).open("xb") as out,(OUT/(n+".stderr.raw")).open("xb") as err:
  p=subprocess.run(args,cwd=cwd,env=env,stdout=out,stderr=err,timeout=timeout)
 save(n+".invocation.json",{"argv":args,"cwd":str(cwd),"environment_overrides":overrides,"started_at":start,"ended_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"actual_exit":p.returncode,"stdout_sha256":sha(OUT/(n+".stdout.raw")),"stderr_sha256":sha(OUT/(n+".stderr.raw"))})
 if p.returncode:raise RuntimeError(n+" failed; stop")
for key in ["go","python","git"]:
 if sha(lock[key]["path"])!=lock[key]["sha256"]:raise RuntimeError("tool hash "+key)
go=lock["go"]["path"];goroot=str(pathlib.Path(go).parent.parent)
for x in [LOCAL/"gocache",LOCAL/"tmp"]:x.mkdir(exist_ok=True)
overrides={"GOTOOLCHAIN":"local","GOENV":"off","GOROOT":goroot,"GOPATH":str(ROOT/".local/gopath"),"GOMODCACHE":str(ROOT/".local/gopath/pkg/mod"),"GOCACHE":str(LOCAL/"gocache"),"GOTMPDIR":str(LOCAL/"tmp"),"GOPROXY":"off","GOSUMDB":"off","GIT_OPTIONAL_LOCKS":"0","CGO_ENABLED":"0"}
env=os.environ.copy();env.update(overrides)
sources=["internal/domain/client_protocol_sessions.go","internal/api/v2_sessions_test.go"]
run("gofmt",[str(pathlib.Path(go).parent/"gofmt.exe"),"-w",*[str(WT/x) for x in sources]])
old=(OUT/"source-1.before").read_bytes();now=(WT/sources[1]).read_bytes();oldbody=old[old.index(b"// Only the host binding port"):];newbody=now[now.index(b"// Only the host binding port"):];
if not newbody.startswith(oldbody):raise RuntimeError("protected old test body drift")
run("go-version",[go,"version"])
run("go-list",[go,"list","-deps","-test","-compiled","-json","./internal/api"])
raw=(OUT/"go-list.stdout.raw").read_text(encoding="utf-8");dec=json.JSONDecoder();pos=0;packages=[]
while pos<len(raw):
 while pos<len(raw) and raw[pos].isspace():pos+=1
 if pos==len(raw):break
 d,pos=dec.raw_decode(raw,pos);packages.append(d)
paths=set()
for d in packages:
 if d.get("Error"):raise RuntimeError(d["Error"])
 directory=d.get("Dir")
 for field in ["GoFiles","CgoFiles","CompiledGoFiles","CFiles","CXXFiles","MFiles","HFiles","FFiles","SFiles","SwigFiles","SwigCXXFiles","SysoFiles","EmbedFiles","TestGoFiles","XTestGoFiles","TestEmbedFiles","XTestEmbedFiles"]:
  for name in d.get(field,[]):
   q=pathlib.Path(name);q=q if q.is_absolute() else pathlib.Path(directory)/q
   if q.is_file():paths.add(q.resolve())
   elif field!="CompiledGoFiles":raise RuntimeError("missing input "+str(q))
 for m in [d.get("Module",{})]:
  if m.get("GoMod"):paths.add(pathlib.Path(m["GoMod"]).resolve())
# Complete public compiler/stdlib and module source closure, including actual dependency resources.
for base in [pathlib.Path(goroot)/"src",pathlib.Path(goroot)/"pkg/tool",pathlib.Path(goroot)/"lib",WT/"migrations",WT/"spec/v2.0/contracts",WT/"internal/api/contracts"]:
 for q in base.rglob("*"):
  if q.is_file():paths.add(q.resolve())
for key in ["go","python","git"]:paths.add(pathlib.Path(lock[key]["path"]).resolve())
for q in [pathlib.Path(go).parent/"gofmt.exe",WT/"go.mod",WT/"go.sum",ROOT/"execution/toolchains/locked.json",pathlib.Path(__file__)]:paths.add(q.resolve())
# Keep every frozen handler38 source, not only the production dependency set.
mp=ROOT/"execution/v2.4/receipts/W05/W05-99/handler38_final_source_review_codex/a639cfcf998f4c7fb182db19c6788c3b/whole38_static_map.json"
md=json.loads(mp.read_bytes())
def walk(v):
 if isinstance(v,dict):
  if isinstance(v.get("path"),str) and (WT/v["path"]).is_file() and v["path"].endswith((".go",".py")):paths.add((WT/v["path"]).resolve())
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
walk(md);paths.add(mp.resolve())
run("handler38-delta",[lock["git"]["path"],"diff-tree","--no-commit-id","--name-only","-r","22752a6a41732c8c158d7d7e1b8932ec958f8cb8"])
frozen38=(OUT/"handler38-delta.stdout.raw").read_text(encoding="utf-8").splitlines()
if len(frozen38)!=38:raise RuntimeError("handler38 scope count")
for name in frozen38:paths.add((WT/name).resolve())
def vector(ps):return [{"path":str(q),"sha256":sha(q),"bytes":q.stat().st_size} for q in sorted(ps)]
before=vector(paths);save("inputs.before_compile.json",before);save("compiler.environment.json",overrides)
exe=OUT/"session-list-api.test.exe"
run("compile",[go,"test","-c","-work","-x","-o",str(exe),"./internal/api"],timeout=600)
text=(OUT/"compile.stderr.raw").read_text(encoding="utf-8",errors="strict");match=re.search(r"^WORK=(.+)$",text,re.M)
if not match:raise RuntimeError("missing compiler WORK")
work=pathlib.Path(match.group(1).strip());workpaths={q.resolve() for q in work.rglob("*") if q.is_file()}
for q in workpaths:
 if q.name=="_testmain.go" or q.name.startswith("importcfg"):
  dest=OUT/"generated"/q.relative_to(work);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(q.read_bytes())
save("compiled_WORK_vector.json",vector(workpaths));save("testexe.json",{"path":str(exe),"sha256":sha(exe),"bytes":exe.stat().st_size,"WORK":str(work)})
after=vector(paths);save("inputs.after_compile.json",after)
if before!=after:raise RuntimeError("compile input drift")
run("exe-buildinfo",[go,"version","-m",str(exe)])
save("build.result.json",{"status":"COMPILED_ONLY_CASES_NOT_RUN","input_count":len(before),"WORK_count":len(workpaths),"source_scope":sources,"source_sha256":{x:sha(WT/x) for x in sources},"new_exe":str(exe),"new_exe_sha256":sha(exe),"drift":0,"cases_executed":0})
print(json.dumps({"status":"COMPILED","inputs":len(before),"work":len(workpaths),"exe":sha(exe)}))
