from pathlib import Path
import hashlib,json,subprocess,zipfile,datetime,re
R=Path('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/codex-w1303-desktop-http-r311';O=Path(__file__).resolve().parent
N=W/'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/98552188a0014da3a6d73be7cdb3f9bd';F=N/'final-audit-c0fea60e04e34fbd803b5d2feae78df8'
checks=[];inputrefs=[];gitrecords=[]
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def ref(p):return {'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size}
def check(n,v):checks.append({'check':n,'ok':bool(v)})
def save(n,v):
 b=v if isinstance(v,bytes) else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 with (O/n).open('xb') as f:f.write(b)
 return ref(O/n)
def read(p):
 inputrefs.append(ref(p));return p.read_bytes()
def resolve(x,base=W):
 p=Path(x['path']);return p if p.is_absolute() else base/p
def verify(x,base=W):
 p=resolve(x,base);a=ref(p);check('ref '+str(p),a['sha256']==x['sha256'] and ('bytes' not in x or a['bytes']==x['bytes']));return p
def git(label,*args):
 argv=['C:/Program Files/Git/cmd/git.exe',*args];z=subprocess.run(argv,cwd=W,capture_output=True)
 gitrecords.append({'argv':argv,'cwd':str(W),'actual_exit':z.returncode,'stdout_ref':save(label+'.stdout.raw',z.stdout),'stderr_ref':save(label+'.stderr.raw',z.stderr)})
 check('git '+label,z.returncode==0);return z.stdout
pins={'handoff.json':'c4bea94e1eec3c9f4a9393e9433d8501a9c51e81b899c51245a8027166a51f60','manifest.json':'835f1ecdb3cf792ca2f058fdc3d0fec052d772f8ecfa75cd5ca2a99b5ca79ab7','finite-matrix.json':'23b88c340151f77a3b3b8eea967f34dc1526909b86bf34eeb46694529f70e135','source-scope-audit.json':'779864f389d7d6fc0abbcc96048fc08db127da15d561d599c7529be03b3f11df'}
for n,h in pins.items():
 b=read(F/n);check('pin '+n,hashlib.sha256(b).hexdigest()==h);save('input-'+n,b)
scope=json.loads(read(N/'scope_registration.json'));check('scope pin',digest(N/'scope_registration.json')=='3595c57c257c097718d5d1debecf219f2707fea9294812c81d7cbfc6a6864a84')
save('scope.original.json',(N/'scope_registration.json').read_bytes())
for key in ['path_bounds_ref','source_proposal_ref','source_roster_ref','scope_review_ref','implementation_conditions_ref','protected_spans_ref','preflight_supplement_ref']:
 p=verify(scope[key],R);save(key+'.json',read(p))
head=git('head','rev-parse','HEAD').decode().strip();check('HEAD',head=='0f708eaf0c624fb721f7c9a00d5465ef5f13a68c')
check('clean tracked',git('status','status','--porcelain=v1','--untracked-files=no')==b'')
source='840bc6cc3237ba4dddd3812d2bec157666dc50ee';base=scope['base_commit']
check('source parent',git('source-parent','rev-parse',source+'^').decode().strip()==base)
changed=git('source-paths','diff-tree','--no-commit-id','--name-only','-r',source).decode().splitlines();check('exact15',len(changed)==15 and set(changed)==set(scope['exact_paths']))
post=git('receipt-only-paths','diff','--name-only',source,head).decode().splitlines();check('postsource receipt only',all(x.startswith('execution/v2.4/receipts/W13/W13-03/') for x in post))
scopeaudit=json.loads((F/'source-scope-audit.json').read_bytes());old={};curr={}
for i,x in enumerate(scopeaudit['rows']):
 p=W/x['path'];b=read(p);curr[x['path']]=b;save('source-%02d.current'%i,b)
 check('current source '+x['path'],hashlib.sha256(b).hexdigest()==x['sha256'] and len(b)==x['bytes'])
 check('gitblob '+x['path'],git('source-blob-%02d'%i,'show',source+':'+x['path'])==b)
 if not x['new']:old[x['path']]=git('base-blob-%02d'%i,'show',base+':'+x['path'])
protected=json.loads((O/'protected_spans_ref.json').read_bytes());spanfacts=[]
for x in protected['rows']:
 e=x['expected'];b=b''.join(old[e['path']].splitlines(keepends=True)[e['first_line']-1:e['last_line']]);h=hashlib.sha256(b).hexdigest();present=b in curr[e['path']]
 check('protected '+e['path']+str(e['first_line']),h==e['sha256'] and len(b)==e['bytes'] and present)
 spanfacts.append({'expected':e,'actual_base_sha256':h,'candidate_contains_exact_bytes':present})
save('protected-independent.json',spanfacts)
manifest=json.loads((F/'manifest.json').read_bytes());mfrows=[]
for x in manifest['files']:
 p=verify(x);mfrows.append({'path':str(p),'matched':checks[-1]['ok']})
save('author-manifest-verification.json',{'count':len(mfrows),'rows':mfrows})
print(json.dumps({'stage':'manifest/source verified','manifest':len(mfrows),'failed':[x for x in checks if not x['ok']]},ensure_ascii=True),flush=True)
inputs=json.loads(read(F/'inputs.current.json'));iv=[]
for x in inputs:
 p=Path(x['path']);a=ref(p);ok=a['sha256']==x['sha256']==x['current_sha256'] and a['bytes']==x['bytes'];check('currentinput '+str(p),ok);iv.append({'expected':x,'actual':a,'matched':ok})
save('inputs.independent-current.json',iv)
archive=json.loads(read(F/'archive-entries.json'));zp=verify(archive['archive_ref']);check('archive pin',digest(zp)=='772ec98d2e39ca9de6b350f433e6ec5ee23e93970be4b91c7395ddbf732b203a')
zs=[]
with zipfile.ZipFile(zp) as z:
 check('zip names exact',len(z.namelist())==len(archive['entries']) and set(z.namelist())=={x['entry'] for x in archive['entries']})
 for x in archive['entries']:
  b=z.read(x['entry']);ok=hashlib.sha256(b).hexdigest()==x['sha256'] and len(b)==x['bytes'];check('zip '+x['entry'],ok);zs.append({'entry':x['entry'],'matched':ok})
save('archive-independent.json',{'entries':len(zs),'checks':zs})
matrix=json.loads((F/'finite-matrix.json').read_bytes());cases=[]
for group in ['leaves','regressions']:
 for row in matrix[group]:
  inv=json.loads(verify(row['invocation_ref']).read_bytes());out=verify(row['stdout_ref']).read_bytes();verify(row['stderr_ref'])
  for x in row['raw_evidence_refs']:verify(x)
  ok=row['exit']==inv['exit']==0 and row['actualargv']==inv['actualargv'] and row['status']=='PASS';check('case '+row['name'],ok)
  if row['unit']=='node:test leaf':check('raw TAP '+row['name'],b'# fail 0' in out and b'# skipped 0' in out and row['name'].encode() in out)
  cases.append({'name':row['name'],'group':group,'unit':row['unit'],'actualargv':inv['actualargv'],'exit':inv['exit'],'http':row['http_count'],'children':row['child_count'],'raw_stdout_ref':row['stdout_ref'],'invocation_ref':row['invocation_ref']})
save('case-independent.json',cases)
check('case counts',len(matrix['leaves'])==159 and len(matrix['regressions'])==7)
check('http154',sum(x['http'] for x in cases)==154)
save('collect-audit.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_refs':inputrefs,'git_invocations':gitrecords,'checks':checks,'failed_checks':[x for x in checks if not x['ok']],'actual_product_execution':False,'manifest_count':len(mfrows),'inputs_count':len(iv),'archive_entries':len(zs),'case_counts':{'finite':159,'regression_units':7},'scope_acceptance':False})
print(json.dumps({'stage':'complete','failed':[x for x in checks if not x['ok']],'checks':len(checks)},ensure_ascii=True),flush=True)
