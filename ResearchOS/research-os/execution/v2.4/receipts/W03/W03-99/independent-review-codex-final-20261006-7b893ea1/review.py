"""Independent current-evidence audit; no product command or gate execution."""
from pathlib import Path
import collections, contextlib, copy, datetime, hashlib, importlib.util, io, json, os, subprocess, sys, types
from unittest.mock import patch

OUT = Path(__file__).resolve().parent
B = OUT.parent
R = B.parents[4]
E = B / 'executor_codex'
FROZEN_HEAD = 'b469cd9ca316248b0bfc82f2c6a6ae9d23ab71e6'
ATOM_HEAD = '9bb09128b94101b6fc9d8581a782c25d0bf59aca'
checks, synthetic, inputs, atoms = [], [], {}, {}

def digest(raw): return hashlib.sha256(raw).hexdigest()
def sha(path): return digest(Path(path).read_bytes())
def read(path): return json.loads(Path(path).read_text(encoding='utf8'))
def save(name, data):
    p = OUT / name
    assert not p.exists(), str(p)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf8')
    return name
def check(name, condition, detail=None):
    checks.append({'id': name, 'passed': bool(condition), 'detail': detail})
    if not condition:
        save('audit_failure.json', checks)
        raise AssertionError(name)
def pin(path):
    path = Path(path)
    inputs[str(path)] = sha(path)
    return read(path)
def git(*args): return subprocess.check_output(['git', *args], cwd=R)
def loadmod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
def forbidden(*a, **kw): raise AssertionError('Product execution is prohibited in independent review')

check('FROZEN_MAIN_HEAD', git('rev-parse','HEAD').decode().strip() == FROZEN_HEAD)
g = loadmod('gate_driver', E/'gate_driver.py')
sys.modules['gate_driver'] = g
bridge = loadmod('independent_final_bridge', E/'bridge.py')
g.run_gate = g.execute_atom = forbidden
plan = pin(E/'expected.json')
dispatch = pin(B/'integration_codex/exact_parent_dispatch_results.json')
binding = pin(B/'integration_codex/parent_command_binding_codex.json')
baseline = pin(B/'integration_codex/binding_baseline_codex.json')
handoff = pin(E/'handoff.json')
prior = pin(B/'independent_source_review_codex_062cce3b.json')
oldfindings = pin(B/'independent_driver_findings_codex.json')
registry = pin(R/'execution/v2.4/commands.json')
legacy = pin(R/'execution/commands.json')
locked = pin(R/'execution/toolchains/locked.json')
check('REGISTERED_REVISION', registry['revision'] == 37 and sha(R/'execution/v2.4/commands.json') == dispatch['registry_sha256'] == binding['registry_sha256'])
check('PATH_AND_CHECKPOINT', read(R/'execution/v2.4/path_ownership.json')['revision'] == 47 and read(R/'execution/v2.4/checkpoint.json')['revision'] == 211)
before, after = baseline['v24_decoded_commands'], registry['commands']
check('ONLY_TWO_REGISTERED_ENTRIES_CHANGED', set(before) == set(after) and {k for k in before if before[k] != after[k]} == {'contracts.validate','test.domain'} and len(before)-2 == 29)
check('LEGACY_REGISTRY_UNCHANGED', sha(R/'execution/commands.json') == baseline['legacy_registry_sha256'] == plan['legacy_registry_sha256'])
check('LEGACY_EXPECTATIONS_EXACT', all(plan['legacy_entries'][k] == legacy['commands'][k] for k in plan['legacy_entries']))
check('ROOT_BINDING_PROTECTED_INPUTS', all(sha(R/f) == h for f,h in binding['protected_source_hashes_unchanged'].items()))
changed_reviewed = [f for f,h in prior['source_hashes'].items() if sha(R/f) != h]
check('ONLY_REVIEWED_TEST_FIXTURE_CHANGED', changed_reviewed == ['internal/domain/w03_current_binding_test.go'], changed_reviewed)
delta = git('diff','062cce3b',ATOM_HEAD,'--','internal/domain/w03_current_binding_test.go').decode()
(OUT/'reviewed_fixture_role_delta.patch').write_text(delta,encoding='utf8')
check('FIXTURE_CALLER_REPAIR_EXACT', 'f.switchPrincipal(executor, []string{"EXECUTOR"})' in delta and '+\texecutor := "w03-evaluation-fixture"' in delta and '"produced_by": executor' in delta and delta.count('\n@@') == 2)
source_args = [*g.SOURCE_PREFIXES,*sorted(g.SOURCE_FILES)]
check('ATOM_COMMIT_CURRENT_SOURCE_EQUAL', not git('diff','--name-only',ATOM_HEAD,FROZEN_HEAD,'--',*source_args).strip())
check('NO_DIRTY_CURRENT_SOURCE', not git('diff','--name-only','HEAD','--',*source_args).strip())
check('CURRENT_DRIVERS_MATCH_ATOM_COMMIT', not git('diff','--name-only',ATOM_HEAD,FROZEN_HEAD,'--',*(str((E/n).relative_to(R)).replace('\\','/') for n in ['gate_driver.py','bridge.py','expected.json','probe/main.go'])).strip())
oldplan = json.loads(git('show','cefc5970:'+str((E/'expected.json').relative_to(R)).replace('\\','/')))
check('ORIGINAL_22_TESTS_RETAINED', sum(map(len,oldplan['tests'].values()))==22 and all(set(v).issubset(plan['tests'][k]) for k,v in oldplan['tests'].items()))
check('CURRENT_29_TESTS_EXACT', {k:len(v) for k,v in plan['tests'].items()} == {'W03-G01':14,'W03-G02':10,'W03-G03':5})
check('ORIGINAL_PROBES_RETAINED', all(set(v).issubset(plan['probe_ids'][k]) for k,v in oldplan['probe_ids'].items()))
for name in ['gate_driver.py','bridge.py','expected.json']:
    (OUT/('snapshot_'+name)).write_bytes((E/name).read_bytes())

