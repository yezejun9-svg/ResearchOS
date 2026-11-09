from pathlib import Path
import json,hashlib,os
HERE=Path(__file__).resolve().parent
N=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-ttl-compile-root-458f017f3c294bb6");I=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-ttl-isolation-root-29cb40af6a46453a")
R=N.parents[5]
refs={}
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def key(p):return str(Path(p).resolve()).casefold()
def verify(r):
 a=pin(r['path']);assert a['sha256']==r['sha256'].removeprefix('sha256:') and a['bytes']==r['bytes'],str(r['path'])
 if key(a['path']) in refs:assert refs[key(a['path'])]==a
 refs[key(a['path'])]=a;return Path(a['path']).read_bytes()
def rd(p):return json.loads(verify(pin(p)))
def write(name,v):
 p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
closed=json.loads(verify(dict(path=str(N/'validation.closed.json'),sha256='87942e547c61479024b5a74634fb7adfe3f9e6dc89928973223c02546ef8bf28',bytes=7205)))
iso=json.loads(verify(dict(path=str(I/'isolation.ready.json'),sha256='e92305cfd83cd199731ab0a5d8ebc903c6d80ac2b62fd4fbc876a8fa9d961848',bytes=3302)))
rio=json.loads(verify(dict(path=str(N/'original-tool-io.json'),sha256='357fa83b94d3b5db3f78fdc3e384b99b6677c643af27d961c574b2b051dbef69',bytes=7165)))
T=Path(closed['current_source_root']);assert T==Path(iso['worktree_root'])
root=Path(iso['repository_root']);assert T.is_relative_to(root/'.local/worktrees')
assert closed['error'] is None and closed['source_count']==43 and closed['all_owned_jobs_closed']
assert closed['unit_actions']=={} and closed['unit_pass_count']==closed['unit_fail_count']==closed['unit_skip_count']==0
assert closed['unchanged_exact_error_units_not_rerun'] and closed['native_migration_cases_executed']==0
for k in ['real_owner_private_input_used','Main_adopted','formal_acceptance']:assert closed[k] is False
for k in ['issuer_signatures_created','production_db_writes','external_model_provider_requests']:assert closed[k]==0
assert closed['original_trial_provider_requests'] is None
assert rio['compile']['completion']['chunk_id']=='ab8542' and rio['compile']['completion']['exit_code']==0
assert 'ROOT_PYTHON_EXIT=0' in rio['compile']['completion']['output']
assert rio['compile']['initial_result']['session_id']==rio['compile']['first_wait']['session_id']==36125
assert 'full completion result object was not stored' in rio['isolation']['completion']['recording_scope']
assert rio['isolation']['completion']['actual_outer_exit']==rio['isolation']['completion']['actual_python_exit']==0
guards={};guard_maps={}
for prefix,d,names in [('compile',N,['input','runtime','candidate','compiler','binary']),('isolation',I,['','runtime'])]:
 for name in names:
  filename=(name+'-' if name else '')+'source-guard.cleanup.actual.json';g=rd(d/filename)
  assert g['closed'] and g['verification']=='PASSED' and g['share_mode']=='FILE_SHARE_READ_ONLY' and g['failure'] is None and not g['errors'] and g['retained_handles_count']==0
  m={}
  for e in g['entries']:
   assert e['verified'] and e['final_path_match'] and e['closed'];verify(e)
   assert key(e['path']) not in m;m[key(e['path'])]=refs[key(e['path'])]
  guards[prefix+'/'+name]=len(m);guard_maps[prefix+'/'+name]=m
