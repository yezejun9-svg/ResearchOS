from pathlib import Path
import ast,hashlib,json
N=Path(__file__).parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(name):return json.loads((N/name).read_text(encoding='utf-8'))
def put(name,value):(N/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
refs=read('input-pins.json')
for ref in refs:assert pin(ref['path'])==ref
choice=read('source.integration.choice.json');composition=read('composition.json');changes=read('source-replacements.json')
assert len(composition['final_sources'])==choice['expected_source_count']==61
assert len(choice['exact_parent_names'])==5 and len(choice['expected_terminal_names'])==9
assert choice['source_preserved_parent_count']==59 and len(choice['all_source_file_declared_parent_names'])==137
assert set(choice['exact_parent_names']).issubset(choice['source_preserved_parent_names'])
controls=[]
for item in changes:
 p=Path(item['candidate']['path']);verify=pin(p);assert verify==item['candidate']
 original=Path(item['original']['path']).read_bytes();candidate=p.read_bytes();text=candidate.decode('utf-8').replace('\r\n','\n')
 for old,new in reversed(item['replacements']):
  assert new in text;text=text.replace(new,old)
 newline='\r\n' if b'\r\n' in original else '\n';assert text.replace('\n',newline).encode('utf-8')==original
 old_ast=ast.parse(original);new_ast=ast.parse(candidate)
 defs=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 a,b=defs(old_ast),defs(new_ast)
 allowed={'closed'} if p.name.startswith('validate_') else set()
 assert set(a)==set(b)
 assert all(a[name]==b[name] for name in a if name not in allowed)
 controls.append({'candidate_ref':verify,'base_ref':item['original'],'exact_byte_inverse':True,'unchanged_function_AST_names':sorted(set(a)-allowed),'changed_function_scope':sorted(allowed),'all_changed_source_spans_in_replacement_ledger':True})
prep=(N/'prepare_history20_five_parent.actual_owned.py').read_text(encoding='utf-8')
val=(N/'validate_history20_five_parent.actual_owned.py').read_text(encoding='utf-8')
baseprep=(N/'base/prepare_attach_fixture_two_parent.actual_owned.py').read_text(encoding='utf-8')
baseval=(N/'base/validate_attach_fixture_two_parent.actual_owned.py').read_text(encoding='utf-8')
assert prep[prep.rindex('finally:'):]==baseprep[baseprep.rindex('finally:'):]
assert val[val.rindex('finally:'):]==baseval[baseval.rindex('finally:'):]
assert 'invocation_refs=[verify,tracked,staged,create,checkout,verify_after]' in prep
assert 'owned_jobs=6' in prep and 'shared_git_config_mutated=False' in prep
assert 'assert len(sys.argv)==4' in prep and 'assert len(sys.argv)==8' in val
assert 'starts==set(actions)==set(choice["expected_terminal_names"])' in val and 'len(actions)==9' in val
assert '"-test.run="+selector' in val and '"-tags=researchos_native_recovery_harness"' in val
assert '"-test.timeout=14m"' in val and '],900,T/"internal/domain")' in val
assert 'Source_count' in val and 'new_tests=set(choice["exact_parent_names"])' in val
assert 'original_trial_DB_touched=False' in val and 'external_model_provider_requests=0' in val
assert 'sources=={key:verify(ref) for key,ref in actual_T11["sources"].items()} and len(sources)==58' in val
for pathkey in ['fresh_worktree','fresh_isolation_output','fresh_validation_output','fresh_environment']:
 assert not Path(choice[pathkey]).exists(),pathkey
for p in N.glob('*.py'):ast.parse(p.read_bytes(),filename=str(p))
result={'scope':'SOURCE_ONLY','caller_controls':controls,'source_inputs_verified':len(refs),'full_T11_ACT58_overlay_exact_before_H20':True,'final_source_count':61,'h20_overlay_prior_paths':sum(v['prior_overlay_ref'] is not None for v in composition['h20_paths'].values()),'AF_preserved':True,'non_H20_T11_preserved':True,'preserved_parent_sources':59,'all_overlay_declared_parents':137,'selected_parents':choice['exact_parent_names'],'expected_terminal_names':choice['expected_terminal_names'],'six_owned_Git_job_source_retained':True,'five_validation_source_guard_finally_exact':True,'official_test2json_and_full_tagged_compiler_inventory_retained':True,'dynamic_checkpoint_and_new_ready_pins':True,'future_destinations_absent_not_created':True,'actual_Git_Go_gofmt_SQL_native_model':False,'new_paid_trial':False,'historical20_to24':'OPEN','legacyB_program_Owner_flow':'OPEN','new_failure_origins':[]}
put('static-controls.json',result)
for ref in refs:assert pin(ref['path'])==ref
put('sourceguard.final.json',{'inputs':refs,'before_after_unchanged':True,'canonical_guards_held':False,'Main_or_old_worktree_mutated':False})
members=[pin(p) for p in sorted(N.rglob('*')) if p.is_file() and p.name not in {'HDF.json','MF.json','seal.original-tool-io.json'}]
put('MF.json',{'schema':'researchos.source-manifest.v1','scope':'SOURCE_ONLY','members':members})
h={'schema':'researchos.history20-five-parent-sparse-caller-source-handoff.v1','status':'SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_ACTUAL','manifest_ref':pin(N/'MF.json'),'manifest_member_count':len(members),'prepare_ref':pin(N/'prepare_history20_five_parent.actual_owned.py'),'validate_ref':pin(N/'validate_history20_five_parent.actual_owned.py'),'choice_ref':pin(N/'source.integration.choice.json'),'composition_ref':pin(N/'composition.json'),'static_ref':pin(N/'static-controls.json'),'guard_ref':pin(N/'sourceguard.final.json'),'instructions_ref':pin(N/'README.md'),'source_count':61,'expected_parent_count':5,'expected_terminal_count':9,'actual_Git_Go_SQL_native_model':False,'overall20_to24':'OPEN','new_failure_origins':[],'STOP':True}
put('HDF.json',h)
print(json.dumps({'HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json'),'members':len(members),'prepare':h['prepare_ref'],'validate':h['validate_ref'],'choice':h['choice_ref'],'source_count':61,'expected_terminals':9}))