for row in dispatch['actual_registered_selectors']:
    gate, mode = row['gate'], row['mode']
    mirror = R/row['mirror_path']
    rec = pin(mirror/'receipt.json')
    original = R/'execution/invocations'/rec['invocation_id']
    check(gate+'_EXACT_REGISTERED_RECEIPT', row['exit_code']==0 and rec['exit_code']==0 and rec['child_exit_code']==0 and rec['status']=='PASS' and rec['assertion_ids']==[gate] and rec['selectors']=={'task_id':'W03','check_id':gate,'case_id':''} and rec['code_revision']==FROZEN_HEAD and rec['registered_command_revision']==sha(R/'execution/v2.4/commands.json') and rec['scope']=='CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE' and rec['registry_spec']=='v2.4')
    check(gate+'_REGISTERED_ARGV_CWD_TOOL', rec['argv']==[locked['tools']['python']['path'],*after[row['command_key']]['argv']] and Path(rec['cwd']).resolve()==R.resolve() and rec['dispatcher_sha256']==sha(R/'execution/command_dispatcher/dispatch.py') and rec['toolchain_revision']==sha(R/'execution/toolchains/locked.json'))
    check(gate+'_MIRROR_RECEIPT_HASH', sha(mirror/'receipt.json')==row['dispatcher_receipt_sha256'] and all((mirror/n).read_bytes()==(original/n).read_bytes() for n in ['receipt.json','stdout.txt','stderr.txt']))
    for stream in ['stdout','stderr']:
        check(gate+'_'+stream.upper()+'_HASH', sha(mirror/(stream+'.txt'))==rec[stream]['sha256']==sha(R/rec[stream]['path']))
    packet = pin(mirror/'stdout.txt')
    check(gate+'_PARENT_SINGLETON_AND_BOUNDARY', packet['status']=='PASS' and packet['assertion_ids']==[gate] and packet['expected_assertion_ids']==[gate] and packet['assertions']==1 and packet['mode']==mode==g.GATES[gate] and packet['formal_product_acceptance']=='NOT_RUN' and packet['owned_acceptance_ids']==[] and packet['associated_cases']=={'A03':'NOT_RUN','C04':'NOT_RUN','C19':'NOT_RUN'})
    index = pin(R/row['index_path'])
    check(gate+'_CURRENT_INDEX_HASH', sha(R/row['index_path'])==row['index_sha256']==packet['evidence_index_sha256'])
    check(gate+'_ATOM_KIND_SET', set(index['atoms'])==({'go'} if gate=='W03-G02' else {'go','probe'}))
    for kind, ref in index['atoms'].items():
        d=E/ref['path']; manifest=pin(d/'manifest.json'); receipt=pin(d/'receipt.json'); raw=(d/'stdout.txt').read_text(encoding='utf8')
        check(gate+'_'+kind+'_REFERENCE_HASHES', sha(d/'manifest.json')==ref['manifest_sha256']==row['atoms'][kind]['manifest_sha256'] and sha(d/'receipt.json')==ref['receipt_sha256']==row['atoms'][kind]['receipt_sha256'])
        check(gate+'_'+kind+'_ACTUAL_PROVENANCE', receipt['source_head']==ATOM_HEAD and Path(receipt['cwd']).resolve()==(R/'.local/worktrees/codex-w0199').resolve() and receipt['started_at'] < receipt['ended_at'] < rec['started_at'] and receipt['invocation']==g.invocation(kind,gate,plan) and type(receipt['exit_code']) is int and receipt['exit_code']==0)
        check(gate+'_'+kind+'_RAW_HASHES', sha(d/'stdout.txt')==receipt['stdout_sha256'] and sha(d/'stderr.txt')==receipt['stderr_sha256'])
        parsed=g.verify_atom(ref,kind,gate,plan)
        check(gate+'_'+kind+'_CURRENT_MANIFEST_AND_PARSE', parsed==receipt['parsed']==packet['atomic_results'][kind]==row['atoms'][kind]['parsed'], {'source_hash_count':len(manifest['source_hashes']),'input_digest':receipt['input_digest']})
        atoms[(gate,kind)]={'directory':d,'manifest':manifest,'receipt':receipt,'raw':raw,'ref':ref}
        if kind=='go':
            events=[json.loads(line) for line in raw.splitlines() if line.strip()]
            expected=collections.Counter((plan['test_packages'][gate][t],t) for t in plan['tests'][gate])
            actual=lambda action:collections.Counter((e.get('Package'),e['Test']) for e in events if e.get('Action')==action and 'Test' in e and '/' not in e['Test'])
            check(gate+'_INDEPENDENT_GO_EVENT_IDENTITY', actual('run')==actual('pass')==expected and not any(e.get('Action') in ['fail','skip'] for e in events))
        else:
            report=json.loads(raw)
            check(gate+'_INDEPENDENT_PROBE_IDS', collections.Counter(c['id'] for c in report['checks'])==collections.Counter(plan['probe_ids'][gate]) and all(c['passed'] is True for c in report['checks']))
            if gate=='W03-G01':
                corpus=pin(R/'tests/contracts/fixtures/client_protocol_v2_fixtures.json')['fixtures']
                expected={'FIXTURE/'+v['name']:v for v in corpus}; actual={v['id']:v for v in report['checks'] if v['group']=='fixtures'}
                check('EXACT_106_FIXTURE_DECISIONS', set(expected)==set(actual) and len(actual)==106 and sum(v['expected_valid'] for v in corpus)==76 and all(actual[k]['detail']['expected_valid'] is v['expected_valid'] and actual[k]['detail']['actual_valid'] is v['expected_valid'] and actual[k]['detail']['schema_definition']==v['schema_definition'] for k,v in expected.items()))

