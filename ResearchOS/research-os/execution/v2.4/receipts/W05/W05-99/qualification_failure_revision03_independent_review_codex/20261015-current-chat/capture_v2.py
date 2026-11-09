from pathlib import Path
import sys,json,subprocess,datetime
out=Path(__file__).resolve().parent
step=json.loads(sys.stdin.read())
name=step['id']; recipe=out/(name+'.recipe.json')
if recipe.exists(): raise RuntimeError('recipe already exists; append a new ordinal')
recipe.write_text(json.dumps(step,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=subprocess.run([sys.executable,'-X','utf8','-c',step['python']],cwd=step['cwd'],capture_output=True)
(out/(name+'.stdout.raw')).write_bytes(p.stdout)
(out/(name+'.stderr.raw')).write_bytes(p.stderr)
(out/(name+'.exit.json')).write_text(json.dumps({'exit_code':p.returncode,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})+'\n',encoding='utf-8')
with (out/'diagnostics.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps({'ordinal':name,'operation':step.get('purpose',''),'recipe':recipe.name,'stdout':name+'.stdout.raw','stderr':name+'.stderr.raw','native_exit':p.returncode},ensure_ascii=False)+'\n')
print(p.stdout.decode('utf-8',errors='replace'))
if p.stderr: print('STDERR '+p.stderr.decode('utf-8',errors='replace'))
print('NATIVE_EXIT='+str(p.returncode))
