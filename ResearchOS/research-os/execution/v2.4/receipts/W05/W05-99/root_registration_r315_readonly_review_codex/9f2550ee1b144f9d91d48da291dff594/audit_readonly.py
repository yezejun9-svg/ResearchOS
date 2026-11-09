from pathlib import Path
import ast, datetime, hashlib, json, subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
N = ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-harness-v3-r315'
SEEN = {}
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p):
    p = Path(p)
    if not p.is_absolute(): p = ROOT/p
    b = p.read_bytes()
    SEEN[p] = b
    return b
def ref(p):
    p = Path(p)
    if not p.is_absolute(): p = ROOT/p
    b = p.read_bytes()
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256':sha(b), 'bytes':len(b)}
def verify(r, base=ROOT):
    p = Path(r['path'])
    if not p.is_absolute(): p=base/p
    b=read(p)
    assert sha(b)==r['sha256'], str(p)
    if 'bytes' in r: assert len(b)==r['bytes'], str(p)
    return b
def write(name, data):
    b = data if isinstance(data,bytes) else (json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with (OUT/name).open('xb') as f: f.write(b)
    return ref(OUT/name)

expected={'register.py':'cf14a8e361dfcde4ae4edc13a4b238d932352ea9674ae30e222c0e6c31ae898a','run.py':'f58b3d9ace6e414fba2d2a0e997584297718bea48c7245a0583b2272a17e6fe3','prepared_refs.json':'aa9e282e22c963530ffb9059d8f6220c66266f39837c0d66872981db52574285','audit.json':'f0f2db08bd70b75b720be38a5a8da128f93dd4e1d14b52df3630147c67ba5809','scope_registration.json':'76489322820c0d8777048ce513acda5413e717b614bd004c500c73e0a8bfe403'}
for name,h in expected.items():
    b=verify({'path':str(N/name),'sha256':h})
    write('input-'+name,b)
    if name.endswith('.py'): ast.parse(b)
p=json.loads(read(N/'prepared_refs.json'))
for r in p['verified_refs']: verify(r)
assert len(p['verified_refs'])==25
canon=[json.loads(verify(r)) for r in p['canonical_before']]
cp,ow=canon[:2]
assert [cp['revision'],ow['revision'],len(cp['failure_counters'])]==[314,142,390]
copied=[write('canonical-before-'+str(i+1)+'-'+Path(r['path']).name,verify(r)) for i,r in enumerate(p['canonical_before'])]
origins=p['origins']; keys=[x['origin_key'] for x in origins]
assert len(keys)==len(set(keys))==3
assert not set(keys)&{x.get('origin_key') for x in cp['failure_counters']}
assert 'W05-99/r314-prefix-boundary-and-Desktop-finite-executor' not in cp['failure_chains']
for o in origins: assert json.loads(verify(o['evidence_ref']))==o['original_payload']
assert origins[0]['actual_outer_exit']==origins[0]['actual_native_exit']==1
assert origins[0]['product_cases_run']==0 and origins[0]['original_payload']['Go_compiles']==0
assert len(origins[0]['original_payload']['NOT_RUN'])==14
for row in origins[0]['original_payload']['subprocesses']:
    native=json.loads(verify(row['ref']))
    assert row['actual_exit']==0
    write('cmd-'+row['name']+'-invocation.json',verify(row['ref']))
desktop=ROOT/'.local/worktrees/codex-w1303-desktop-http-r311'
desktop_facts=[]
for idx,o in enumerate(origins[1:]):
    assert o['actual_outer_exit']==0 and o['actual_native_exit']==1
    selected={}
    for r in o['original_payload']['refs']:
        b=verify(r,desktop); name=Path(r['path']).name
        if name in ('stdout','stderr','invocation.json','result.json'):
            write('desktop-'+str(idx)+'-'+name,b)
            selected[name]=b
    inv=json.loads(selected['invocation.json']); result=json.loads(selected['result.json'])
    assert inv['exit']==1 and inv['stdout_sha256']==sha(selected['stdout']) and inv['stderr_sha256']==sha(selected['stderr'])
    assert result['drift']==[] and result['source_acceptance'] is False
    assert result['pass']==(0 if idx==0 else 9)
    assert sum(x['exit']==0 for x in result['rows'])==(0 if idx==0 else 9)
    assert sum(x['exit']!=0 for x in result['rows'])==1
    assert [inv['http_count'],inv['child_count']]==([0,0] if idx==0 else [1,2])
    assert (b'ERR_UNSUPPORTED_ESM_URL_SCHEME' if idx==0 else b'Do not know how to serialize a BigInt') in selected['stdout']
    desktop_facts.append({'origin':o['origin_key'],'outer_exit':0,'native_exit':1,'historical_pass':result['pass'],'product_failed_leaf':idx,'http_count':inv['http_count'],'child_count':inv['child_count'],'numeric_behavior_certified':False})
scope=json.loads(read(N/'scope_registration.json'))
assert scope['source_exact_paths']==['internal/api/v2_sessions_test.go']
assert [scope['cases'],scope['per_case_HTTP_maximum'],scope['total_HTTP_maximum']]==[14,16,224]
assert scope['first_unexpected_stop'] and not scope['automatic_same_input_retry'] and scope['previous_same_chain_actual_failures']==2
assert scope['SDK_MODEL_Node_external_paid_private_calls']==0 and not scope['source_acceptance']
assert not (ROOT/p['pins']['v3_driver']['path']).with_name('started.json').exists()
assert json.loads(verify(p['pins']['harness_review']))['decision']=='TARGETED_HARNESS_REVISION_REVIEWED_FOR_ONCE_ONLY_NEW_INPUT_EXECUTION'
lock=json.loads(read(ROOT/'execution/toolchains/locked.json'))['tools']
for key in ('python','git'): verify(lock[key])
git=lock['git']['path']; git_results=[]
g2=ROOT/'.local/worktrees/codex-w0599-provider-g2-finite-r307'
for label,cwd,args in [('main-head',ROOT,['rev-parse','HEAD']),('main-status',ROOT,['status','--porcelain=v1','--untracked-files=no']),('main-index',ROOT,['diff','--cached','--name-only']),('g2-head',g2,['rev-parse','HEAD']),('g2-status',g2,['status','--porcelain=v1'])]:
    argv=[git,*args]; result=subprocess.run(argv,cwd=cwd,capture_output=True)
    sr=write(label+'.stdout.raw',result.stdout); er=write(label+'.stderr.raw',result.stderr)
    git_results.append({'argv':argv,'cwd':str(cwd),'actual_exit':result.returncode,'stdout_ref':sr,'stderr_ref':er})
    assert result.returncode==0
    if label=='main-head': assert result.stdout.decode().strip()==p['head']
    if label=='main-status': assert sha(result.stdout)==p['git_status_sha256'] and len(result.stdout.splitlines())==13 and sum(x[:2]==b' D' for x in result.stdout.splitlines())==11
    if label in ('main-index','g2-status'): assert result.stdout==b''
    if label=='g2-head': assert result.stdout.decode().strip()=='9a34aacbaeb775566e524f5af3518ea86a5d41b9'
for name,h in [('runtime_coordinator_windows_test.go','a3f6ccfa16a3ea5d3770802eeb376789988bfcbd7b0b9b745e01c2821c4cacd8'),('runtime_provider_binding_windows_test.go','df176f5252e1b7eb6ac6f997052844b3af3f98997f7c2ac232eddb5307eaa8c4')]: verify({'path':str(g2/'internal/domain'/name),'sha256':h})
assert all(path.read_bytes()==b for path,b in SEEN.items())
audit=write('audit.json',{'actual_registration_executed':False,'verified_prepared_ref_count':25,'actual_read_refs':[ref(path) for path in SEEN],'all_read_inputs_unchanged':True,'readonly_git_invocations':git_results,'origins':keys,'desktop_actual_facts':desktop_facts,'static_findings':['Four ordered canonical byte pins at wrapper launch and each replace; HEAD/status rechecked; unchanged ST/CM and old390 prefix.','Original and desired bytes, intent, temporary files, per-write done and terminal verification; no automatic rollback/retry.','READS cache updated after each canonical replacement before handoff refs.','Exact1 source lease and Desktop15 ownership unchanged; G2 immutable313 grant untouched.','Desktop BigInt diagnostic failure retained as one real failed leaf; original wording correctly returned is an unverified author inference, not accepted numeric proof.'],'known_limitations':['Existing wrapper subprocess-launch exception can precede invocation.json; actual Root outer/raw must retain such failure if it occurs.','Same-user path TOCTOU remains documented by harness scope.','No product/test/SQL/helper execution or source acceptance.'],'new_failure_origins':[]})
review=write('review.json',{'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','requested_changes':[],'actual_registration_executed':False,'expected_before':[314,142,390],'expected_after':[315,143,393],'register_sha256':expected['register.py'],'wrapper_sha256':expected['run.py'],'prepared_refs_sha256':expected['prepared_refs.json'],'audit_sha256':expected['audit.json'],'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copied,'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope_ref':ref(N/'scope_registration.json'),'independent_audit_ref':audit,'conditions':['Root alone executes pinned wrapper while all four canonical originals and HEAD/status remain unchanged.','Only actual CAS315 and precise Root followup permit one new-input v3 run; all previous stops retained.','Desktop last diagnostic is a failed leaf, not proof of correct numeric behavior.'],'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'new_failure_origins':[]})
manifest=write('manifest.json',{'schema':'researchos.independent-review-manifest.v1','entries':[ref(x) for x in sorted(OUT.iterdir()) if x.is_file()]})
handoff=write('handoff.json',{'decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','review_ref':review,'manifest_ref':manifest,'actual_registration_executed':False,'new_failure_origins':[],'formal_increment':0})
print(json.dumps({'review':review,'manifest':manifest,'handoff':handoff},ensure_ascii=True))
