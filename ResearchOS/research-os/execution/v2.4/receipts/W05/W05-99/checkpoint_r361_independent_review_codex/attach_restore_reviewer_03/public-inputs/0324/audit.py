import pathlib,json,hashlib,re,collections,sys,types,datetime
R=pathlib.Path(r'D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';O=pathlib.Path(__file__).resolve().parent
Q=B/'legacy_migration_fixture_source_revision_codex/fc052947b4d14f769bff1e735151c52d';OLD=B/'legacy_migration_fixture_source_codex/edd7ae2789974a469dd2fc3a1bce50a9'
def pin(p):
 p=pathlib.Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def j(p):return json.loads(pathlib.Path(p).read_bytes())
def save(n,x):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def refs(x):
 if isinstance(x,dict):
  if all(k in x for k in ['path','sha256','bytes']):yield {k:x[k] for k in ['path','sha256','bytes']}
  for v in x.values():yield from refs(v)
 elif isinstance(x,list):
  for v in x:yield from refs(v)
def members(x):
 m=x['members'];return list(m.values()) if isinstance(m,dict) else m
h=j(Q/'HDF.json');mf=j(Q/'MF.json');sp=j(Q/'source-pins.json');ip=j(Q/'input-pins.json');expected=[]
for x in [h,mf,sp,ip]:expected+=list(refs(x))
for key in ['independent_request_changes_HDF_ref','independent_request_changes_MF_ref','previous_source_HDF_ref','previous_source_MF_ref']:
 ref=h[key];actual=pin(ref['path']);assert all(actual[k]==ref[k] for k in ['sha256','bytes']),ref
for key in ['independent_request_changes_MF_ref','previous_source_MF_ref']:
 expected+=list(refs(j(h[key]['path'])))
expected += [pin(p) for p in Q.rglob('*') if p.is_file()]
canonical=[R/'execution/v2.4'/(n+'.json') for n in ['checkpoint','path_ownership','step_state','commands']]
main=[R/'internal/domain'/n for n in ['client_session_bootstrap_test.go','retrieval_test.go','client_session_fence.go','backup_migration.go','store.go']]
expected += [pin(p) for p in canonical+main]+[pin(R/'AGENTS.md'),pin(R/'execution/project_identity.json')]
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py';graw=gp.read_bytes();assert hashlib.sha256(graw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85';expected += [pin(gp),pin(sys.executable)]
unique={}
for ref in expected:
 ref=dict(path=str(pathlib.Path(ref['path']).resolve()),sha256=ref['sha256'].removeprefix('sha256:'),bytes=ref['bytes']);key=ref['path'].casefold()
 if key in unique:assert unique[key]==ref,(unique[key],ref)
 unique[key]=ref
checked=[]
for ref in unique.values():
 actual=pin(ref['path']);checked.append(dict(expected=ref,actual=actual,matched=actual==ref))
save('input-pins.json',dict(refs=checked,all_matched=all(x['matched'] for x in checked)))
assert all(x['matched'] for x in checked)
m=types.ModuleType('legacy2_guard');m.__file__=str(gp);sys.modules[m.__name__]=m;exec(compile(graw,str(gp),'exec'),m.__dict__)
guard=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(unique.values()))
checks=[]
def check(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail,verification='INDEPENDENT_STATIC_SOURCE_OR_FILE_FACT'))
def masked(s):
 out=list(s);i=0
 while i<len(s):
  start=i
  if s.startswith('//',i):
   stop=s.find('\n',i);i=len(s) if stop<0 else stop
  elif s.startswith('/*',i):
   stop=s.find('*/',i+2);i=len(s) if stop<0 else stop+2
  elif s[i] in ['"', "'",chr(96)]:
   delim=s[i];i+=1
   while i<len(s):
    if s[i]==delim:i+=1;break
    if s[i]=='\\' and delim!=chr(96):i+=2
    else:i+=1
  else:i+=1;continue
  for n in range(start,min(i,len(s))):
   if s[n]!='\n':out[n]=' '
 return ''.join(out)
def balanced_end(m,left,op,cl):
 depth=1;i=left+1
 while i<len(m) and depth:
  depth+=(m[i]==op)-(m[i]==cl);i+=1
 assert depth==0
 return i
