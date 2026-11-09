import hashlib,json,os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os')
META=json.loads((HERE/'product-v1-managed-environment-source.json').read_bytes());WT=Path(META['worktree'])
OUT=HERE/'product-v1-managed-environment-author';assert not OUT.exists();OUT.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
for ref,digest in META['source_sha256'].items():
 assert sha(WT/ref)==digest
 dest=OUT/'source'/ref;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((WT/ref).read_bytes())
commands=[('syntax',[r'C:\nvm4w\nodejs\node.exe','--check','apps/desktop/main/lib/desktop-management.js']),('tests',[r'C:\nvm4w\nodejs\node.exe','--test','--test-reporter=spec','tests/ui/desktop/managed-environment.test.mjs','tests/ui/desktop/desktop-management-boundary.test.mjs']),('diff-check',['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks','diff','--check'])]
results=[]
for name,argv in commands:
 with (OUT/(name+'.stdout.raw')).open('xb') as stdout,(OUT/(name+'.stderr.raw')).open('xb') as stderr:
  r=subprocess.run(argv,cwd=WT,stdout=stdout,stderr=stderr,timeout=90,env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA'}})
 results.append(dict(name=name,argv=argv,exit_code=r.returncode,stdout_sha256=sha(OUT/(name+'.stdout.raw')),stderr_sha256=sha(OUT/(name+'.stderr.raw'))))
put(OUT/'checks.json',results);assert all(v['exit_code']==0 for v in results),results
for ref,digest in META['source_sha256'].items():assert sha(WT/ref)==digest
freeze=dict(schema='researchos.product-v1-source-freeze/1',source_sha256=META['source_sha256'],scope_ref=META['scope_ref'],worktree=str(WT),checks=results,formal_increment=0,product_acceptance_increment=0,real_cli_model_gui='NOT_RUN',status='FROZEN_FOR_INDEPENDENT_REVIEW')
put(OUT/'FROZEN.json',freeze);(OUT/'verify_product_v1_managed_environment.py').write_bytes(Path(__file__).read_bytes())
put(OUT/'EVIDENCE_MANIFEST.json',dict(files=[dict(path=str(p.relative_to(OUT)).replace('\\','/'),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(OUT.rglob('*')) if p.is_file()]))
print(json.dumps(dict(checks=results,freeze_sha256=sha(OUT/'FROZEN.json'),manifest_sha256=sha(OUT/'EVIDENCE_MANIFEST.json'))))
