"""Focused CP573 delta review. No helper/build/native/window action."""
import ast,datetime,hashlib,io,json,os,queue,runpy,stat,sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

OUT=Path(__file__).resolve().parent
BASE=OUT.parents[2]
PREP=BASE/'product_host_native_20261028'/'native-init-diagnosis-02'/'environment-probe'/'preparation03'
SCOPE=BASE/'resume_cp528_codex'/'20261025-current-chat'/'continuation-cp573'/'Native-folder-followup-preparation03-scope.json'
SNAP=OUT/'input-snapshots';SNAP.mkdir(exist_ok=False)
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
scope=load(SCOPE);prep=load(PREP/'PREPARATION.json');template=load(PREP/'RUN-SCOPE-TEMPLATE.json')
assert ref(SCOPE)['sha256']=='f43998c1617d0e7596b7ef9f05b618e8b30f7de789511b295d66be992af7bb7a'
assert ref(PREP/'PREPARATION.json')['sha256']=='14772591b1998e1ee6de7d7d6b71f1bdfd2b99de10455fc5f35c491e8c8a22db'
assert ref(PREP/'controller.py')['sha256']=='88b2dc8dfd736e16b9edd57d45dc39b6c2ad6053c3498148b7ff1e5139113d23'
assert ref(PREP/'controller.diff')['sha256']=='4030241a5ca6465793ee54a8f6fa8fb0bc32ac9e844411114f2d605007b94972'
assert not scope['native_execution_authorized'] and not prep['native_execution_authorized'] and not template['native_execution_authorized']
refs=[]
for p in sorted(PREP.iterdir()):
    if p.is_file():(SNAP/p.name).write_bytes(p.read_bytes());refs.append(ref(p))
(SNAP/'SOURCE-SCOPE.json').write_bytes(SCOPE.read_bytes());refs.append(ref(SCOPE))
for label,row in prep['files'].items():
    actual=ref(Path(row['path']));assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'],label
    refs.append(actual)
for name in ('prior_controller_ref','prior_preparation_ref','helper_ref','actual_adoption_ref','analysis_ref','old_probe_environment_ref','old_probe_spawn_ref'):
    actual=ref(Path(scope[name]['path']));assert actual['sha256']==scope[name]['sha256'] and actual['bytes']==scope[name]['bytes'],name
    refs.append(actual)
prior=Path(scope['prior_controller_ref']['path']).read_text(encoding='utf-8')
current=(PREP/'controller.py').read_text(encoding='utf-8')
(SNAP/'prior-controller.py').write_text(prior,encoding='utf-8')
old_tree,new_tree=ast.parse(prior),ast.parse(current)
old_funcs={n.name:ast.dump(n,include_attributes=False) for n in old_tree.body if isinstance(n,ast.FunctionDef)}
new_funcs={n.name:ast.dump(n,include_attributes=False) for n in new_tree.body if isinstance(n,ast.FunctionDef)}
inherited=['process_identity','windows_for','exact_dialog','next_event','safe_record','safe_append','ignore_interrupts','release_valid','unresolved_hold']
for name in inherited:assert old_funcs[name]==new_funcs[name],name
save('INPUTS.json',refs)
g=runpy.run_path(str(PREP/'controller.py'))
baseline=load(PREP/'BASELINE-INPUTS.json')
actual_manifest=g['manifest_state'](g['OLD_STATE'])
a,c,workspace=g['build_environments'](g['OLD_STATE'],os.environ['SystemRoot'],os.environ['WINDIR'])
assert actual_manifest==baseline['state_manifest']
assert actual_manifest['sha256']==template['state_manifest_sha256']==prep['state_manifest_sha256']
assert a==baseline['A_values']
assert g['env_digest'](a)==baseline['A_sha256']==template['a_env_sha256']
assert g['env_digest'](c)==baseline['C_sha256']==template['c_env_sha256']
assert {key:c[key] for key in a}==a
assert set(c)-set(a)<=set(scope['approved_os_environment_keys'])|{'HOMEDRIVE','HOMEPATH'}
assert c['HOMEDRIVE']+c['HOMEPATH']==a['USERPROFILE']
save('CURRENT-READONLY-BASELINE.json',{'state_manifest_sha256':actual_manifest['sha256'],'entry_count':len(actual_manifest['entries']),
    'A_sha256':g['env_digest'](a),'C_sha256':g['env_digest'](c),'A_keys':sorted(a),'C_added_keys':sorted(set(c)-set(a)),
    'synthetic_HOME_matches_USERPROFILE':True,'state_mutations':0})

