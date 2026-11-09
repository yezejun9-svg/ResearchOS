from pathlib import Path
import ast,hashlib,json,types
N=Path(__file__).parent
def pin(p):
 b=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 p=N/n
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
known=json.loads((N/'known-inputs.json').read_bytes())
refs=[v for v in known.values() if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}]
for r in refs:assert pin(r['path'])==r
gref=known['guard_source'];g=types.ModuleType('recipe_guard')
raw=Path(gref['path']).read_bytes();exec(compile(raw,gref['path'],'exec'),g.__dict__)
guard=g.SourceReadGuard();guard.acquire(refs)
def read(key):return guard.get_buffer(known[key]['path']).decode('utf-8')
try:
 bridge=ast.parse(read('bridge'));profile=ast.parse(read('main_profile'));review=ast.parse(read('review_prep_v3'));role=ast.parse(read('role_builder'))
 contract=json.loads(read('review_contract_v3'))
 documents={}
 def describe(tree,name):
  fn=next(x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name==name)
  keys=sorted({x.slice.value for x in ast.walk(fn) if isinstance(x,ast.Subscript) and isinstance(x.value,ast.Name) and x.value.id=='req' and isinstance(x.slice,ast.Constant) and isinstance(x.slice.value,str)})
  return dict(name=name,start=fn.lineno,end=fn.end_lineno,direct_request_keys=keys)
 observations={'bridge': [describe(bridge,n) for n in ['root_request','source_review','registered','consume','roles','publish_registration','seed','assemble','main']],
  'Main':[describe(profile,n) for n in ['_role_audit','_role_registry','_vector','_dispatches','_global']],
  'review':[describe(review,n) for n in ['validate_bundle','review_actual']]}
 save('source-observations.json',dict(schema='researchos.w09-br8-recipe-static-source-observations.v1',
  extraction='AST only; no reviewed module import or function call',functions=observations))
 templates={p.relative_to(N).as_posix():json.loads(p.read_bytes()) for p in sorted(N.rglob('*.template.json'))}
 expected={
 'extras/consume.template.json':{'proposal_ref','context_seed_ref','c19_policy','isolated_environment'},
 'extras/roles.template.json':{'proposal_ref','c19_policy','role_registry_input_ref','role_protection_refs'},
 'extras/publish-registration.template.json':{'publication_ref','expected_previous_registry_ref'},
 'extras/seed-after-role-registration.template.json':{'context_input_ref'},
 'extras/assemble.template.json':{'proposal_ref','context_seed_ref','consumer_result_ref','c19_policy','plan_ref','code_revision','dirty','package_manifest_ref','refusal_evidence_refs'}}
 for name,fields in expected.items():assert set(templates[name])==fields
 common=templates['common-request.template.json']
 source_review=json.loads(read('bridge_source_review'))
 for key in ('bridge_source_ref','consumer_launcher_ref','source_hdf_ref','source_mf_ref'):
  other='source_ref' if key=='bridge_source_ref' else key
  assert common[key]==source_review[other]
 for name in ('grant_ref','grant_audit','source_review_audit','output_directory','created_at','expires_at','actor_id','Root_thread_id'):
  assert common[name] is None
 assert set(templates['role-builder-request.template.json'])=={'schema','actor_id','preparation_id','proposal_ref','context_seed_ref','scope_observation_audit_ref','assembly_owner_observation_audit_ref','mode01_observation_audit_ref'}
 for name,value in templates['role-builder-request.template.json'].items():
  if name!='schema':assert value is None
 glob=templates['future-global-refs.template.json'];order=['run_receipt','version_manifest','command_receipt','assertion_results']
 assert list(glob)==['C19','A06']
 for value in glob.values():assert list(value)==order and all(v is None for v in value.values())
 stage=next(x for x in bridge.body if isinstance(x,ast.FunctionDef) and x.name=='assemble')
 stage_calls=[(x.lineno,x.func.attr) for x in ast.walk(stage) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in ('_role_registry','_dispatches','_global')]
 assert [x[1] for x in sorted(stage_calls)]==['_role_registry','_dispatches','_global']
 publish=next(x for x in bridge.body if isinstance(x,ast.FunctionDef) and x.name=='publish_registration')
 assert any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='transact' for x in ast.walk(publish))
 transaction=ast.parse(read('transaction_source'))
 update=next(x for x in transaction.body if isinstance(x,ast.FunctionDef) and x.name=='update_pair')
 returns=[x.value for x in ast.walk(update) if isinstance(x,ast.Return) and isinstance(x.value,ast.Dict)]
 assert any({k.value for k in item.keys}=={'checkpoint_ref','ownership_ref','transaction_journal'} for item in returns)
 # Record the newly identified static self-pin cycle, without invoking review.
 rv=read('review_prep_v3')
 for text in ["resources = bundle['resource_refs']","required = [input_ref,","held is not None and same_ref(held, ref, guard_module._canonical)"]:
  assert text in rv
 raw_export=json.loads(read('existing_A06_02_export'))
 assert raw_export['assertion_id']=='A06-02'
 rawref=templates['extras/assemble.template.json']['refusal_evidence_refs'][0]
 assert rawref['sha256']==known['existing_A06_02_export']['sha256'] and rawref['locator']=={'json_pointer':'/actual'}
 # Only preserve prior references from the existing preparation contract.
 save('reused-evidence-references.json',dict(schema='researchos.w09-br8-recipe-existing-evidence.v1',
  source_contract_ref=known['review_contract_v3'],existing_NF6_qualification_ref=contract['existing_NF6_qualification_ref'],
  existing_six_Mode_refs=contract['existing_six_Mode_refs'],old_validation_replayed=False,new_Mode_issued=False,
  A06_02_existing_ref=rawref,actual_pointer_value_observed=raw_export['actual'],
  observation_not_a_new_execution=True))
 checks=save('metadata-checks.json',dict(schema='researchos.w09-br8-recipe-metadata-checks.v1',
  status='METADATA_ONLY_CONSISTENCY_CHECKS_PASSED_WITH_OPEN_REVIEW_CONTRACT_GAP',
  exact_extras_key_sets=True,common_Source_refs_exact_original_spelling=True,
  future_values_not_fabricated=True,eight_GLOBAL_ref_slots_null_in_correct_order=True,
  static_assembler_gate_order=sorted(stage_calls),TP_result_keys_verified_static=True,
  self_pin_source_cycle_observed=True,existing_A06_02_pointer_observed=True,
  BR8_role_builder_Main_review_modules_imported=0,reviewed_function_calls=0,Root_stages=0,Main_calls=0,
  Native_Go_SQL_TP_dispatcher_model_calls=0,old_tests_replayed=False))
