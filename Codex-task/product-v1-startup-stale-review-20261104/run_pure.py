from pathlib import Path
import os,json,subprocess,hashlib
R=Path(__file__).resolve().parent
node=Path('C:/nvm4w/nodejs/node.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
env={k:os.environ[k] for k in ['SystemRoot','WINDIR','COMSPEC','TEMP','TMP'] if k in os.environ}
env['PATH']=str(node.parent)+os.pathsep+str(Path(env['SystemRoot'])/'System32')
cmd=[str(node),str(R/'reproduce.cjs')]
for name in ['pure.command.json','pure.stdout.raw','pure.stderr.raw','pure.result.json']:assert not (R/name).exists()
(R/'pure.command.json').write_text(json.dumps({'argv':cmd,'environment':env,'script_sha256':sha(R/'reproduce.cjs'),'node_sha256':sha(node),'no_product_boot':True},indent=2)+'\n',encoding='utf-8')
with (R/'pure.stdout.raw').open('wb') as out,(R/'pure.stderr.raw').open('wb') as err:
 code=subprocess.run(cmd,env=env,cwd=R,stdout=out,stderr=err,timeout=20).returncode
result={'exit_code':code,'stdout_sha256':sha(R/'pure.stdout.raw'),'stderr_sha256':sha(R/'pure.stderr.raw'),'formal_increment':0}
(R/'pure.result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
raise SystemExit(code)
