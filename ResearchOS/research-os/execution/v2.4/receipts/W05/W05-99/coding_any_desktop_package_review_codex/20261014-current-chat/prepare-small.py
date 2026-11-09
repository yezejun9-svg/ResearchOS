import pathlib,json,hashlib,shutil
E=pathlib.Path(__file__).parent;S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-combined-build-20261014')
old=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/status-package-independent-review-20261014/run-packaged-boundary-final.py')
raw=old.read_text(encoding='utf8').replace('normal-status-combined-5ddc0abb-20261014','normal-coding-any-a7ec7ebf-20261014').replace('qualification-status-repair-20261014','coding-any-combined-build-20261014').replace('74ad36a6a49588ff5fb42b9f9549115402bdbf1d710c15e90a4eadd324197fe9','31970ce5f6f797d859686c5cdc8bda28728bbc4549eb1f1a1e3cbcf9930ec16d')
(E/'run-packaged-boundary.py').write_text(raw,encoding='utf8')
mini=E/'react-fixture';mini.mkdir(exist_ok=False);files=[]
for p in (S/'apps/web').rglob('*'):
 if p.is_file():
  rel=p.relative_to(S/'apps/web');assert 'node_modules' not in rel.parts
  dest=mini/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());files.append({'source':str(p),'fixture':str(dest),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
(E/'small-fixture-inputs.json').write_text(json.dumps({'boundary_script_reused_from':str(old),'boundary_original_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'web_files':files},ensure_ascii=True,indent=2),encoding='utf8')
print(json.dumps({'small_web_files':len(files),'small_web_bytes':sum(x['bytes'] for x in files)}))
