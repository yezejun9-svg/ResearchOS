import json, os, pathlib, subprocess, sys, time
recipe_path=pathlib.Path(sys.argv[1])
r=json.loads(recipe_path.read_text(encoding='utf-8-sig'))
root=recipe_path.parent
id=r['id']
base=root/id
base.mkdir(exist_ok=False)
env=os.environ.copy()
env.update(r.get('env',{}))
argv=r['argv']
inv={'id':id,'argv':argv,'cwd':r['cwd'],'env':{k:env.get(k) for k in ('TMP','TEMP','GOTMPDIR','GOCACHE','GOPATH','GOTOOLCHAIN','GOFLAGS','PYTHONUTF8')},'recipe':str(recipe_path.resolve()),'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
(base/'invocation.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2),encoding='utf-8')
with (base/'stdout.raw').open('wb') as out, (base/'stderr.raw').open('wb') as err:
    try:
        result=subprocess.run(argv,cwd=r['cwd'],env=env,stdout=out,stderr=err,timeout=r.get('timeout',None))
        code=result.returncode
    except Exception as e:
        err.write((repr(e)+'\n').encode('utf-8'))
        code=127
(base/'exit.json').write_text(json.dumps({'exit':code,'end_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2),encoding='utf-8')
print((base/'stdout.raw').read_text(encoding='utf-8',errors='replace'))
if (base/'stderr.raw').stat().st_size: print((base/'stderr.raw').read_text(encoding='utf-8',errors='replace'),file=sys.stderr)
sys.exit(code)
