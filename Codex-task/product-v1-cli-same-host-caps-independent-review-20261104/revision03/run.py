from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
node=Path('C:/nvm4w/nodejs/node.exe');assert sha(node)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
env={k:os.environ[k] for k in ['SystemRoot','WINDIR','COMSPEC','TEMP','TMP'] if k in os.environ};env['PATH']=str(node.parent)
cmd=[str(node),str(R/'pure.mjs')]
for n in ['command.json','stdout.raw','stderr.raw','result.json']:assert not (R/n).exists()
(R/'command.json').write_text(json.dumps({'argv':cmd,'environment':env,'test_sha256':sha(R/'pure.mjs'),'node_sha256':sha(node)},indent=2)+'\n',encoding='utf-8')
with (R/'stdout.raw').open('wb') as out,(R/'stderr.raw').open('wb') as err:code=subprocess.run(cmd,cwd=R,env=env,stdout=out,stderr=err,timeout=20).returncode
v={'exit_code':code,'stdout_sha256':sha(R/'stdout.raw'),'stderr_sha256':sha(R/'stderr.raw'),'formal_increment':0};(R/'result.json').write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');print(json.dumps(v));raise SystemExit(code)
