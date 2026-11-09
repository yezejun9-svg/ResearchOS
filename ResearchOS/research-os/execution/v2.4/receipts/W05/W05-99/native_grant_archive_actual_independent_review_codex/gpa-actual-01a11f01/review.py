from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;B=O.parent.parent
def load(n):return json.loads((O/n).read_bytes())
def norm(ref):return dict(path=str(Path(ref['path']).resolve()),sha256=ref['sha256'].removeprefix('sha256:'),bytes=ref['bytes'])
def same(a,b):return norm(a)==norm(b)
checks=[]
def check(name,value):checks.append(dict(name=name,passed=bool(value)))
def save(n,obj):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
a=load('archive.manifest.input.json');q=load('request.input.json');p=load('payload_ref.input');cfg=load('config_ref.input');snap=load('snapshot_ref.input');backup=load('backup_manifest.input');equal=load('raw-equality.json');io=load('root-original-tool-io.input.json');source=(O/'helper_source.input').read_bytes()
check('exact reviewed helper',hashlib.sha256(source).hexdigest()=='96a7195080dc99a6b669336c7563a51cc1ba60b4f3584b6f4b7a6330a05d0771' and len(source)==23941)
source_gate=B/'native_grant_bounded_read_independent_review_codex/gbr-review-01a11f01/HDF.json';sgraw=source_gate.read_bytes();check('Source resource gate exact HDF',hashlib.sha256(sgraw).hexdigest()=='72189762f788bdd69a0b67fc7447be8c1196f7b11465bbee6b1e0a34d241ea02' and len(sgraw)==6588);sg=json.loads(sgraw);check('Source gate accepts exact helper',sg['status']=='SOURCE_ACCEPTED_FOR_ROOT_BOUNDED_ARCHIVE_RESOURCE_GATE' and same(sg['helper_ref'],q['HelperSource']))
for field,key in (('request_ref',None),('config_ref','Config'),('snapshot_ref','Snapshot'),('payload_ref','Payload')):
 check('archive request binding '+field,same(a[field],load('initial-pins.json')[1]) if key is None else same(a[field],q[key]))
check('fixed C12 config',norm(a['config_ref'])['sha256']=='38a1305ed39835194678d0e9a6f06acec1b74b1f2ba1071bc1769841c57c2256' and a['config_ref']['bytes']==1106152)
check('fixed C12 case grant phase',a['case_id']==snap['case_id']=='t12cl149d6f49321' and snap['phase']=='grant' and same(snap['payload_ref'],q['Payload']))
check('full closure exact counts',a['closure']=='FULL_TEMP_PIN_CLOSURE' and a['missing_roles']==[] and a['required_unique_temp_pin_count']==a['archived_unique_count']==len(a['members'])==61)
pins={x['role']:x for x in p['pins']};members={x['role']:x for x in a['members']};selected={x['role']:x for x in q['Entries']}
check('unique grant roles',len(pins)==len(p['pins'])==69);check('unique archive and request roles',len(members)==len(selected)==len(q['Entries'])==61)
tree=ast.parse(source);inv=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='INVENTORY')
source_roles={'source-inventory:'+name for name in inv if not name.startswith('migrations/sqlite/0024_')};target_roles={'target-inventory:'+name for name in inv};ciphers={'encrypted-backup-payload:'+file['name']+'.enc' for file in backup['files']}
expected=source_roles|target_roles|ciphers|{'encrypted-backup-manifest','isolated-restore-rehearsal'}
check('57 inventory and 2 cipher roles',len(source_roles)==28 and len(target_roles)==29 and len(ciphers)==2 and len(expected)==61)
check('complete selection exact roles',set(members)==set(selected)==expected)
check('counts agree actual roles',a['source_inventory_count']==len(source_roles) and a['target_inventory_count']==len(target_roles))
for role,member in members.items():
 check('selected original binds grant '+role,same(member['original_ref'],selected[role]) and same(selected[role],pins[role]))
 original=norm(member['original_ref']);archived=norm(member['archived_ref']);check('raw identity preserved '+role,original['sha256']==archived['sha256'] and original['bytes']==archived['bytes'])
 check('archive path scope '+role,Path(archived['path']).parent==Path(q['OutputDirectory']).resolve())
 check('original TEMP scope '+role,Path(original['path']).is_relative_to(Path(cfg['Environment']['TEMP']).resolve()))
 if role in source_roles|target_roles:
  relative=role.split(':',1)[1];check('fixed inventory pin '+role,original['sha256']==inv[relative]['sha256'].removeprefix('sha256:') and original['bytes']==inv[relative]['bytes'])
 if role in ciphers:check('opaque cipher only '+role,member['kind']=='opaque-ciphertext' and archived['path'].endswith('.enc'))
