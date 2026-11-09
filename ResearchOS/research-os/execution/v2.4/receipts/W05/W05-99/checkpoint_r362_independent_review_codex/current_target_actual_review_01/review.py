import sys
sys.dont_write_bytecode=True
import json,hashlib,types,collections,re
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).resolve().parent
N=B/'sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r362-native-failed-closed-current-target-results'
checks=[];issues=[];refs={};copies=[]
def raw(p):return Path(p).read_bytes()
def read(p):return json.loads(raw(p))
def pin(p):
 p=Path(p).resolve();b=raw(p);return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def check(n,c,d=None):
 entry=dict(check=n,passed=bool(c),detail=d);checks.append(entry)
 if not c:issues.append(entry)
def add(v,label):
 p=Path(v['path']);p=p if p.is_absolute() else R/p
 expected=dict(path=str(p.resolve()),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes'])
 try:a=pin(p)
 except Exception as e:check('reference-readable',False,dict(label=label,expected=expected,error=repr(e)));return
 check('exact-reference',a==expected,dict(label=label,expected=expected,actual=a) if a!=expected else None)
 key=a['path'].casefold()
 if key in refs:check('consistent-reference',refs[key]==expected,label)
 else:refs[key]=expected
def walk(v,label):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=v.keys():
   p=Path(v['path']);p=p if p.is_absolute() else R/p
   if p.resolve().parent==R/'execution/v2.4' and p.name in ('checkpoint.json','path_ownership.json','step_state.json','commands.json'):return
   add(v,label)
  else:
   for k,x in v.items():walk(x,label+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk(x,label+'/'+str(i))
def copy(p,folder):
 p=Path(p);dest=O/'originals'/folder/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('xb') as f:f.write(raw(p))
 copies.append(dict(source=pin(p),copy=pin(dest)))
def members(v):return list(v.values()) if isinstance(v,dict) else v
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
code=raw(gp);check('guard-source-pin',hashlib.sha256(code).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85')
m=types.ModuleType('cp362_review_source_guard');m.__file__=str(gp);exec(compile(code,str(gp),'exec'),m.__dict__)
expected=[('checkpoint.json','84c970d86ab96b78a7621595839005f68a440fc9a540d3b619500c7cbed2669b',4195882),('path_ownership.json','48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452',192861),('step_state.json','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),('commands.json','b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129',68156)]
canonical=[dict(path=str(R/'execution/v2.4'/n),sha256=h,bytes=z) for n,h,z in expected]
cg=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);cg.acquire(canonical)
try:
 for v in canonical:
  p=O/'canonical-short-snapshot'/Path(v['path']).name;p.parent.mkdir(exist_ok=True)
  with p.open('xb') as f:f.write(cg.get_buffer(v['path']))
finally:save('canonical-short-sourceguard.close.json',cg.close())
cpraw=raw(O/'canonical-short-snapshot/checkpoint.json');cp=json.loads(cpraw)
check('canonical-revision',cp['revision']==362 and cp['expected_previous_revision']==361)
check('other-revisions',read(O/'canonical-short-snapshot/path_ownership.json')['revision']==168 and read(O/'canonical-short-snapshot/commands.json')['revision']==39)
facts=read(N/'checkpoint.execution.facts.current.json');resume=read(N/'RESUME.r362.original.json');handoff=read(N/'handoff.json');mf=read(N/'manifest.json');proof=read(N/'canonical_pair.actual.json')
for p in sorted(N.iterdir()):
 if p.is_file():add(pin(p),'CP362 namespace');copy(p,'CP362')
for v in members(mf['members']):add(v,'CP362 original manifest')
check('CP362-handoff-pin',pin(N/'handoff.json')['sha256']=='600d512305b356e7580be057b8e8fb6432ea1761315eaaaf987ed8406e302f7a' and pin(N/'handoff.json')['bytes']==1150)
check('CP362-resume-pin',pin(N/'RESUME.r362.original.json')['sha256']=='394678d2ac90024af8e619d566a3add94571ce5dbcf023a7f7ec47a340ef3985' and pin(N/'RESUME.r362.original.json')['bytes']==2125)
walk(handoff,'handoff')
manifestnames={Path(v['path']).name for v in members(mf['members'])}
extra={p.name for p in N.iterdir() if p.is_file()}-manifestnames
check('manifest-cutoff-exclusions',extra=={'manifest.json','handoff.json','postwrite-original-tool-io.json','failure-origin.877.json'},sorted(extra))
tx=Path(proof['transaction']['transaction_journal'])
for p in sorted(tx.iterdir()):
 if p.is_file():add(pin(p),'transaction');copy(p,'transaction')
oldraw=raw(tx/'0.before.json');old=json.loads(oldraw)
check('CP361-preimage-pin',hashlib.sha256(oldraw).hexdigest()=='27b6680899a8ba49b0f76fa6c7c917a80edecd0bcf68059de4dfc8da91088845' and len(oldraw)==4147646)
check('atomic-after-matches-current',raw(tx/'0.after.proposed.json')==cpraw)
check('ownership-before-after-identical',raw(tx/'1.before.json')==raw(tx/'1.after.proposed.json')==raw(O/'canonical-short-snapshot/path_ownership.json'))
for r in facts['reviews']:
 for k in ('handoff_ref','manifest_ref'):
  add(r[k],r['name']+'/'+k);p=Path(r[k]['path']);copy(p,'reviews/'+p.parent.parent.name+'/'+k)
 for v in members(read(r['manifest_ref']['path'])['members']):add(v,r['name']+'/member')
for d in facts['diagnostics']:add(d['origin_ref'],'diagnostic/'+str(d['ordinal']));copy(d['origin_ref']['path'],'diagnostics/'+str(d['ordinal']))
for v in facts['actual_refs']:add(v,'actual-ref');copy(v['path'],'actual/'+Path(v['path']).parent.name)
add(facts['trace_bundle_ref'],'TRACE9');copy(facts['trace_bundle_ref']['path'],'TRACE9')
add(pin(gp),'guard')
guard=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(refs.values()))
try:
 def slices(data):
  s=data.decode();p=s.index('"failure_counters"');p=s.index('[',p)+1;dec=json.JSONDecoder();out=[]
  while True:
   while s[p].isspace() or s[p]==',':p+=1
   if s[p]==']':break
   start=p;_,p=dec.raw_decode(s,p);out.append(s[start:p].encode())
  return out
 olds,news=slices(oldraw),slices(cpraw)
 check('old845-semantic-identical',len(old['failure_counters'])==845 and cp['failure_counters'][:845]==old['failure_counters'])
 check('old845-raw-record-bytes-identical',len(olds)==845 and news[:845]==olds)
 check('count-873',len(cp['failure_counters'])==len(news)==873)
 pending=facts['diagnostics'];new=cp['failure_counters'][845:]
 check('ordinals-848-through875-once',[d['ordinal'] for d in pending]==list(range(848,876)) and [x['original_payload']['observed_ordinal'] for x in new]==list(range(848,876)))
 check('unique-origin-keys',len({x['origin_key'] for x in cp['failure_counters']})==873)
 qualified=[]
 for d,c in zip(pending,new):
  n=d['ordinal'];p=c['original_payload'];ref=d['origin_ref'];origin=read(ref['path'])
  check(str(n)+':original-binding',c['evidence_ref']==ref==p['immutable_origin_ref'] and c['origin_key']==hashlib.sha256((ref['sha256']+'#'+str(n)).encode()).hexdigest())
  check(str(n)+':once-no-reset',c['counted_once'] is True and c['counter_reset'] is False and c['automatic_retry'] is False)
  check(str(n)+':exit-qualification',all(p[k]==d[k] for k in ('actual_outer_exit','actual_python_exit','actual_native_exit')))
  qualified.append({'ordinal':n,'origin':ref,'outer':p['actual_outer_exit'],'python':p['actual_python_exit'],'native':p['actual_native_exit'],'origin_keys':list(origin)})
 trace=read(facts['trace_bundle_ref']['path']);calls=trace['calls'];check('TRACE9-call-count',trace['failed_call_count']==len(calls)==9)
 q=[]
 for n in range(859,868):
  d=pending[n-848];origin=read(d['origin_ref']['path']);idx=origin['original_index'];q.append(idx)
  check(str(n)+':TRACE-exact-call',origin['original_payload']==calls[idx-1] and calls[idx-1]['index']==idx and origin['immutable_bundle_ref']==facts['trace_bundle_ref'])
  check(str(n)+':TRACE-exits',origin['actual_outer_exit']==(None if idx==1 else 1) and origin['actual_python_exit'] is None and origin['actual_native_exit'] is None)
 check('TRACE9-distinct-indices',q==list(range(1,10)))
 for n,ex in {873:(None,None,None),874:(1,1,None),875:(1,None,None),868:(1,1,1),871:(1,1,1)}.items():
  d=pending[n-848];check(str(n)+':required-exits',tuple(d[k] for k in ('actual_outer_exit','actual_python_exit','actual_native_exit'))==ex)
 w=cp['work_in_progress'];wf=facts['work_in_progress'];branch=w['mu_sdk_r362']
 check('facts-installed-exact',all(w[k]==v for k,v in wf.items()))
 check('cutoff-fields',w['r362_registered_failure_count']==resume['registered_failures']==873 and w['r362_highest_observed_diagnostic_ordinal']==resume['highest_observed_diagnostic_ordinal']==875 and w['r362_next_failure_ordinal_at_cutoff']==resume['next_failure_ordinal_at_cutoff']==876)
 check('old-WIP-preserved-except-explicit-updates',all(k in w and w[k]==v for k,v in old['work_in_progress'].items() if k not in wf))
 check('formal-entire-status-unchanged',cp['current_effective_formal_status']==old['current_effective_formal_status'] and cp['current_effective_formal_status']['formal_cases_accepted']==0 and len(cp['current_effective_formal_status']['historical_parent_registrations'])==6)
 check('accepted-lists-unchanged',all(cp[k]==old[k] for k in ('accepted_steps','parent_tasks_accepted','substeps','evidence_index','artifacts','blocked_steps')))
 check('formal-and-parent-boundaries',all(branch[k]==v for k,v in {'historical_accepted_parents':6,'current_formal_accepted':0,'required_parents':22,'required_formal':42,'overall_completion':False,'counter_reset':False}.items()))
 check('paid-business-open',all(branch[k]==v for k,v in {'original_trial_once_consumed':True,'original_trial_clock_expired':True,'original_trial_business_open':True,'original_trial_financial_closed':False,'original_trial_provider_requests':None,'global_provider_requests':None}.items()))
 check('T8-no-native-promotion',branch['T8_compile_and_28_boundary_units_limited_accepted'] and branch['T8_native_positive_failed_868'] and branch['T8_whole_sql_87_tables_equal_before'] and branch['T8_specific_fixture_released'] and branch['T8_owned_jobs_closed'] and branch['T8_broker_held_exit'] is None and branch['T8_broker_source_reported_exit']==1)
 compile_actual=read(facts['actual_refs'][0]['path']);check('T8-28-units',compile_actual['unit_pass_count']==28 and compile_actual['unit_fail_count']==compile_actual['unit_skip_count']==0 and compile_actual['all_owned_jobs_closed'] and not compile_actual['native_migration_cases_executed'])
 native_review=next(r for r in facts['reviews'] if 'native_temp_actual_failure_independent_review_codex' in r['name']);nr=read(native_review['handoff_ref']['path']);review=read(nr['review_json_ref']['path'])
 check('native-review-limited-failure',nr['decision']=='LIMITED_FAILED_EXECUTION_WHOLE_SQL_SPECIFIC_RELEASE_ACCEPTED' and nr['historical_failed_execution_whole_SQL_specific_release_accepted'] and not nr['native_positive_accepted'] and all(c['passed'] for c in review['checks']) and review['broker_python_exit_independently_held'] is None and review['broker_python_exit_source_reported']==1)
 t9=branch['T9_target_actual'];check('T9-limited-real-failure',t9['parents']==54 and t9['pass_terminals']==152 and t9['fail_terminals']==5 and t9['skip_terminals']==0 and not t9['full_domain_acceptance'] and not t9['formal_acceptance'] and t9['child_pass_terminal_count']==10 and t9['child_jsonl_event_count']==68 and not t9['exact_child_native_pid_and_exit_observed'])
 check('BR4-source-only',branch['broker4_source']=='SOURCE_ACCEPTED_PENDING_ROOT_BOUNDARY_ACTUAL' and branch['broker4_17_pure_tests']=='NOT_RUN' and resume['broker4_pure17_actual_done'] is False)
 check('historical-upgrade-still-blocked',branch['historical20_ordinary_upgrade']=='BLOCKED_NO_MATCHING_PROGRAM_BACKUP_ISOLATED_RESTORE_UPGRADE')
 old_qualified=[c for c in old['failure_counters'] if re.search(r'(?:[./_-])(?:833|835)(?:[./_-])',json.dumps(c,ensure_ascii=False))]
 save('old833-835-preserved-records.json',old_qualified)
 preserved_qualification={k:v for k,v in old['work_in_progress'].items() if '361' in k}
 save('CP361-preserved-qualifications.json',preserved_qualification)
 summary={'status':'CP362_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY' if not issues else 'CP362_CONSISTENCY_FINDINGS','checkpoint_revision':362,'cutoff':875,'registered_failures':873,'next_failure_ordinal_at_cutoff':876,'old845_raw_and_semantic_equal':news[:845]==olds and cp['failure_counters'][:845]==old['failure_counters'],'new_ordinals':list(range(848,876)),'diagnostic_qualifications':qualified,'TRACE9_distinct_bundle_indices':q,'source_manifest':pin(N/'manifest.json'),'manifest_cutoff_extras':sorted(extra),'T8_native_failed':True,'T8_broker_held_exit':None,'T8_broker_source_reported_exit':1,'T9_limited_actual':t9,'BR4_pure17_at_cutoff':'NOT_RUN','formal_progress':'0/42','historical_parents':'6/22','paid_business':'OPEN_ONCE_CONSUMED_CLOCK_EXPIRED_PROVIDER_REQUESTS_NULL','product_acceptance':False,'formal_acceptance':False,'reviewer_execution':'read-only files; no Go/SQL/native/model execution','canonical_write':False,'new_review_diagnostics':[880],'new_review_diagnostics_registered_in_CP362':False,'refs_verified':len(refs),'checks':checks,'issue_count':len(issues),'issues':issues,'canonical_short_guard_closed_before_extended_review':True}
 save('report.json',summary);save('input-refs.json',list(refs.values()));save('original-copy-index.json',copies)
finally:save('sourceguard.close.json',guard.close())
closing=[pin(v['path']) for v in canonical];save('canonical.closing-pins.json',closing)
print(json.dumps({'status':summary['status'],'issue_count':len(issues),'issues':issues,'refs':len(refs),'checks':len(checks),'canonical_pins_still_match':closing==canonical,'manifest_pin':pin(N/'manifest.json'),'old_qualified_count':len(old_qualified)},ensure_ascii=False))
