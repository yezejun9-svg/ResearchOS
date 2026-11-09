import ast,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)));assert ok,name
proof=json.loads((N/'caller-complete-inverse.json').read_bytes())
for p in proof['callers']:
 old=Path(p['original_ref']['path']).read_bytes();new=Path(p['candidate_ref']['path']).read_bytes();inverse=new.decode()
 for change in reversed(p['substitutions']):inverse=inverse.replace(change['new'],change['old'])
 label=Path(p['candidate_ref']['path']).name
 check(label+'_full_byte_inverse',inverse.encode()==old)
 check(label+'_full_AST_inverse',ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False))
 of={n.name:n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)}
 check(label+'_function_set_identical',set(of)==set(nf))
 for name,node in of.items():check(label+'_function_AST_unchanged_'+name,ast.dump(node,include_attributes=False)==ast.dump(nf[name],include_attributes=False))
 for oldpath,newpath in proof['allowed_path_replacements']:check(label+'_no_old_fixed_path_'+oldpath,oldpath not in new.decode())
 check(label+'_no_dispatcher_or_consumer_addition','dispatch.py' not in new.decode() and 'run_c19_consumers' not in new.decode())
choice=json.loads((N/'source.integration.choice.json').read_bytes());delta=json.loads((N/'choice-complete-inverse.json').read_bytes());old=json.loads(Path(delta['original_ref']['path']).read_bytes())
check('exact_six_Source_target_set',set(choice['sources'])==set(old['sources']) and len(choice['sources'])==6)
for rel,v in old['sources'].items():
 if rel!='ops/ci/w09_evidence_closure.py':check('unchanged_source_'+rel,choice['sources'][rel]==v)
check('v7_closure_exact',choice['sources']['ops/ci/w09_evidence_closure.py']['sha256']=='1cc37f4fec48d2e2bae39db3c1f8d1da9fdfe6bd788a44396ea0a8b877be6777' and choice['sources']['ops/ci/w09_evidence_closure.py']['bytes']==42716)
for k in ('selected_tests','expected_native_ids','expected_formal_ids','canonical_input_binding','native_producer_runs','formal_consumers','main_adopted','execution_grant','exact_six_targets'):check('unchanged_choice_'+k,choice[k]==old[k])
check('test_order_Chain_then_Explicit',choice['selected_tests']==['TestW09C19ChainInvalidation','TestW09C19ExplicitOriginAndUnknown'])
check('one_producer_no_formal_consumers',choice['native_producer_runs']==1 and choice['formal_consumers']=='NOT_RUN_REGISTRY_UNBOUND')
for key,path in choice['fixed_paths'].items():check('future_path_absent_'+key,not Path(path).exists())
check('five_unique_fixed_roots',len(set(choice['fixed_paths'].values()))==5)
check('CP365_OW169_history_only',choice['provenance_original']['checkpoint_revision']==365 and choice['provenance_original']['ownership_revision']==169 and 'NOT_ACTUAL_BINDING' in choice['provenance_original']['purpose'])
historical_paths={v['path'] for v in choice['provenance_original']['canonical_refs']}
check('live_canonical_not_static_current_refs',not any(v['path'] in historical_paths for v in choice['original_input_refs']))
inverse=json.loads(json.dumps(choice))
for d in delta['semantic_deltas']:
 if d['old_present']:inverse[d['key']]=d['old']
 else:del inverse[d['key']]
check('choice_full_semantic_inverse',inverse==old)
check('choice_full_byte_inverse',''.join(line for op in delta['opcodes'] for line in op['old_lines']).encode()==Path(delta['original_ref']['path']).read_bytes())
contract=json.loads((N/'root-calling-contract.json').read_bytes())
check('prepare_exact_six_explicit_args',len(contract['preparation_argv'])==13 and contract['prepare_parameter_count']==6)
check('producer_exact_ten_explicit_args',len(contract['producer_caller_argv'])==17 and contract['producer_parameter_count']==10)
check('both_calls_isolated_no_site_no_bytecode_utf8',all(v[1:6]==['-I','-S','-B','-X','utf8'] for v in (contract['preparation_argv'],contract['producer_caller_argv'])))
check('choice_exact_call_pin',contract['producer_caller_argv'][7:9]==[pin(N/'source.integration.choice.json')['sha256'],str(pin(N/'source.integration.choice.json')['bytes'])])
check('same_dynamic_vector_and_no_future_revision_guess',contract['same_vector_in_both_invocations'] is True and contract['expected_future_checkpoint'] is None)
check('no_Go_format_or_actual_compiler_claim',contract['Go_formatting_executed'] is False and contract['compiler_input_inventory_actual']=='NOT_RUN_THIS_SOURCE_TASK')
for filename in ('source-input-pins.original.json','choice-input-pins.original.json'):
 for ref in json.loads((N/filename).read_bytes()):check('unchanged_input_'+ref['path'],pin(ref['path'])==ref)
result=dict(status='PASS',count=len(checks),checks=checks,scope='PURE_STATIC_BYTE_AND_AST_INVERSE_ONLY',actual_caller_executed=False,actual_Git_Go_SQL_native_API_model=False,canonical_read_as_current_or_written=False)
assert not (N/'HDF.json').exists() and not (N/'MF.json').exists()
with (N/'source-controls.json').open('wb') as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(status='PASS',check_count=len(checks),controls_ref=pin(N/'source-controls.json'))))
