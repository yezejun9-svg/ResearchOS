import hashlib, json, uuid
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path('D:/作品集/ResearchOS/research-os')
BASE=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_independent_replay_codex'
OUT=BASE/'cli44-r309-c927f880'
OLD=BASE/'cli47-r308-7d5925db'
LAUNCH=Path(__file__).resolve().parent
HERE=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_continuation_preparation_codex/cli44-r309-grant-1bd789af'
AUDIT=BASE/('cli44-r309-stopped-'+uuid.uuid4().hex)
def load(p): return json.loads(Path(p).read_bytes())
def ref(p):
 p=Path(p);raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,data):
 p=AUDIT/name
 with p.open('xb') as f:f.write((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(p)
def require(b,msg):
 if not b:raise RuntimeError(msg)
def case_audit(root,index,frozen,phases):
 c=root/'cases'/f'{index:02d}';invp=root/'invocations'/f'case-{index:02d}'/'invocation.json'
 inv=load(invp);proc=inv['owned_process'];job=proc['job_cleanup']
 raw=invp.parent/'stdout.raw'
 events=[json.loads(x) for x in raw.read_text(encoding='utf-8').splitlines() if x.strip()]
 terminal=[e for e in events if e.get('Test') and e.get('Action') in ('pass','fail','skip')]
 leaves=[e for e in terminal if not any(x['Test'].startswith(e['Test']+'/') for x in terminal)]
 checks={phase:load(c/f'inputs.{phase}.json')==frozen for phase in phases if (c/f'inputs.{phase}.json').exists()}
 return dict(index=index,invocation=ref(invp),stdout=ref(raw),stderr=ref(invp.parent/'stderr.raw'),selector=inv['argv'][-1].removeprefix('-test.run='),native_exit=proc['actual_exit'],leaf_pass=sum(x['Action']=='pass' for x in leaves),leaf_fail=sum(x['Action']=='fail' for x in leaves),leaf_skip=sum(x['Action']=='skip' for x in leaves),leaves=[{'name':x['Test'],'status':x['Action']} for x in leaves],job_complete=proc['error'] is None and not proc['timed_out'] and proc['resumed'] and all(job[k] is True for k in ['assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and not job['errors'],closure_checks=checks,result_exists=(c/'result.json').exists())

AUDIT.mkdir(exist_ok=False)
stopped=load(OUT/'execute.stopped.json');outer=load(LAUNCH/'execute.outer.json')
require(outer['actual_native_exit']==1,'OUTER_EXIT')
frozen=load(OUT/'execution.inputs.before-first-case.json');by_path={x['path']:x for x in frozen}
current=[ref(x['path']) for x in frozen]
drift=[{'before':x,'current':y} for x,y in zip(frozen,current) if x!=y]
curref=save('current.original7803.inputs.json',current)
roster=load(HERE/'finite_selectors.v3.json')['selectors']
cases=[]
for index,entry in enumerate(roster):
 invp=OUT/'invocations'/f'case-{index:02d}'/'invocation.json'
 if invp.exists():
  r=case_audit(OUT,index,frozen,('before','after-native','after-fixtures'))
  require(r['selector']==entry['selector'],'SELECTOR')
  require(sorted(x['name'] for x in r['leaves'])==sorted(entry['expected_leaf_names']),'LEAF_NAMES')
  r.update(original_index=entry['original_index'],state='COMPLETE_PASS' if r['result_exists'] else 'NATIVE_RESULT_CONTROLLER_CLOSURE_INCOMPLETE')
 else:r=dict(index=index,original_index=entry['original_index'],selector=entry['selector'],state='NOT_RUN',expected_leaf_names=entry['expected_leaf_names'])
 cases.append(r)
actual=[c for c in cases if c['state']!='NOT_RUN'];qualified=[c for c in cases if c['state']=='COMPLETE_PASS']
require(len(actual)==27 and len(qualified)==26,'ACTUAL_COUNTS')
require(all(c['native_exit']==0 and c['job_complete'] and c['leaf_fail']==0 and c['leaf_skip']==0 for c in actual),'NATIVE')
require(all(len(c['closure_checks'])==3 and all(c['closure_checks'].values()) for c in qualified),'QUALIFIED_CLOSURES')
last=OUT/'cases/26'
runtime_before=load(last/'runtime.before.json');runtime_after=load(last/'runtime.after-native.json')
runtime_delta=[{'before':by_path.get(x['path']),'after':x} for x in runtime_after if by_path.get(x['path'])!=x]
oldfrozen=load(OLD/'execution.inputs.before-first-case.json')
old=[case_audit(OLD,i,oldfrozen,('before','after')) for i in range(3)]
require(sum(x['leaf_pass'] for x in old)==76 and all(x['native_exit']==0 and all(x['closure_checks'].values()) for x in old),'OLD76')
dbs=[]
for p in sorted((OUT/'cases').rglob('*.independent-alltables.json')):
 d=load(p);f=d['closed_database'];actualref=ref(f['path'])
 require(f==actualref,'DB_MUTATION')
 dbs.append(dict(database=actualref,alltables=ref(p)))
dbref=save('closed_public_fixture_refs.json',dbs)
cause=save('readonly_cause.json',dict(observed_stop=stopped,runtime_before=ref(last/'runtime.before.json'),runtime_after=ref(last/'runtime.after-native.json'),delta=runtime_delta,original_known_input_count=len(frozen),original_input_drift=drift,current_inputs=curref,loader_cause=None,loader_cause_limitation='Observed newly loaded OS DLL only; no loader trace establishes which action caused its load. No repair/preload/replay executed.',status='NEW_PUBLIC_OS_RUNTIME_RESOURCE_NOT_FROZEN_BEFORE_CASE',read_only=True))
origin=save('failure_origins.json',[dict(origin_id='CLI44-r309-execute-6583c0-17b27c',kind='INDEPENDENT_CONTROLLER_RUNTIME_CLOSURE_FAILURE',single_invocation=True,counter_delta=1,outer_exit=1,native_controller_exit=1,underlying_case_native_failures=0,started_tool='6583c0',completion_tool='17b27c',session_id=24126,outer=ref(LAUNCH/'execute.outer.json'),stderr=ref(LAUNCH/'execute.stderr.raw'),stdout=ref(LAUNCH/'execute.stdout.raw'),stopped=ref(OUT/'execute.stopped.json'),cause=cause,old_origin_already_registered='CLI47-r308-execute-4d65b6-2caf3a')])
matrix=save('case_matrix.json',dict(original_qualified76=old,continuation44=cases,qualified_union_leaves=76+sum(c['leaf_pass'] for c in qualified),native_observed_union_leaves=76+sum(c['leaf_pass'] for c in actual),planned_union_leaves=221,planned_not_executed_leaf_count=sum(len(c.get('expected_leaf_names',[])) for c in cases if c['state']=='NOT_RUN'),all_plan_complete=False))
review=save('review.json',dict(schema='researchos.cli44-independent-execution-review.v1',reviewer='codex:/root/w05_merge_review',decision='STOPPED_NEW_OS_RUNTIME_INPUT_SOURCE_ACCEPTANCE_WITHHELD',candidate='b98738ac093ea55bb8700cfa724ddd9e6b2a1251',at=datetime.now(timezone.utc).isoformat(),native_selector_processes_executed=27,completed_controller_case_records=26,selector_processes_NOT_RUN=17,native_leaf_pass=sum(c['leaf_pass'] for c in actual),native_leaf_fail=0,native_leaf_skip=0,qualified_new_leaves=sum(c['leaf_pass'] for c in qualified),original_qualified_leaves=76,controller_native_exit=1,known_input_count=len(frozen),known_input_drift_count=len(drift),new_unfrozen_runtime_inputs=runtime_delta,new_primary_compile_count=0,retry_count=0,case_matrix=matrix,closed_public_fixture_count=len(dbs),closed_public_fixtures=dbref,current_inputs=curref,cause=cause,failure_origins=origin,source_acceptance=False,Main_integration=False,formal_increment=0,effects=dict(SDK_Node_worker_model_external_provider_paid_calls=0,loopback_HTTP_request_count=None,loopback_count_limitation='No aggregate request instrumentation. Original fixture/HTTP records retained; no new requests issued by review.'),progress_correction='Intermediate commentary reported case25 from concurrently advancing directory snapshot; sealed terminal facts establish failed closure at case26 after 27th native process. case25 fully completed.',held=['existing2 session.list500 in pinned base','P01-03 actual API layer gap','P02','actual attach durable completion','fullharness','Main/source/parent/formal'],next_action='STOP. Root decides explicit additional runtime input and finite continuation scope; no same-input retry.'))
entries=[]
for base in (OUT,LAUNCH,AUDIT):
 for p in sorted(base.rglob('*')):
  if p.is_file():entries.append(ref(p))
manifest=save('manifest.json',dict(schema='researchos.receipt-manifest.v1',entries=entries,count=len(entries),includes_self=False,unexecuted_success_sealer=str(LAUNCH/'seal.py')))
handoff=save('handoff.json',dict(review=review,manifest=manifest,case_matrix=matrix,cause=cause,failure_origins=origin,current_inputs=curref,scope=ref(ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/closure-and-finite-continuation-r309/cli_continuation_scope.v2.json'),source_acceptance=False))
print(json.dumps(dict(namespace=str(AUDIT),review=review,manifest=manifest,handoff=handoff,failure_origins=origin,counts=load(AUDIT/'review.json')),ensure_ascii=False))
