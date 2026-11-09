from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ps=Path('C:/Users/yqyyds/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
assert sha(ps)=='362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139'
env={k:os.environ[k] for k in ['SystemRoot','WINDIR','COMSPEC','TEMP','TMP'] if k in os.environ};env['PATH']=str(ps.parent)
argv=[str(ps),'-NoLogo','-NoProfile','-File',str(R/'owner-order.ps1')]
for n in ['owner-command.json','owner-stdout.raw','owner-stderr.raw','owner-result.json']:assert not (R/n).exists()
(R/'owner-command.json').write_text(json.dumps({'argv':argv,'environment':env,'powershell_sha256':sha(ps),'test_sha256':sha(R/'owner-order.ps1'),'scope':'AST functions only, fake PSCustomObject getter, no helper entrypoint or UIA'},indent=2)+'\n',encoding='utf-8')
with (R/'owner-stdout.raw').open('wb') as out,(R/'owner-stderr.raw').open('wb') as err:code=subprocess.run(argv,cwd=R,env=env,stdout=out,stderr=err,timeout=20).returncode
v={'exit_code':code,'stdout_sha256':sha(R/'owner-stdout.raw'),'stderr_sha256':sha(R/'owner-stderr.raw')};(R/'owner-result.json').write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');print(json.dumps(v));raise SystemExit(code)
