from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ps=Path('C:/Users/yqyyds/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
assert sha(ps)=='362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139'
env={k:os.environ[k] for k in ['SystemRoot','WINDIR','COMSPEC','TEMP','TMP'] if k in os.environ};env['PATH']=str(ps.parent)
argv=[str(ps),'-NoLogo','-NoProfile','-File',str(R/'owner-regression.ps1')]
for n in ['command.json','stdout.raw','stderr.raw','result.json']:assert not (R/n).exists()
(R/'command.json').write_text(json.dumps({'argv':argv,'environment':env,'powershell_sha256':sha(ps),'test_sha256':sha(R/'owner-regression.ps1'),'scope':'Actual AST functions only, synthetic property getters; no helper entry/UIA/SDK'},indent=2)+'\n',encoding='utf-8')
with (R/'stdout.raw').open('wb') as out,(R/'stderr.raw').open('wb') as err:code=subprocess.run(argv,cwd=R,env=env,stdout=out,stderr=err,timeout=20).returncode
v={'exit_code':code,'stdout_sha256':sha(R/'stdout.raw'),'stderr_sha256':sha(R/'stderr.raw')};(R/'result.json').write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');print(json.dumps(v));raise SystemExit(code)
