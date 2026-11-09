import datetime,hashlib,json,pathlib,sqlite3,subprocess
E=pathlib.Path(__file__).resolve().parent;BASE=E.parent;R=E.parents[7]
P='a7ebcf2a322c6abcf87e043f601ee804';S='a09d4435036b2b32a0d7076bfc53fd93';Q='bb0cb22142a08e1cc63a722739c1f069';MC='mc-3f9329b391eaca14d82e7c4d3b9b6f34'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def h(obj):return 'sha256:'+hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(name,obj):
    with (E/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
pins=[]
def pin(p):
    x=dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size);pins.append(x);return x
base=read(BASE/'FINAL-manifest.json');assert len(base['members'])==35
for x in base['members']:assert sha(pathlib.Path(x['path']))==x['sha256']
put('prior-diagnosis-integrity.json',dict(manifest=pin(BASE/'FINAL-manifest.json'),members=35,unchanged=True,not_modified=True))
obs=R/'execution/v2.4/receipts/W05/W05-99/coding_model_observer_codex/20261014-current-chat/new-config-qualification-bb0cb221-after-confirm.json'
assert sha(obs)=='9ef07d026c94e60d8c461fe06fb898b8927eb68ea79039b45aea517136f1380f';pin(obs);o=read(obs)
put('observer-safe-fields.json',{k:o[k] for k in ['at','session','runtime','runtime_binding','runtime_plans','qualification_request','runtime_qualification_runs','stage','current_session_hash_matches_request','qualification_request_time_valid_now']})
req=o['qualification_request']['request'];assert h(req)==o['qualification_request']['request_hash']
data=R/'.local/live/current-chat-normal-desktop-first-use-20261012/data'
registry=data/'host/runtime-verifier-installation.json';old=read(registry);pin(registry)
current=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014/apps/desktop/resources/control/runtime-verifier-installation.json');new=read(current);pin(current)
oldmanifest=pathlib.Path(old['installation']['executable']).with_name('runtime-verifier-installation.json');pin(oldmanifest)
assert read(oldmanifest)==old['installation']
assert h(old['installation'])==old['installation_hash']
root='local-verifier-root-'+h([req['owner_host'],new['service_id']]).removeprefix('sha256:')[:24]
candidate=dict(schema='researchos.runtime-verifier-registration.v1',owner_host=req['owner_host'],owner_principal=req['owner_principal'],service_root=root,installation_hash=h(new),installation=new)
differences=[dict(field=k,old=old['installation'][k],new=new[k]) for k in new if old['installation'].get(k)!=new[k]]
assert len(differences)==3 and {r['field'] for r in differences}=={'executable','executable_hash','source_commit'}
assert all(old[k]==candidate[k] for k in ['schema','owner_host','owner_principal','service_root'])
binary=[]
for kind,install in [('registered',old['installation']),('current',new)]:
    p=pathlib.Path(install['executable']);pin(p);assert 'sha256:'+sha(p)==install['executable_hash']
    binary.append(dict(kind=kind,path=str(p),sha256=sha(p),bytes=p.stat().st_size,source_commit=install['source_commit']))
put('registration-comparison.json',dict(at=now(),persisted_record=old,current_candidate_record=candidate,old_installation_hash_recomputed=h(old['installation']),new_installation_hash_recomputed=h(new),old_record_hash_recomputed=h(old),new_record_hash_recomputed=h(candidate),production_hash_comparison_equal=h(old)==h(candidate),definite_rejection='registered verifier installation changed; explicit administrator replacement required',different_fields=differences,binary_hash_checks=binary,old_manifest_exactly_matches_registry=True,old_and_new_owner_host_principal_service_root_identical=True,canonical_hash_scope='all registration/installation values are strings or empty arrays; sorted UTF-8 JSON agrees with domain.Hash; old stored installation hash independently matched'))
put('registered-installation.public.json',old);put('candidate-installation.public.json',new)
for name,digest in [('attach-desktop-package-review-20261014/FINAL-report.json','d2da9b62846051b01f5d206b649de879d10d44bf4d2b221fe42aebed8fd17101'),('original-model-qualification-review-20261014/FINAL-report.json','dfe4ade015ad1f0ad81885d960e1a0f28e904cac445dcb83e2d1da52d00e7ae8')]:
    p=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees')/name;assert sha(p)==digest;pin(p)
