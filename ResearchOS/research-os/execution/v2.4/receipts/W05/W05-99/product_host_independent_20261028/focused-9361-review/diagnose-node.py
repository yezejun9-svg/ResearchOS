import os,json,subprocess,pathlib,hashlib
E=pathlib.Path(__file__).resolve().parent;W=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/desktop-installed-delivery-20261025')
env=dict(os.environ)
for k in list(env):
 if k.upper().startswith(('RESEARCHOS','ROS_DESKTOP','NODE','ELECTRON')) or 'PROXY' in k.upper(): del env[k]
env.update(json.loads((E/'environment.json').read_text(encoding='utf8'))['overrides'])
cmd=['C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe','--require',str(E/'trace-fs.cjs'),'--test','--test-name-pattern=generated tree refuses','tests/ui/desktop/product-host.test.mjs']
p=subprocess.run(cmd,cwd=W,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
(E/'node-diagnostic.stdout.raw').write_bytes(p.stdout);(E/'node-diagnostic.stderr.raw').write_bytes(p.stderr)
(E/'node-diagnostic.result.json').write_text(json.dumps({'argv':cmd,'exit':p.returncode,'source_input':hashlib.sha256((E/'source.after.json').read_bytes()).hexdigest()}),encoding='utf8')
print(p.stdout.decode('utf8'));print(p.stderr.decode('utf8'))
