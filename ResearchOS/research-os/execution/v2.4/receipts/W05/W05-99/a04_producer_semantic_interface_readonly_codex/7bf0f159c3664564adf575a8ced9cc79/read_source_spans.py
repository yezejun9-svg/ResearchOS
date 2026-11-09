"""Read-only source spans. Saves exact public input bytes in this audit namespace."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');OUT=Path(__file__).resolve().parent
q=json.loads(Path(sys.argv[1]).read_bytes()); label=q['label']; entries=[]
for i,row in enumerate(q['files']):
 p=Path(row['path']);p=p if p.is_absolute() else ROOT/p
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();dst=OUT/('source-'+h+'.raw')
 if not dst.exists():
  with dst.open('xb') as f:f.write(raw)
 else:assert dst.read_bytes()==raw
 entries.append({'path':str(p),'sha256':h,'bytes':len(raw),'snapshot':str(dst)})
 lines=raw.decode('utf-8-sig').splitlines()
 print('\nFILE '+row['path'])
 for start,end in row.get('spans',[]):
  for n in range(start,min(end,len(lines))+1):print(str(n)+':'+lines[n-1])
 if row.get('symbols'):
  import re
  for n,line in enumerate(lines,1):
   if re.search(row['symbols'],line):print(str(n)+':'+line)
 assert p.read_bytes()==raw
with (OUT/('read-'+label+'.json')).open('xb') as f:f.write((json.dumps(entries,ensure_ascii=False,indent=2)+'\n').encode())
