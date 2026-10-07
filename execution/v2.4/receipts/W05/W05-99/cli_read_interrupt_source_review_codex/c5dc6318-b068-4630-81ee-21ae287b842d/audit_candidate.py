from pathlib import Path
import json,subprocess,hashlib,os
R=Path.cwd();W=R/'.local/worktrees/codex-w0599-cli-read-interrupt';O=R/'execution/v2.4/receipts/W05/W05-99/cli_read_interrupt_source_review_codex/c5dc6318-b068-4630-81ee-21ae287b842d';C='f565599af3679fef6d5233fe27d16b8c92a61db2';B='d799ee058f59dc778d288566e25a72ae9f4f78a3';sha=lambda b:hashlib.sha256(b).hexdigest();E={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};E['GIT_NO_REPLACE_OBJECTS']='1'
def git(*a):return subprocess.check_output(['git','--no-replace-objects',*a],cwd=R,env=E)
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
mp=R/'execution/v2.4/receipts/W05/W05-99/cli_read_interrupt_executor_codex/freeze-r270/manifest.json';assert sha(mp.read_bytes())=='1f6dd352e724d1c3ddf1d5855c1eb03534c1a2d8958ee05bc12b901f2f392613';m=json.loads(mp.read_bytes());names=git('diff','--name-only',B,C).decode().splitlines();audit=[]
for n in names:
 raw=git('show',C+':'+n);entry={'path':n,'sha256':sha(raw),'bytes':len(raw),'git_blob_oid':git('rev-parse',C+':'+n).decode().strip(),'author_current_match':(W/n).read_bytes()==raw};assert entry['author_current_match'];audit.append(entry)
assert len(audit)==178
for e in m['sources']+m['public_receipts']:
 a=next(x for x in audit if x['path']==e['path']);assert a['sha256']==e['sha256'] and a['bytes']==e['bytes']
extras=[a['path'] for a in audit if a['path'] not in [e['path'] for e in m['sources']+m['public_receipts']]]
source=[n for n in names if not n.startswith('execution/v2.4/receipts/W05/W05-99/cli_read_interrupt_executor_codex/')];assert set(source)=={e['path'] for e in m['sources']}
checks=[]
for key in ['actual_current_full_result_ref','actual_focused_result_ref']:
 e=m[key];p=W/e['path'];assert sha(p.read_bytes())==e['sha256'];d=p.parent;before=json.loads((d/'source_before.json').read_bytes());after=json.loads((d/'source_after.json').read_bytes());assert before==after;drift=[]
 for k,v in before.items():
  prefix,n=k.split(':',1);q=(W/n if prefix=='repo' else R/n if prefix=='main' else Path(n));actual=sha(q.read_bytes()) if q.is_file() else 'MISSING'
  if actual!=v:drift.append({'key':k,'expected':v,'actual':actual})
 counts={'pass':0,'fail':0,'skip':0,'top_pass':0}
 for line in (d/'test.stdout.raw').read_bytes().splitlines():
  x=json.loads(line)
  if x.get('Test') and x.get('Action') in counts:
   counts[x['Action']]+=1
   if x['Action']=='pass' and '/' not in x['Test']:counts['top_pass']+=1
 checks.append({'name':key,'result':json.loads(p.read_bytes()),'actual_counts':counts,'vector_equal':before==after,'inputs':len(before),'current_drift':drift,'invocation':json.loads((d/'test.invocation.json').read_bytes())})
save('candidate_blob_audit.json',audit);save('author_evidence_audit.json',{'manifest':str(mp),'all178blobs_verified':True,'source4':source,'manifest_receipts171':len(m['public_receipts']),'extra_commit_receipts3':extras,'actual_cohorts':checks});print(json.dumps({'blobs':len(audit),'extras':extras,'cohorts':[(x['actual_counts'],len(x['current_drift'])) for x in checks]}))