# Execute only main's control flow with run_case mocked; never spawn or call WinAPI.
fg=g['main'].__globals__
flow_cases=[]
for label,cancelled,elapsed,expected in [('visible',True,600_000_000,['C','A2']),('null',False,100_000_000,['C','D']),('unexpected',False,3_000_000_000,['C'])]:
    calls=[]
    root=OUT/('flow-'+label)
    def fake_case(case_label,helper,hint,env,out,scope_hash,state,hidden,expected_flags):
        calls.append({'label':case_label,'env_is_A':env is a,'env_is_C':env is c,'hidden':hidden,'expected_flags':expected_flags})
        return {'case':case_label,'cancelled':cancelled if case_label=='C' else False,
            'result':{'event':'result','error':'INVALID_REQUEST: folder selection cancelled','elapsed_ns':elapsed},
            'ready':{'startup_flags':257,'startup_show':0}}
    failed=False
    with mock.patch.dict(fg,{'validate_scope':lambda path:({},g['OLD_STATE'],root,a,c,workspace,actual_manifest),
                            'digest':lambda path:'mock-scope','run_case':fake_case}),mock.patch.object(sys,'argv',['controller.py','mock-run-scope.json']):
        try:g['main']()
        except RuntimeError as error:
            assert str(error)=='C_UNEXPECTED_BRANCH_STATE';failed=True
    assert [row['label'] for row in calls]==expected and len(calls)<=2
    assert calls[0]['env_is_C'] and calls[0]['hidden'] is True
    if len(calls)==2:
        assert calls[1]['expected_flags']==257
        assert calls[1]['hidden'] is (expected[1]=='A2')
        assert calls[1]['env_is_A'] is (expected[1]=='A2')
        assert calls[1]['env_is_C'] is (expected[1]=='D')
    assert failed is (label=='unexpected')
    flow_cases.append({'case':label,'calls':calls,'unexpected_aborts_before_second':failed})

startup_negatives=[]
for flags,hidden,expected_flags in [(257,False,257),(258,False,257),(1,False,257),(256,True,257)]:
    try:g['verify_startup']({'startup_flags':flags,'startup_show':0},hidden,expected_flags)
    except AssertionError as error:startup_negatives.append({'flags':flags,'hidden':hidden,'rejected':str(error)})
    else:raise AssertionError('unexpected startup accepted')
g['verify_startup']({'startup_flags':256,'startup_show':0},False,257)
g['verify_startup']({'startup_flags':257,'startup_show':0},True,257)
raw=b'{"event":"ready","pid":7}\r\n\xff\n'
inbox=queue.Queue();buffer=bytearray();faults=[]
g['read_lines'](io.BytesIO(raw),inbox,buffer,faults)
assert bytes(buffer)==raw and g['next_event'](inbox,1)['event']=='ready' and faults
try:g['next_event'](inbox,1)
except RuntimeError as error:raw_failure=str(error)
else:raise AssertionError('invalid UTF8 not refused')
with mock.patch.object(g['no_reparse'].__globals__['os'],'lstat',return_value=SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=0x400)):
    try:g['no_reparse'](Path('mock-junction'))
    except AssertionError as error:reparse_refusal=str(error)
    else:raise AssertionError('reparse accepted')
