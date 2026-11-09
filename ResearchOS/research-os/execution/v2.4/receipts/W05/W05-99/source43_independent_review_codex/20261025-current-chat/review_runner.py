import argparse, datetime, hashlib, json, os, pathlib, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

p = argparse.ArgumentParser()
p.add_argument('--label', required=True)
p.add_argument('--cwd', required=True)
p.add_argument('--env', default='{}')
p.add_argument('argv', nargs=argparse.REMAINDER)
a = p.parse_args()
base = pathlib.Path(__file__).parent / 'commands' / a.label
base.mkdir(parents=True, exist_ok=False)
argv = a.argv[1:] if a.argv[0] == '--' else a.argv
override = json.loads(a.env)
recipe = {'argv': argv, 'cwd': a.cwd, 'env_overrides': override, 'inherited_env': 'process environment; secrets not serialized', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
(base/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2),encoding='utf-8')
env = os.environ.copy(); env.update(override)
try:
    with (base/'stdout.raw').open('wb') as out, (base/'stderr.raw').open('wb') as err:
        run = subprocess.run(argv,cwd=a.cwd,env=env,stdout=out,stderr=err)
    code = run.returncode
except Exception as e:
    (base/'launcher-error.txt').write_text(repr(e),encoding='utf-8'); code = 127
result={'native_exit':code,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{}}
for f in base.iterdir():
    result['files'][f.name]={'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size}
(base/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'label':a.label,'native_exit':code},ensure_ascii=False))
for name in ['stdout.raw','stderr.raw']:
    f=base/name
    if f.exists(): print(f.read_bytes().decode('utf-8',errors='replace'))
sys.exit(code)
