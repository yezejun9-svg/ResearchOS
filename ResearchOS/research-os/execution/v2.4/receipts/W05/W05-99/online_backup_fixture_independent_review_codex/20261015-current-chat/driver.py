import os,sys,json,hashlib,subprocess,time,shutil
from pathlib import Path
E=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os")
W=R/".local/worktrees/online-backup-fixture-qualification-20261015"
A=R/"execution/v2.4/receipts/W05/W05-99/online_backup_fixture_qualification_codex/20261015-current-chat"
T=R/".local/online-backup-independent-review-20261015-tmp"
ENV=os.environ.copy()
for k,n in [("TMP","tmp"),("TEMP","tmp"),("GOTMPDIR","go-tmp"),("GOCACHE","go-cache")]:
    p=T/n;p.mkdir(parents=True,exist_ok=True);ENV[k]=str(p)
ENV["GOMODCACHE"]=str(R/".local/tools/gopath/pkg/mod")
ENV["GOTOOLCHAIN"]="local"
ENV["PYTHONUTF8"]="1"
GO=R/".local/tools/go1.27.1/go/bin/go.exe"
def save(n,x):
    (E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def recipe(i,args,cwd=W):
    assert not (E/(i+".recipe.json")).exists(),i
    save(i+".recipe.json",dict(id=i,fullargv=list(map(str,args)),cwd=str(cwd),relevantenv={k:ENV.get(k) for k in ["TMP","TEMP","GOTMPDIR","GOCACHE","GOMODCACHE","GOTOOLCHAIN","PYTHONUTF8","PATH"]},rawstdout=i+".stdout.raw",rawstderr=i+".stderr.raw",nativeexit=i+".exit.json",at=time.time()))
def run(i,args,expected=0,cwd=W):
    recipe(i,args,cwd)
    with (E/(i+".stdout.raw")).open("wb") as out,(E/(i+".stderr.raw")).open("wb") as err:
        p=subprocess.run(list(map(str,args)),cwd=cwd,env=ENV,stdout=out,stderr=err)
    save(i+".exit.json",dict(native_exit=p.returncode,expected=expected,at=time.time()))
    if p.returncode!=expected:raise RuntimeError(f"{i}: {p.returncode} expected {expected}")
    print(i,p.returncode,flush=True)
    return (E/(i+".stdout.raw")).read_text(encoding="utf8",errors="replace")
def prepare():
    scope=R/"execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp522/online-backup-fixture-independent-review-scope.json"
    raw=scope.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=="b6cfd9fdd2406ae771e6a8949dedba611dc0764bd4671747c49a654c208c45a3"
    pins=[]
    for ent in json.loads(raw)["inputs"]:
        b=(R/ent["path"]).read_bytes()
        assert len(b)==ent["bytes"] and hashlib.sha256(b).hexdigest()==ent["sha256"],ent["path"]
        pins.append(ent)
    save("verified-input-pins.json",pins)
    code=(A/"fixture_setup.go").read_text(encoding="utf8")
    code=code.replace('"context"','"context"\n "bufio"\n "runtime"\n leaseRuntime "researchos.local/research-os/adapters/runtime"')
    code=code.replace('fatal(json.NewEncoder(os.Stdout).Encode(result))',r'''
    lease, err := leaseRuntime.AcquireDataRootLease(data); fatal(err)
    defer lease.Close()
    result["status"]="LIVE_HOST_DB_LEASE"
    result["pid"]=os.Getpid()
    result["held"]=lease.Held()
    result["host_instance_id"]=h.InstanceID()
    result["db_open_connections"]=db.Stats().OpenConnections
    fatal(db.PingContext(ctx))
    fatal(json.NewEncoder(os.Stdout).Encode(result))
    scan := bufio.NewScanner(os.Stdin)
    for scan.Scan() {
       if scan.Text()=="release" { break }
       fatal(db.PingContext(ctx))
       fatal(json.NewEncoder(os.Stdout).Encode(map[string]any{"status":"STILL_LIVE","host_instance_id":h.InstanceID(),"held":lease.Held(),"db_open_connections":db.Stats().OpenConnections,"pid":os.Getpid()}))
    }
    fatal(scan.Err())
    runtime.KeepAlive(h)
    fatal(db.Close())
    fatal(lease.Close())
    fmt.Println("{\"status\":\"CLOSED_NORMALLY\"}")
''')
    (E/"live_fixture.go").write_text(code,encoding="utf8")
    shutil.copyfile(A/"lease_probe.go",E/"lease_probe.go")
    shutil.copyfile(A/"census.py",E/"census.py")
    for helper in ["live_fixture","lease_probe"]:
        save(helper+".overlay.json",{"Replace":{str(W/"ops/backup/main.go"):str(E/(helper+".go"))}})
    (T/"build").mkdir(exist_ok=True)
    (T/"private").mkdir(exist_ok=True)
    save("preparation.json",dict(production_code_override=False,helper_only_overlay=True,concurrent_writer=False))
    print("prepared inputs and fresh helpers",flush=True)
def build():
    run("b01-build-real-cli",[GO,"build","-o",T/"build/backup.exe","./ops/backup"])
    for helper in ["live_fixture","lease_probe"]:
        run("b02-build-"+helper,[GO,"build","-overlay",E/(helper+".overlay.json"),"-o",T/("build/"+helper+".exe"),"./ops/backup"])
def fresh():
    case=T/"fixture"; data=case/"source-data"; db=data/"researchos.sqlite"
    cli=T/"build/backup.exe"; key=T/"private/recovery.key"; badkey=T/"private/wrong.key"
    backup=case/"encrypted-backup"; restore=case/"restored-data"
    run("f01-keygen",[cli,"keygen","--key-file",key])
    args=[T/"build/live_fixture.exe","Q02",case,W]
    i="f02-live-host-holder";recipe(i,args)
    err=(E/(i+".stderr.raw")).open("wb");out=(E/(i+".stdout.raw")).open("wb")
    p=subprocess.Popen(list(map(str,args)),cwd=W,env=ENV,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err)
    def line():
        raw=p.stdout.readline();out.write(raw);out.flush()
        if not raw:raise RuntimeError("holder exited before response")
        return json.loads(raw)
    try:
        ready=line();assert ready["status"]=="LIVE_HOST_DB_LEASE" and ready["held"] and ready["db_open_connections"]>=1
        save("live-ready.json",ready)
        probe=T/"build/lease_probe.exe"
        run("f03-probe-before",[probe,data],10)
        for tag in ["before"]:
            run("f04-db-"+tag,[sys.executable,"-B","-Xutf8",E/"census.py","db",db])
            run("f05-files-"+tag,[sys.executable,"-B","-Xutf8",E/"census.py","files",data])
            run("f06-acl-"+tag,["icacls",data,"/T"])
        run("f07-real-create",[cli,"create","--db",db,"--out",backup,"--key-file",key,"--root",W])
        assert p.poll() is None
        p.stdin.write(b"check\n");p.stdin.flush()
        check=line();assert check["status"]=="STILL_LIVE" and check["held"] and check["db_open_connections"]>=1
        assert check["host_instance_id"]==ready["host_instance_id"]
        save("live-after-create.json",check)
        run("f08-probe-after",[probe,data],10)
        run("f09-db-after",[sys.executable,"-B","-Xutf8",E/"census.py","db",db])
        run("f10-files-after",[sys.executable,"-B","-Xutf8",E/"census.py","files",data])
        run("f11-acl-after",["icacls",data,"/T"])
        run("f12-package-before-negative",[sys.executable,"-B","-Xutf8",E/"census.py","files",backup])
        run("f13-existing-destination",[cli,"create","--db",db,"--out",backup,"--key-file",key,"--root",W],1)
        assert b"DESTINATION_EXISTS" in (E/"f13-existing-destination.stderr.raw").read_bytes()
        run("f14-package-after-negative",[sys.executable,"-B","-Xutf8",E/"census.py","files",backup])
        run("f15-db-after-negative",[sys.executable,"-B","-Xutf8",E/"census.py","db",db])
    finally:
        if p.poll() is None:p.stdin.write(b"release\n");p.stdin.flush();p.stdin.close()
        tail=p.stdout.read();out.write(tail);out.close()
        code=p.wait(timeout=15);err.close();save(i+".exit.json",dict(native_exit=code,pid=p.pid))
    assert code==0
    run("f16-probe-released",[probe,data])
    run("f17-wrong-keygen",[cli,"keygen","--key-file",badkey])
    run("f18-wrong-key-restore",[cli,"restore","--as-data-root","--backup",backup,"--out",case/"wrong-restored","--key-file",badkey,"--root",W],1)
    assert b"BACKUP_MANIFEST_INVALID" in (E/"f18-wrong-key-restore.stderr.raw").read_bytes()
    assert not (case/"wrong-restored").exists()
    run("f19-real-restore",[cli,"restore","--as-data-root","--backup",backup,"--out",restore,"--key-file",key,"--root",W])
    run("f20-db-restored",[sys.executable,"-B","-Xutf8",E/"census.py","db",restore/"researchos.sqlite"])
    print("FRESH_REAL_CLI_LIVE_HOST_BACKUP_RESTORE_COMPLETE",flush=True)
if __name__=="__main__":
    globals()[sys.argv[1]]()

