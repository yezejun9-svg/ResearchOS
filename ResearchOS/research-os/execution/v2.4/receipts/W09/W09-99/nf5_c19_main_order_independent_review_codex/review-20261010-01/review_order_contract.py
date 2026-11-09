"""Source-only advisory. Candidate bytes stay in memory; Main is never written."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,difflib,hashlib,json,types,traceback,sys
R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99';N=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-05';D=Path(__file__).resolve().parent
p=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py';s=types.ModuleType('review_support');s.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),s.__dict__);s.D=D
paths={'retrieval':R/'ops/ci/retrieval.py','router':R/'ops/ci/w09_formal_router.py','closure':R/'ops/ci/w09_evidence_closure.py','profile':R/'execution/v2.4/formal_profile_w09.py','NF5_runtime':N/'full_w09_runtime.source.py','NF5_choice':N/'source.choice.json','NF5_HDF':N/'HDF.json','NF5_MF':N/'MF.json'}
refs={k:s.pin(v) for k,v in paths.items()};g=s.guard();checks=[];failure=None;details={};patch_ref=None
def check(name,ok,evidence=None):
 checks.append(dict(name=name,passed=bool(ok),evidence=evidence))
 if not ok:raise ValueError(name)
def parsed(name):return ast.parse(g.get_buffer(str(paths[name])),filename=str(paths[name]))
def only_node(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
def excerpt(name,fn):
 tree=parsed(name);n=only_node(tree,fn);lines=g.get_buffer(str(paths[name])).decode('utf-8').splitlines()
 return dict(module_ref=refs[name],function=fn,line=n.lineno,end_line=n.end_lineno,source='\n'.join(lines[n.lineno-1:n.end_lineno]))
try:
 g.acquire(list(refs.values()))
 choice=json.loads(g.get_buffer(str(paths['NF5_choice'])));source=g.get_buffer(str(paths['retrieval']));tree=parsed('retrieval')
 assignments=[copy.deepcopy(n) for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'TESTS','GROUPS','CASES','SOURCES'}]
 values={};exec(compile(ast.fix_missing_locations(ast.Module(body=assignments,type_ignores=[])),'<pure-selector-constants>','exec'),values)
 TESTS,GROUPS,CASES=values['TESTS'],values['GROUPS'],values['CASES']
 runtime_tree=parsed('router');router={}
 for n in runtime_tree.body:
  if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'SELECTED','NATIVE','FORMAL'}:router[n.targets[0].id]=ast.literal_eval(n.value)
 old=b'selected = GROUPS[check] if check else list(TESTS)'
 new=b'selected = GROUPS[check] if check else [name for name in CASES[case] if name in TESTS]'
 check('unique_minimal_case_only_source_expression',source.count(old)==1 and source.count(new)==0)
 candidate=source.replace(old,new,1);candidate_tree=ast.parse(candidate,filename='<advisory-only-retrieval>')
 check('exact_whole_byte_inverse_current_Main',candidate.replace(new,old,1)==source,dict(original_bytes=len(source),candidate_in_memory_bytes=len(candidate),original_sha256=hashlib.sha256(source).hexdigest(),candidate_in_memory_sha256=hashlib.sha256(candidate).hexdigest(),actual_candidate_Source_file_written=False))
 first=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='selected' for t in n.targets) and isinstance(n.value,ast.IfExp))
 changed=next(n for n in ast.walk(candidate_tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='selected' for t in n.targets) and isinstance(n.value,ast.IfExp))
 saved=copy.deepcopy(changed.value.orelse);changed.value.orelse=copy.deepcopy(first.value.orelse)
 check('only_case_only_initial_selection_AST_changed',ast.dump(tree,include_attributes=False)==ast.dump(candidate_tree,include_attributes=False),dict(line=first.lineno,old_expression=ast.unparse(first.value),proposed_expression=ast.unparse(saved)))
 original_function='def selection(check, case):\n    selected = GROUPS[check] if check else list(TESTS)\n    if case:\n        selected = [name for name in selected if name in CASES[case]]\n    return selected\n'
 proposed_function=original_function.replace(old.decode(),new.decode(),1)
 a=dict(TESTS=TESTS,GROUPS=GROUPS,CASES=CASES);b=dict(a);exec(compile(original_function,'<original-source-condition>','exec'),a);exec(compile(proposed_function,'<proposed-source-condition>','exec'),b)
 route_results=[]
 for route,expected in router['SELECTED'].items():
  previous=a['selection'](route[2],route[3]);proposed=b['selection'](route[2],route[3]);route_results.append(dict(route=list(route),previous=previous,proposed=proposed,formal_expected=list(expected),changed=previous!=proposed))
  check('proposed_exact_Main_router_'+':'.join(route),proposed==list(expected))
 check('only_two_current_C19_routes_change_order',len(route_results)==6 and [r['route'] for r in route_results if r['changed']]==[['test.research.fixture','W09','','C19'],['test.retrieval','W09','','C19']])
 exhaustive=[]
 for check_id in ('',*GROUPS):
  for case_id in ('',*CASES):
   if not check_id and not case_id:continue
   before=a['selection'](check_id,case_id);after=b['selection'](check_id,case_id);exhaustive.append(dict(check_id=check_id,case_id=case_id,previous=before,proposed=after))
 check('all_check_branches_and_A06_case_only_identical',all(r['previous']==r['proposed'] for r in exhaustive if r['check_id'] or r['case_id']=='A06'),dict(bounded_valid_combinations=len(exhaustive),actual_products_called=0))
 check('case_only_stable_CASES_intersection_no_foreign_tests',all(b['selection']('',case)==[n for n in CASES[case] if n in TESTS] and len(b['selection']('',case))==len(set(b['selection']('',case))) for case in CASES))
 nf5_results=[]
 for selector,variant in choice['selectors'].items():
  c={**choice['common'],**variant};ids=c['selector'];names=b['selection'](ids['check_id'],ids['case_id']);packages=sorted({TESTS[n][0] for n in names});suffix=['test','-count=1','-json','-run','^(?:'+'|'.join(names)+')$',*packages]
  nf5_results.append(dict(selector=selector,selected=names,expected=c['selected_tests'],computed_suffix=suffix,frozen_expected_suffix=c['go_test_argv_suffix']))
  check('proposed_exact_nf5_frozen_argv_'+selector,names==c['selected_tests'] and suffix==c['go_test_argv_suffix'])
 check('retrieval_is_fixed_complete_Source21_member',len(choice['common']['source21'])==21 and next(r for r in choice['common']['source21'] if r['path']==str(paths['retrieval']))==refs['retrieval'] and 'ops/ci/retrieval.py' in values['SOURCES'])
 closure_evidence=excerpt('closure','verify_native');nf5_evidence=excerpt('NF5_runtime','validate_packet');profile_evidence=excerpt('profile','_source21')
 check('existing_exact_argv_and_current_source_gates_preserved','ACTUAL_INVOCATION_MISMATCH' in closure_evidence['source'] and 'CURRENT_SOURCE_CLOSURE_MISMATCH' in closure_evidence['source'] and 'EXACT_NATIVE_ARGV' in nf5_evidence['source'] and 'EXACT_SOURCE21' in nf5_evidence['source'])
 patch=''.join(difflib.unified_diff(source.decode('utf-8').splitlines(keepends=True),candidate.decode('utf-8').splitlines(keepends=True),fromfile='a/ops/ci/retrieval.py',tofile='b/ops/ci/retrieval.py'))
 patch_path=D/'advisory.case-order.diff'
 with patch_path.open('xb') as f:f.write(patch.encode('utf-8'))
 patch_ref=s.pin(patch_path)
 details=dict(input_refs=refs,actual_Main_retrieval_source_ref=refs['retrieval'],source_choice_common_keys=list(choice['common']),Source_choice_executor_sources_field_present='executor_sources' in choice['common'],candidate_diff_ref=patch_ref,candidate_in_memory_sha256=hashlib.sha256(candidate).hexdigest(),candidate_in_memory_bytes=len(candidate),only_business_change='case-only selects in CASES[case] order intersected with TESTS; subsequent original intersection retained',all_current_routes=route_results,bounded_selector_properties=exhaustive,nf5_expected_argv_properties=nf5_results,gate_source_excerpts=[closure_evidence,nf5_evidence,profile_evidence],current_Source21_refs=choice['common']['source21'],conclusion='RECOMMENDED_MINIMAL_FIX_PENDING_ACTUAL_SOURCE_PUBLICATION_AND_ROOT_ADOPTION',all_four_native_must_be_fresh_after_Main_adoption=True,six_CM40_consumers_must_bind_new_current_reports=True,old_three_passes_retained_as_historical_only_after_adoption=True,current_Main_not_modified=True,formal_acceptance=False,execution_grant=False)
except BaseException as e:failure=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
finally:
 closed=g.close();guard_ref=s.write('main-order.guard.closed.json',closed)
 report=s.write('main-order.properties.json',dict(schema='researchos.w09-c19-main-order-independent-source-advisory.v1',review_actor='/root/full_w09_source_review',canonical_review_author='codex:/root/full_w09_source_review',created_utc=datetime.now(timezone.utc).isoformat(),checks=checks,successful_check_count=sum(x['passed'] for x in checks),failure=failure,guard_ref=guard_ref,details=details,original_failure_ordinals_retained=[1158,1159],Main_Canon_NF5_Scope_written=False,actual_Go_Native_SQL_model_TP_calls=0,Mode_qualified=False,execution_grant=False,formal_acceptance=False))
print(json.dumps(dict(report_ref=report,guard_ref=guard_ref,candidate_diff_ref=patch_ref,successful_checks=sum(x['passed'] for x in checks),failure=failure,closed=closed['closed'],retained_handles_count=closed['retained_handles_count'],formal_acceptance=False,execution_grant=False),ensure_ascii=False))
if failure or not closed['closed'] or closed['retained_handles_count'] or closed['errors']:sys.exit(1)