finally:
 closed=guard.close();guard_ref=save('SourceGuard.closed.json',closed)
assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
for r in refs:assert pin(r['path'])==r
mf=save('MF.json',dict(schema='researchos.w09-br8-postactivation-recipe-manifest.v1',
 members=[pin(p) for p in sorted(N.rglob('*')) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal-tool-io.json')],
 exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
hdf=save('HDF.json',dict(schema='researchos.w09-br8-postactivation-recipe-handoff.v1',
 actor_id='codex:/root/attach_restore_independent_review',
 status='METADATA_RECIPE_READY_WITH_LATER_REVIEW_INPUT_SELF_PIN_GAP',
 manifest_ref=mf,guide_ref=pin(N/'FIELD_GUIDE.md'),known_inputs_ref=pin(N/'known-inputs.json'),
 templates=[pin(N/n) for n in templates],result_selectors_ref=pin(N/'result-selectors.json'),
 open_boundaries_ref=pin(N/'OPEN_BOUNDARIES.json'),source_observations_ref=pin(N/'source-observations.json'),
 reused_evidence_refs=pin(N/'reused-evidence-references.json'),metadata_checks_ref=checks,SourceGuard_ref=guard_ref,
 current_Source8_review_reused=known['bridge_source_review'],new_acceptance_issued=False,
 Root_Main_Canon_registry_writes=0,Root_stages_Main_calls_Native_Go_SQL_TP_dispatcher_model_calls=0,
 old_successful_checks_replayed=False,future_actual_inputs=None,execution_grant=False,formal_acceptance=False,STOP=True))
for r in json.loads((N/'MF.json').read_bytes())['members']:assert pin(r['path'])==r
print(json.dumps(dict(HDF_ref=hdf,MF_ref=mf,guide_ref=pin(N/'FIELD_GUIDE.md'),
 gap_ref=pin(N/'OPEN_BOUNDARIES.json'),status='METADATA_RECIPE_SEALED_NO_RUNTIME'),ensure_ascii=False))