def funcs(s):
 mask=masked(s);out={}
 for hit in re.finditer(r'^func\s+(Test\w+)\s*\(',mask,re.M):
  left=mask.find('{',hit.end());end=balanced_end(mask,left,'{','}');out[hit.group(1)]=s[hit.start():end]
 return out
def assertions(s):
 mask=masked(s);out=[]
 for hit in re.finditer(r'\bt\.(?:Fatalf?|Errorf?|FailNow|Fail)\s*\(',mask):
  out.append(s[hit.start():balanced_end(mask,hit.end()-1,'(',')')])
 return collections.Counter(out)
try:
 def raw(p):return guard.get_buffer(str(p))
 def text(p):return raw(p).decode('utf-8')
 name='internal/domain/client_session_bootstrap_test.go';old=text(OLD/'candidate-root'/name);new=text(Q/'candidate-root'/name);target='TestClientTranscriptIndexUpgradeRollsBackWithCallerTransaction'
 a=funcs(old);z=funcs(new);newbody=z[target];oldbody=a[target]
 before="\tf := setup(t)\n\tctx := context.Background()\n\tif err := useLegacyTranscriptFixture(t, f); err != nil {"
 after="\tctx := context.Background()\n\tdb, err := legacyTranscriptFixtureDatabase(t)\n\tif err != nil {"
 inverse=newbody.replace(after,before,1).replace('db.Begin()','f.db.Begin()',1).replace('db.QueryRow(','f.db.QueryRow(',1)
 check('exact inverse recovers v1 bytes',inverse==oldbody and new.replace(newbody,oldbody,1).encode()==raw(OLD/'candidate-root'/name))
 check('only original rollback Test body changed',set(a)==set(z) and all(a[k]==z[k] for k in a if k!=target))
 check('same rollback assertion calls',assertions(oldbody)==assertions(newbody))
 other=[]
 for row in h['unchanged_other_three_candidates']:
  same=raw(pathlib.Path(row['previous_ref']['path']))==raw(pathlib.Path(row['candidate_ref']['path']));other.append(dict(relative_path=row['relative_path'],equal=same))
 check('other three candidates byte unchanged',len(other)==3 and all(x['equal'] for x in other),other)
 comparisons=[];total_names=0;total_asserts=0;equal_bodies=0
 for base in h['base_refs']:
  p=pathlib.Path(base['path']);a0=text(p);b0=text(Q/'candidate-root/internal/domain'/p.name);af=funcs(a0);bf=funcs(b0);aa=assertions(a0);ba=assertions(b0)
  total_names+=len(af);total_asserts+=sum(aa.values());equal=[n for n in af if af[n]==bf.get(n)];equal_bodies+=len(equal)
  comparisons.append(dict(file=p.name,original_names=list(af),missing_names=list(set(af)-set(bf)),original_assertion_count=sum(aa.values()),candidate_assertion_count=sum(ba.values()),missing_assertions=list((aa-ba).elements()),equal_bodies=equal))
 check('12 original Test names 126 assertions 9 unrelated bodies preserved',total_names==12 and total_asserts==126 and equal_bodies==9 and all(not x['missing_names'] and not x['missing_assertions'] for x in comparisons),comparisons)
 helper=text(Q/'candidate-root/internal/domain/legacy_migration_fixture_test.go')
 check('schema db no Project copy route', 'db, err := legacyTranscriptFixtureDatabase(t)' in newbody and 'setup(t)' not in newbody and 'useLegacyTranscriptFixture' not in newbody and 'f.' not in masked(newbody))
 check('same db Begin and postrollback query', 'tx, err := db.Begin()' in newbody and 'if err = db.QueryRow(' in newbody)
 check('explicit and deferred rollback kept',newbody.count('defer tx.Rollback()')==1 and 'if err = tx.Rollback(); err != nil {' in newbody)
 check('tx visibility and rollback absence assertions preserved', 'installClientSessionFence(ctx, tx, false)' in newbody and 'if err = tx.QueryRow(' in newbody and 'count != 1' in newbody and 'count != 0' in newbody)
 check('constructor registered close before migration and returns same db',helper.index('t.Cleanup(func() { _ = db.Close() })')<helper.index('if _, err = legacyFixtureMigrationSQL(1)') and 'return db, nil' in helper)
 fencepath=pathlib.Path(next(x['path'] for x in sp['production_and_contract_refs'] if pathlib.Path(x['path']).name=='client_session_fence.go'));fence=text(fencepath)
 check('production installed false only skips Run seeding', 'if restored {' in fence and 'ALTER TABLE client_sessions ADD COLUMN transcript_artifact_id TEXT' in fence and all(k in fence for k in ['client_session_epoch_no_regression','client_session_require_fresh']) and 'INSERT' not in newbody)
 migrations=j(Q/'inputs/previous-source/migration-resources.json');mig=[]
 for item in migrations['migration_sources']:
  content=raw(pathlib.Path(item['actual_source_ref']['path']));blob=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest();mig.append(dict(version=item['version'],matched=blob==item['git_blob'],git_blob=blob))
 check('20 genuine numbered resources unchanged',[x['version'] for x in mig]==list(range(1,21)) and all(x['matched'] for x in mig),mig)
 ddl=raw(Q/'candidate-root/internal/domain/testdata/pretranscript-3225a31f.sql');blob=hashlib.sha1(b'blob '+str(len(ddl)).encode()+b'\0'+ddl).hexdigest()
 check('pretranscript DDL exact Git blob',blob=='9efc768f8f4cfb6ac31e1f88a78ad095877328af',dict(git_blob=blob,sha256=hashlib.sha256(ddl).hexdigest(),bytes=len(ddl)))
 reviewmf=pathlib.Path(h['independent_request_changes_MF_ref']['path']);copymf=Q/'inputs/review/MF.json'
 memberpaths={str(pathlib.Path(x['path']).resolve()).casefold() for x in members(mf)}
 exclusions=[pin(q) for q in Q.rglob('*') if q.is_file() and str(q.resolve()).casefold() not in memberpaths]
 check('excluded review MF separately verified against original',raw(reviewmf)==raw(copymf) and pin(copymf)['sha256']=='8d6e16c64fc68ce802c07d38dadc782f02d273082c8f427acfd805e6c4050c2e' and pin(copymf)['bytes']==17122)
 check('postseal IO separate exact pin',pin(Q/'postseal-tool-io.json')['sha256']=='942255f3f7f0455b8a9d5c246feb58e23c2d6f18e95559686ac50db80088cfcc' and pin(Q/'postseal-tool-io.json')['bytes']==105376)
 post=json.loads(raw(Q/'postseal-tool-io.json'));post_results=[]
 for call in post['calls']:
  result=call.get('result',{});result=result.get('value',result) if isinstance(result,dict) else result
  if isinstance(result,dict):post_results.append(dict(key=call.get('key'),outer=result.get('exit_code'),marked=re.findall(r'ROOT_PYTHON_EXIT=(\d+)',result.get('output','')),chunk_id=result.get('chunk_id')))
 check('postseal result has actual outer0 and markedPython0',any(x['outer']==0 and '0' in x['marked'] for x in post_results),post_results)
 check('ordinary stays blocked no execution acceptance',h['ordinary']=='BLOCKED_HISTORICAL20_MATCHING_PROGRAM_BACKUP_RESTORE_UPGRADE' and h['execution']['Go'] is None and h['execution']['SQL'] is None and h['formal_acceptance'] is False)
 for i,ref in enumerate(unique.values()):
  p=pathlib.Path(ref['path']);dest=O/'public-inputs'/str(i).zfill(4)/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(raw(p))
 save('static-verification.json',dict(checks=checks,all_passed=all(x['passed'] for x in checks),manifest_members=len(members(mf)),manifest_excluded_actual=exclusions,postseal_actual_results=post_results,Source_guard_count=len(unique),ordinary=h['ordinary'],source_only=True,Go_AST_Go_SQL_native_model_executed=False,candidate_refs=h['candidate_refs']))
finally:
 closed=guard.close();save('sourceguard.close.json',closed);assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
closing=[dict(before=ref,after=pin(ref['path']),matched=pin(ref['path'])==ref) for ref in unique.values()]
save('closing-pins.json',dict(refs=closing,all_unchanged=all(x['matched'] for x in closing),canonical_refs=[pin(p) for p in canonical],Main_refs=[pin(p) for p in main]))
print(json.dumps(dict(all_passed=all(x['passed'] for x in checks),failed_checks=[x for x in checks if not x['passed']],sourceguard_entries=len(closed['entries']),closed=closed['closed'],manifest_excluded_actual=[str(pathlib.Path(x['path']).relative_to(Q)) for x in exclusions],new_mechanical_errors=0),ensure_ascii=False))

