import datetime,hashlib,json,uuid
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
BASE=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_independent_replay_codex'
HERE=Path(__file__).resolve().parent
PREP=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_continuation_preparation_codex/cli18-r310-67487c3a'
AUDIT=BASE/('cli18-r310-audit-'+uuid.uuid4().hex)
LANES={'remaining17':BASE/'cli17-r310-67487c3a','windows4':BASE/'cli-windows4-r310-67487c3a'}
def load(p):return json.loads(Path(p).read_bytes())
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (AUDIT/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(AUDIT/n)
def check(b,m):
 if not b:raise RuntimeError(m)
def parse_native(p):
 inv=load(p);proc=inv['owned_process'];cleanup=proc.get('job_cleanup') or {}
 raw=p.parent/'stdout.raw';events=[json.loads(x) for x in raw.read_text(encoding='utf-8').splitlines() if x.strip()]
 terms=[x for x in events if x.get('Test') and x.get('Action') in ('pass','fail','skip')]
 leaves=[x for x in terms if not any(y['Test'].startswith(x['Test']+'/') for y in terms)]
 return dict(invocation=ref(p),stdout=ref(raw),stderr=ref(p.parent/'stderr.raw'),native_exit=proc['actual_exit'],owned_job_success=proc.get('error') is None and not proc.get('timed_out') and proc.get('resumed') is True and all(cleanup.get(k) is True for k in ('kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')) and cleanup.get('errors')==[],leaves=[dict(name=x['Test'],status=x['Action']) for x in leaves],pass_count=sum(x['Action']=='pass' for x in leaves),fail_count=sum(x['Action']=='fail' for x in leaves),skip_count=sum(x['Action']=='skip' for x in leaves))
AUDIT.mkdir(exist_ok=False)
previous=load(BASE/'cli44-r309-stopped-aecd69f538014b068358ab527e547e53/case_matrix.json')
prior=[dict(cohort='r308-original3',**x) for x in previous['original_qualified76']]+[dict(cohort='r309-complete26',**x) for x in previous['continuation44'] if x['state']=='COMPLETE_PASS']
check(sum(x['leaf_pass'] for x in prior)==110,'PRIOR110')
rows=[];lane_reports=[];origins=[];qualified=list(prior);dbs=[];windows=[]
for lane,out in LANES.items():
 outer=load(HERE/lane/'invocation.json');roster=load(PREP/('roster.'+lane+'.json'))['selectors']
 frozen=load(out/'execution.inputs.before-first-case.json') if (out/'execution.inputs.before-first-case.json').is_file() else []
 by_path={x['path']:x for x in frozen};native=[];complete=[]
 for index,entry in enumerate(roster):
  case=out/'cases'/f'{index:02d}';ip=out/'invocations'/f'case-{index:02d}'/'invocation.json'
  record=dict(lane=lane,index=index,original_index=entry['original_index'],selector=entry['selector'],expected_leaves=entry['expected_leaf_names'])
  if not ip.is_file():record['state']='NOT_RUN';rows.append(record);continue
  record.update(parse_native(ip));native.append(record)
  check(sorted(x['name'] for x in record['leaves'])==sorted(entry['expected_leaf_names']),'LEAF_INVENTORY')
  if (case/'result.json').is_file():
   check(record['owned_job_success'] and record['native_exit']==0 and not record['fail_count'] and not record['skip_count'],'COMPLETE_NATIVE')
   for phase in ('before','after-native','after-fixtures'):
    check(load(case/f'inputs.{phase}.json')==frozen,'CLOSURE')
    check(all(by_path.get(x['path'])==x for x in load(case/f'runtime.{phase}.json')),'RUNTIME_CLOSURE')
   record['state']='COMPLETE_PASS';complete.append(record)
   qualified.append(dict(cohort='r310-'+lane,leaf_pass=record['pass_count'],leaves=record['leaves'],selector=record['selector'],original_index=record['original_index']))
  else:record['state']='NATIVE_OBSERVED_CLOSURE_OR_CASE_INCOMPLETE'
  rows.append(record)
  if (case/'windows-child-binding.json').is_file():windows.append(dict(binding=ref(case/'windows-child-binding.json'),value=load(case/'windows-child-binding.json'),stdout=record['stdout']))
 for p in sorted((out/'cases').rglob('*.independent-alltables.json')) if (out/'cases').exists() else []:
  d=load(p);check(ref(d['closed_database']['path'])==d['closed_database'],'DB_CHANGED');dbs.append(dict(database=d['closed_database'],alltables=ref(p)))
 current=[ref(x['path']) for x in frozen]
 drift=[dict(before=x,current=y) for x,y in zip(frozen,current) if x!=y]
 curref=save(lane+'.current.inputs.json',current)
 success=outer['actual_exit']==0 and (out/'execute.completed.json').is_file() and len(complete)==len(roster)
 if success:check(not drift and load(out/'inputs.after-all.json')==frozen,'FINAL_CLOSURE')
 else:origins.append(dict(origin_id='CLI-r310-'+lane+'-controller',counter_delta=1,outer=ref(HERE/lane/'invocation.json'),outer_exit=outer['actual_exit'],stopped=ref(out/'execute.stopped.json') if (out/'execute.stopped.json').is_file() else None))
 lane_reports.append(dict(lane=lane,success=success,outer=ref(HERE/lane/'invocation.json'),native_selector_processes=len(native),complete_selectors=len(complete),native_leaf_pass=sum(x['pass_count'] for x in native),native_leaf_fail=sum(x['fail_count'] for x in native),native_leaf_skip=sum(x['skip_count'] for x in native),complete_leaf_pass=sum(x['pass_count'] for x in complete),NOT_RUN=len(roster)-len(native),input_count=len(frozen),current_input_drift=drift,current_inputs=curref,kernel_preload=ref(out/'kernel-preload.json') if (out/'kernel-preload.json').is_file() else None))
names=[x['name'] for r in qualified for x in r['leaves']]
check(len(names)==len(set(names)),'DUPLICATE_UNION')
matrix=save('typed_case_union.json',dict(prior_qualified110=prior,new_lane_cases=rows,complete_unique_leaves=len(names),complete_unique_selectors=len(qualified),planned_unique_leaves=221,all_planned_complete=all(x['success'] for x in lane_reports),preserved_extra_unclosed_native_pass_leaves=6,preserved_prior_controller_failures=2,cohorts_and_executables_not_conflated=True))
failref=save('failure_origins.json',dict(new_origins=origins,prior_origins_already_registered=['CLI47-r308-execute-4d65b6-2caf3a','CLI44-r309-execute-6583c0-17b27c'],no_counter_reset=True))
dbref=save('closed_fixture_refs.json',dbs);winref=save('windows_child_evidence.json',windows)
review=save('review.json',dict(schema='researchos.cli-split-independent-execution-review.v1',reviewer='codex:/root/w05_merge_review',decision='FINITE_LANES_COMPLETED_SOURCE_ACCEPTANCE_WITHHELD' if not origins else 'STOPPED_SOURCE_ACCEPTANCE_WITHHELD',candidate='b98738ac093ea55bb8700cfa724ddd9e6b2a1251',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),lanes=lane_reports,unique_qualified_leaf_union=len(names),planned_unique_leaf_union=221,new_leaf_pass=sum(x['native_leaf_pass'] for x in lane_reports),new_leaf_fail=sum(x['native_leaf_fail'] for x in lane_reports),new_leaf_skip=sum(x['native_leaf_skip'] for x in lane_reports),prior_controller_failures_preserved=2,prior_unclosed_native_pass_leaves_preserved=6,typed_case_union=matrix,closed_fixtures=dbref,windows_child_evidence=winref,failure_origins=failref,new_primary_compile_count=0,windows_test_internal_temporary_compile_count=1 if windows else None,source_acceptance=False,Main_integration=False,formal_increment=0,effects=dict(SDK_Node_worker_model_external_provider_paid_calls=0,loopback_HTTP_request_count=None,loopback_count_limitation='No aggregate request counter; original fixture method/wire evidence retained.'),limitations=['Reuse original verified CLI/test/harness binaries and compilation graph; no new primary compilation claim.','Native 221 union is composed from four distinct successful evidence cohorts, with two prior failed controller attempts retained.','Explicit kernel preload binds resource only; original dynamic loader cause remains unknown.','Existing2 nonnull list500/P01-03 realAPI layer gap/P02/true attach completion/fullharness/Main/parent/formal remain outside this qualification.']))
entries=[]
for base in [*LANES.values(),HERE,AUDIT]:
 for p in sorted(base.rglob('*')):
  if p.is_file():entries.append(ref(p))
manifest=save('manifest.json',dict(schema='researchos.receipt-manifest.v1',entries=entries,count=len(entries),includes_self=False))
handoff=save('handoff.json',dict(review=review,manifest=manifest,matrix=matrix,failure_origins=failref,windows_evidence=winref,source_acceptance=False,formal_increment=0))
print(json.dumps(dict(namespace=str(AUDIT),review=review,manifest=manifest,handoff=handoff,counts=lane_reports,qualified_union=len(names)),ensure_ascii=False))
