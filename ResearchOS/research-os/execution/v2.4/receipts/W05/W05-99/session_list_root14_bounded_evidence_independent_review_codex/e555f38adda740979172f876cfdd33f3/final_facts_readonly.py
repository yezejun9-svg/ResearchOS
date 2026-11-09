import base64, collections, hashlib, json, os, subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
N=R/'execution/v2.4/receipts/W05/W05-99'
H=Path(__file__).resolve().parent
P=N/'session_list_closedcopy_exact1_root_replay_codex/0b2ae4ec4e824c968553ff884c3fa132'
S=N/'root14_evidence_sealed_codex/e1b3d1e2a8404f6997dab28af163d25c'
checks=[]; refs=[]
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();refs.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)});return b
def load(p):return json.loads(read(p))
def check(n,v,detail=None):checks.append({'check':n,'passed':bool(v),'details':detail})
def save(n,x):
 with (H/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def norm(p):return os.path.normcase(os.path.abspath(p))
def rows(doc,table):
 cols=[json.loads(x)[1] for x in doc['columns'][table]];out=[]
 for r in doc['tables'][table]:
  values=[]
  for typ,value in json.loads(r):
   values.append(base64.b64decode(value).decode('utf-8') if typ in ['text','blob'] else int(value) if typ=='integer' else None if typ=='null' else value)
  out.append(dict(zip(cols,values)))
 return out
manifest=load(S/'manifest.json'); mm={norm(x['path']):x for x in manifest['entries']}
for x in load(S/'audit.json')['old_failure_refs']:
 b=read(x['path']);full=R/x['path'];check('corrected_repo_relative_old_failure_ref',norm(full) in mm and hashlib.sha256(b).hexdigest()==x['sha256'] and len(b)==x['bytes'],x)
cases=load(P/'result.json')['cases'];actual=[]
for c in cases:
 name=c['leaf'];C=P/('cases/TestSessionListHTTPOriginalContextIdentity__'+name)
 a=load(C/'assertions.json');target=[]
 for p in sorted(C.glob('http-*.request.raw')):
  b=read(p)
  if hashlib.sha256(b).hexdigest()==a['original_request_sha256']:target.append(p)
 p=target[0];stem=p.name.removesuffix('.request.raw');env=json.loads(read(p));response=load(C/(stem+'.response.json'));body=json.loads(read(C/(stem+'.response.raw')))
 expected_code={'CrossProjectContext':'NOT_FOUND','ForeignPrincipalContext':'FORBIDDEN','UnknownContext':'NOT_FOUND','ProjectGrantDenied':'FORBIDDEN','CrossProjectCursor':'CURSOR_INVALID','CrossPrincipalCursor':'CURSOR_INVALID','MalformedRequest':'INVALID_REQUEST'}.get(name)
 if name=='MalformedRequest':check(name+'_actual_short_refusal',response['status']==400 and body['error']['code']=='INVALID_REQUEST')
 else:
  check(name+'_actual_identity',body['command_id']==env['command_id'] and body['session_id']==env['session_id'] and body['revision'] is None and body['method']=='session.list')
  check(name+'_actual_typed_result',response['status']==(403 if name=='ProjectGrantDenied' else 200) and body['status']==('REJECTED' if expected_code else 'COMPLETED') and body['error_code']==expected_code)
 if not expected_code:
  items=body['result']['items'];check(name+'_actual_item_count',len(items)==(0 if name=='ForeignPrincipalNullList' else 1 if name=='ContextNotResultFilter' else 2))
  if name=='ContextNotResultFilter':check(name+'_context_not_filter',items[0]['session_id']!=body['session_id'])
 if name=='OwnedContext':check(name+'_other_writer_read_allowed',env['client_id']=='same-principal-readonly-client' and body['status']=='COMPLETED')
 closed=load(C/'closed.rows.json')
 for jp in C.glob('journal-*.json'):
  j=load(jp);ident=[x for x in rows(closed,'client_command_identities') if x['principal']==j['principal'] and x['command_id']==j['command_id']]
  journal=[x for x in rows(closed,'idempotency') if x['principal']==j['principal'] and x['project']==j['project'] and x['operation']==j['operation'] and x['key']==j['command_id']]
  check(name+'_identity_sole_journal_join',len(ident)==len(journal)==1 and all(ident[0][k]==j[k] for k in ident[0]) and all(journal[0][k]==j['command_id' if k=='key' else k] for k in journal[0]))
  # Fixture's recorded canonical request bytes hash is also the actual stored ContentHash.
  request=base64.b64decode(json.loads(j['headers'])['raw_envelope_base64'],validate=True)
  check(name+'_original_hash_anchor',j['request_hash']=='sha256:'+hashlib.sha256(request).hexdigest())
 actual.append({'leaf':name,'target_HTTP':response['status'],'expected_error':expected_code,'actual_status':body.get('status'),'actual_error':body.get('error_code',body.get('error',{}).get('code') if isinstance(body.get('error'),dict) else None)})
chain=load(H/'continuation-structural/source-chain.json');m=load(H/'continuation-structural/source38-current-map.json')
env={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')};env.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul')
argv=['C:/Program Files/Git/cmd/git.exe','-C',str(R),'show','a5d6d16ffaf129de0361470c3a1570228bd259a2:apps/control/main.go']
proc=subprocess.run(argv,env=env,capture_output=True)
for suffix,b in [('stdout.raw',proc.stdout),('stderr.raw',proc.stderr)]:
 with (H/('apps-control-Git.'+suffix)).open('xb') as f:f.write(b)
save('apps-control-Git.invocation.json',{'argv':argv,'actual_exit':proc.returncode,'product_execution':False})
check('read_missing_non_API_compiled_source_blob',proc.returncode==0)
m.append({'relative_path':'apps/control/main.go','git_blob':hashlib.sha1(b'blob '+str(len(proc.stdout)).encode()+b'\0'+proc.stdout).hexdigest(),'sha256':hashlib.sha256(proc.stdout).hexdigest(),'bytes':len(proc.stdout),'path':str(H/'apps-control-Git.stdout.raw'),'API_replay_compiled_input':False})
check('unique38_source_map_complete',len(m)==38 and {x['relative_path'] for x in m}==set(chain['unique_source_paths']))
save('source38-frozen-Git-map.json',m)
prior=N/'handler38_independent_replay_codex/c09-attach-correction-r304-0acd8177a821441395e8902ba16def0c/source_review.json'
b=read(prior);check('prior_handler38_original_review_pin',hashlib.sha256(b).hexdigest()=='7fdf7f2ced5d29adb4ba7c8e420e0d0235c74f7227fe500fa7a1d547f9958680')
save('final-facts.json',{'checks':checks,'raw_targets':actual,'read_refs':refs,'SQL_executions':0,'product_executions':0,'old_failure_membership_correction':'Only normalized repository-relative paths against explicit repository root; prior two false check observations remain unchanged.'})
print(json.dumps({'checks':len(checks),'failed':[x for x in checks if not x['passed']]},ensure_ascii=False))
