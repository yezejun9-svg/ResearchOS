import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
rows=json.loads((N/'failure959-963.original-tool-io.json').read_bytes())['records']
refs=[]
for i,row in enumerate(rows):
 row.update(schema='researchos.original-tool-io.v1',actor_id='codex:/root/attach_fixture_source_review',root_assigned_ordinal=959+i,root_reported_next_failure=964,assignment='Root message confirmed chunk to ordinal mapping; five independent calls, counted once each')
 p=N/f'failure{959+i}.original-tool-io.json'
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
 raw=p.read_bytes();refs.append(dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
print(json.dumps(refs))

