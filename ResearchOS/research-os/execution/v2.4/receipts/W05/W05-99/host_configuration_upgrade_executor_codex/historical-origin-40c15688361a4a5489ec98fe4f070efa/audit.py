import datetime, hashlib, json, pathlib, subprocess
out=pathlib.Path(__file__).resolve().parent
root=out.parents[6]
commit='396287cc5427eb125aaedb8a2b7fadf63e6b9322'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(name,value): (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
rows=[]
for index,path in enumerate(['internal/domain/backup_upgrade_test.go','internal/domain/durability.go','internal/domain/runtime_dispatch.go'],1):
    argv=['git','show',commit+':'+path]
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    r=subprocess.run(argv,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out/(str(index)+'.stdout')).write_bytes(r.stdout)
    (out/(str(index)+'.stderr')).write_bytes(r.stderr)
    save(str(index)+'.invocation.json',dict(actualargv=argv,cwd=str(root),started_at=start,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit=r.returncode))
    assert r.returncode==0
    current=(root/path).read_bytes()
    assert current==r.stdout,path
    rows.append(dict(path=path,base_commit=commit,base_sha256=sha(r.stdout),current_sha256=sha(current),equal=True,git_blob_raw=str(index)+'.stdout'))
save('audit.json',dict(status='READONLY_BASELINE_BYTE_CAUSAL_AUDIT_NOT_RUNTIME_REEXECUTION',actor='codex:/root/sources_parent_impl',rows=rows,conclusion='Historical14 ActiveRecovery helper, current ResumeCheckpoint method and runtimeDispatch query are byte-identical to immutable base396287. Source14 fixture lacks the later runtime_dispatches table; the same unchanged method queries it unconditionally. This preserves an inherited historical-fixture/current-runtime incompatibility, not proof of a new23 source regression. No baseline execution is fabricated.',limitations='This is the requested unchanged-byte causal comparison; not a new matching-source historical14 resume qualification or approval to modify protected tests.',raw_current_failure='execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/closure-214eca5bd7b542f195ff14c505c46e9f/test.stdout',tool_diagnostic={'chunk':'2063a6','exit':1,'reason':'Windows literal wildcard rg argument invalid; read-only. Corrected using -g flag in chunk18ffff.'}))
files=sorted(p for p in out.iterdir() if p.is_file())
save('manifest.json',{'files':[dict(path=p.relative_to(root).as_posix(),sha256=sha(p.read_bytes())) for p in files]})
print(json.dumps({'path':(out/'audit.json').relative_to(root).as_posix(),'sha256':sha((out/'audit.json').read_bytes())},ensure_ascii=False))