worker=pin(E/'python-runs/driver-3b2088153b934788a8bd5f7e6f4c2428/receipt.json')
check('WORKER_30_SYNTHETIC_SEPARATE', worker['exit_code']==0 and worker['scope']=='SYNTHETIC_DRIVER_REGRESSION_NOT_PRODUCT_ATOM' and all(sha(E/n)==v for n,v in worker['source_hashes'].items()) and all(sha(E/'python-runs/driver-3b2088153b934788a8bd5f7e6f4c2428'/(n+'.txt'))==worker[n+'_sha256'] for n in ['stdout','stderr']) and 'Ran 30 tests' in (E/'python-runs/driver-3b2088153b934788a8bd5f7e6f4c2428/stderr.txt').read_text())
check('FAILED_G02_PRESERVED', sha(E/'runs/W03-G02-go-539e02fb3dc4424190511d40d561ee72/receipt.json')=='f36a3a6fefd48d9c6ae49a70cb4c295542f0f727df55e574a7678708bf173b8a' and read(E/'runs/W03-G02-go-539e02fb3dc4424190511d40d561ee72/receipt.json')['status']=='FAIL')
check('CURRENT_G02_REACHED_GUARD', '"Action":"pass","Package":"researchos.local/research-os/internal/domain","Test":"TestW03CurrentEvaluationArtifactGuard"' in atoms[('W03-G02','go')]['raw'])