assert guards=={'compile/input':155,'compile/runtime':29,'compile/candidate':44,'compile/compiler':3920,'compile/binary':5,'isolation/':80,'isolation/runtime':30}
jobs=[];receipts={}
for family,d,rr in [('compile',N,closed['invocation_refs']),('isolation',I,iso['invocation_refs'])]:
 assert len(rr)==(7 if family=='compile' else 5)
 for ref in rr:
  inv=json.loads(verify(ref));label=Path(ref['path']).name.removesuffix('.invocation.json')
  receipts[family+'/'+label]=inv
  assert inv['exception'] is None and inv['actual_native_exit']==0
  q=inv['result'];c=q['job_cleanup']
  assert q['actual_exit']==0 and q['resumed'] and not q['timed_out'] and q['error'] is None
  assert isinstance(q['owned_child_pid'],int) and q['owned_child_pid']>0 and q['creation_time_100ns']>0
  for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']:assert c[k] is True
  assert c['active_processes_last_observed']==0 and not c['errors'] and c['termination_requested'] is False
  verify(inv['stdout_ref']);verify(inv['stderr_ref'])
  jobs.append(dict(family=family,label=label,pid=q['owned_child_pid'],creation_time_100ns=q['creation_time_100ns'],actual_exit=0,assigned_before_resume=True,closed=True,elapsed_seconds=q['elapsed_seconds']))
assert len({(x['pid'],x['creation_time_100ns']) for x in jobs})==12
assert set(k.split('/',1)[1] for k in receipts if k.startswith('compile/'))=={'format','tagged-compiler-input-list','control-build','maintenance-root-build','enrollment-build','backup-build','tagged-test-binary-compile'}
for k,v in receipts.items():
 if k.startswith('compile/'):
  assert Path(v['cwd'])==T
  env=v['public_environment']
  for f in ['GOWORK','GOENV','GOPROXY','GOSUMDB']:assert env[f]=='off'
  assert env['GOTOOLCHAIN']=='local' and env['CGO_ENABLED']=='0' and env['GOFLAGS']=='-mod=readonly -p=1'
