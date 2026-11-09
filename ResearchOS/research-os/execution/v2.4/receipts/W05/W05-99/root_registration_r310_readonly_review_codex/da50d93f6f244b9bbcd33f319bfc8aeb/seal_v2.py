import ast,hashlib,json,os,subprocess,datetime
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
N=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/complete-public-graph-and-g2-r310'
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def load(p):return json.loads(Path(p).read_bytes())
def save(n,v):
 with (HERE/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(HERE/n)
def check(b,msg):
 if not b:raise RuntimeError(msg)
expected={'register.v2.py':'ecd2f9a12891d63f4211cc2b095b9ad733746b59832278228df854adb7fa3086','run.v2.py':'eeecbdda12a327f2965134cf87b32dbf6c946841a65c062cc140b0f2dc148ad1','prepared_refs.v2.json':'dab62a2fe57ad3b213d409ee329697978cb60bb7aac677e9ecd1cb76a149307a','audit.v2.json':'d4ad5856edfe0e486df0add5a0f661835ceef186074790e0ad29c4a6bf443b0d','list_replay.v2.py':'85e35100bd7ed509883a0ae4729f68aab283032002f8eb8784d28900e97c54ea','g2_replay.v4.py':'e687bd35560d4c34b4e939609b617a5d4770b4a45d51c3b132fca60a4bfa39f5'}
for name,sha in expected.items():
 check(ref(N/name)['sha256']==sha,'PIN:'+name)
 if name.endswith('.py'):ast.parse((N/name).read_bytes())
 with (HERE/('reviewed-'+name)).open('xb') as f:f.write((N/name).read_bytes())
p=load(N/'prepared_refs.v2.json');old=load(N/'prepared_refs.json')
verified=[]
for row in p['verified_refs']:
 check(ref(ROOT/row['path'])==row,'REF:'+row['path']);verified.append(row)
check(len(verified)==57 and all(x in verified for x in old['verified_refs']),'OLD49')
copied=[]
for row in p['canonical_before']:
 check(ref(ROOT/row['path'])==row,'CANONICAL')
 copy=HERE/('before-'+Path(row['path']).name)
 check(copy.read_bytes()==(ROOT/row['path']).read_bytes(),'COPY')
 copied.append(ref(copy))
check(p['origins']==old['origins'],'ORIGINS')
cp=load(ROOT/'execution/v2.4/checkpoint.json');ow=load(ROOT/'execution/v2.4/path_ownership.json')
check([cp['revision'],ow['revision'],len(cp['failure_counters'])]==[309,137,379],'TUPLE')
lock=load(ROOT/'execution/toolchains/locked.json')['tools'];git=lock['git']['path']
check(hashlib.sha256(Path(git).read_bytes()).hexdigest()==lock['git']['sha256'],'GIT_HASH')
env={k:os.environ[k] for k in ('SystemRoot','WINDIR','ComSpec','PATH','PATHEXT') if k in os.environ}
env.update(GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_OPTIONAL_LOCKS='0')
for label,args in [('final-head',['rev-parse','HEAD']),('final-status',['status','--porcelain=v1','--untracked-files=no'])]:
 with (HERE/(label+'.stdout.raw')).open('xb') as out,(HERE/(label+'.stderr.raw')).open('xb') as err:
  r=subprocess.run([git,*args],cwd=ROOT,env=env,stdout=out,stderr=err)
 save(label+'.invocation.json',dict(argv=[git,*args],actual_exit=r.returncode,stdout=ref(HERE/(label+'.stdout.raw')),stderr=ref(HERE/(label+'.stderr.raw'))))
 check(r.returncode==0,'GIT_READ')
check((HERE/'final-head.stdout.raw').read_text().strip()==p['head'],'HEAD')
check(hashlib.sha256((HERE/'final-status.stdout.raw').read_bytes()).hexdigest()==p['git_status_sha256'],'STATUS')
launchers=[]
for rel,sha in [('root-list14-launch-r310/launch.v2.py','8d621cf97dcac47ae1fee09254d12af8c090720077eb10e9986c7bd5fbf95478'),('root-g2-prepare-launch-r310/launch.v2.py','4a727ec923012d6cc0c231c1346e596e89656b5a467608c3fc4ab2a1766df13d')]:
 src=N.parent/rel;check(ref(src)['sha256']==sha,'LAUNCHER_PIN');ast.parse(src.read_bytes())
 with (HERE/(src.parent.name+'-launch.v2.py')).open('xb') as f:f.write(src.read_bytes())
 launchers.append(ref(src))
for name in ('cli17_scope.json','cli_windows4_scope.json'):
 scope=load(N/name);g=scope['cli_bounded_continuation']
 check(scope['registration_checkpoint']==310 and not scope['source_acceptance'],'CLI_SCOPE')
 check(not Path(g['output']).exists(),'CLI_OUT_EXISTS')
 for key in ('kernel_resource_ref','roster_ref','owned_process_helper_ref'):
  rr=g[key];raw=Path(rr['path']).read_bytes();check(hashlib.sha256(raw).hexdigest()==rr['sha256'] and len(raw)==rr['bytes'],'CLI_REF')
ls=load(N/'list_independent_scope.v2.json');g2=load(N/'g2_prepare_scope.v2.json')
check(len(ls['ordered_cases'])==14 and len(ls['public_JEV_sources'])==36 and ls['maximum_loopback_HTTP_calls_including_setup']==224,'LIST_LIMITS')
check(all(not Path(ls[k]).exists() for k in ('checkout','output')),'LIST_OUTPUT')
check(g2['phases']==['prepare'] and g2['prepare_product_test_cases']==0 and g2['future_cases']==29,'G2_PREPARE_ONLY')
check(all(not Path(g2[k]).exists() for k in ('work_root','output_root')),'G2_OUTPUT')
audit=save('v2_reference_audit.json',dict(verified_refs=verified,count=57,original49_retained=True,canonical_before=p['canonical_before'],copied_canonical_before_refs=copied,origins=p['origins'],new_counter_delta=5,actual_registration_executed=False,new_tool_failures=0,static_only=True,outer_launchers=launchers))
review=save('review.json',dict(schema='researchos.root-registration-source-review.v1',reviewer='codex:/root/w05_merge_review',decision='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION',requested_changes=[],actual_registration_executed=False,expected_before=[309,137,379],expected_after=[310,138,384],register_sha256=expected['register.v2.py'],wrapper_sha256=expected['run.v2.py'],prepared_refs_sha256=expected['prepared_refs.v2.json'],audit_sha256=expected['audit.v2.json'],canonical_before=p['canonical_before'],copied_canonical_before_refs=copied,reviewed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),evidence_audit_ref=audit,original_request_changes_ref=ref(HERE/'original_draft_audit.json'),resolved_findings=[dict(id='R310-01',resolution='list v2 hashes the exact helper_raw and compiles those bytes into ModuleType; helper SourceFileLoader/pyc use removed. Explicit helper source plus actual imported source/cache/DLL remain frozen.'),dict(id='R310-02',resolution='G2 v4 keeps resource_baseline immutable and checks it after export/graph before expanding inputs and again after build; existing build closure checks retained.')],registration_guards=['Wrapper checks four actual metadata bytes and copied independent originals, review/registrar/wrapper/prepared/audit hashes, locked Python/Git, HEAD/status before child launch.','Registrar caches same-read ref bytes and verifies57 references, five unique new origins and unchanged379 prefix.','Original/desired/intent/temp records precede replacements. All four canonical bytes and HEAD/status rechecked before every replace; own expected bytes/cache updated only after exact write.','Post checks310/138/384, old379prefix, ST/commands, exact trackedstatus with11 old deletions and formalstatus. Exception records current four hashes and phase; no rollback/auto retry.'],scope_limits=['CLI: registration of separate17/107 then1/4 scopes only; old110 retained, no source acceptance. This review of Root routing/pins does not independently accept reviewer-authored prepared CLI controller or CLI product.','List: exact pinned2source and14selectors, complete known518publiccatalog in fresh713export; resource tests are not selected, no SDK/model/private execution. All14assertions and input/job/DB boundaries unchanged.','G2: prepare-only grant generated by reviewed outer launcher only after actualCP310 and exact registered scope; actual checkpoint copied and added to scope_refs. No29 execution authorization: future immutable grant must bind real prepared.json SHA.','Desktop remains REQUEST_CHANGES with no source writer. Main/source/whole9/formal acceptance stays unchanged.'],outer_launchers=launchers,outer_launcher_findings=['List outer binds actualCP/OWdesired, ST/CMunchanged,310/384, exact current scope/innerSHA/HEAD/status, publicenvironment and nullable invocation viafinally.','G2 outer binds actualCP310+scoperef before writing actual_registration_completed=true prepare grant. Only phases=[prepare]; grant includes CPsnapshot, scope, launcher and innerrefs. It does not launch execute.'],actual_product_tests=0,actual_SQL_HTTP_SDK_model_calls=0,actual_helper_import_or_DLL_load=0,actual_source_writes=0,formal_increment=0))
entries=[ref(f) for f in sorted(HERE.iterdir()) if f.is_file()]
manifest=save('manifest.json',dict(schema='researchos.receipt-manifest.v1',entries=entries,count=len(entries),includes_self=False))
handoff=save('handoff.json',dict(review=review,manifest=manifest,audit=audit,actual_registration_executed=False,decision='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION',source_or_formal_acceptance=False))
print(json.dumps(dict(review=review,manifest=manifest,handoff=handoff),ensure_ascii=False))
