from pathlib import Path
import json, hashlib, subprocess, sys, datetime
r=Path(__file__).resolve().parent
recipe=r/'25.recipe.json'
if recipe.exists() or (r/'FINAL-manifest.json').exists():
    raise RuntimeError('already sealed; append a separate revision instead')
code="from pathlib import Path; import json; r=Path('.'); names=['review.md','review.json','mandatory-addenda.json','classification-decisions.json','final-validation.json']; assert all((r/n).is_file() for n in names); [json.loads((r/n).read_text(encoding='utf-8')) for n in names if n.endswith('.json')]; print('Final review files present and JSON parseable; product tests=0; formal_increment=0')"
step={'id':'25','purpose':'Validate completed review then seal all owned files with SHA256 manifest','cwd':str(r),'argv':[sys.executable,'-X','utf8','-c',code],'seal_algorithm':'After native validation capture and diagnostic append, enumerate every regular owned file except FINAL-manifest.json, record relative path/raw SHA256/bytes, write new FINAL-manifest.json exactly once; no later file writes.'}
recipe.write_text(json.dumps(step,indent=2)+'\n',encoding='utf-8')
p=subprocess.run(step['argv'],cwd=r,capture_output=True)
(r/'25.stdout.raw').write_bytes(p.stdout)
(r/'25.stderr.raw').write_bytes(p.stderr)
(r/'25.exit.json').write_text(json.dumps({'exit_code':p.returncode,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})+'\n',encoding='utf-8')
with (r/'diagnostics.jsonl').open('a',encoding='utf-8') as f:
    f.write(json.dumps({'ordinal':'25','operation':step['purpose'],'recipe':recipe.name,'stdout':'25.stdout.raw','stderr':'25.stderr.raw','native_exit':p.returncode})+'\n')
if p.returncode: raise RuntimeError('final validation failed')
files=[]
for q in sorted(r.rglob('*')):
    if q.is_file() and q.name!='FINAL-manifest.json':
        raw=q.read_bytes()
        files.append({'path':q.relative_to(r).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
manifest={'schema':'researchos.immutable-independent-review-manifest.v1','reviewer':'codex:/root/qualification_failure_arch_review','scope':'CP509','root':str(r),'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,'file_count':len(files),'exclusions':['FINAL-manifest.json (self-reference)'],'actual_authority':False,'source_acceptance':False,'formal_increment':0}
target=r/'FINAL-manifest.json'
target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'files':len(files),'raw_validation_exit':p.returncode,'formal_increment':0},ensure_ascii=False))
