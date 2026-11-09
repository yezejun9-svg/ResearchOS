"""Only finish retained truncation/1111 observations after the accepted prefix."""
from pathlib import Path
import ast,json,hashlib,types,traceback,re
N=Path(__file__).resolve().parent
source=N/'review_binding.py';tree=ast.parse(source.read_bytes());start=next(i for i,x in enumerate(tree.body) if isinstance(x,ast.Try))
env={'__file__':str(source)};exec(compile(ast.Module(body=tree.body[:start],type_ignores=[]),str(source),'exec'),env)
pin,doc,save,need,exact,clean,original,actual_exec=[env[x] for x in ['pin','doc','save','need','exact','clean','original','actual_exec']]
S=env['S'];B=env['B'];key=env['key'];checks=env['checks']
prefixref=pin(N/'review-checks.json');need(prefixref['sha256']=='c9b3ae0ad0bb2b0e0a0c4cadc58cf8fede459e9d31ede5b6231e9b4777513a9f','EXACT_PASSED_PREFIX')
prefix=doc(prefixref);clean(doc(prefix['guard_ref']))
need(prefix['check_count']==300 and prefix['held_ref_count']==148 and prefix['error']['message']=='UNIQUE_ACTUAL_TOOL_RESULT_ce7571','EXACT_PENDING_TAIL_BOUNDARY')
need(all(x in prefix['checks'] for x in ['ACTUAL_FINAL_REFS_EXACTLY_BOUND','TYPED_136_ALL_REQUESTED_VERIFIED','TRUE_FINAL_PAYLOAD_OBSERVATION_BINDING_CAUSAL_ORDER','PROGRAMME_ONLY_QUALIFICATION_BOUNDARY','EXACT_FULL_THREE_LINE_CAPTURE_initial_truncated_observer']),'REUSE_PASSED_ROOT_BINDING_PREFIX')
boundref=pin(S/'old21.programme.qualification.bound.actual.root.json');bound=doc(boundref);payload=doc(bound['payload_ref'])
trref=pin(S/'old21.programme.initial-observer.API-truncation.root.json');truncation=doc(trref)
dbref=pin(S/'original1111.actual-host.binding.root.json');db=doc(dbref)
guardref=dict(path=str(B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404)
held=[pin(__file__),pin(source),prefixref,prefix['guard_ref'],boundref,bound['payload_ref'],trref,dbref,db['original_capture_ref'],guardref]+truncation['original_pair_refs']
gm=types.ModuleType('root_binding_tail_guard');exec(compile(exact(guardref),guardref['path'],'exec'),gm.__dict__);guard=gm.SourceReadGuard(per_file_cap=16*1024*1024,total_cap=64*1024*1024)
error=None;result={}
try:
 guard.acquire(held)
 rows=[json.loads(x) for x in exact(truncation['original_pair_refs'][0]).splitlines()]
 texts=[x['text'] for x in rows[2]['payload']['output'] if x.get('type')=='input_text']
 need(len(texts)==2 and texts[0].startswith('Script completed\n'),'ORIGINAL_TRUNCATED_API_BLOCK_SHAPE')
 text=texts[1]
 need(text.startswith('Warning: truncated output (original token count: 10910)\nTotal output lines: 2\n\nOLD21_CAPTURE_OPERATION:OLD21_PROGRAMME_QUALIFICATION_BINDING\n'),'REAL_API_TRUNCATION_WARNING_AND_OPERATION')
 visible=re.search(r'\{"chunk_id":"ce7571","wall_time_seconds":([0-9.]+),"exit_code":(\d+),',text)
 need(visible is not None and visible.group(2)=='0','VISIBLE_ORIGINAL_CE7571_OUTER_ZERO')
 need('ROOT_SOURCE_PYTHON_EXIT=0\\r\\n"}' in text and 'tokens truncated' in text,'VISIBLE_ORIGINAL_PYTHON_ZERO_AND_ACTUAL_OMISSION')
 need(truncation['original_API_response_truncated'] is True and truncation['original_full_process_stdout_asserted'] is False and truncation['original_stdout_reconstructed'] is False,'NO_RECONSTRUCTED_OR_COMPLETE_INITIAL_STDOUT_CLAIM')
 need(truncation['compact_completed_observer_binding_ref']==bound['root_issuance_binding_ref'] and truncation['Go_or_Native_rerun'] is False,'COMPLETE_COMPACT_OBSERVER_IS_SEPARATE_EVIDENCE')
 rows,binding=original(dbref,db['original_capture_ref'],'original1111');actual=actual_exec(rows,'0f1ac2')
 need(type(actual['exit_code']) is int and actual['exit_code']==1 and actual['output'].splitlines()[-1]=='ROOT_SOURCE_PYTHON_EXIT=1','ORIGINAL_1111_OUTER_PYTHON_ONE_PRESERVED')
 need('AssertionError' in actual['output'] and 'capture(AUDIT,106045' in actual['output'],'ORIGINAL_1111_CAPTURE_ASSERTION_RETAINED')
 result=dict(verdict='ROOT_PROGRAMME_BINDING_VERIFIED',bound_qualification_ref=boundref,prior_programme_review_refs=bound['review_refs'],Root_issuance_binding_ref=bound['root_issuance_binding_ref'],actual_final_binding_ref=bound['independent_peer_delivery_binding_ref'],program_refs=bound['program_refs'],provenance_ref=bound['provenance_ref'],source_commit=bound['source_commit'],source_tree=bound['source_tree'],source_schema_version=21,original_requested_refs=136,Root_source_guard_entries=133,actual_compact_outer_exit=0,actual_compact_python_exit=0,initial_truncated_observer_ref=trref,original1111_binding_ref=dbref,reused_prefix_ref=prefixref,reused_prefix_checks=300,previous_controls_rerun=False,reused_task83_checks=dict(prefix=31132,continuation=465,authority=192),original_review_failure_ordinal=1114,new_product_runs=0,new_Go_runs=0,new_Native_runs=0,new_SQL_runs=0,new_model_requests=0,live_canonical_read_or_held=False,Canon_written=False,formal_acceptance=False,parent_acceptance=False,execution_grant=False)
except BaseException as e:error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
finally:closed=guard.close()
gr=save('tail-Source-guard.closed.json',closed);clean(closed)
out=save('tail-review-checks.json',dict(status='ROOT_PROGRAMME_BINDING_VERIFIED' if error is None else 'CHANGES_REQUIRED',check_count=len(checks),checks=checks,error=error,result=result,prefix_ref=prefixref,prefix_rerun=False,guard_ref=gr,held_ref_count=len(held),formal_acceptance=False,parent_acceptance=False,execution_grant=False))
print(json.dumps(dict(report_ref=out,guard_ref=gr,check_count=len(checks),error=error),ensure_ascii=False),flush=True);print('ROOT_SOURCE_PYTHON_EXIT='+str(1 if error else 0),flush=True);raise SystemExit(1 if error else 0)
