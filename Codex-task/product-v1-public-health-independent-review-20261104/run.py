from pathlib import Path
import os,json,subprocess,hashlib
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
node=Path('C:/nvm4w/nodejs/node.exe');assert sha(node)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
env={k:os.environ[k] for k in ['SystemRoot','WINDIR','COMSPEC','TEMP','TMP'] if k in os.environ};env['PATH']=str(node.parent)
args=[str(node),str(R/'reproduce.cjs')]
for name in ['command.json','stdout.raw','stderr.raw','result.json']:assert not (R/name).exists()
(R/'command.json').write_text(json.dumps({'argv':args,'environment':env,'script_sha256':sha(R/'reproduce.cjs'),'node_sha256':sha(node)},indent=2)+'\n',encoding='utf-8')
with (R/'stdout.raw').open('wb') as out,(R/'stderr.raw').open('wb') as err:code=subprocess.run(args,cwd=R,env=env,stdout=out,stderr=err,timeout=15).returncode
result={'exit_code':code,'stdout_sha256':sha(R/'stdout.raw'),'stderr_sha256':sha(R/'stderr.raw'),'formal_increment':0}
(R/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));raise SystemExit(code)
