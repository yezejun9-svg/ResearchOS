import pathlib,json,hashlib,datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/codex-w0599-host-configuration-handler';N=pathlib.Path(__file__).parent
P=R/'execution/v2.4/receipts/W05/W05-99/handler38_final_source_review_codex/a639cfcf998f4c7fb182db19c6788c3b';H=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(n,o):(N/n).write_bytes((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode())
m=json.loads((P/'author-final-evidence.manifest.json').read_bytes()); rows=[]
for x in m['files']:
 p=W/x['path'];v={'path':x['path'],'expected_sha256':x['sha256'],'bytes':x['bytes']}
 if not p.is_file():v['error']='missing'
 else:v.update({'actual_sha256':digest(p),'actual_bytes':p.stat().st_size,'match':digest(p)==x['sha256'] and p.stat().st_size==x['bytes']})
 rows.append(v)
save('author_manifest_audit.json',{'rows':rows,'count':len(rows),'bad':[v for v in rows if not v.get('match')],'total_bytes':sum(v.get('actual_bytes',0) for v in rows)})
c=json.loads((P/'author-final-coverage.actual.v2.json').read_bytes()); co=[]
for name,cohort in c['cohorts'].items():
 refs=cohort.get('refs',{});out={'cohort':name,'reported':cohort.get('result'), 'changed_repo_inputs_since_this_cohort':cohort.get('changed_repo_inputs_since_this_cohort',[])}
 if 'command.stdout' in refs:
  rp=W/refs['command.stdout']['path'];out['raw_sha256']=digest(rp);events=[]
  for line in rp.read_bytes().splitlines():
   try:e=json.loads(line)
   except (ValueError,UnicodeDecodeError):continue
   if e.get('Action') in ['pass','fail','skip'] and e.get('Test'):events.append({'test':e['Test'],'action':e['Action'],'package':e.get('Package')})
  out['actual_test_counts']={k:sum(e['action']==k for e in events) for k in ['pass','fail','skip']};out['actual_top_counts']={k:sum(e['action']==k and '/' not in e['test'] for e in events) for k in ['pass','fail','skip']};out['test_events']=events
 if 'command.invocation.json' in refs:out['actual_invocation']=json.loads((W/refs['command.invocation.json']['path']).read_bytes())
 if 'source.before.json' in refs and 'source.after.json' in refs:
  before=json.loads((W/refs['source.before.json']['path']).read_bytes());after=json.loads((W/refs['source.after.json']['path']).read_bytes());out['source_before_count']=len(before);out['source_after_count']=len(after);out['same_vector']=before==after
 co.append(out)
save('cohort_raw_audit.json',co)
f=json.loads((P/'author-source.freeze.json').read_bytes());v=json.loads((W/f['source_after_ref']['path']).read_bytes());current=[]
for key,expected in v.items():
 prefix,path=key.split(':',1)
 if prefix=='repo':p=W/path
 elif prefix=='main':p=R/path
 elif prefix=='absolute':p=pathlib.Path(path)
 else:current.append({'key':key,'error':'unrecognized prefix'});continue
 # Compile-only public sources may have a holdout path segment; no datasets or generator execution.
 if '/evaluation/holdout/' in str(p).replace('\\','/') and p.suffix not in ['.go','.md']:
  current.append({'key':key,'error':'non-source holdout disallowed'});continue
 if p.is_file():current.append({'key':key,'sha256':digest(p),'expected':expected,'match':digest(p)==expected})
 else:current.append({'key':key,'error':'missing'})
save('author_current_vector_audit.json',{'count':len(current),'rows':current,'bad':[x for x in current if not x.get('match')]})
# Hash exact path/sha references embedded in coverage and handoff without executing their content.
seen={}
def walk(o):
 if isinstance(o,dict):
  if isinstance(o.get('path'),str) and isinstance(o.get('sha256'),str):seen[(o['path'],o['sha256'])]=True
  for z in o.values():walk(z)
 elif isinstance(o,list):
  for z in o:walk(z)
walk(c);handoff=json.loads((P/'author-final-handoff.json').read_bytes());walk(handoff)
refs=[]
for path,sha in seen:
 p=pathlib.Path(path) if pathlib.Path(path).is_absolute() else W/path
 if not p.exists() and not pathlib.Path(path).is_absolute():p=R/path
 r={'path':path,'expected':sha}
 if p.is_file():r.update({'actual':digest(p),'match':digest(p)==sha})
 else:r['error']='missing'
 refs.append(r)
save('coverage_refs_audit.json',{'count':len(refs),'refs':refs,'bad':[r for r in refs if not r.get('match')]})
print(json.dumps({'namespace':str(N),'manifest_files':len(rows),'manifest_bad':sum(not x.get('match') for x in rows),'vector_count':len(current),'vector_bad':[x for x in current if not x.get('match')],'coverage_refs':len(refs),'ref_bad':[x for x in refs if not x.get('match')],'cohorts':[{'name':x['cohort'],'counts':x.get('actual_test_counts'),'vector_same':x.get('same_vector')} for x in co]},ensure_ascii=True))