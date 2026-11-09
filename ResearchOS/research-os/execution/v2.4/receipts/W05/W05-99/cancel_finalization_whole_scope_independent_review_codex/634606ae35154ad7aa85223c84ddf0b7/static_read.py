from pathlib import Path
import sys, json, hashlib, datetime, subprocess

NS = Path(__file__).resolve().parent
SRC = NS / 'sources' / 'cancel_finalization_udf_producer_supplement_codex'
actions = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
stamp = sys.argv[2]
out = []
results = []
for i, item in enumerate(actions):
    kind = item['kind']
    if kind == 'range':
        path = SRC / item['path']
        raw = path.read_bytes()
        lines = raw.decode('utf-8').splitlines()
        lo, hi = item['start'], min(item['end'], len(lines))
        body = '\n'.join(f'{j+1}: {lines[j]}' for j in range(lo-1, hi))
        out.append(f"FILE {item['path']} SHA256 {hashlib.sha256(raw).hexdigest()} LINES {lo}-{hi}\n{body}")
        results.append({'kind':kind,'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'lines':[lo,hi],'actual_exit':0})
    elif kind == 'rg':
        argv = ['rg', '-n', item['pattern'], str(SRC / item['path'])]
        if 'glob' in item: argv += ['--glob', item['glob']]
        p = subprocess.run(argv, capture_output=True)
        prefix = NS / 'commands' / f'{stamp}-{i}'
        prefix.with_suffix('.stdout.raw').write_bytes(p.stdout)
        prefix.with_suffix('.stderr.raw').write_bytes(p.stderr)
        result = {'argv':argv,'cwd':str(SRC),'actual_exit':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()}
        prefix.with_suffix('.result.json').write_text(json.dumps(result,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
        results.append(result)
        out.append('ARGV ' + json.dumps(argv,ensure_ascii=True) + '\n' + p.stdout.decode('utf-8','strict') + p.stderr.decode('utf-8','strict'))
        if p.returncode != 0: raise RuntimeError(f'rg actual_exit={p.returncode}; retained {prefix}')
    elif kind == 'schema':
        path = SRC / item['path']; raw = path.read_bytes(); d = json.loads(raw)
        for k in item['keys']: d = d[k]
        out.append(f"SCHEMA {item['path']} SHA256 {hashlib.sha256(raw).hexdigest()} " + json.dumps(d,ensure_ascii=True,indent=2))
        results.append({'kind':kind,'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'keys':item['keys'],'actual_exit':0})
    else: raise ValueError(kind)
payload = '\n\n'.join(out)
(NS/'commands'/f'{stamp}.stdout.txt').write_text(payload+'\n',encoding='utf-8')
(NS/'commands'/f'{stamp}.result.json').write_text(json.dumps({'argv':['python',str(Path(__file__).resolve()),sys.argv[1],stamp],'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actions':actions,'results':results,'actual_exit':0,'stdout_sha256':hashlib.sha256((payload+'\n').encode()).hexdigest()},ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print(payload)
