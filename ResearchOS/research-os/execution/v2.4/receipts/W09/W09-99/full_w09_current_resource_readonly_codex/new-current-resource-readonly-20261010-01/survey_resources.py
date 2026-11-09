from pathlib import Path
import datetime, json, os, shutil, types
p=Path(__file__).with_name('review_support.py');m=types.ModuleType('support');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)

fixed=[
 m.exact_ref(m.N/'HDF.json','0b3000c9ca1d46a1df980535dfb0e57c55798d7eb5d7819c09dcab792168a447',8412),
 m.exact_ref(m.N/'MF.json','71f2c09424c3fa75153a173fa5208c3d91e510390c500826e5f258855cd0f4c3',4399),
 m.exact_ref(m.A/'HDF.json','265747939bf081d26225de5937e8cca7e5787d23320c1d59b7f4ff6c004f1a92',6617),
 m.exact_ref(m.A/'MF.json','540bc3571c13b77c5333ea71b7461aca20de12dbf2d0cb5879a7299dc253c003',13386),
 m.exact_ref(m.R/'internal/domain/retrieval_test.go','1254f8c7524638cac6bee492fe7d4daf685722250779f86e36e97b0e7a9f1141',32352),
 m.exact_ref(m.S/'legacy-fixture-Main-adoption-20261010-01/adoption.closed.json','b5e6b7236691409bce4fe4dae79849b4ccf46f2906f05feda11dc65764e1dbc7',1978),
 m.exact_ref(m.T/'HDF.json','8736edead7afeab47341b2f8e484c469e4c24aa86c31244f03109afc96152233',8373),
 m.exact_ref(m.T/'MF.json','aaa891e9e4b0d176cf1221b80ea107d91b2f177c697398061ba001dc5093297a',22740),
 m.exact_ref(m.T/'decision.json','1ae11e296dec248d1044ba247960c5ffd2a34a74abfe840bd9ef7f9cae607e5d',18883),
]
# MF is the bounded published member inventory. This does not recursively follow foreign historic refs.
for index in (1,3):
    item=fixed[index];assert m.pin(item['path'])==item
    fixed.extend(json.loads(Path(item['path']).read_bytes())['members'])
actual_dirs={
 'W09-G01':m.N/'actual-W09-G01-4fd62ca511684dc39d62c5571d8ddaf5/producer',
 'W09-G02':m.N/'actual-W09-G02-28aa266121d24ad2988d578df02d23a4/producer',
 'A06':m.N/'actual-A06-ba9a185f551c4d4caf123da7eafb4245/producer',
}
for directory in actual_dirs.values():
    fixed.extend([m.pin(directory/'validation.closed.json'),m.pin(directory/'actual-compiler-input-inventory.json')])
for path in (m.R/'ops/ci/retrieval.py',m.R/'ops/ci/w09_evidence_closure.py',m.R/'execution/v2.4/formal_profile_w09.py'):
    fixed.append(m.pin(path))
unique={ref['path']:ref for ref in fixed}
g=m.guard()
try:
    g.acquire(list(unique.values()))
    read=lambda path:g.get_buffer(str(path))
    choice=json.loads(read(m.N/'source.choice.json'))
    blueprint=json.loads(read(m.N/'compiler-source-blueprint.json'))
    nmanifest=json.loads(read(m.N/'MF.json'));amanifest=json.loads(read(m.A/'MF.json'))
    sources={}
    funcs={
      m.N/'full_w09_runtime.source.py':['exact_path','choice','validate_authority','build_environment','read_inputs','compiler_inventory','validate_packet','stage','verify_directories'],
      m.N/'runtime-overrides.source.py':['choice','validate_authority','validate_packet','verify_directories'],
      m.N/'full_w09_launcher.source.py':['run','main'],
      m.A/'register_w09_adoption.source.py':['path_checked','own_source','model','scope_audits','finalize'],
      m.A/'adoption_core.source.py':['make_native_scopes','canonical_changes','validate_own_review'],
      m.R/'ops/ci/w09_evidence_closure.py':['verify_mode'],
      m.R/'ops/ci/retrieval.py':['selected','run'],
    }
    for path,names in funcs.items():sources[str(path)]={'ref':unique[str(path)],'functions':m.code_evidence(read(path),path,names)}
    metadata={}
    for selector,directory in actual_dirs.items():
        validation=json.loads(read(directory/'validation.closed.json'))
        inventory=json.loads(read(directory/'actual-compiler-input-inventory.json'))
        metadata[selector]={'validation_ref':unique[str(directory/'validation.closed.json')],'inventory_ref':unique[str(directory/'actual-compiler-input-inventory.json')],'validation_shape':m.shape(validation),'inventory_shape':m.shape(inventory),'inventory_field_shapes':{k:m.shape(v) for k,v in inventory.items()}}
    survey={'schema':'researchos.w09-current-resource-readonly-survey.v1','reviewer':m.ACTOR,'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'held_input_refs':list(unique.values()),'Source_member_counts':{'NF3':len(nmanifest['members']),'AD2':len(amanifest['members'])},'choice':choice,'blueprint_shape':m.shape(blueprint),'blueprint_field_shapes':{k:m.shape(v) for k,v in blueprint.items()},'actual_closed_resources':metadata,'code_evidence':sources,'disk_usage':{drive:dict(zip(('total','used','free'),shutil.disk_usage(drive))) for drive in ('C:/','D:/')},'current_Main_test_ref':unique[str(m.R/'internal/domain/retrieval_test.go')],'Main_adoption_ref':unique[str(m.S/'legacy-fixture-Main-adoption-20261010-01/adoption.closed.json')],'Main_adoption':json.loads(read(m.S/'legacy-fixture-Main-adoption-20261010-01/adoption.closed.json')),'product_calls':0,'live_Canon_refs_held':False,'old_Source_controls_rerun':False,'old_3905_resources_rechecked':False,'execution_grant':False,'formal_acceptance':False}
    survey_ref=m.write('resource-survey.json',survey)
finally:
    closed=g.close();closed_ref=m.write('resource-survey.guard.closed.json',closed)
    assert closed['closed'] is True and closed['retained_handles_count']==0 and not closed['errors']
diagnostic=m.capture('95e86c',1,None,1135)
print(json.dumps({'survey_ref':survey_ref,'guard_ref':closed_ref,'guard_closed':True,'retained_handles_count':0,'input_count':len(unique),'Source_member_counts':survey['Source_member_counts'],'disk_usage':survey['disk_usage'],'choice_keys':list(choice),'blueprint_keys':list(blueprint),'inventory_keys':{k:v['inventory_shape']['keys'] for k,v in metadata.items()},'original1135':diagnostic,'product_calls':0},ensure_ascii=False),flush=True)
