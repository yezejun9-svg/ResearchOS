import sys
sys.dont_write_bytecode=True
import json,hashlib,types,collections,re
from pathlib import Path
O=Path(__file__).resolve().parent;R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
N=B/'sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r362-native-failed-closed-current-target-results'
def raw(p):return Path(p).read_bytes()
def read(p):return json.loads(raw(p))
def pin(p):
 p=Path(p).resolve();b=raw(p);return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,o):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def verify(v):
 a=pin(v['path']);assert a['sha256']==v['sha256'].removeprefix('sha256:') and a['bytes']==v['bytes'];return a
facts=read(N/'checkpoint.execution.facts.current.json');prior=read(O/'attempt2/report.json')
assert prior['issues']==[{'check':'T8-28-units','passed':False,'detail':None}]
compile_ref=facts['actual_refs'][0];actual=read(compile_ref['path']);detail=read(actual['unit_detail_ref']['path']);refs=[verify(compile_ref),verify(actual['unit_detail_ref']),verify(detail['original_jsonl_ref']),pin(O/'attempt2/report.json')]
for v in actual['invocation_refs']:
 refs.append(verify(v));j=read(v['path'])
 for k in ('stdout_ref','stderr_ref'):refs.append(verify(j[k]))
qualified=read(O/'attempt2/old833-835-preserved-records.json')
for q in qualified:refs.append(verify(q['original_payload']['evidence_accuracy_qualification_ref']))
refs=list({r['path'].casefold():r for r in refs}.values())
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py';code=raw(gp)
assert hashlib.sha256(code).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
m=types.ModuleType('correction_guard');m.__file__=str(gp);exec(compile(code,str(gp),'exec'),m.__dict__)
g=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire(refs)
try:
 for i,v in enumerate(refs):
  p=O/'correction-inputs'/str(i)/Path(v['path']).name;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(g.get_buffer(v['path']))
 ev=[json.loads(l) for l in g.get_buffer(detail['original_jsonl_ref']['path']).decode().splitlines()]
 runs=collections.Counter(e['Test'] for e in ev if e['Action']=='run' and e.get('Test'));terms=collections.defaultdict(list)
 for e in ev:
  if e.get('Test') and e['Action'] in ('pass','fail','skip'):terms[e['Test']].append(e['Action'])
 assert set(runs)==set(terms) and all(v==1 for v in runs.values()) and all(v==['pass'] for v in terms.values())
 actions={n:v[0] for n,v in terms.items()};parents=[n for n in actions if '/' not in n];leaves=[n for n in actions if '/' in n]
 assert len(parents)==detail['parent_count']==2 and len(leaves)==detail['leaf_count']==28 and len(actions)==actual['unit_pass_count']==30
 assert actual['unit_fail_count']==actual['unit_skip_count']==actual['native_migration_cases_executed']==0 and actual['all_owned_jobs_closed']
 assert actions==actual['unit_actions']==detail['actions'] and ev[-1]['Action']=='pass' and 'Test' not in ev[-1]
 jobs=[]
 for v in actual['invocation_refs']:
  j=read(v['path']);res=j['result'];cleanup=res['job_cleanup']
  assert res['actual_exit']==0 and not res['timed_out'] and not res['error']
  assert all(cleanup[k] for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')) and cleanup['active_processes_last_observed']==0 and not cleanup['errors']
  jobs.append({'ref':v,'actual_exit':0,'closed':True})
 qmap={q['original_payload']['observed_ordinal']:q['original_payload'] for q in qualified}
 assert qmap[833]['actual_python_exit'] is None and qmap[833]['source_reported_previous_actual_python_exit']==qmap[833]['inferred_python_exit']==1 and qmap[833]['inferred_exits_are_not_directly_observed']
 assert qmap[835]['effective_native_rehearsal_creation_time_100ns_decimal']=='134359787476336016' and qmap[835]['effective_native_harness_creation_time_100ns_decimal']=='134359787460741284' and qmap[835]['original_origin_FILETIME_fields_source_reported_inexact']
 exit_evidence=[]
 for d in facts['diagnostics']:
  obj=read(d['origin_ref']['path']);observations=[]
  def visit(v,path):
   if isinstance(v,dict):
    for k,x in v.items():
     if 'exit' in k.lower() and not isinstance(x,(dict,list)):observations.append({'field':path+'/'+k,'value':x})
     visit(x,path+'/'+k)
   elif isinstance(v,list):
    for i,x in enumerate(v):visit(x,path+'/'+str(i))
   elif isinstance(v,str):
    for match in re.finditer(r'(?:ROOT_PYTHON_EXIT|REVIEW_PYTHON_EXIT|PYTHON_EXIT|ACTUAL_PYTHON_EXIT)\s*[:=]\s*(?:-?\d+|null|NULL)',v):observations.append({'field':path,'marker':match.group()})
  visit(obj,'origin');exit_evidence.append({'ordinal':d['ordinal'],'declared':[d[k] for k in ('actual_outer_exit','actual_python_exit','actual_native_exit')],'original_exit_fields_and_markers':observations})
 save('diagnostic-exit-observations.json',exit_evidence)
 correction={'status':'CORRECTED_REVIEWER_LEAF_TERMINAL_COUNT_NO_CANONICAL_FINDING','supersedes_only':{'report':pin(O/'attempt2/report.json'),'check':'T8-28-units','failure_ordinal':884},'parent_count':len(parents),'leaf_count':len(leaves),'terminal_count':len(actions),'raw_line_count':len(ev),'actions':actions,'owned_jobs':jobs,'original833_Python_NULL_qualification_preserved':True,'original835_exact_decimal_FILETIME_qualification_preserved':True,'test_rerun':False,'new_formal_acceptance':False,'refs':refs}
 save('count-correction.report.json',correction)
 final={'schema':'researchos.independent-checkpoint-consistency-review.v1','status':'CP362_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY','base_review':pin(O/'attempt2/report.json'),'only_base_false_finding_corrected_by':pin(O/'count-correction.report.json'),'remaining_canonical_findings':0,'checkpoint_revision':362,'checkpoint_cutoff':875,'registered_failures':873,'highest_observed_diagnostic_ordinal':875,'next_failure_ordinal_at_cutoff':876,'new_registry_ordinals':list(range(848,876)),'old845_raw_and_semantic_equal':True,'TRACE9_distinct_original_calls':9,'T8_compile_boundary_leaves':28,'T8_compile_boundary_parents':2,'T8_compile_boundary_terminals':30,'T8_native_failure868_preserved':True,'T8_whole87_sql_inspection_specific_release_closed':True,'T8_broker_held_exit':None,'T8_broker_source_reported_exit':1,'T9_raw':{'pass':152,'fail':5,'skip':0,'suite_failed':True,'actual_review_limited_accepted':True,'child_native_pid_exit':None},'BR4_source_approved_but_pure17_at_cutoff':'NOT_RUN','formal':'0/42','historical_parent':'6/22','original_paid_business':'OPEN_ONCE_CONSUMED_EXPIRED_PROVIDER_NULL','new_review_failure_ordinals':[880,883,884],'review_failure_registry':'post-CP362; reserved by Root for later checkpoint','cutoff_manifest_exclusions':['postwrite-original-tool-io.json','failure-origin.877.json'],'counter_reset':False,'new_model_call':False,'product_authority':'NONE','formal_acceptance':False,'Main_canonical_Source_writes':False,'Go_SQL_native_model_execution':False}
 save('final-review.json',final)
finally:save('correction.sourceguard.close.json',g.close())
print(json.dumps({'status':final['status'],'remaining_canonical_findings':0,'T8_leaf_parent_terminal':[28,2,30],'guard_closed':True,'new_review_failures':[880,883,884]},ensure_ascii=False))
