"""Finite guarded static reads only; no product or producer entrypoint."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import uuid

N=Path(__file__).resolve().parent
G=N.parents[4]/'W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
# Explicit established SourceReadGuard bootstrap path.
G=Path(r'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\source_read_guard_revision_v2_codex\d6d10c192b1940ed9c11a957411aecd9\source_read_guard.py')
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(p,v):
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def main():
 spec=json.loads(sys.stdin.read());paths=[Path(x['path']).resolve(strict=True) for x in spec]
 loader=importlib.util.spec_from_file_location('w09_gap_sourceguard',G);m=importlib.util.module_from_spec(loader);sys.modules[loader.name]=m;loader.loader.exec_module(m)
 refs=[pin(p) for p in dict.fromkeys([G,Path(__file__),*paths])]
 guard=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
 try:
  guard.acquire(refs)
  for x,p in zip(spec,paths):
   text=p.read_text(encoding='utf-8-sig');lines=text.splitlines();mode=x.get('mode','text')
   print('FILE '+str(p))
   if mode=='grep':
    pattern=re.compile(x['pattern'])
    print('\n'.join(f'{i+1}: {line}' for i,line in enumerate(lines) if pattern.search(line)))
   elif mode=='jsonkeys':print(json.dumps(list(json.loads(text)),ensure_ascii=False))
   elif mode=='jsonfields':
    obj=json.loads(text)
    print(json.dumps({k:obj.get(k) for k in x['fields']},ensure_ascii=False,indent=2))
   else:
    start=x.get('start',1);end=x.get('end',len(lines));print('\n'.join(f'{i+1}: {lines[i]}' for i in range(start-1,min(end,len(lines)))))
  assert all(pin(r['path'])==r for r in refs)
 finally:cleanup=guard.close()
 assert cleanup['closed'] and cleanup['retained_handles_count']==0 and cleanup['errors']==[]
 out=save(N/('guarded-read-'+uuid.uuid4().hex+'.json'),dict(inputs=refs,source_guard=cleanup))
 print('GUARDED_READ '+json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
