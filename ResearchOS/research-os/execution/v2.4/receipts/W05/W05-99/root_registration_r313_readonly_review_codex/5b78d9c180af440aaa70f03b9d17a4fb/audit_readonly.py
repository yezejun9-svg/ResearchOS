import ast,hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
D=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-g2-finite29-execute-r313'
L=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/root-g2-execute29-launch-r313/launch.py'
PINS={'register.py':'fcb7f06fe4ca629c976b68d203f01f68c958127dc18af53cd9b11b5052270b77','run.py':'a9f7ebe08fab043f5d98a1127e342224c33a01affce277d404437cf9400264eb','prepared_refs.json':'138776b221754901e20b54ddd81d5f9c0cbf7633b3c09a6b4f20b0677cfca02b','audit.json':'37e65e3ebdbff67f352b0c24d1ef6e1eb826128982446fcded7d82981df4f971'}
def need(v,m):
 if not v:raise RuntimeError(m)
def digest(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(ROOT).as_posix(),'sha256':digest(b),'bytes':len(b)}
def check(pin):
 p=Path(pin['path']);p=p if p.is_absolute() else ROOT/p
 b=p.read_bytes();need(digest(b)==pin['sha256'] and len(b)==pin['bytes'],'pin '+str(p));return ref(p)
def save(n,x):
 with (HERE/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
for n,h in PINS.items():need(digest((D/n).read_bytes())==h,'draft '+n)
need(digest(L.read_bytes())=='d6d869e9558f9627e2a1297ab8040257a4e9f1477f9ae765a708cc104878328a','launcher')
p=json.loads((D/'prepared_refs.json').read_bytes())
checked=[check(x) for x in p['verified_refs']]
pins=p['pins'];scope=json.loads((ROOT/pins['scope']['path']).read_bytes())
copies=[];before=[]
need([Path(x['path']).name for x in p['canonical_before']]==['checkpoint.json','path_ownership.json','step_state.json','commands.json'],'canonical order')
for i,pin in enumerate(p['canonical_before']):
 check(pin);b=(ROOT/pin['path']).read_bytes();before.append(b)
 c=HERE/f'canonical-before-{i+1}-{Path(pin["path"]).name}'
 with c.open('xb') as f:f.write(b)
 copies.append(ref(c))
cp,ow=json.loads(before[0]),json.loads(before[1])
need([cp['revision'],ow['revision'],len(cp['failure_counters'])]==[312,140,386],'before state')
new=p['origins'];need(len(new)==2 and len({x['origin_key'] for x in new})==2,'two unique origins')
need(not {x['origin_key'] for x in new}&{x.get('origin_key') for x in cp['failure_counters']},'existing origins')
need(new==json.loads((D/'audit.json').read_bytes())['new_origins']==json.loads((D/'failure-origins.cut.json').read_bytes())['origins'],'cut equality')
need('aa7b24' not in json.dumps(new),'late origin outside fixed cut')
need(new[0]['actual_outer_exit']==1 and new[0]['actual_native_exit'] is None and new[1]['actual_outer_exit']==0 and new[1]['actual_native_exit']==1,'failure exit classifications')
need('W05-99/r312-review-boundary-and-Desktop-development-resource' not in cp['failure_chains'],'new chain not overwrite')
sub=ow['card_path_bindings']['W05-99']['subtasks']
need(sub['session_list_closedcopy_exact1']['current_source_writer']=='codex:/root/command_queue_impl','Cmd lease')
need(ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer']=='codex:/root/sources_parent_impl','Desktop lease')
need('provider_g2_independent_execute29' not in sub,'new execution ownership')
need(Path(sub['session_list_closedcopy_exact1']['worktree']).is_dir(),'Cmd fresh WT exists')
spec=json.loads((ROOT/scope['spec_ref']['path']).read_bytes())
prep=json.loads((ROOT/scope['prepared_ref']['path']).read_bytes())
need(scope['phases']==['execute'] and scope['case_count']==29 and len(spec['roster'])==29,'exact29')
need(scope['finite_future_roster']==[x['selector'] for x in spec['roster']] and len(set(scope['finite_future_roster']))==29,'same unique roster')
need(scope['candidate']==spec['candidate']==prep['source_commit']=='8d0921b7c42ecd40300c58192d54af1064947aed','candidate')
need(scope['output_root']==spec['output_root'] and scope['work_root']==spec['work_root'],'layout')
need(not (Path(scope['output_root'])/'execute').exists(),'execute not started')
need(len(prep['inputs'])==scope['prepared_inputs']==41958,'prepared vector count')
for k in ['spec','runner','exe']:check(prep[k])
need(prep['exe']['sha256']==scope['compiled_exe_ref']['sha256'],'compiled exe match')
need(scope['prepared_ref']['sha256']=='fe01bef395b10c5308d28ce006bc42fca6a7465d6847ddc1711586f449ab60ec','actual prepared hash')
need(sum(x['MODEL_calls'] for x in spec['roster'])==scope['MODEL_loopback_maximum']==4,'finite MODEL loopback sum')
prepaudit=json.loads((ROOT/pins['g2_preparation_audit']['path']).read_bytes())
auditrefs=[]
for k in ['outer_ref','prepared_ref','exe_ref','actual_all_WORK_ref']:auditrefs.append(check(prepaudit[k]))
for k in ['resource_baseline_checks','before_after_build_input_refs']:
 auditrefs.extend(check(x) for x in prepaudit[k])
need(prepaudit['cases_run']==0 and prepaudit['all9_owned_process_native_exits']==0 and prepaudit['all9_full_owned_job_cleanup_confirmed'] is True,'prepared audit limits')
lock=json.loads((ROOT/'execution/toolchains/locked.json').read_bytes())['tools']
for name in ['python','git']:need(digest(Path(lock[name]['path']).read_bytes())==lock[name]['sha256'],'tool '+name)
observations=[]
def git(args,cwd=ROOT):
 r=subprocess.run([lock['git']['path'],*args],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 i=len(observations)+1
 for k,v in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (HERE/f'git-{i:02d}.{k}.raw').open('xb') as f:f.write(v)
 observations.append({'argv':[lock['git']['path'],*args],'cwd':str(cwd),'actual_exit':r.returncode,'stdout_ref':ref(HERE/f'git-{i:02d}.stdout.raw'),'stderr_ref':ref(HERE/f'git-{i:02d}.stderr.raw')})
 need(r.returncode==0,'readonly git failure');return r.stdout
need(git(['rev-parse','HEAD']).decode().strip()==p['head']==cp['head'],'Main HEAD')
status=git(['status','--porcelain=v1','--untracked-files=no'])
need(digest(status)==p['git_status_sha256'] and len(status.splitlines())==13 and sum(x[:2]==b' D' for x in status.splitlines())==11,'Main status')
need(git(['diff','--cached','--name-only'])==b'','index')
g2=ROOT/'.local/worktrees/codex-w0599-provider-g2-finite-r307'
need(git(['rev-parse','HEAD'],g2).decode().strip()=='9a34aacbaeb775566e524f5af3518ea86a5d41b9','G2 HEAD')
need(git(['status','--porcelain=v1'],g2)==b'','G2 clean')
for n,h in [('runtime_coordinator_windows_test.go','a3f6ccfa16a3ea5d3770802eeb376789988bfcbd7b0b9b745e01c2821c4cacd8'),('runtime_provider_binding_windows_test.go','df176f5252e1b7eb6ac6f997052844b3af3f98997f7c2ac232eddb5307eaa8c4')]:need(digest((g2/'internal/domain'/n).read_bytes())==h,'G2 test pin')
for n in ['register.py','run.py','prepared_refs.json','audit.json','scope_registration.json','failure-origins.cut.json']:
 with (HERE/('reviewed-'+n)).open('xb') as f:f.write((D/n).read_bytes())
with (HERE/'reviewed-launch.py').open('xb') as f:f.write(L.read_bytes())
for source in [D/'register.py',D/'run.py',L,ROOT/scope['runner_ref']['path']]:ast.parse(source.read_bytes(),filename=str(source))
checks=[
 'All17 prepared references and9 preparation-audit direct references verified against actual current bytes; prepared41958 entries parsed, no whole41958 current rehash claimed by this registration review.',
 'Actual execute runner will verify every prepared input before case01 and freeze new grant/scope/controller/CP snapshot/Python py+pyc/DLL resources before cases, with before/nativeafter/fixtureafter and unknown-runtime refusal.',
 'Wrapper binds independent review, four draft hashes, four ordered canonical copies to exact current bytes, locked Python/Git, optimize0, HEAD/status before launch.',
 'Registrar original4/desired2/intent/temp persisted before replacements; every replace checks all4 expected bytes and HEAD/status. READS invalidated with new bytes; done/exception and forward-only exact original/desired recovery guards retained.',
 '386→388 imports exactly2 distinct origins; nativeNULL reviewer tool and Desktop outer0/native1 remain distinct. aa7b24 deliberately pending nextCAS. Old386/formal/ST/commands/11D preserved.',
 'Launcher requires actual CP313 desired checkpoint+ownership plus unchanged ST/commands, exact scope pin, preparedfe01 bytes, compiled e01e bytes through runner verification, same29 roster and absent execute output.',
 'Launcher only after CAS creates completed=true execute-only grant with currentCP raw/scope/controller refs; no prepare phase,29 broadening,heldpositive,paid/external,or source acceptance.',
 'Owned Job per native child; first failed/skip/unbound input stops, new output directory refuses replay; actual nullable process exits/raw preserved. Four local MODEL maximum, bootstrapHTTP UNKNOWN remains explicit.',
 'DB claims remain fixture VACUUM snapshots with typed row/schema comparison; no claim to original storage type/implicit rowid bytes. No independent cases/SQL/SDK launched during this review.',
 'Existing Desktop15 and Cmdclosedcopy exact1 leases remain; G2 has no source writer. Main/source/formal HOLD unchanged.'
]
save('audit.json',{'checks':checks,'checked_refs':checked,'preparation_audit_checked_refs':auditrefs,'git_observations':observations,'scope_roster':scope['finite_future_roster'],'prepared_inputs_count':len(prep['inputs']),'new_failure_origins':[],'actual_registration_or_G2_execution':False})
for x,b in zip(p['canonical_before'],[before[0],before[1],before[2],before[3]]):need((ROOT/x['path']).read_bytes()==b,'canonical moved')
for n,h in PINS.items():need(digest((D/n).read_bytes())==h,'draft moved')
review={'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','requested_changes':[],'actual_registration_executed':False,'expected_before':[312,140,386],'expected_after':[313,141,388],'register_sha256':PINS['register.py'],'wrapper_sha256':PINS['run.py'],'prepared_refs_sha256':PINS['prepared_refs.json'],'audit_sha256':PINS['audit.json'],'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copies,'reviewed_at':datetime.now(timezone.utc).isoformat(),'launcher_ref':ref(L),'launcher_statically_reviewed_not_executed':True,'scope_ref':ref(D/'scope_registration.json'),'independent_audit_ref':ref(HERE/'audit.json'),'future_execution_bound':'Root actualCAS then exact29 once; no auto retry; first unexpected stops; no paid/external/heldpositive/source/formal acceptance.','late_origin_aa7b24':'EXCLUDED_FROM_FIXED_CUT_PENDING_NEXT_REGISTRATION','source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'new_failure_origins':[]}
save('review.json',review)
files=[ref(x) for x in sorted(HERE.rglob('*')) if x.is_file()]
save('manifest.json',{'entries':files,'count':len(files)})
save('handoff.json',{'review_ref':ref(HERE/'review.json'),'manifest_ref':ref(HERE/'manifest.json'),'audit_ref':ref(HERE/'audit.json'),'actual_registration_executed':False,'G2_started':False,'new_failure_origins':[]})
print(json.dumps({n:ref(HERE/n) for n in ['review.json','manifest.json','handoff.json']},ensure_ascii=False,indent=2))