def parsecase(name, kind, raw, code=0, reject=False, gate='W03-G01'):
    filename=name+'.synthetic.txt';(OUT/filename).write_text(raw,encoding='utf8')
    error=None
    try: g.parse_atom(kind,gate,raw,atoms[(gate,kind)]['manifest'],code)
    except g.EvidenceError as e: error=str(e)
    ok=(error is not None)==reject
    synthetic.append({'id':name,'scope':'SYNTHETIC_PARSER_ONLY','baseline_actual_atom':str(atoms[(gate,kind)]['directory'].relative_to(R)), 'payload':filename,'exit_code':code,'expected_rejection':reject,'rejection':error,'passed':ok})
    check(name,ok,error)

go=atoms[('W03-G01','go')]['raw']; probe=atoms[('W03-G01','probe')]['raw']
parsecase('full_current_go_positive', 'go', go)
parsecase('full_current_probe_positive', 'probe', probe)
x=json.loads(probe); fs=[c for c in x['checks'] if c['group']=='fixtures'];fs[0]['detail']['actual_valid']=not fs[0]['detail']['actual_valid']
parsecase('fixture_actual_contradiction','probe',json.dumps(x),reject=True)
x=json.loads(probe);fs=[c for c in x['checks'] if c['group']=='fixtures'];pos=next(c for c in fs if c['detail']['expected_valid']);neg=next(c for c in fs if not c['detail']['expected_valid']);pos['detail'],neg['detail']=neg['detail'],pos['detail']
parsecase('fixture_swapped_labels_same_76_30','probe',json.dumps(x),reject=True)
events=[json.loads(s) for s in go.splitlines() if s.strip()];target=plan['tests']['W03-G01'][0]
for event in events:
    if event.get('Test')==target and event.get('Action') in ('run','pass'):event['Package']='researchos.local/research-os/UNREGISTERED'
parsecase('go_wrong_package_same_test','go','\n'.join(json.dumps(e) for e in events),reject=True)
events=[json.loads(s) for s in go.splitlines() if s.strip()];events[0]['Elapsed']=float('nan')
parsecase('go_nonfinite_nan','go','\n'.join(json.dumps(e) for e in events),reject=True)
x=json.loads(probe);x['elapsed']=float('inf')
parsecase('probe_nonfinite_infinity','probe',json.dumps(x),reject=True)
parsecase('go_boolean_exit','go',go,code=False,reject=True)
parsecase('probe_boolean_exit','probe',probe,code=False,reject=True)
parsecase('go_nonzero_exit','go',go,code=7,reject=True)
x=json.loads(probe);x['checks'][0]['passed']=False
parsecase('probe_reported_false','probe',json.dumps(x),reject=True)