put('historical-provenance-refs.json',pins[-2:])
rawdir=E/'raw';rawdir.mkdir()
ui=R/'execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry11_codex/20261014-current-chat'
uimeta=[]
for p in sorted(ui.glob('0[5-9]-*')):
    pin(p);(rawdir/p.name).write_bytes(p.read_bytes());uimeta.append(dict(path=str(p),last_write_utc=datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),timestamp_kind='filesystem metadata, not private-frame timing'))
put('UI-file-metadata.json',uimeta)
sources=['internal/host/runtime_qualification_windows.go','internal/host/runtime_verifier_process_windows.go','internal/host/desktop_management_windows.go','internal/domain/runtime_qualification_execution_windows.go','internal/domain/runtime_qualification_confirmation_windows.go','internal/domain/client_runtime_coding_windows.go','internal/domain/runtime_qualification.go','internal/domain/contracts.go','internal/canonical/jcs.go','apps/control/main.go','apps/control/runtime_qualification_windows.go','apps/runtime-verifier/main_windows.go']
caps=[]
core='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2'
for rel in sources:
    p=subprocess.run(['git','show',core+':'+rel],cwd=R,capture_output=True);assert p.returncode==0
    target=E/'source'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.stdout);caps.append(dict(commit=core,path=rel,sha256=sha(target),native_exit=0))
for rel in ['apps/desktop/main/main.js','apps/desktop/main/lib/desktop-management.js']:
    p=subprocess.run(['git','show','c8b7adab9f0c15eb33f235f8d0d9eb205794e376:'+rel],cwd=R,capture_output=True);assert p.returncode==0
    target=E/'source'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.stdout);caps.append(dict(commit='c8b7adab9f0c15eb33f235f8d0d9eb205794e376',path=rel,sha256=sha(target),native_exit=0))
