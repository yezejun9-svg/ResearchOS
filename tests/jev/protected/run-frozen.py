"""Bounded public preparation only. Never installs service or reads real keys."""
import datetime,hashlib,json,os,platform,subprocess,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def digest(p):return "sha256:"+hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def main():
 if platform.system()!="Windows":raise SystemExit("Windows required")
 go=Path(os.environ["RESEARCHOS_GO"])
 if subprocess.check_output([str(go),"version"],text=True).strip()!="go version go1.27.1 windows/amd64":raise SystemExit("Go 1.27.1 required")
 env={k:v for k,v in os.environ.items() if "TYPESAFE" not in k.upper() and "JEV" not in k.upper()}
 source=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
 dirty=subprocess.check_output(["git","status","--porcelain"],cwd=ROOT,text=True)
 if dirty:raise SystemExit("commit reviewed source before receipt")
 out=ROOT/"execution/receipts/W11/frozen-service-preparation"/str(uuid.uuid4());out.mkdir(parents=True)
 paths=[p for pattern in ["adapters/protectedstore/*.go","adapters/protectedstore/*.json","adapters/protectedstore/cmd/canary-broker/*","adapters/decision/*.go","evaluation/holdout/jev/*.go","tests/jev/protected/*","go.mod","go.sum"] for p in ROOT.glob(pattern) if p.is_file()]
 manifest={p.relative_to(ROOT).as_posix():digest(p) for p in paths}
 save(out/"source.json",{"revision":source,"dirty":False,"manifest":manifest,"platform":platform.platform(),"go":"go1.27.1","formal_holdout_accessed":False,"real_provider_called":False})
 commands=[]
 def run(name,args):
  cp=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=180)
  (out/(name+".stdout.log")).write_text(cp.stdout,encoding="utf-8");(out/(name+".stderr.log")).write_text(cp.stderr,encoding="utf-8")
  commands.append({"name":name,"argv":args,"exit":cp.returncode});save(out/"commands.json",commands)
  if cp.returncode:raise SystemExit("failed "+name+"; receipt "+str(out))
  return cp.stdout
 raw=run("public-tests",[str(go),"test","./adapters/protectedstore","-v","-count=1","-timeout=90s","-run","^TestFrozen|^TestCanary"])
 rows=[json.loads(line.split("FROZEN_ASSERTION ",1)[1]) for line in raw.splitlines() if line.startswith("FROZEN_ASSERTION ")]
 expected=json.loads((ROOT/"tests/jev/protected/frozen-expected.json").read_text())
 if sorted(r["assertion_id"] for r in rows)!=sorted(expected) or any(r["status"]!="PASS" or r["scope"]!="PUBLIC_FIXTURE_ONLY" or r["formal_holdout_accessed"] or r["real_provider_called"] for r in rows):raise SystemExit("assertion inventory failed")
 binary=ROOT/".local/canary-broker.exe";binary.parent.mkdir(exist_ok=True)
 run("build",[str(go),"build","-trimpath","-o",str(binary),"./adapters/protectedstore/cmd/canary-broker"])
 run("build-info",[str(go),"version","-m",str(binary)])
 run("plan",["pwsh","-NoProfile","-File",str(ROOT/"tests/jev/protected/deployment.ps1"),"-Binary",str(binary),"-ExpectedSHA256",digest(binary)[7:]])
 if manifest!={p.relative_to(ROOT).as_posix():digest(p) for p in paths}:raise SystemExit("source drift")
 save(out/"assertions.json",rows)
 save(out/"result.json",{"status":"EXECUTION_REPORTED","scope":"PUBLIC_FIXTURE_PREPARATION_ONLY","assertions":len(rows),"source_revision":source,"binary_sha256":digest(binary),"binary_path":str(binary),"formal_holdout_accessed":False,"real_provider_called":False,"service_installed":False,"formal_G04":"BLOCKED","formal_A08":"BLOCKED","utc":datetime.datetime.now(datetime.timezone.utc).isoformat()})
 print(str(out))
if __name__=="__main__":main()