# verify_atom receives only virtual in-memory files for tampering cases.
class MemoryPath:
    def __init__(self, name=''):self.name=name
    def __truediv__(self, name):return MemoryPath(name)
    def read_text(self, **kw):return mem[self.name].decode('utf8')
    def __str__(self):return 'SYNTHETIC_MEMORY/'+self.name
baseline_atom=atoms[('W03-G01','go')]
def verifycase(name, mutate=None, reject=True):
    global mem
    m=copy.deepcopy(baseline_atom['manifest']);r=copy.deepcopy(baseline_atom['receipt']);raw=go
    extra={}
    if mutate:raw=mutate(m,r,raw,extra)
    def encoded(x):return (json.dumps(x,ensure_ascii=False)+'\n').encode()
    mem={'manifest.json':encoded(m),'stdout.txt':raw.encode(),'stderr.txt':b''}
    if not extra.get('preserve_raw_hash'):r['stdout_sha256']=digest(mem['stdout.txt'])
    r['input_digest']=g.digest(m)
    mem['receipt.json']=encoded(r)
    ref={'path':'runs/SYNTHETIC_MEMORY','receipt_sha256':digest(mem['receipt.json']),'manifest_sha256':digest(mem['manifest.json'])}
    if extra.get('tamper_ref'):ref['receipt_sha256']='0'*64
    error=None
    with patch.object(g,'checked_directory',return_value=MemoryPath()),patch.object(g,'sha',side_effect=lambda p:digest(mem[p.name])),patch.object(g,'read',side_effect=lambda p:g.loads(mem[p.name].decode())),patch.object(g,'input_manifest',return_value=baseline_atom['manifest']),patch.object(g,'invocation',return_value=baseline_atom['receipt']['invocation']):
        try:g.verify_atom(ref,'go','W03-G01',plan)
        except g.EvidenceError as e:error=str(e)
    save(name+'.synthetic.json',{'scope':'SYNTHETIC_MEMORY_ONLY_NOT_ATOM','ref':ref,'manifest':m,'receipt':r,'stdout':raw,'expected_rejection':reject,'rejection':error})
    synthetic.append({'id':name,'scope':'SYNTHETIC_IMMUTABLE_REUSE','expected_rejection':reject,'rejection':error,'passed':(error is not None)==reject})
    check(name,(error is not None)==reject,error)
def change(container,key,value):
    def mutate(m,r,raw,extra): (m if container=='manifest' else r if container=='receipt' else extra)[key]=value;return raw
    return mutate
verifycase('reuse_full_current_positive',reject=False)
verifycase('reuse_stale_rehashed_manifest',change('manifest','source_hashes',{'synthetic_changed_source':'changed'}))
verifycase('reuse_wrong_mode',change('receipt','mode','LIVE'))
verifycase('reuse_failed_status',change('receipt','status','FAIL'))
verifycase('reuse_boolean_exit',change('receipt','exit_code',False))
verifycase('reuse_wrong_invocation',change('receipt','invocation',['UNREGISTERED']))
verifycase('reuse_wrong_receipt_hash',change('extra','tamper_ref',True))
verifycase('reuse_changed_parsed_result',change('receipt','parsed',{}))
verifycase('reuse_claimed_formal_ownership',change('receipt','owned_acceptance_ids',['A03']))
verifycase('reuse_missing_provenance',change('receipt','source_head',''))
def missing_test(m,r,raw,extra):return '\n'.join(s for s in raw.splitlines() if json.loads(s).get('Test')!=target)
verifycase('reuse_rehashed_missing_test',missing_test)
def raw_hash(m,r,raw,extra):extra['preserve_raw_hash']=True;return raw+'\n'
verifycase('reuse_raw_hash_mismatch',raw_hash)