save('FOCUSED-PROBES.json',{'status':'PASS','mocked_main_flows':flow_cases,'startup_negative_cases':startup_negatives,
    'invalid_utf8_preserved_raw_then_refused':raw_failure,'reparse_refused':reparse_refusal,
    'unchanged_accepted_functions':inherited,'helper_spawns':0,'native_calls':0,'go_builds':0})
report={'schema':'researchos.independent-native-folder-followup-source-review.v1',
    'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/product_host_independent_20261028',
    'status':'SOURCE_ACCEPTED_FOR_SEPARATE_FINITE_C_THEN_A2_OR_D_SCOPE','controller_source_accepted':True,
    'fixed_preparation_ref':ref(PREP/'PREPARATION.json'),'controller_ref':ref(PREP/'controller.py'),'diff_ref':ref(PREP/'controller.diff'),
    'helper_ref':scope['helper_ref'],'template_ref':ref(PREP/'RUN-SCOPE-TEMPLATE.json'),'findings':[],
    'formal_increment':0,'reviewer_helper_runs':0,'reviewer_native_actions':0,'go_builds':0,'old_state_or_shared_source_mutations':0,
    'checks':[
        'Frozen preparation/controller/diff/helper and referenced source-scope inputs all match. Helper remains byte-identical; no rebuild performed.',
        'Current CP572 synthetic-state manifest has8 entries and matches frozen hash. Exact A values retained; C only adds approved OS keys and HOME derived from synthetic USERPROFILE. Current A/C environment digests match frozen template.',
        'Mocked main takes exactly C->A2 for confirmed cancel or C->D for bounded fast Shell-null; unexpected slow-null aborts before a second call. No third path or automatic same-input retry exists.',
        'A2 retains hidden mode and original A values; D uses exactly C values and verifies observed flags differ from C solely in STARTF_USESHOWWINDOW. Wrong bit deltas refused before open handshake.',
        'Raw stdout bytes are retained before strict decoding; invalid UTF8 is preserved and reported as an error. Completed cases persist raw stdout after reader join plus before/after synthetic-state manifests and deltas.',
        'Retained handle identity, owned-window matching, normal IDCANCEL, release validation and persistent hold functions are AST-identical to accepted prep02. New postspawn operations remain inside BaseException-to-hold boundary.',
        'Exact old-state root and per-entry no-reparse checks prevent routine symlink/junction traversal; injected reparse entry refused. Preflight binds max2/branch plan, hashes, current clean candidate, fresh receipts and initial state/env hashes; optimized Python explicitly refused. Git flags disable auto gc/maintenance.'
    ],
    'run_scope_requirements':['Root must issue a new exact run scope binding these final hashes and the observed unchanged state/environment digests; current template remains native_execution_authorized=false.',
        'Only CP572-owned synthetic state is reusable. Keep original receipts and helper/source bytes unchanged; preserve every new before/after manifest.',
        'C is always first; run only the selected second case. Unexpected state ends remaining plan; no extra case or force termination.',
        'Treat results as environment-group/startup diagnostic evidence only, never single-key causality or product qualification.'],
    'limitations':['No helper/native execution. No full old regression or Go rebuild rerun; only changed control-flow/boundary probes and accepted-function equivalence checked.',
        'Shared preexisting synthetic state and fixed order can influence outcomes; manifests record changes rather than erase them.',
        'Window polling remains sampled; missing observations are not proof a window never existed.',
        'On a failure, stdout.partial.raw is a best-effort snapshot at hold entry; subsequent bytes may remain in the live reader buffer. Damaged receipts can intentionally keep the controller fail-closed.'],
    'evidence_refs':[ref(OUT/'INPUTS.json'),ref(OUT/'CURRENT-READONLY-BASELINE.json'),ref(OUT/'FOCUSED-PROBES.json')]}
save('REVIEW.json',report)
print(json.dumps(ref(OUT/'REVIEW.json'),ensure_ascii=False))