head=iso['head'];assert head=='adc460c2138528f163f7fdab5e8d81dde157b7fb'
for label in ['head-before','head-after']:assert (I/(label+'.stdout.raw')).read_text().strip()==head
dirty=(I/'tracked-status.stdout.raw').read_text(encoding='utf8').splitlines()
assert dirty==iso['tracked_dirty_paths'] and len(dirty)==13 and sum(x.startswith(' D ') for x in dirty)==11
assert not (I/'staged-status.stdout.raw').read_bytes().strip() and iso['staged_index_empty'] and iso['main_canonical_unchanged']
identity=json.loads(verify(iso['project_identity_ref']));assert identity['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
create=receipts['isolation/create-worktree']['argv'];assert 'worktree' in create and '--detach' in create and str(T) in create and head in create
canonA=rd(I/'canonical.pre-run.exact.json');canonB=json.loads(verify(closed['canonical_pre_run_ref']))
assert canonA['refs']==canonB['refs'] and canonA['revision']==canonB['checkpoint_revision']==358
for r in canonA['refs']:verify(r)
assert canonA['refs'][0]['sha256']=='370c3b73f630a952a80c9082b27ed09e28278cc79bdf65bfbe453c317cb42064' and canonA['refs'][0]['bytes']==4093175
overlay=json.loads(verify(closed['source_overlay_ref']));formatted=json.loads(verify(closed['formatted_source_ref']))
base=json.loads(verify(closed['base43_formatted_ref']));assert len(overlay['sources'])==len(formatted)==len(base)==43
baseRoot=Path(base[0]['path'])
# Every baseline path carries the T5 worktree segment; derive its root from the known source manifest.
t5=root/'.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2'
baseMap={Path(x['path']).relative_to(t5).as_posix():x for x in base}
formatMap={Path(x['path']).relative_to(T).as_posix():x for x in formatted}
assert set(baseMap)==set(formatMap)==set(overlay['sources'])
changed=[]
for name,r in overlay['sources'].items():
 data=verify(r);b=verify(baseMap[name]);actual=verify(formatMap[name])
 assert data==actual
 if data!=b:changed.append(name)
assert changed==['internal/domain/native_migration_authority_harness_windows_test.go']
name=changed[0];new=Path(formatMap[name]['path']).read_bytes();old=Path(baseMap[name]['path']).read_bytes()
assert new.count(b'15*time.Minute')==2 and old.count(b'time.Hour')==2 and new.replace(b'15*time.Minute',b'time.Hour')==old
deltaReview=json.loads(verify(closed['source_delta_review_ref']));assert deltaReview['source_accepted'] and not deltaReview['native_acceptance']
verify(deltaReview['manifest_ref']);verify(deltaReview['review_ref'])
inv=json.loads(verify(closed['compiler_input_inventory_ref']))
assert inv['build_tag']=='researchos_native_recovery_harness' and inv['GOWORK']=='off' and inv['CGO_ENABLED']=='0'
raw=(N/'tagged-compiler-input-list.stdout.raw').read_text(encoding='utf8');pos=0;decoder=json.JSONDecoder();pkgs=[];expectedInputs={};expectedEmbeds=[];selected=[]
fields=('GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles')
harness='native_migration_authority_harness_windows_test.go'
while pos<len(raw):
 while pos<len(raw) and raw[pos].isspace():pos+=1
 if pos==len(raw):break
 p,pos=decoder.raw_decode(raw,pos);assert not p.get('Error') and not p.get('DepsErrors');pkgs.append(p)
 if not p.get('Dir'):continue
 for field in fields:
  for filename in p.get(field,[]):
   pp=Path(filename);pp=pp if pp.is_absolute() else Path(p['Dir'])/pp
   r=pin(pp);verify(r);expectedInputs[key(pp)]=r
   if field.endswith('EmbedFiles'):expectedEmbeds.append(dict(package=p['ImportPath'],ref=r,field=field))
   if pp.name==harness:selected.append(dict(package=p['ImportPath'],field=field,ref=r))
assert len(pkgs)==inv['package_count']==364 and [p.get('ImportPath') for p in pkgs]==inv['packages']
assert len(expectedInputs)==inv['build_input_count']==3793
assert {key(r['path']):r for r in inv['build_inputs']}==expectedInputs
assert expectedEmbeds==inv['actual_embed_files'] and len(expectedEmbeds)==38
assert any(x['field']=='TestGoFiles' for x in selected) and any(x['field'] in ['GoFiles','CompiledGoFiles'] and '[' in x['package'] for x in selected)
product={}
for relative in ['apps/control','internal','adapters','evaluation','ops','migrations/sqlite','spec/v2.0/contracts']:
 d=T/relative;assert d.is_dir() and not d.is_symlink()
 for p in d.rglob('*'):
  assert not p.is_symlink()
  if p.is_dir():continue
  assert p.is_file();r=pin(p);verify(r);product[key(p)]=r
for relative in ['go.mod','go.sum','execution/toolchains/locked.json']:
 r=pin(T/relative);verify(r);product[key(r['path'])]=r
assert product=={key(r['path']):r for r in inv['product_inventory']} and len(product)==inv['product_inventory_count']==599
goRef=inv['GoRef'];go=Path(goRef['path']);verify(goRef)
tools=[pin(p) for p in (go.parent.parent/'pkg/tool/windows_amd64').iterdir() if p.is_file()]
assert len(tools)==len(inv['compiler_tool_refs'])==8 and {key(x['path']):x for x in tools}=={key(x['path']):x for x in inv['compiler_tool_refs']}
expectedCompiler={**expectedInputs,**product,**{key(x['path']):x for x in tools}}
for r in [closed['compiler_input_inventory_ref'],goRef,pin(go.parent.parent/'VERSION')]:expectedCompiler[key(r['path'])]=r
assert expectedCompiler==guard_maps['compile/compiler']
expectedCandidate={key(x['path']):x for x in [*formatted,closed['formatted_source_ref']]}
assert expectedCandidate==guard_maps['compile/candidate']
assert {key(x['path']):x for x in closed['binary_refs'].values()}==guard_maps['compile/binary']
assert key(go.parent.parent/'src/go.mod') in guard_maps['compile/input']
assert len(closed['binary_refs'])==5
for label,r in closed['binary_refs'].items():
 verify(r);label2='tagged-test-binary-compile' if label=='tagged-test-harness' else label
 argv=receipts['compile/'+label2]['argv'];assert Path(argv[0])==go and argv[argv.index('-o')+1]==r['path']
 assert '-trimpath' in argv and '-buildvcs=false' in argv
 if label=='tagged-test-harness':assert argv[1:3]==['test','-c'] and '-tags=researchos_native_recovery_harness' in argv
 else:assert argv[1]=='build'
# Copy exact public source/actual artifacts into this review; executable binaries remain pinned inputs.
copies=[]
for label,d in [('root-compile-evidence',N),('root-isolation-evidence',I)]:
 for p in sorted(d.iterdir()):
  if not p.is_file():continue
  original=pin(p);verify(original);target=HERE/label/p.name;target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as out:out.write(p.read_bytes())
  copied=pin(target);assert copied['sha256']==original['sha256'] and copied['bytes']==original['bytes']
  copies.append(dict(original_ref=original,copied_ref=copied))
review=dict(schema='researchos.independent-native-ttl-compile-review.v1',decision='T7_TTL43_COMPILE_COMPONENT_ACCEPTED_NATIVE_ACTUAL_PENDING',
 source_count=43,unchanged_T5_sources=42,changed_source=changed,TTL_inverse_entire_baseline=True,
 compile_jobs=7,isolation_jobs=5,jobs=jobs,guard_groups=guards,
 package_count=364,build_input_count=3793,product_inventory_count=599,embed_occurrences=38,compiler_tool_count=8,
 compiler_guard_exact_reconstruction=True,GoRef_and_VERSION_explicitly_guarded=True,GOROOT_src_go_mod_held_input=True,
 selected_harness_compiler_fields=selected,binary_refs=closed['binary_refs'],
 canonical_pre_run_independently_persisted_twice=True,canonical_refs=canonA['refs'],canonical_current_exact=True,
 project_identity_ref=iso['project_identity_ref'],Main_head_before_after=head,recorded_dirty_paths=13,recorded_staged_index_empty=True,
 Main_pinned_sources_unchanged=True,unit_executed=False,new_unit_pass_count=0,native_migration_executed=False,issuer_signatures=0,private_owner_input=False,production_DB_writes=0,external_model_requests=0,original_provider_requests=None,
 original_tool_io_ref=pin(N/'original-tool-io.json'),Root_compile_original_objects_persisted=True,
 isolation_final_tool_result_complete_object_persisted=False,isolation_final_metadata_only=True,
 copied_public_evidence_count=len(copies),copies=copies,reference_count=len(refs),
 authority='NONE',Main_adopted=False,native_acceptance=False,Owner_acceptance=False,formal_acceptance=False,
 new_mechanical_errors=0,counter_reset=False,
 limitations=['Compiled test binary was not executed; old 25 exact-error units were not rerun','Isolation final outer tool object was not stored: only rendered completion metadata; five Git subprocess receipts/raw are exact','Dirty/staged Git state is the recorded pre-isolation observation; Main HEAD is observed before and after, with selected Main source bytes and canonical unchanged','Compilation validation.closed.json preceded finally cleanup; independent acceptance additionally requires all five saved cleanup receipts and outer completion'],
 stop=True)
write('review.json',review)
write('verified-input-pins.json',dict(schema='researchos.independent-verified-pins.v1',count=len(refs),references=list(refs.values()),drift_count=0))
print(json.dumps(dict(decision=review['decision'],references=len(refs),copied_public_files=len(copies),guards=guards,compile_jobs=7,isolation_jobs=5,selected_harness_occurrences=len(selected),drift=0),ensure_ascii=True))

