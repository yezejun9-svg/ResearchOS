"""Independent C22 fixed-source replay and evidence audit. Writes only this directory."""
import hashlib, importlib.util, json, os, pathlib, subprocess, sys, time
ROOT=pathlib.Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\protected-c22")
OUT=pathlib.Path(__file__).resolve().parent
AUTHOR=ROOT/"execution/receipts/W17/c22/20260930T161530Z-6fb9a11789"
SOURCE="6d070c8aeb9aa11c4fc48ced8048aa99ba45c84a"
RAW="3057b9cf21cd2f4756a2d18799f6973d7ff4e309"
GO=pathlib.Path(r"D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin\go.exe")
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v): (OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def git(*args):return subprocess.check_output(["git",*args],cwd=ROOT)
def audit():
    assert git("rev-parse","HEAD").decode().strip()==RAW
    baseline=git("status","--porcelain").decode()
    assert " M " not in baseline and "M  " not in baseline
    assert sha(AUTHOR/"report.json")=="85f1ff5a2172bf85761d9ea76e0e7da42e4647b40de103dbe23d034f2f289e23"
    assert sha(AUTHOR/"evidence-index.json")=="445f1eb401c7c4b7a72b419995e328882a4a3fa9d4bf2b5457df8e7a2247d491"
    indexed=read(AUTHOR/"evidence-index.json")["files"]
    for name,h in indexed.items():assert "sha256:"+sha(AUTHOR/name)==h,name
    report=read(AUTHOR/"report.json")
    for name,h in report["evidence_hashes"].items():assert "sha256:"+sha(AUTHOR/name)==h,name
    manifest=read(AUTHOR/"source-manifest.json")
    files=[]
    for name,h in manifest["files"].items():
        data=(ROOT/name).read_bytes()
        blob=git("show",SOURCE+":"+name)
        assert "sha256:"+hashlib.sha256(data).hexdigest()==h,name
        assert blob.replace(b"\r\n",b"\n")==data.replace(b"\r\n",b"\n"),name
        files.append({"path":name,"git_blob_sha256":hashlib.sha256(blob).hexdigest(),"working_sha256":hashlib.sha256(data).hexdigest(),"normalized_match":True})
    lock=read(ROOT/"execution/toolchains/locked.json")["tools"]["go"]
    assert sha(GO)==lock["sha256"]
    assert not git("diff","--name-only",SOURCE,RAW,"--","spec/v2.0").strip()
    save("source-audit.json",{"source_commit":SOURCE,"review_head":RAW,"baseline_status":baseline,"author_files_verified":len(indexed),"author_source_manifest_files_verified":len(files),"files":files,"author_report_sha256":sha(AUTHOR/"report.json"),"author_index_sha256":sha(AUTHOR/"evidence-index.json"),"hygiene":read(ROOT/"execution/receipts/W17/c22/hygiene.json"),"go_sha256":sha(GO),"spec_unchanged":True})
    return baseline
def validator(out):
    sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location("c22_author_validator",ROOT/"tests/security/c22_fixture.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    events=[json.loads(s) for s in (out/"go.stdout.jsonl").read_text(encoding="utf-8").splitlines()]
    checked=module.validate_evidence(out,events,read(ROOT/"tests/security/c22_expected.json"))
    save("replay-validation.json",checked)
    return checked
def main():
    baseline=audit()
    run=OUT/"replay"
    run.mkdir(exist_ok=False)
    command=[str(GO),"test","./internal/domain","-run","^TestW17C22ProtectedIsolation$","-count=1","-timeout=120s","-json"]
    env=dict(os.environ,GOTOOLCHAIN="local",GOENV="off",RESEARCHOS_GO=str(GO),RESEARCHOS_C22_EVIDENCE=str(run),PYTHONDONTWRITEBYTECODE="1")
    started=time.time()
    result=subprocess.run(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
    (run/"go.stdout.jsonl").write_bytes(result.stdout);(run/"go.stderr.log").write_bytes(result.stderr)
    save("command-replay.json",{"command":command,"cwd":str(ROOT),"source":SOURCE,"head":RAW,"environment":{k:env[k] for k in ("GOTOOLCHAIN","GOENV","RESEARCHOS_GO","RESEARCHOS_C22_EVIDENCE","PYTHONDONTWRITEBYTECODE")},"exit_code":result.returncode,"elapsed_seconds":time.time()-started,"stdout":"replay/go.stdout.jsonl","stderr":"replay/go.stderr.log"})
    assert result.returncode==0
    checked=validator(run)
    assert git("status","--porcelain").decode()==baseline
    print(json.dumps({"exit_code":result.returncode,"assertions":len(checked["assertions"]),"http":checked["http_count"],"scan":checked["scan"]}))
if __name__=="__main__":main()

