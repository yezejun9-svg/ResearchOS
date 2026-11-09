import ast,hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
R=Path('D:/作品集/ResearchOS/research-os');H=Path(__file__).resolve().parent
D=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-harness-v2-r314'
PINS={'register.py':'912126a7b0c7958f2d2820c97dcbab6cd4223187b0cb04e87723fc4c469a8e77','run.py':'813c014ea7cd5d0e4a4645f86fbd490b55f339b6721257471d19c057854f8cae','prepared_refs.json':'f23d56b10702f83b68b519c0f38d93d5114dac533d9857f9c3c3a0a39c43f4c3','audit.json':'a9513ad3f04b2fe1a2be6049f257db312c214d4abdec120ad3b9be7ca3229093','scope_registration.json':'ceabb196e8e6f35dfaa187a0403149f7220497d5d021054c18bcca694c66cf27'}
def need(x,m):
 if not x:raise RuntimeError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(f):
 b=f.read_bytes();return {'path':f.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def save(n,v):
 with (H/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
for n,h in PINS.items():need(sha((D/n).read_bytes())==h,'draft '+n)
p=json.loads((D/'prepared_refs.json').read_bytes());checked=[]
for x in p['verified_refs']:
 a=ref(R/x['path']);need(a==x,'ref '+x['path']);checked.append(a)
copies=[];before=[]
need([Path(x['path']).name for x in p['canonical_before']]==['checkpoint.json','path_ownership.json','step_state.json','commands.json'],'ordered canonical')
for i,x in enumerate(p['canonical_before']):
 f=R/x['path'];need(ref(f)==x,'canonical');b=f.read_bytes();before.append(b)
 c=H/f'canonical-before-{i+1}-{f.name}'
 with c.open('xb') as out:out.write(b)
 copies.append(ref(c))
cp,ow=json.loads(before[0]),json.loads(before[1]);need([cp['revision'],ow['revision'],len(cp['failure_counters'])]==[313,141,388],'revisions')
origins=p['origins'];need(len(origins)==2 and len({x['origin_key'] for x in origins})==2,'unique2')
need(not {x['origin_key'] for x in origins}&{x.get('origin_key') for x in cp['failure_counters']},'old prefix origins')
need(origins==json.loads((D/'audit.json').read_bytes())['new_origins']==json.loads((D/'failure-origins.cut.json').read_bytes())['origins'],'cut exact')
need(origins[0]['actual_outer_exit']==1 and origins[0]['actual_native_exit']==1 and origins[0]['native_kind']=='OWNED_PYTHON_DRIVER' and origins[0]['actual_product_exit'] is None and origins[0]['product_cases_run']==0,'Cmd exit classification')
need(origins[1]['actual_outer_exit']==1 and origins[1]['actual_native_exit'] is None and origins[1]['product_cases_run']==0,'Desktop locator classification')
need('W05-99/r312-directory-precondition-and-Desktop-readonly-locator' not in cp['failure_chains'],'new chain')
s=json.loads((D/'scope_registration.json').read_bytes());pins=p['pins']
need(s['registration_checkpoint']==314 and s['cases']==14 and s['source_exact_paths']==['internal/api/v2_sessions_test.go'],'scope')
need(s['original_source_lease_ref']==pins['original_source_scope'] and s['harness_review_ref']==pins['harness_review'],'scope review bound')
need(s['driver_ref']==pins['v2_driver'] and s['launcher_ref']==pins['v2_launcher'] and s['source_current_ref']==pins['cmd_source_before_new_execution'],'current scope refs')
need(not (R/pins['v2_driver']['path']).with_name('started.json').exists(),'v2 not started')
need(s['per_case_HTTP_maximum']==16 and s['total_HTTP_maximum']==224 and s['previous_same_chain_actual_failures']==1 and s['first_unexpected_stop'] and not s['counter_reset'],'caps/history')
sub=ow['card_path_bindings']['W05-99']['subtasks'];need(sub['session_list_closedcopy_exact1']['current_source_writer']=='codex:/root/command_queue_impl','Cmd writer')
need(ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer']=='codex:/root/sources_parent_impl','Desktop writer')
review=json.loads((R/pins['harness_review']['path']).read_bytes());need(review['decision']=='TARGETED_HARNESS_REVISION_REVIEWED_FOR_ONCE_ONLY_NEW_INPUT_EXECUTION' and review['requested_changes']==[],'prior review')
lock=json.loads((R/'execution/toolchains/locked.json').read_bytes())['tools']
for k in ['python','git']:need(sha(Path(lock[k]['path']).read_bytes())==lock[k]['sha256'],'locked tool '+k)
observed=[]
def git(args,cwd=R):
 r=subprocess.run([lock['git']['path'],*args],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE);n=len(observed)+1
 for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (H/f'git-{n:02d}.{k}.raw').open('xb') as f:f.write(b)
 observed.append({'argv':[lock['git']['path'],*args],'cwd':str(cwd),'actual_exit':r.returncode,'stdout_ref':ref(H/f'git-{n:02d}.stdout.raw'),'stderr_ref':ref(H/f'git-{n:02d}.stderr.raw')});need(r.returncode==0,'readonly Git');return r.stdout
need(git(['rev-parse','HEAD']).decode().strip()==p['head']==cp['head'],'Main HEAD')
status=git(['status','--porcelain=v1','--untracked-files=no']);need(sha(status)==p['git_status_sha256'] and len(status.splitlines())==13 and sum(x[:2]==b' D' for x in status.splitlines())==11,'status')
need(git(['diff','--cached','--name-only'])==b'','index')
g2=R/'.local/worktrees/codex-w0599-provider-g2-finite-r307';need(git(['rev-parse','HEAD'],g2).decode().strip()=='9a34aacbaeb775566e524f5af3518ea86a5d41b9','G2HEAD');need(git(['status','--porcelain=v1'],g2)==b'','G2 status')
for n,h in [('runtime_coordinator_windows_test.go','a3f6ccfa16a3ea5d3770802eeb376789988bfcbd7b0b9b745e01c2821c4cacd8'),('runtime_provider_binding_windows_test.go','df176f5252e1b7eb6ac6f997052844b3af3f98997f7c2ac232eddb5307eaa8c4')]:need(sha((g2/'internal/domain'/n).read_bytes())==h,'G2 protected source')
for n in ['register.py','run.py','prepared_refs.json','audit.json','scope_registration.json','failure-origins.cut.json']:
 with (H/('reviewed-'+n)).open('xb') as f:f.write((D/n).read_bytes())
for n in ['register.py','run.py']:ast.parse((D/n).read_bytes())
checks=[
 'Draft5 hashes/all prepared refs and ordered4 current canonical bytes verified; old388 prefix and exact two unique origins, zero product test executions retained.',
 'Cmd aa7b24 native1 is owned Python driver, not Go/test; Desktop ad9051 nativeNULL/outer1 is locator. No double counting or historical reset.',
 'Existing exact1 source lease remains unchanged; v2 hash-bound narrow review and current54abc44/domain7fb40 pins match. No new source path or writer; original15+1 preserved.',
 'Wrapper checks independent review/four draft hashes/ordered copied4pins/live4pins/locked tools/HEAD/status before isolated optimize0 Root launch.',
 'Registrar snapshots original4 and desired2 before intent/temp; each replace checks all4 expected bytes+HEAD/status. expected_live and READS update prevents stale handoff.',
 'Postcondition checks314/142/390, old388 prefix, ST/commands/formal/HEAD/status. Exception records exact phase/current SHA; recovery only forward against exact own original/desired, no automatic retry.',
 'G2 r313 grant/CP snapshot/input41958/source/runtime output are not changed by these mutation statements; this review neither polls nor starts G2.',
 'Actual CAS314 then Root exact followup is required before once-only v2 launch. Exact14/max224HTTP/firststop and noSDK/model/Node/external limits retained; source/Main/formal acceptance remain false.'
]
save('audit.json',{'checked_refs':checked,'git_observations':observed,'checks':checks,'all_resource_rehash_or_product_test':False,'actual_registration_executed':False,'new_failure_origins':[]})
for x,b in zip(p['canonical_before'],before):need((R/x['path']).read_bytes()==b,'final canonical stable')
for n,h in PINS.items():need(sha((D/n).read_bytes())==h,'final draft stable')
save('review.json',{'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','requested_changes':[],'actual_registration_executed':False,'expected_before':[313,141,388],'expected_after':[314,142,390],'register_sha256':PINS['register.py'],'wrapper_sha256':PINS['run.py'],'prepared_refs_sha256':PINS['prepared_refs.json'],'audit_sha256':PINS['audit.json'],'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copies,'reviewed_at':datetime.now(timezone.utc).isoformat(),'scope_ref':ref(D/'scope_registration.json'),'independent_audit_ref':ref(H/'audit.json'),'conditions':['Root alone executes pinned reviewed wrapper against unchanged fourcanonical/HEAD/status.','After actualCAS314, Root precise followup authorizes one new-input v2 launch; no pre-CAS execution or old-output retry.'],'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'new_failure_origins':[]})
files=[ref(f) for f in sorted(H.rglob('*')) if f.is_file()];save('manifest.json',{'entries':files,'count':len(files)})
save('handoff.json',{'review_ref':ref(H/'review.json'),'manifest_ref':ref(H/'manifest.json'),'audit_ref':ref(H/'audit.json'),'actual_registration_executed':False,'v2_started':False,'new_failure_origins':[]})
print(json.dumps({n:ref(H/n) for n in ['review.json','manifest.json','handoff.json']},ensure_ascii=False,indent=2))
