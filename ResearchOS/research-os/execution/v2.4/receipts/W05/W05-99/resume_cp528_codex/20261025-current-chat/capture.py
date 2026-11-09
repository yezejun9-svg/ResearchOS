from pathlib import Path
import subprocess,json,hashlib,sys
p=Path(sys.argv[1]);v=json.loads(p.read_text(encoding='utf-8-sig'))
def ref(q):
 x=q.read_bytes();return {'path':str(q),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
dest=[p.with_name(p.stem+x)for x in ['.stdout.raw','.stderr.raw','.result.json']]
assert all(not q.exists()for q in dest)
r=subprocess.run(v['argv'],cwd=v['cwd'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
dest[0].write_bytes(r.stdout);dest[1].write_bytes(r.stderr)
dest[2].write_text(json.dumps({'recipe':ref(p),'native_exit':r.returncode,'stdout':ref(dest[0]),'stderr':ref(dest[1])},ensure_ascii=False,indent=2)+chr(10),encoding='utf8')
print(json.dumps({'result':ref(dest[2]),'native_exit':r.returncode},ensure_ascii=False));sys.stdout.flush();sys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr);raise SystemExit(r.returncode)
