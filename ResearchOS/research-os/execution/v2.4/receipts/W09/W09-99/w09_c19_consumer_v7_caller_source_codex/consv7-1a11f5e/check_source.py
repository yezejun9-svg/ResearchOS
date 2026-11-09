import ast,copy,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)));assert ok,name
proof=json.loads((N/'caller.allowed-substitutions.json').read_bytes());old=Path(proof['original_ref']['path']).read_bytes();new=Path(proof['candidate_ref']['path']).read_bytes();back=new.decode()
for change in reversed(proof['substitutions']):back=back.replace(change['new'],change['old'])
check('caller_full_byte_inverse',back.encode()==old)
check('caller_full_AST_inverse',ast.dump(ast.parse(back))==ast.dump(ast.parse(old)))
of={n.name:n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)}
check('exact_same_function_set',set(of)==set(nf))
for name,node in of.items():
 if name!='main':check('unchanged_function_'+name,ast.dump(node)==ast.dump(nf[name]))
check('exact_nine_allowed_substitutions',len(proof['substitutions'])==9)
for a in proof['substitutions']:check('allowed_literal_present_once_'+a['new'][:90],a['occurrences']==1 and new.decode().count(a['new'])==1)
for name in ('caller.complete-byte-inverse.json','consumer-contract.complete-inverse.json','choice.complete-inverse.json','calling-contract.complete-inverse.json'):
 value=json.loads((N/name).read_bytes());check('complete_inverse_flags_'+name,value['whole_old_byte_inverse'] and value['whole_new_byte_forward'])
choice=json.loads((N/'source.choice.json').read_bytes());contract=json.loads((N/'calling-contract.json').read_bytes());derived=json.loads(Path(choice['contract_ref']['path']).read_bytes())
oldchoice=json.loads((Path(proof['original_ref']['path']).parent/'source.choice.json').read_bytes())
for relative,v in oldchoice['six_source_refs'].items():
 if relative!='ops/ci/w09_evidence_closure.py':check('same_other_Source_'+relative,choice['six_source_refs'][relative]==v)
