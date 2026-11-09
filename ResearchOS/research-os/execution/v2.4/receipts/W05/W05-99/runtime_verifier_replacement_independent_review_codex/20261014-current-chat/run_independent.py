from pathlib import Path
import os,sys,json,subprocess,hashlib,datetime
MAIN=Path(r"D:\作品集\ResearchOS\research-os")
E=MAIN/"execution/v2.4/receipts/W05/W05-99/runtime_verifier_replacement_independent_review_codex/20261014-current-chat"
W=MAIN/".local/worktrees/verifier-replacement-20261014"
GO=MAIN/".local/tools/go1.27.1/go/bin/go.exe"
TMP=MAIN/".local/tmp/vr-independent-20261014"
TMP.mkdir(parents=True,exist_ok=True)
label=sys.argv[1];args=sys.argv[2:]
env={k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT","WINDIR","COMSPEC","PATH","PATHEXT","USERPROFILE","LOCALAPPDATA","APPDATA","PROGRAMDATA","PROGRAMFILES","PROGRAMFILES(X86)","HOMEDRIVE","HOMEPATH"}}
env.update(TEMP=str(TMP),TMP=str(TMP),GOCACHE=str(MAIN/".local/go-cache/verifier-replacement-20261014"),GOMODCACHE=str(MAIN/".local/tools/gopath/pkg/mod"),GOTOOLCHAIN="local",GOPROXY="off",GOSUMDB="off")
start=datetime.datetime.now(datetime.timezone.utc).isoformat();argv=[str(GO)]+args
log=E/(label+".log")
with log.open("wb") as f:
 r=subprocess.run(argv,cwd=W,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
raw=log.read_bytes();meta={"label":label,"argv":argv,"cwd":str(W),"environment_allowlist":env,"started_at":start,"ended_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"exit_code":r.returncode,"log_sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
(E/(label+".json")).write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
with (E/"attempt-ledger.jsonl").open("a",encoding="utf-8") as f:f.write(json.dumps(meta,ensure_ascii=False)+"\n")
print(json.dumps({k:meta[k] for k in ["label","exit_code","bytes","log_sha256"]}));print(raw.decode("utf-8","replace")[-1800:]);sys.exit(r.returncode)
