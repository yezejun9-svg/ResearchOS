import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,importlib.util,traceback
P=pathlib.Path;O=P(__file__).resolve().parent
def pin(p):
 b=P(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
g=None;code=0
try:
 refs=json.loads((O/'input-pins.json').read_bytes())
 for p in [O/'review.json',O/'guard.final.json',O/'supplemental_review.py']:refs.append(pin(p))
 G=next(P(v['path']) for v in refs if P(v['path']).name=='source_read_guard.py')
 s=importlib.util.spec_from_file_location('cp364_supp_guard',G);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 g=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire(refs)
 def obj(p):return json.loads(g.get_buffer(str(p)))
 old=obj(O/'review.json');entries=[]
 def ck(n,v,detail):entries.append(dict(check=n,passed=bool(v),detail=detail))
 expected={'writer-helper-and-runtime-held','review-component-authority:N12_ACTUAL_C12_SOURCE_COMPONENT_ACCEPTED_NO_NATIVE_AUTHORITY','review-component-authority:CTL4_N12_SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL'}
 ck('only-three-schema-assumptions-reconsidered',{x['check'] for x in old['remaining_findings']}==expected,'Original 480 passing checks and original findings are immutable.')
 for label,dirname in [('N12_ACTUAL_C12_SOURCE_COMPONENT_ACCEPTED_NO_NATIVE_AUTHORITY','native_n12actual_c12source_independent_review_codex'),('CTL4_N12_SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL','native_ctl4_n12_independent_review_codex')]:
  path=next(P(v['path']) for v in refs if dirname in v['path'] and P(v['path']).name=='HDF.json');h=obj(path)
  ck('review-component-authority:'+label,h.get('formal_Owner_whole9_acceptance') is False and h.get('full_native_retention_qualified') is False and h.get('Main_canonical_write') is False,dict(schema=h['schema'],authority_fields=['formal_Owner_whole9_acceptance','full_native_retention_qualified','Main_canonical_write'],reason='HDF schema declares the required false authority via these explicit fields, not a generic formal_acceptance field.'))
 guardpath=next(P(v['path']) for v in refs if 'checkpoint-r364-component-actuals-source-ready' in v['path'] and P(v['path']).name=='source_guard.cleanup.actual.json');wg=obj(guardpath);names={P(v['path']).name for v in wg['entries']}
 required={'source_read_guard.py','canonical_transactions.py','python.exe','checkpoint_component_actuals.atomic.py','checkpoint.execution.facts.json','_ctypes.pyd','_hashlib.pyd','_uuid.pyd'}
 ck('writer-helper-and-declared-runtime-held',required.issubset(names) and wg['closed'] is True and wg['retained_handles_count']==0 and not wg['errors'] and all(v['verified'] and v['closed'] and v['final_path_match'] for v in wg['entries']),dict(required=sorted(required),guard_entries=len(wg['entries']),reason='Original writer enumerates sys.modules __file__/__cached__; actual extension modules are .pyd. No claim of exhaustive Windows loader DLL inventory.'))
 oldguard=obj(O/'guard.final.json');ck('original-review-guard-closed',oldguard['closed'] is True and oldguard['retained_handles_count']==0 and not oldguard['errors'],'Original attempt held canonical read-only and closed all handles.')
 closure=g.close();save('supplemental.guard.final.json',closure)
 ck('supplemental-guard-closed',closure['closed'] is True and closure['retained_handles_count']==0 and not closure['errors'],'All rechecked inputs released.')
 accepted=all(v['passed'] for v in entries)
 result=dict(schema='researchos.independent-cp364-consistency-final.v1',decision='CP364_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY' if accepted else 'REQUEST_CHANGES',original_review_ref=pin(O/'review.json'),original_passed_checks=480,original_checks=483,superseded_schema_assumptions=sorted(expected),supplemental_checks=entries,remaining_findings=[v for v in entries if not v['passed']],registered_failures=900,highest_registered_ordinal=902,next_at_cutoff=903,later_pending=[903,904],live_next_as_reported_by_Root=905,review_execution_failures=[904],formal_acceptance=False,canonical_writes=False,reviewer_is_not_checkpoint_author=True,authority='CHECKPOINT_CONSISTENCY_ONLY',limitations=['Writer runtime proof covers declared sys.modules artifacts and executable; no exhaustive Windows loader DLL claim.','900/901 inferred rg2 is not actual captured rg exit.','902 evidence file is qualified summary and original chat locator.','H20 followup REQUEST_CHANGES and C12 preparation are later than checkpoint cutoff.'],all_guards_closed=closure['closed'],STOP=True)
 save('review.final.json',result)
 print(json.dumps(dict(decision=result['decision'],supplemental_checks=len(entries),passed=sum(v['passed'] for v in entries),remaining_findings=result['remaining_findings'],guarded_input_count=len(refs),all_guards_closed=closure['closed'])))
except Exception:traceback.print_exc();code=1
finally:
 if g is not None:
  c=g.close()
  if not (O/'supplemental.guard.final.json').exists():save('supplemental.guard.final.json',c)
 print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)