transport=[]
def env(task='W03',gate='W03-G01',case=''):
    return {'RESEARCHOS_TASK_ID':task,'RESEARCHOS_CHECK_ID':gate,'RESEARCHOS_CASE_ID':case,'RESEARCHOS_GO':locked['tools']['go']['path']}
for gate,key in g.KEYS.items():
    check('route_parent_'+gate,bridge.route(key,env(gate=gate))==('parent',gate))
    for name,otherkey,otherenv in [('wrongkey','test.domain' if key=='contracts.validate' else 'contracts.validate',env(gate=gate)),('formalcase',key,env(gate=gate,case='A03'))]:
        caught=False
        try:bridge.route(otherkey,otherenv)
        except ValueError:caught=True
        check('route_'+gate+'_'+name,caught)
for key,child in [('contracts.validate','W03-02'),('test.domain','W03-01')]:
    original=baseline['v24_decoded_commands'][key]
    childenv=env(gate=child);childenv.update(original['fixed_env'])
    calls=[]
    def call(*args,**kwargs):calls.append((args,kwargs));return 37
    with patch.object(bridge,'subprocess',types.SimpleNamespace(call=call)),patch.dict(os.environ,childenv,clear=True),patch.object(sys,'argv',['bridge.py',key]):result=bridge.main()
    check('transport_child_'+child,result==37 and calls==[(([locked['tools']['go']['path'],*original['argv']],),{'cwd':bridge.ROOT})])
    transport.append({'kind':'child','key':key,'invocation':calls[0][0][0],'environment':'inherited unchanged','stdio':'inherited','exit_code':result})
    wrong=env(gate='W03-01' if child=='W03-02' else 'W03-02')
    caught=False
    try:bridge.route(key,wrong)
    except ValueError:caught=True
    check('route_wrong_child_'+child,caught)
    inherited=dict(os.environ);inherited.update(after[key]['fixed_env']);inherited.update(env(task='W06',gate='W06-G01',case='A03'))
    legacyentry=legacy['commands'][key]
    wanted={k:inherited[k] for k in legacyentry['allowed_env'] if k in inherited};wanted.update(legacyentry['fixed_env']);wanted.update({k:inherited[k] for k in ['RESEARCHOS_TASK_ID','RESEARCHOS_CHECK_ID','RESEARCHOS_CASE_ID'] if inherited.get(k)})
    wanted.update({k:locked['tools'][v]['path'] for k,v in legacyentry['tool_env'].items()})
    calls=[]
    with patch.object(bridge,'subprocess',types.SimpleNamespace(call=call)),patch.dict(os.environ,inherited,clear=True),patch.object(sys,'argv',['bridge.py',key]):result=bridge.main()
    check('transport_legacy_'+key,result==37 and calls==[(([sys.executable,*legacyentry['argv']],),{'cwd':bridge.ROOT,'env':wanted})])
    transport.append({'kind':'legacy','key':key,'argv':calls[0][0][0],'environment_matches_original_registry':True,'environment_names':sorted(wanted),'stdio':'inherited','exit_code':result})
    for i,(task,gate,case) in enumerate([('W04','W03-G01',''),('W13','',''),('','',''),('W03','','')]):
        check('route_legacy_'+key+'_'+str(i),bridge.route(key,env(task,gate,case))==('legacy',[sys.executable,*legacyentry['argv']]))
save('transport_interception.synthetic.json',{'scope':'SYNTHETIC_NO_SUBPROCESS_EXECUTED','records':transport})
save('synthetic_results.json',synthetic)

