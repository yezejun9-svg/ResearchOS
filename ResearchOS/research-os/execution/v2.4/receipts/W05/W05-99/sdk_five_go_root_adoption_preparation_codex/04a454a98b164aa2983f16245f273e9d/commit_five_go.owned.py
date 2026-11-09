import sys
sys.dont_write_bytecode=True
import hashlib,json,os,types,uuid
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os"); P=Path(__file__).resolve().parent
O=P/"owned-git-five-go-commit"; O.mkdir(exist_ok=False)
H=R/"execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
raw=H.read_bytes(); assert hashlib.sha256(raw).hexdigest()=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad" and len(raw)==18901
m=types.ModuleType("owned_git_root");m.__file__=str(H);exec(compile(raw,str(H),"exec"),m.__dict__)
lock=json.loads((R/"execution/toolchains/locked.json").read_bytes()); G=Path(lock["tools"]["git"]["path"]);assert hashlib.sha256(G.read_bytes()).hexdigest()==lock["tools"]["git"]["sha256"]
T=R/".local"/("sdk5-git-"+uuid.uuid4().hex); T.mkdir();(T/"temp").mkdir();(T/"profile").mkdir();(T/"hooks").mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(G.parent)+";C:/Windows/System32","PATHEXT":".EXE;.COM;.CMD;.BAT","USERPROFILE":str(T/"profile"),"APPDATA":str(T/"profile"),"LOCALAPPDATA":str(T/"profile"),"TEMP":str(T/"temp"),"TMP":str(T/"temp"),"GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_GLOBAL":"nul","GIT_NO_REPLACE_OBJECTS":"1","GIT_TERMINAL_PROMPT":"0","GIT_OPTIONAL_LOCKS":"0"}
prep=json.loads((P/"preparation.json").read_bytes()); F=[x["target"].replace("\\","/") for x in prep["mapping"]]
canon=[R/"execution/v2.4"/(x+".json") for x in ("checkpoint","path_ownership","step_state","commands")]; C=[x.read_bytes() for x in canon]
after=[(Path(x["prepared_ref"]["path"])).read_bytes() for x in prep["mapping"]]
assert [R.joinpath(x).read_bytes() for x in F]==after
assert json.loads(C[0])["revision"]==340
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,obj):
 p=O/n;p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode());return pin(p)
seq=0
def git(args):
 global seq
 seq+=1;n=f"{seq:02d}-git";argv=[str(G),"-c","core.hooksPath="+str(T/"hooks"),"-c","commit.gpgsign=false","-c","core.autocrlf=false"]+args
 so=O/(n+".stdout.raw");se=O/(n+".stderr.raw");save(n+".intent.json",{"argv":argv,"cwd":str(R),"environment":env,"timeout":60})
 result=None;error=None
 try:
  with so.open("xb") as out,se.open("xb") as err: result=m.run_owned(argv,str(R),env,out,err,60)
 except BaseException as exc: error=repr(exc);raise
 finally: save(n+".invocation.json",{"argv":argv,"result":result,"exception":error,"actual_native_exit":result["actual_exit"] if result else None,"stdout_ref":pin(so) if so.exists() else None,"stderr_ref":pin(se) if se.exists() else None})
 assert result["actual_exit"]==0 and not result["timed_out"] and result["error"] is None
 c=result["job_cleanup"];assert c["errors"]==[] and c["active_processes_last_observed"]==0 and all(c[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 assert [x.read_bytes() for x in canon]==C and [R.joinpath(x).read_bytes() for x in F]==after
 return so.read_bytes()
old=git(["rev-parse","HEAD"]).decode().strip();assert old=="e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7"
assert git(["symbolic-ref","--short","HEAD"]).decode().strip()=="main"
before=git(["status","--porcelain=v1","-z","--untracked-files=no"]);assert not git(["diff","--cached","--name-only","-z"])
entries=[x for x in before.split(b"\x00") if x]
old_other={e[3:].decode():e[:2] for e in entries if e[3:].decode().replace("\\","/") not in F}
assert len(old_other)==13,repr(old_other)
for i,f in enumerate(F,1): assert git(["show","HEAD:"+f])==(P/(str(i)+".before.go")).read_bytes()
git(["add","--"]+F)
staged=git(["diff","--cached","--name-only","-z"]);assert set(x.decode() for x in staged.split(b"\x00") if x)==set(F)
save("precommit.verified.json",{"old_head":old,"files":F,"preserved_dirty":{k:v.decode() for k,v in old_other.items()},"frozen_source_refs":[pin(R/f) for f in F],"canonical_refs":[pin(x) for x in canon]})
git(["-c","user.name=Codex","-c","user.email=codex@localhost","commit","-m","Wire read-only credentials and current Mu runtime qualification"])
new=git(["rev-parse","HEAD"]).decode().strip();assert len(new)==40 and new!=old
assert git(["rev-parse","HEAD^"]).decode().strip()==old
changed=git(["diff-tree","--no-commit-id","--name-only","-r","-z","HEAD"]);assert set(x.decode() for x in changed.split(b"\x00") if x)==set(F)
assert not git(["diff","--cached","--name-only","-z"])
now=git(["status","--porcelain=v1","-z","--untracked-files=no"])
now_entries={e[3:].decode():e[:2] for e in now.split(b"\x00") if e};assert now_entries==old_other
ref=save("commit.closed.json",{"old_head":old,"new_head":new,"files":F,"owned_git_operations":seq,"preserved_dirty_count":len(now_entries),"status_ref":pin(O/(f"{seq:02d}-git.stdout.raw")),"canonical_unchanged":True,"runtime_qualification":False,"formal_acceptance":False})
print(json.dumps({"commit_ref":ref,"new_head":new,"owned_git_operations":seq}),flush=True)
