import pathlib,json,subprocess,hashlib,os
R=pathlib.Path(__file__).resolve().parent;S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-status-repair-20261014')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=json.loads((R/'inputs/web-dependencies-census.json').read_text(encoding='utf-8-sig'));root=pathlib.Path(v['root'])
for e in v['files']:
 p=root/e['path'];assert p.stat().st_size==e['bytes'] and h(p)==e['sha256']
node=pathlib.Path('C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe')
argv=[str(node),str(root/'vite/bin/vite.js'),'build','apps/web','--outDir',str(R/'web-dist')]
(R/'build-command.json').write_text(json.dumps({'argv':argv,'cwd':str(S),'dependency_members_verified':len(v['files'])},ensure_ascii=False,indent=2),encoding='utf8')
with (R/'build.raw.txt').open('xb') as f:p=subprocess.run(argv,cwd=S,stdout=f,stderr=subprocess.STDOUT)
(R/'build.exit.json').write_text(json.dumps({'native_exit':p.returncode}),encoding='utf8')
for e in v['files']:assert h(root/e['path'])==e['sha256']
outputs=[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':h(p)} for p in (R/'web-dist').rglob('*') if p.is_file()]
(R/'build-outputs.json').write_text(json.dumps({'dependency_members_unchanged':len(v['files']),'outputs':outputs},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'build_native_exit':p.returncode,'dependency_members':len(v['files']),'output_files':len(outputs)}))
raise SystemExit(p.returncode)