tasks=pin(R/'.local/worktrees/v24-continuation/spec/v2.4/contracts/tasks.json');task=next(t for t in tasks['tasks'] if t['task_id']=='W03')
card=R/'.local/worktrees/v24-continuation/spec/v2.4/tasks/steps/W03-99.md';inputs[str(card)]=sha(card)
check('FROZEN_TASK_AND_CARD',sha(card)=='5874067a5e5a2fcd267a01776965422f83ab288a77d0e120c8046dc35d8f0590' and sha(R/'.local/worktrees/v24-continuation/spec/v2.4/contracts/tasks.json')=='37e1bc901a8843b91ae750c90164ef58560bccc50fa011908b5f3c30809cb8d4')
check('NO_FORMAL_OWNERSHIP',task['owned_acceptance_ids']==[] and handoff['owned_acceptance_ids']==[] and handoff['formal_product_acceptance']=='NOT_RUN')
coverage=[
 {'requirement':task['development_checklist'][0],'evidence':['G01 TestW03SchemaMigrationDefaults','G01 CORE-AGGREGATES-UNIQUE','G01 TestW03CurrentMuHTTPPersistenceAndInheritance','G01 CURRENT-PROJECT-PERSISTED'],'boundary':'current aggregate construction and contract/storage consistency'},
 {'requirement':task['development_checklist'][1],'evidence':['G02 TestW03PreconditionReplayAuthorization','G02 TestW03ConcurrentWriteOutboxRollback','G02 TestW03GoalTaskDraftAndRefusals'],'boundary':'409/412, idempotency, transactional persistence'},
 {'requirement':task['development_checklist'][2],'evidence':['G03 MONEY-* / UTC-* / UNLIMITED-*','G02 TestW03ConcurrentWriteOutboxRollback','G02 TestW03CursorSnapshotAndReceipt'],'boundary':'base types and ordered/de-duplicated outbox; fixture mode'},
 {'requirement':task['development_checklist'][3],'evidence':['G01 ACCEPTANCE-INDEPENDENT-EXACT','G03 RECEIPT-BINDS-* and RUBRIC-CONTRACT-SHAPE','G03 TestW03ContentSealAccessAndImmutability'],'boundary':'contract independence and immutable version/hash binding; full W06 service and A03 remain NOT_RUN'},
 {'requirement':task['development_checklist'][4],'evidence':['G01 RUNTIME-DEFINITION-PROJECTION / RUNTIME-OPERATION-PROJECTION / CURRENT-LOCAL-REFS','G01 NO-EVALUATION-SCHEDULING-ENTITY / STATE-ENUMS-UNCHANGED','G01 106 original protocol fixture decisions'],'boundary':'frozen API definitions and evaluation contract authority unchanged'}]