check('original backup binding',same(members['encrypted-backup-manifest']['original_ref'],p['binding']['backup']))
check('original rehearsal binding',same(members['isolated-restore-rehearsal']['original_ref'],p['binding']['rehearsal']))
check('all 61 direct original vs archive raw equality',len(equal)==61 and all(x['original_and_archive_exact_raw_equal'] for x in equal))
check('unique physical archive copies',len({norm(x['archived_ref'])['path'].casefold() for x in members.values()})==61)
check('one declared migration alias',len(a['role_aliases'])==1)
alias=a['role_aliases'][0];target=members['target-inventory:migrations/sqlite/0024_prepared_run_abandonment.sql'];check('alias one copy exact original/archive',alias['role']=='migration-sql' and alias['target_role']==target['role'] and same(alias['original_ref'],pins['migration-sql']) and same(alias['original_ref'],target['original_ref']) and same(alias['archived_ref'],target['archived_ref']) and 'migration-sql' not in members)
g=a['source_guard_cleanup'];check('archive actual finally guard success',g['attempted'] is True and g['verification']=='PASSED' and g['closed'] is True and g['retained_handles_count']==0 and g['errors']==[] and g['failure'] is None)
entries={norm(x)['path'].casefold():x for x in g['entries']};check('archive actual70 entries unique verified closed',len(entries)==len(g['entries'])==70 and all(x['verified'] and x['final_path_match'] and x['closed'] for x in entries.values()))
for role,member in members.items():
 expectedref=norm(member['original_ref']);actual=entries.get(expectedref['path'].casefold());check('archive guard covered original '+role,actual is not None and norm(actual)==expectedref)
for ref in [a[k] for k in ('request_ref','config_ref','snapshot_ref','payload_ref')]+[q['HelperSource']]:
 e=entries.get(norm(ref)['path'].casefold());check('archive guard support '+Path(ref['path']).name,e is not None and same(e,ref))
ours=load('readguard.actual.closed.json');check('independent guard released',ours['closed'] and ours['retained_handles_count']==0 and not ours['errors'] and ours['verification']=='PASSED')
steps=io['byStep'];wanted={'root_c12_archive_request_builder_actual':('121052','ROOT_ARCHIVE_REQUEST_WRITTEN '),'root_c12_archive_concrete_request_review_actual':('a7853f','{"Schema"'),'root_c12_full_temp_archive_actual':('6a08f0','GRANT_PUBLIC_ARCHIVE_OK ')}
for name,(chunk,marker) in wanted.items():
 entry=steps[name];check('actual outer Python exit0 '+name,entry['chunk_id']==chunk and entry['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in entry['output'] and marker in entry['output'])
archive_step=steps['root_c12_full_temp_archive_actual'];line=next(x for x in archive_step['output'].splitlines() if x.startswith('GRANT_PUBLIC_ARCHIVE_OK '));emitted=json.loads(line[len('GRANT_PUBLIC_ARCHIVE_OK '):]);check('actual output binds exact archive manifest',same(emitted,load('initial-pins.json')[0]))
check('nonacceptance fields preserved',a['copied_raw_bytes_only'] is True and a['recursive_reference_follow'] is False and all(a[k] is False for k in ('signature_verified','grant_freshness_or_authority_claim','original_owner_acceptance','nine_cases_acceptance','formal_42_acceptance')))
check('grant timing preserved as raw strings',p['issued_utc']==io['grantIssuedUTC'] and p['expires_utc']==io['grantExpiresUTC'])
check('Root observation has no grant publish/apply claim',io['grantPublished'] is False and io['migrationApplyNotStarted'] is True and io['partialAttemptNotAccepted'] is True and io['NativePrimaryFinalExit'] is None and io['RootOuterServeFinalExit'] is None)
save('checks.json',checks);save('review.json',dict(status='FULL_TEMP_PIN_CLOSURE_ACCEPTED_ARCHIVE_COMPONENT_ONLY',checks=len(checks),failed=sum(not c['passed'] for c in checks),originals=61,archives=61,raw_equal=61,source_inventory=28,target_inventory=29,backup=1,rehearsal=1,ciphertexts=2,actual_guard_entries=70,actual_guard_closed=True,independent_guard_inputs=128,independent_guard_closed=True,TEMP_handles_released=True,helper_ref=q['HelperSource'],source_review_HDF=dict(path=str(source_gate),sha256=hashlib.sha256(sgraw).hexdigest(),bytes=len(sgraw)),actual_archive_output_ref=emitted,actual_builder_outer_exit=0,actual_builder_python_exit=0,actual_archive_outer_exit=0,actual_archive_python_exit=0,actual_product_native_exit=None,private_refs_followed=False,SQL_or_rawDB_or_decryption=False,new_failure_ordinals=[],grant_publish_or_apply_accepted=False,Native_case_success=False,formal_acceptance=False))
print(json.dumps(dict(checks=len(checks),failed=[c['name'] for c in checks if not c['passed']],archive_component='FULL_TEMP_PIN_CLOSURE',Native_success=False,TEMP_handles_released=True)))