put('source-captures.json',caps)
args=['git','grep','-n','-i','-E','replace.{0,40}verifier|verifier.{0,40}replace|registered verifier installation|runtime-verifier-installation',core,'--','*.go','*.js','*.mjs','*.py','*.md',':!**/node_modules/**',':!execution/receipts/**',':!execution/v2.4/receipts/**',':!spec/v2.0/**']
p=subprocess.run(args,cwd=R,capture_output=True);(rawdir/'replacement-search.stdout').write_bytes(p.stdout);(rawdir/'replacement-search.stderr').write_bytes(p.stderr);put('replacement-search.process.json',dict(argv=args,cwd=str(R),native_exit=p.returncode));assert p.returncode==0
c=sqlite3.connect((data/'researchos.sqlite').as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON');c.execute('BEGIN');queries=[]
def query(sql,args=()):
    queries.append(dict(sql=sql,parameters=list(args)));return [dict(x) for x in c.execute(sql,args)]
state=dict(at=now(),mode='URI mode=ro; PRAGMA query_only=ON; BEGIN/ROLLBACK',session=query('SELECT id,revision,writer_epoch,writer_client_id,lease_expires_at,model_config_ref,workspace_ref,run_id FROM client_sessions WHERE project_id=? AND id=?',(P,S)),consumption=query("SELECT key,created_at,json_extract(body,'$.run_ref.id') AS run_id FROM idempotency WHERE project=? AND operation='host:managed-runtime-qualification' AND key=?",(P,Q)),runs=query('SELECT run,task,runtime,epoch FROM runtime_qualification_runs WHERE project=? AND runtime=?',(P,req['runtime_id'])))
state['profile_summaries']=[]
for rt in query('SELECT runtime,profile_ref,profile_hash,technical_hash FROM runtime_bindings WHERE project=?',(P,)):
    ref=json.loads(rt['profile_ref']);a=query("SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?",(P,ref['id']))
    if not a:continue
    art=json.loads(a[0]['body']);raw=c.execute('SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1',(P,art['storage_key'])).fetchone()[0]
    if isinstance(raw,str):raw=raw.encode()
    profile=json.loads(raw);config=profile.get('model_config',{})
    if config.get('ref') not in [MC,'mc-079c6ca85595aaac2dd17c2d0ed77b93']:continue
    queries.append(dict(sql='SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1',parameters=[P,art['storage_key']],output='read in memory; persist only hashes and allowlisted non-secret fields'))
    assert 'sha256:'+hashlib.sha256(raw).hexdigest()==art['content_hash']==ref['content_hash']
    q=profile.get('model_qualification',{});auth=profile.get('coding_authorization');policy=profile.get('tool_policy') or {}
    safe=dict(runtime=rt['runtime'],model_ref=config.get('ref'),profile_ref=ref,profile_hash_valid=h(ref)==rt['profile_hash'],sealed_profile_bytes_hash_valid=True,profile_content_bytes=len(raw),backend=profile.get('backend'),command_id=profile.get('command_id'),credential_revision=profile.get('credential_revision'),normal_model_calls=config.get('max_calls'),normal_tool_names=[x.get('function',{}).get('name') for x in config.get('tools',[])],model_qualification=q,model_config_hash_matches_qualification=q.get('model_config_hash')==h(config),coding_authorization_present=bool(auth),tool_policy_hash=h(policy),coding_tool_policy_hash_matches=h(policy)==h(auth.get('tool_policy')) if auth else None)
    if auth:
        safe['authorization_scope']={k:auth.get(k) for k in ['schema','confirmation_id','model_config_ref','session_id','workspace_ref','workspace_hash','freeze_hash']}
        safe['check_summaries']=[{k:x.get(k) for k in ['id','executable','build_hash','toolchain_root','toolchain_hash','argv','resources']} for x in policy.get('checks',[])]
        safe['write_paths']=policy.get('write_paths');safe['read_paths_count']=len(policy.get('read_paths',[]))
        safe['checks_source_counts']=[dict(id=x.get('id'),source_paths=len(x.get('source_paths',[]))) for x in policy.get('checks',[])]
        safe['authorization_model_matches']=auth.get('model_config_ref')==config.get('ref');safe['authorization_session_matches']=auth.get('session_id')==S
    state['profile_summaries'].append(safe)
state['unsettled_counts']={}
for label,sql in read(BASE/'live-readonly-global-idle.json')['queries'].items():state['unsettled_counts'][label]=query(sql)
state['verifier_principals']=query('SELECT id,roles,revoked,can_create_project FROM auth_principals WHERE id=? OR id=?',(root,'local-verifier-'+h([root,P]).removeprefix('sha256:')[:32]))
state['verifier_lineage']=query('SELECT principal,root,parent FROM orchestration_identity WHERE principal=? OR principal=?',(root,'local-verifier-'+h([root,P]).removeprefix('sha256:')[:32]))
c.rollback();c.close();state['queries']=queries;state['mutations']=0;state['api_calls']=0;state['model_calls']=0;put('live-readonly-gate-observation.json',state);put('input-pins.json',pins)
print(json.dumps({'mismatch_fields':differences,'original_registration_hash':h(old),'new_candidate_hash':h(candidate),'new_installation_hash':h(new),'consumption':state['consumption'],'runs':state['runs'],'profiles':[{k:x[k] for k in ['model_ref','runtime','normal_model_calls','normal_tool_names','model_config_hash_matches_qualification']} for x in state['profile_summaries']],'unsettled':state['unsettled_counts']},ensure_ascii=False))
