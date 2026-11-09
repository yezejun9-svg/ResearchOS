import pathlib,json,os,hashlib
E=pathlib.Path(__file__).parent;S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-combined-build-20261014')
old=E/'react-fixture/node_modules';assert old.is_junction() and old.parent.resolve()==(E/'react-fixture').resolve();os.rmdir(old)
dest=E/'react-source';rows=[]
for prefix in ['apps/web','spec/v2.0/ui','apps/desktop/main/lib']:
 for p in (S/prefix).rglob('*'):
  if p.is_file():
   rel=p.relative_to(S);assert 'node_modules' not in rel.parts
   q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());rows.append({'source':str(p),'fixture':str(q),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
(E/'react-fixture-supplement.json').write_text(json.dumps({'reason':'First independent small fixture flattened apps/web so original relative design-token import did not resolve. Recreated exact small source topology; first failure raw remains unchanged.','files':rows},ensure_ascii=True,indent=2),encoding='utf8')
script=(E/'run-react.py').read_text(encoding='utf8').replace("W=E/'react-fixture'","W=E/'react-source/apps/web'").replace("react-build.stdout.raw","react-build-r2.stdout.raw").replace("react-build.stderr.raw","react-build-r2.stderr.raw").replace("react-build.process.json","react-build-r2.process.json")
(E/'run-react-r2.py').write_text(script,encoding='utf8')
print(json.dumps({'files':len(rows),'bytes':sum(r['bytes'] for r in rows)}))
