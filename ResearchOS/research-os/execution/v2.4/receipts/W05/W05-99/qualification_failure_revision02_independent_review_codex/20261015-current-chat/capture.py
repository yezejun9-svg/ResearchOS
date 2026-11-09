import sys, subprocess, json, hashlib, datetime
from pathlib import Path
ROOT=Path(r'D:\作品集\ResearchOS\research-os')
OWN=Path(__file__).parent
COMMIT='4f4023c956f84d65743f39ce77d6c8899a21ada1'
def record(tag,argv):
    r=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    for kind,data in [('stdout',r.stdout),('stderr',r.stderr)]:
        (OWN/(tag+'.'+kind+'.raw')).write_bytes(data)
    with (OWN/'diagnostics.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tag':tag,'argv':argv,'exit':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()})+'\n')
    return r
if sys.argv[1]=='source':
    files=sys.argv[2:]
    for p in files:
        tag='source--'+p.replace('/','--')
        r=record(tag,['git','show',COMMIT+':'+p])
        print(json.dumps({'path':p,'exit':r.returncode,'sha256':hashlib.sha256(r.stdout).hexdigest(),'bytes':len(r.stdout)}))
elif sys.argv[1]=='read':
    p=sys.argv[2]; a=int(sys.argv[3]); b=int(sys.argv[4])
    text=(OWN/('source--'+p.replace('/','--')+'.stdout.raw')).read_text(encoding='utf-8').splitlines()
    print('\n'.join(f'{i+1}: {line}' for i,line in enumerate(text) if a<=i+1<=b))
elif sys.argv[1]=='search':
    record(sys.argv[2],['git','grep','-n','-E',sys.argv[3],COMMIT,'--',*sys.argv[4:]])
    print((OWN/(sys.argv[2]+'.stdout.raw')).read_text(encoding='utf-8'))
