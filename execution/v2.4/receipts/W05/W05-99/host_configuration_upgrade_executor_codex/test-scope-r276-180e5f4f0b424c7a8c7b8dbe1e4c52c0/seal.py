import concurrent.futures, datetime, hashlib, json, pathlib, sqlite3, subprocess
out=pathlib.Path(__file__).resolve().parent
root=out.parents[6]
main=pathlib.Path('D:/作品集/ResearchOS/research-os')
receipts=out.parent
parent='125ea34ca0878f18c4dce47f9259ab5e9e77c2eb'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(root).as_posix(),'sha256':sha(p)}
def save(name,value):
    p=out/name
    assert not p.exists(),p
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def git(args): return subprocess.run(['git',*args],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
assert git(['rev-parse','HEAD']).decode().strip()==parent
assert not git(['diff','--cached','--name-only']).strip()
build=receipts/'closure-e24d5ab7b9e6444abc8fc2e087aca6f5'
execution=[]
for d in receipts.glob('closure-*'):
    p=d/'test.invocation.json'
    if p.is_file():
        v=json.loads(p.read_text('utf8'))
        if 'test2json' in v['actualargv'] and '-test.v=test2json' in v['actualargv'] and str(out/'current-domain.test.exe') in [str(pathlib.Path(x)) for x in v['actualargv']]: execution.append(d)
assert len(execution)==1,execution
run=execution[0]
for d in [build,run]:
    result=json.loads((d/'result.json').read_text('utf8'))
    assert result['exit']==0 and not result['source_drift'],(d,result)
    assert (d/'source_before.json').read_bytes()==(d/'source_after.json').read_bytes()
events=[json.loads(line) for line in (run/'test.stdout').read_text('utf8').splitlines()]
counts={a:sum(x.get('Action')==a and bool(x.get('Test')) for x in events) for a in ['pass','fail','skip']}
assert counts['pass']>=191 and counts['fail']==0 and counts['skip']==0,counts
new_tests=['TestClientQueueFreshNumberedSchema','TestClientQueueHistorical22NumberedSchema']
assert all(any(x.get('Test')==n and x['Action']=='pass' for x in events) for n in new_tests)
vector=json.loads((run/'source_after.json').read_text('utf8'))
def check(item):
    k,h=item; prefix,p=k.split(':',1)
    actual=({'repo':root,'main':main}.get(prefix,pathlib.Path())/p)
    got=sha(actual) if actual.is_file() else 'MISSING'
    return {'path':k,'expected':h,'actual':got} if h!=got or got=='MISSING' else None
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: drift=[x for x in pool.map(check,vector.items()) if x]
assert not drift,drift[:3]
save('current_inputs_audit.json',{'inputs':len(vector),'drift':drift,'build_invocation':ref(build/'test.invocation.json'),'build_before':ref(build/'source_before.json'),'build_after':ref(build/'source_after.json'),'execution_invocation':ref(run/'test.invocation.json'),'execution_before':ref(run/'source_before.json'),'execution_after':ref(run/'source_after.json'),'test_executable':ref(out/'current-domain.test.exe')})

test_path='internal/domain/backup_command_queue_test.go'
original=git(['show',parent+':'+test_path]); current=(root/test_path).read_bytes()
assert original.split(b'func TestClientQueueFreshNumberedSchema')[0]==current.split(b'func TestClientQueueFreshNumberedSchema')[0]
assert original.split(b'func TestClientQueueBackupAllPhasesAndPendingControl')[1]==current.split(b'func TestClientQueueBackupAllPhasesAndPendingControl')[1]
assert git(['diff','--name-only']).decode().splitlines()==[test_path]
git(['diff','--check'])
git(['add','--',test_path])
old_handoff=receipts/'handoff-5375496dd2b24206b5db17fc9bc358c3'
ten=json.loads((old_handoff/'source.before_after.json').read_text('utf8'))
foundation=['migrations/sqlite/0023_host_model_configuration.sql']+['internal/domain/'+x for x in ['client_configuration.go','client_configuration_test.go','client_command_identity.go','client_command_identity_test.go']]
source_rows=[]
for p in [r['path'] for r in ten]+[test_path]+foundation:
    blob=git(['rev-parse',':'+p]).decode().strip()
    raw=git(['cat-file','blob',blob])
    assert raw==(root/p).read_bytes()
    origin='fef0ee2d56351e74ceed11b0b37d3f87e9c83494' if p in foundation else parent
    if p!=test_path: assert git(['show',origin+':'+p])==raw
    source_rows.append(dict(path=p,sha256=sha(root/p),git_blob_oid=blob,origin_commit=origin if p!=test_path else None,role='FOUNDATION5_FROZEN' if p in foundation else 'CURRENT_TEST_ONLY' if p==test_path else 'FROZEN10',same_bytes_as_origin=p!=test_path))
save('exact11_foundation5_git_blobs.json',{'rows':source_rows,'test_parent_commit':parent,'test_outside_allowed_functions_exact_bytes_unchanged':True,'candidate_commit_note':'The staged Git blob OIDs are actual immutable Git objects; final candidate commit is returned by commit command and independently checked against each OID.'})
snapshots=[]
for name,version in [('TestClientQueueFreshNumberedSchema',23),('TestClientQueueHistorical22NumberedSchema',22)]:
    dbfiles=list((run/'actual-fixtures'/name).glob('*.sqlite')); assert len(dbfiles)==1
    p=dbfiles[0]; before=sha(p)
    db=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
    versions=[r[0] for r in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
    assert versions==list(range(1,version+1)),versions
    queue={table:db.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in ['client_queue_fences','client_command_queue','client_control_requests','client_control_receipts']}
    assert set(queue.values())=={0}
    configurations=db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('host_model_configurations','host_model_config_heads','client_command_identities') ORDER BY name").fetchall()
    assert len(configurations)==(3 if version==23 else 0)
    db.close(); assert before==sha(p)
    snapshots.append(dict(test=name,snapshot=ref(p),mode='mode=ro&immutable=1',versions=versions,empty_queue_counts=queue,configuration_tables=configurations,hash_before=before,hash_after=sha(p)))
save('closed_sqlite_schema_audit.json',snapshots)
bad=receipts/'closure-99f15ba16ba7411aa469c310e1a366b1'
save('new_failure_origin.json',{'classification':'ACTUAL_COMMAND_ARGUMENT_FAILURE_BEFORE_TESTS','invocation':ref(bad/'test.invocation.json'),'stdout':ref(bad/'test.stdout'),'stderr':ref(bad/'test.stderr'),'source_after':ref(bad/'source_after.json'),'actual_exit':1,'executed_test_count':0,'cause':'PowerShell split unquoted -test.v=test2json and -test.timeout=300s into -test plus suffix; corrected invocation quotes complete parameters. Product source unchanged; original failure retained.'})
save('handoff.json',{'schema':'researchos.configuration-upgrade-test-only-handoff.v1','status':'FROZEN_EXECUTOR_CANDIDATE_FOR_INDEPENDENT_SOURCE_REVIEW','actor':'codex:/root/sources_parent_impl','verifier':'codex:/root/w05_merge_review','root':'codex:/root','formal_increment':0,'main23_hold':True,'parent_candidate':parent,'scope':ref(out/'scope.original.json'),'source16':ref(out/'exact11_foundation5_git_blobs.json'),'current_inputs':ref(out/'current_inputs_audit.json'),'sqlite':ref(out/'closed_sqlite_schema_audit.json'),'counts':counts,'new_tests':new_tests,'actual_invocation':ref(run/'test.invocation.json'),'stdout':ref(run/'test.stdout'),'stderr':ref(run/'test.stderr'),'programs':{'new_test_binary':ref(out/'current-domain.test.exe'),'unchanged_target23':ref(receipts/'implementation-df2b17aedb254da9b0fb902ca7f8575f/target23-final-backup.exe'),'unchanged_source22':ref(receipts/'old22-build-40e94f3f6e53442fa07068089c0de64a/old22-control.exe'),'fixed_historical14':ref(old_handoff/'historical14-control.exe')},'old_failures_preserved':ref(old_handoff/'failure_origins.final.json'),'old_manifest':ref(receipts/'historical-origin-40c15688361a4a5489ec98fe4f070efa/commit_manifest.json'),'historical14_open':ref(receipts/'historical-origin-40c15688361a4a5489ec98fe4f070efa/audit.json'),'resolved':'Original fresh22 hardpin is now split into strictly pinned current23 and historical22 meaningful assertions; old failed raw retained.','remaining':'Inherited historical14 ActiveRecovery has unchanged baseline helper/current-runtime mismatch, remains OPEN. No provider/model/F08 finalization/host.configure or formal acceptance claimed. CLI194 evidence remains the previous frozen production10 run; no new fullCLI run claimed for this test-only change.','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
tracked=set(filter(None,git(['ls-files','-z','--',receipts.relative_to(root).as_posix()]).decode().split('\0')))
files=sorted(p for p in receipts.rglob('*') if p.is_file() and p.relative_to(root).as_posix() not in tracked)
save('manifest.json',{'scope':'Only new r276 test-round receipts; previous1514 receipts remain immutable in parent125ea. Excludes only this manifest itself.','files':[{**ref(p),'bytes':p.stat().st_size} for p in files]})
files.append(out/'manifest.json')
for start in range(0,len(files),35): git(['add','-f','--',*[p.relative_to(root).as_posix() for p in files[start:start+35]]])
actual=set(filter(None,git(['diff','--cached','--name-only','-z']).decode().split('\0')))
assert actual=={test_path,*[p.relative_to(root).as_posix() for p in files]}
git(['commit','-m','test(domain): separate fixed current23 and historical22 queue schema checks'])
commit=git(['rev-parse','HEAD']).decode().strip()
assert all(git(['rev-parse',commit+':'+r['path']]).decode().strip()==r['git_blob_oid'] for r in source_rows)
assert not git(['status','--porcelain=v1']).strip()
print(json.dumps({'candidate_commit':commit,'handoff':ref(out/'handoff.json'),'manifest':ref(out/'manifest.json'),'source_manifest':ref(out/'exact11_foundation5_git_blobs.json'),'counts':counts,'actual_commit16_blobs_verified':True,'worktree_clean':True},ensure_ascii=False))
