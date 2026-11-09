from pathlib import Path
import json,re,hashlib
O=Path(__file__).resolve().parent
mapping=json.loads((O/'snapshot-map.json').read_text(encoding='utf8'))
raw={Path(x['original']['path']):Path(x['snapshot']['path']).read_bytes() for x in mapping}
for p,b in raw.items():assert p.read_bytes()==b
sqlpath=next(p for p in raw if p.name=='candidate.sql.txt')
sql=raw[sqlpath].decode('utf8')
def split(s):
 result=[];start=0;depth=0;quote=False;i=0
 while i<len(s):
  c=s[i]
  if c=="'":
   if quote and i+1<len(s) and s[i+1]=="'":i+=2;continue
   quote=not quote
  elif not quote:
   if c=='(':depth+=1
   elif c==')':depth-=1
   elif c==',' and depth==0:result.append(s[start:i].strip());start=i+1
  i+=1
 result.append(s[start:].strip());return result
rows=[]
ddl='\n'.join(b.decode('utf8') for p,b in raw.items() if p.suffix=='.sql')+'\n'+sql
for line_no,line in enumerate(sql.splitlines(),1):
 if not 316<=line_no<=350:continue
 m=re.search(r"SELECT '([^']+)',json_array\((.*)\) FROM ([a-z_][a-z_0-9]*)",line)
 if not m:continue
 category,expression,table=m.groups()
 declarations=list(re.finditer(r'CREATE TABLE(?: IF NOT EXISTS)?\s+'+table+r'\s*\((.*?)\);',ddl,re.S|re.I))
 assert declarations,(table,'missing DDL')
 body=declarations[-1][1]
 gates=[x for x in sql.splitlines() if 'FROM '+table+' WHERE ' in x and 'typeof(' in x]
 if gates:
  types={k:re.findall(r"'([^']+)'",v) for k,v in re.findall(r'typeof\((\w+)\) NOT IN \(([^)]+)\)',gates[-1])}
 else:
  types={}
  for clause in split(body):
   cm=re.match(r'(\w+)\s+(TEXT|INTEGER|BLOB)\b',clause)
   if cm:types[cm[1]]=[cm[2].lower()]+([] if 'NOT NULL' in clause else ['null'])
 fields=[];mask=''
 for expr in split(expression):
  if expr.startswith('typeof('):col=expr;kind='s'
  elif 'hex(' in expr:
   hm=re.search(r'hex\(CAST\((\w+) AS BLOB\)\)',expr) or re.search(r'hex\((\w+)\)',expr)
   assert hm,(category,expr)
   col=hm[1];kind='H' if 'null' in types[col] else 'h'
  else:
   col=expr;kind='i' if 'integer' in types[col] else 's'
   if 'null' in types[col]:kind=kind.upper()
  fields.append(col);mask+=kind
 constraints=[]
 for clause in split(body):
  cm=re.match(r'(?:PRIMARY KEY|UNIQUE)\s*\(([^)]+)\)',clause,re.I)
  if cm:constraints.append([x.strip() for x in cm[1].split(',')]);continue
  cm=re.match(r'(\w+)\s+\w+\b.*\b(?:PRIMARY KEY|UNIQUE)\b',clause,re.S|re.I)
  if cm:constraints.append([cm[1]])
 if table=='client_sessions':constraints.append(['run_id'])
 assert (not constraints)==(table=='domain_refs'),(table,constraints)
 rows.append({'category':category,'table':table,'columns':fields,'mask':mask,'line':line_no,'unique_keys':[[fields.index(k) for k in key] for key in constraints]})
assert len(rows)==34
with (O/'source-registry.generated.json').open('x',encoding='utf8',newline='\n') as f:
 json.dump({'rows':rows,'basis':'Exact SQL view expressions; original typeof gates or own new-table DDL; NULL unique keys do not collide'},f,ensure_ascii=False,indent=2);f.write('\n')
lines=['// Static extraction of exact original SQL; no SQL evaluation.','func f08SourceRules() map[string]f08SourceRule {',' return map[string]f08SourceRule{']
for row in rows:
 keys=', '.join('{'+','.join(map(str,k))+'}' for k in row['unique_keys'])
 lines.append('  '+json.dumps(row['category'])+': {mask:'+json.dumps(row['mask'])+', unique:[][]int{'+keys+'}},')
lines+=[' }','}']
with (O/'registry.go.proposed.txt').open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
print(json.dumps({'categories':len(rows),'inputs_unchanged':len(raw),'output_sha256':hashlib.sha256((O/'registry.go.proposed.txt').read_bytes()).hexdigest()}))