check('closure_v7_only',choice['six_source_refs']['ops/ci/w09_evidence_closure.py']['sha256']=='1cc37f4fec48d2e2bae39db3c1f8d1da9fdfe6bd788a44396ea0a8b877be6777')
check('historical_canonical_provenance_preserved',choice['canonical_at_source_preparation']==oldchoice['canonical_at_source_preparation'])
historical_paths={v['path'] for v in choice['canonical_at_source_preparation']}
check('no_static_current_canonical_refs',not any(v['path'] in historical_paths for v in choice['input_refs']))
check('exact_Source21_roster',len(derived['source_roster'])==21 and derived['source_roster']==json.loads(Path(oldchoice['contract_ref']['path']).read_bytes())['source_roster'])
constants={}
for n in ast.parse(new).body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('CHOICE_SHA','CHOICE_BYTES','ROUTES','EXPECTED_NATIVE','EXPECTED_FORMAL','SELECTED'):constants[n.targets[0].id]=ast.literal_eval(n.value)
check('exact_choice_constants',(constants['CHOICE_SHA'],constants['CHOICE_BYTES'])==(pin(N/'source.choice.json')['sha256'],pin(N/'source.choice.json')['bytes']))
check('two_routes_order_unchanged',constants['ROUTES']==(('test.research.fixture','W09','','C19'),('test.retrieval','W09','','C19')))
check('three_formal_five_native_ids_unchanged',constants['EXPECTED_FORMAL']==['C19-01','C19-02','C19-03'] and constants['EXPECTED_NATIVE']==['C19-01','C19-02','C19-03','C19-04','C19-05'])
check('explicit_request_three_args',len(contract['Root_argv'])==10 and contract['Root_argv'][-3:]==['REQUEST_ABSOLUTE_PATH','REQUEST_BARE_SHA256','REQUEST_BYTES'])
check('caller_ref_exact',contract['source_caller_ref']==pin(N/'run_c19_consumers.actual_owned.py') and contract['scope_fixed_values']['source_caller_ref']==contract['source_caller_ref'])
check('same_future_candidate_contract',contract['scope_fixed_values']['candidate_root']==derived['consumer_root'] and 'w09c19v7-1a11f30' in derived['consumer_root'])
check('source_status_not_ready',contract['status']=='SOURCE_PREPARED_PENDING_NEW_PRODUCER_QUALIFICATION_AND_ROOT_SCOPE' and contract['actual_ready'] is False and contract['do_not_execute'] is True)
check('new_actual_receipts_required',contract['new_producer_report_tool_mode_actual_review_and_Root_scope_required'] is True and contract['actual_root_request_or_scope_generated'] is False and contract['actual_mode_decisions_generated'] is False)
for p in choice['fixed_future_paths']:check('future_consumer_path_absent_'+p,not Path(p).exists())
check('mode_and_scope_schema_unchanged',contract['request_schema']=='researchos.w09-c19-component-consumer-request.v1' and contract['scope_schema']=='researchos.root-w09-c19-component-consumer-scope.v1')
check('no_new_vector_field',contract['canonical_vector_contract']['exact_fields']==['schema','checkpoint_revision','refs'])
# Evaluate only the revised pure predicates, using synthetic in-memory bytes.
main=nf['main'];trybody=next(n for n in main.body if isinstance(n,ast.Try)).body
schema_stmt=next(n for n in trybody if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and n.value.args and isinstance(n.value.args[-1],ast.Constant) and n.value.args[-1].value=='CANONICAL_VECTOR_EXPLICIT_REVISION')
revision_stmt=next(n for n in trybody if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and n.value.args and isinstance(n.value.args[-1],ast.Constant) and n.value.args[-1].value=='EXACT_VECTOR_BOUND_CANONICAL_REVISIONS')
schema_code=compile(ast.Expression(schema_stmt.value.args[0]),'<source-schema-predicate>','eval');revision_code=compile(ast.Expression(revision_stmt.value.args[0]),'<source-revision-predicate>','eval')
base=dict(schema='researchos.w09-c19-canonical-input-vector.v1',checkpoint_revision=366,refs=[])
check('synthetic_CP366_OW170_accepted',eval(schema_code,{},dict(vector=base)) and eval(revision_code,{},dict(vector=base,checkpoint_revision=366,ownership_revision=170)))
check('synthetic_dynamic_CP367_OW171_accepted',eval(schema_code,{},dict(vector=dict(base,checkpoint_revision=367))) and eval(revision_code,{},dict(vector=dict(base,checkpoint_revision=367),checkpoint_revision=367,ownership_revision=171)))
for label,v in [('zero',dict(base,checkpoint_revision=0)),('bool',dict(base,checkpoint_revision=True)),('text',dict(base,checkpoint_revision='366')),('extra_OW_field',dict(base,ownership_revision=170)),('wrong_schema',dict(base,schema='other')),('missing_revision',{k:v for k,v in base.items() if k!='checkpoint_revision'})]:check('reject_vector_'+label,not eval(schema_code,{},dict(vector=v)))
for label,cp,ow in [('checkpoint_mismatch',365,170),('checkpoint_bool',True,170),('ownership_zero',366,0),('ownership_bool',366,True),('ownership_string',366,'170')]:check('reject_canonical_'+label,not eval(revision_code,{},dict(vector=base,checkpoint_revision=cp,ownership_revision=ow)))
for v in json.loads((N/'source-input-pins.original.json').read_bytes()):check('unchanged_source_input_'+v['path'],pin(v['path'])==v)
result=dict(status='PASS',count=len(checks),checks=checks,scope='STATIC_FULL_INVERSE_AND_SYNTHETIC_PURE_VECTOR_PREDICATES_ONLY',actual_caller_or_guard_job_executed=False,actual_Git_Go_SQL_API_model=False,current_canonical_read_or_written=False,new_original_failures=[])
with (N/'source-controls.json').open('xb') as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(status='PASS',count=len(checks),controls_ref=pin(N/'source-controls.json'))))