check('FIVE_DEVELOPMENT_CHECKLIST_ITEMS',len(coverage)==len(task['development_checklist'])==5)
cardchecks=[{'id':'W03-99-OUTPUT','result':'PASS','basis':'Three current exact registered parent gates accepted in their original modes; owned formal cases empty.'},{'id':'W03-99-NEGATIVE','result':'PASS','basis':'Full current baselines pass; stale rehashed evidence, missing tests, invalid parser payloads and altered hashes reject; child completion alone is not gate evidence.'},{'id':'W03-99-EVIDENCE','result':'PASS','basis':'Current immutable manifests, authorized commit/worktree, real raw command output, source hashes and preserved original failure independently verified.'}]
check('CARD_THREE_CHECKS',all(c['id'] in card.read_text(encoding='utf8') for c in cardchecks))
check('HEAD_UNCHANGED_AT_CLOSE',git('rev-parse','HEAD').decode().strip()==FROZEN_HEAD)
save('checks.json',checks)
save('inputs_manifest.json',{'scope':'INDEPENDENT_READ_ONLY_EVIDENCE_INPUTS','files':inputs,'frozen_main_head':FROZEN_HEAD,'actual_atom_head':ATOM_HEAD})
manifest={'schema':'researchos.independent-review-manifest.v1','files':{p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'},'actual_product_commands_run':0,'actual_dispatcher_commands_run':0,'forbidden_run_gate_and_execute_atom':'replaced by raising sentinel','synthetic_payloads_in_product_atom_directory':False}
save('manifest.json',manifest)
review={'schema':'researchos.independent-parent-review.v1','reviewer':'codex:/root/w1702_review','model':'gpt-6-astra','reasoning_effort':'high','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'ACCEPT_W03_PARENT_CONSTRUCTION','task_id':'W03','step_id':'W03-99','main_head':FROZEN_HEAD,'atom_source_head':ATOM_HEAD,'candidate_commit':handoff.get('candidate_commit','d3f46a8b9bb11c530e92c4cb1faeaabe980eeecb'),'registry_revision':37,'independent_check_count':len(checks),'independent_checks_passed':sum(c['passed'] for c in checks),'synthetic_parser_and_reuse_cases':len(synthetic),'historical_seven_parser_counterexamples_rejected':7,'new_complete_baselines_passed':2,'transport_interception_count':len(transport),'prior_source_review':{'path':str((B/'independent_source_review_codex_062cce3b.json').relative_to(R)),'sha256':sha(B/'independent_source_review_codex_062cce3b.json'),'checks':17,'current_delta':'Only authorized EXECUTOR caller and matching produced_by in test fixture; all other reviewed source hashes unchanged.'},'resolved_findings':[{'id':i,'classification':'RESOLVED_BY_COMPLETE_CURRENT_BASELINE_SINGLE_MUTATION_OR_TRANSPORT'} for i in ['W0399-FIXTURE-DETAIL-CORPUS-BINDING','W0399-GO-PACKAGE-TEST-IDENTITY','W0399-LEGACY-TRANSPORT-CONTRACT','W0399-STRICT-JSON-EXIT-TYPES']],'source_projection_issue':'RESOLVED_CURRENT_PERSISTENCE_AND_SUMMARY','guard_fixture_role_issue':'RESOLVED_CURRENT_TEST_REACHES_SCHEMA_PROJECT_AND_SEALING_REFUSALS','gate_results':[{'check_id':v['gate'],'mode':v['mode'],'assertion_ids':[v['gate']],'invocation_id':v['dispatcher']['invocation_id'],'result':'ACCEPTED_CURRENT_CONSTRUCTION_EVIDENCE'} for v in dispatch['actual_registered_selectors']],'counts_separate':{'registered_parent_assertions':3,'actual_go_atoms':3,'actual_probe_atoms':2,'go_top_level_tests':29,'go_subtests':2,'g01_probe_checks':126,'g03_probe_checks':26,'original_fixture_decisions_in_g01':106,'fixture_positive':76,'fixture_negative':30,'worker_synthetic_driver_tests':30},'development_checklist':coverage,'card_checks':cardchecks,'owned_acceptance_ids':[],'formal_case_count_delta':0,'formal_product_acceptance':'NOT_RUN','associated_cases':{'A03':{'status':'NOT_RUN','final_owner':'W06'},'C04':{'status':'NOT_RUN','final_owner':'W04'},'C19':{'status':'NOT_RUN','final_owner':'W09'}},'full_W06_acceptance_service':'NOT_RUN','state_written':False,'root_must_register_acceptance':True,'new_product_executions':0,'new_dispatcher_executions':0,'review_manifest':{'path':str((OUT/'manifest.json').relative_to(R)),'sha256':sha(OUT/'manifest.json')},'limitations':['Construction acceptance only; no product LIVE/formal 42-case qualification inferred.','Historical failed raw evidence remains immutable and separate from current accepted atoms.','No provider, GUI, service, legacy product, resource retry or old W13 workspace audit performed.']}
reviewpath=B/'independent_review_codex.json';assert not reviewpath.exists();reviewpath.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'verdict':review['verdict'],'checks':len(checks),'synthetic_cases':len(synthetic),'transport_cases':len(transport),'review_sha256':sha(reviewpath),'manifest_sha256':sha(OUT/'manifest.json')},ensure_ascii=False))
