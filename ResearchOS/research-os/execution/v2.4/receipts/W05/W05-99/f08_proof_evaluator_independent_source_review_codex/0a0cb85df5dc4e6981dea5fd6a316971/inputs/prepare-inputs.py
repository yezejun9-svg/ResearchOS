from pathlib import Path
import re,json,hashlib
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
B=ROOT/'execution/v2.4/receipts/W05/W05-99'
START=B/'cancel_finalization_v5_startup_caller_revision_codex/4639ce79ec914062ad92c278533a128f'
DOC=START/'snapshots/author-fd227/snapshot/v5'
PRIOR=B/'f08_callback_implementation_preparation_codex/6ed471dc8e114128a794b13b58691fc5'
SQL=START/'snapshots/author-fd227/candidate.sql.txt'
def ref(p,b):return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,v):
 with (OUT/n).open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
paths=[ROOT/x for x in ['go.mod','go.sum','internal/domain/store.go','internal/domain/contracts.go','internal/domain/client_protocol.go','internal/domain/client_command_identity.go','internal/domain/client_protocol_schema.go','internal/domain/backup_host_configuration.go','internal/domain/runtime_dispatch.go','internal/domain/runtime_admission.go','internal/domain/runtime_qualification.go','internal/domain/durability_checkpoint.go','internal/domain/client_command_queue.go','internal/domain/client_protocol_queue_control.go','internal/domain/orchestration.go','internal/domain/contracts/client.protocol.schema.json','internal/domain/contracts/client.protocol.domain.schema.json']]
paths += sorted((ROOT/'migrations/sqlite').glob('*.sql'))
paths += [DOC/x for x in ['closed-contract.md','source-contract.md','evaluator-v5.md']]+[SQL]
paths += [PRIOR/x for x in ['handoff.json','manifest.json','client_cancel_finalization.go.proposed.txt','client_cancel_finalization_test.go.proposed.txt','next-evaluator-implementation.json','source-registry34.exact.json']]
raw={p:p.read_bytes() for p in paths}
put('inputs.before.json',[ref(p,b) for p,b in raw.items()])
(OUT/'snapshots').mkdir(exist_ok=False)
mapping=[]
for i,(p,b) in enumerate(raw.items()):
 q=OUT/'snapshots'/f'{i:03d}-{p.name}'
 q.write_bytes(b)
 mapping.append({'original':ref(p,b),'snapshot':ref(q,b)})
put('snapshot-map.json',mapping)

# Text extraction of the frozen view and actual DDL, never SQLite evaluation.
def split(s):
 out=[];start=0;depth=0;quote=False;i=0
 while i<len(s):
  c=s[i]
  if c=="'":
   if quote and i+1<len(s) and s[i+1]=="'":i+=2;continue
   quote=not quote
  elif not quote:
   if c=='(':depth+=1
   elif c==')':depth-=1
   elif c==',' and depth==0:out.append(s[start:i].strip());start=i+1
  i+=1
 out.append(s[start:].strip());return out
sql=raw[SQL].decode('utf8')
registry=[]
for line_no,line in enumerate(sql.splitlines(),1):
 if not 316<=line_no<=350:continue
 m=re.search(r"SELECT '([^']+)',json_array\((.*)\) FROM ([a-z_]+)",line)
 if not m:continue
 category,expr,table=m.groups()
 gates=[x for x in sql.splitlines() if ('FROM '+table+' WHERE ') in x and 'typeof(' in x]
 assert gates,(category,'no typegate')
 types={k:re.findall(r"'([^']+)'",v) for k,v in re.findall(r'typeof\((\w+)\) NOT IN \(([^)]+)\)',gates[-1])}
 fields=[];mask=''
 for e in split(expr):
  if e.startswith('typeof('):col=e;kind='s'
  elif 'hex(' in e:
   mm=re.search(r'hex\(CAST\((\w+) AS BLOB\)\)',e) or re.search(r'hex\((\w+)\)',e)
   assert mm,(category,e)
   col=mm[1];kind='H' if 'null' in types[col] else 'h'
  else:
   col=e;ts=types[col];kind='i' if 'integer' in ts else 's'
   if 'null' in ts:kind=kind.upper()
  fields.append(col);mask+=kind
 registry.append({'category':category,'table':table,'columns':fields,'mask':mask,'line':line_no})
assert len(registry)==34
all_ddl='\n'.join(raw[p].decode('utf8') for p in paths if p.suffix=='.sql')+'\n'+sql
for item in registry:
 table=item['table'];matches=list(re.finditer(r'CREATE TABLE(?: IF NOT EXISTS)?\s+'+table+r'\s*\((.*?)\);',all_ddl,re.S|re.I))
 assert matches,(table,'DDL missing')
 body=matches[-1][1];constraints=[]
 for clause in split(body):
  match=re.match(r'(?:PRIMARY KEY|UNIQUE)\s*\(([^)]+)\)',clause,re.I)
  if match:constraints.append([x.strip() for x in match[1].split(',')]);continue
  match=re.match(r'(\w+)\s+\w+\b.*\b(?:PRIMARY KEY|UNIQUE)\b',clause,re.I|re.S)
  if match:constraints.append([match[1]])
 # Actual partial UNIQUE index from next_v24_sessions.sql. SQL NULLs never
 # collide under this constraint; nullable PKs likewise retain SQLite semantics.
 if table=='client_sessions':constraints.append(['run_id'])
 item['unique_keys']=[[item['columns'].index(k) for k in key] for key in constraints]
 assert (not constraints)==(table=='domain_refs'),(table,constraints)
put('source-registry.generated.json',{'source_ref':ref(SQL,raw[SQL]),'rows':registry,'basis':'STATIC_TEXT_ONLY; masks s/i/h, uppercase permits NULL; unique keys from actual DDL, NULL keys do not conflict'})
lines=['// Generated from exact frozen SQL view/typegates and actual DDL.','func f08SourceRules() map[string]f08SourceRule {',' return map[string]f08SourceRule{']
for row in registry:
 keys=', '.join('{'+','.join(map(str,k))+'}' for k in row['unique_keys'])
 lines.append('  '+json.dumps(row['category'])+': {mask:'+json.dumps(row['mask'])+', unique:[][]int{'+keys+'}},')
lines+=[' }','}']
with (OUT/'registry.go.proposed.txt').open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
print(json.dumps({'inputs':len(raw),'registry':ref(OUT/'source-registry.generated.json',(OUT/'source-registry.generated.json').read_bytes()),'source_rules':34},ensure_ascii=False))
