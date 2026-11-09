import os,sys,json,hashlib,subprocess,time,re
from pathlib import Path
E=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os")
S=R/"execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp524/original-online-backup-readonly-resource-scope.json"
scope=json.loads(S.read_text(encoding="utf8"))
W=Path(scope["source_readonly_worktree"])
T=Path(scope["own_temporary_root"])
D=Path(scope["original_data_root"])
DB=Path(scope["original_database"])
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def native(i,args):
    recipe=dict(id=i,group="G01",fullargv=list(map(str,args)),cwd=str(W),relevantenv={k:os.environ.get(k) for k in ["TMP","TEMP","PYTHONUTF8","PATH"]},exact_sql=[],rawstdout=i+".stdout.raw",rawstderr=i+".stderr.raw",nativeexit=i+".exit.json",prewritten_at=time.time())
    save(i+".recipe.json",recipe)
    with (E/(i+".stdout.raw")).open("wb") as o,(E/(i+".stderr.raw")).open("wb") as e:
        p=subprocess.run(list(map(str,args)),cwd=W,stdout=o,stderr=e)
    save(i+".exit.json",dict(native_exit=p.returncode))
    if p.returncode:raise RuntimeError(i)
    return (E/(i+".stdout.raw")).read_text(encoding="utf8").strip()
def g01():
    assert hashlib.sha256(S.read_bytes()).hexdigest()=="56387a95a4158cbc4c83f7e350c2563b4b93c202acf4d555a29956d947cc366d"
    inp=[]
    for item in scope["inputs"]:
        p=R/item["path"];got=pin(p)
        assert got["sha256"]==item["sha256"] and got["bytes"]==item["bytes"]
        inp.append(got)
        if p.name.endswith("manifest.json"):
            v=json.loads(p.read_text(encoding="utf-8-sig"))
            print("INPUT_MANIFEST",str(p))
            # Only show evidence file names to locate public prior resource reports.
            if isinstance(v.get("files"),list):
                print(json.dumps([x.get("path",x.get("name")) for x in v["files"] if isinstance(x,dict)],ensure_ascii=False))
            elif isinstance(v.get("files"),dict):print(json.dumps(list(v["files"]),ensure_ascii=False))
        else:print(p.read_text(encoding="utf8"))
    save("input-pins.json",inp)
    assert native("g01-source-head",["git","-C",W,"rev-parse","HEAD"])==scope["source_commit"]
    assert native("g01-source-status",["git","-C",W,"status","--porcelain=v1"])==""
    src=W/"ops/backup/main.go";text=src.read_text(encoding="utf8")
    a=text.index("var active int");b=text.index("var m domain.BackupManifest",a)
    print("EXACT_ACTIVE_WORKSPACE_SELECTOR",text[a:b])
    names=["client_command_queue","client_control_requests","runtime_dispatches","resource_effects","resource_resolutions","runtime_observations","model_stream","resource_progress","budget"]
    for p in sorted((W/"migrations/sqlite").glob("*.sql")):
        txt=p.read_text(encoding="utf8")
        for line in txt.splitlines():
            if re.search(r"CREATE TABLE",line,re.I) and any(n in line for n in names):print(p.name,line)
    # Fixed public Source excerpts only; no original DB access in this group.
    for rel in ["internal/domain/backup_workspace.go","internal/domain/backup_recovery.go","internal/domain/backup_command_queue.go"]:
        p=W/rel;txt=p.read_text(encoding="utf8")
        if rel.endswith("backup_workspace.go"):print("WORKSPACE_LIMITS","\n".join(txt.splitlines()[13:24]))
        if rel.endswith("backup_recovery.go"):print("RESTORE_CONSTRAINT","\n".join(txt.splitlines()[220:245]))
    save("source-input-pins.json",[pin(W/r) for r in ["ops/backup/main.go","internal/domain/backup_workspace.go","internal/domain/backup_recovery.go","internal/domain/backup_command_queue.go","internal/host/host.go","apps/control/main.go"]])
    print("G01_SOURCE_AND_INPUTS_COMPLETE")
if __name__=="__main__":globals()[sys.argv[1]]()

