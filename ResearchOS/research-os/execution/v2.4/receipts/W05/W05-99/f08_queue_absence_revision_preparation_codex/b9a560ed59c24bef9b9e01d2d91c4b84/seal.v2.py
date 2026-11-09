from pathlib import Path
import ast, hashlib, json, re
HERE=Path(__file__).resolve().parent
def ref(p):
    b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,d):
    b=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with (HERE/name).open('xb') as f:f.write(b)
    return ref(HERE/name)
for p in [HERE/'assemble.py',HERE/'seal.py',HERE/'seal.v2.py',HERE/'prepare-seal-v2.py']:ast.parse(p.read_text(encoding='utf-8'))
before=json.loads((HERE/'inputs.before.json').read_text(encoding='utf-8'))['files']
for r in before:
    a=ref(Path(r['path']));assert a['sha256']==r['sha256'] and a['bytes']==r['bytes'],r['path']
source=HERE/'client_cancel_finalization.go.proposed.txt'
text=source.read_text(encoding='utf-8')
locations={}
for name in ['noSessionQueueHistory','queueAdmission','emptyQueueFinal','bootstrapAdmission','deriveInitialOrigin','evaluate']:
    for n,line in enumerate(text.splitlines(),1):
        if line.startswith('func') and re.search(r'\b'+re.escape(name)+r'\s*\(',line): locations[name]={'line':n,'source_ref':ref(source)}
assert len(locations)==6
origins=[ref(HERE/('failure-origin.'+chunk+'.json')) for chunk in ['5b7ca2','a1e3bf','3d077c','86f70b']]
base=HERE.parents[1]/'f08_proof_evaluator_implementation_preparation_codex'/'b6b765563c9640bd8a2b9e54f643352c'
review=HERE.parents[1]/'f08_proof_evaluator_independent_source_review_codex'/'0a0cb85df5dc4e6981dea5fd6a316971'
inherit=[r for r in before if 'failure' in Path(r['path']).name or 'erratum' in Path(r['path']).name]
diagnostics=write('tool-diagnostics.json',{
 'kind':'VISIBLE_TOOL_FIELDS_RECORDED_NOT_ORIGINAL_NATIVE_STREAMS',
 'events':[
 {'chunk':'2c6e75','actual_outer_exit':0,'actual_native_exit':None,'kind':'PowerShell read'},
 {'chunk':'5b7ca2','actual_outer_exit':1,'actual_native_exit':None,'origin_ref':origins[0]},
 {'chunk':'95821e','actual_outer_exit':0,'actual_native_exit':None,'kind':'inventory'},
 {'chunk':'026ee7','actual_outer_exit':0,'actual_native_exit':None,'kind':'PowerShell read'},
 {'chunk':'13742f','actual_outer_exit':0,'actual_native_exit':None,'kind':'PowerShell read'},
 {'chunk':'22aa38','actual_outer_exit':0,'actual_native_exit':None,'kind':'read and search'},
 {'chunk':'5b59d8','actual_outer_exit':0,'actual_native_exit':None,'kind':'Python metadata displayed through PowerShell without explicit native exit bridge'},
 {'chunk':'dc2797','actual_outer_exit':0,'actual_native_python_exit':0,'kind':'exclusive receipt namespace creation; explicit exit LASTEXITCODE'},
 {'chunk':'7d3f8f','actual_outer_exit':0,'actual_native_exit':None,'kind':'PowerShell read'},
 {'chunk':'a1e3bf','actual_outer_exit':1,'actual_native_python_exit':1,'origin_ref':origins[1]},
 {'chunk':'99dc72','actual_outer_exit':0,'actual_native_python_exit':0,'kind':'changed metadata selection, explicit exit LASTEXITCODE'},
 {'chunk':'7dfdc1','actual_outer_exit':0,'actual_native_python_exit':0,'kind':'metadata shape read'},
 {'chunk':'ab0ed1','actual_outer_exit':0,'actual_native_python_exit':0,'kind':'Python AST only'},
 {'chunk':'3ea5b7','actual_outer_exit':0,'actual_native_python_exit':0,'kind':'receipt assembly/hash/inverse diff, target not run'},
 {'chunk':'3d6eba','actual_outer_exit':0,'actual_native_exit':None,'kind':'read emitted metadata'}
 ],'apply_patch_responses':'{}; independent native/outer process exits not returned and not inferred',
 'new_failure_origin_refs':origins,'prior_failure_and_erratum_refs':inherit,'counter_mutations':0,'supplemental_failures':['3d077c Python1/outer1','86f70b Python1/outer1'],'locator_cause_verified_by':'062f8f outer0/nativeNULL actual declaration func(v ... evaluate',
 'candidate_target_calls':0})
write('public-inputs.final.json',{'files':before,'rehash_count':len(before),'drift':[],'basis':'This invocation rehashed previously sealed public receipt inputs; not current Main qualification.'})
write('source-locators.json',locations)
handoff=write('handoff.json',{
 'schema':'researchos.f08-queue-absence-revision-preparation.v1',
 'actor':'codex:/root/sources_parent_impl','status':'RECEIPT_SOURCE_REVISION_PREPARED_WITH_OPEN_GATES','writer':'STOPPED',
 'source_ref':ref(source),'test_proposal_ref':ref(HERE/'client_cancel_finalization_test.go.proposed.txt'),
 'patch_ref':ref(HERE/'narrow-revision.proposed.patch'),'base_source_ref':ref(base/'client_cancel_finalization.go.proposed.txt'),
 'base_manifest_ref':ref(base/'manifest.json'),'non_author_review_ref':ref(review/'REVIEW.md'),
 'coverage_ref':ref(HERE/'coverage-and-open-matrix.json'),'selectors_ref':ref(HERE/'future-selectors.json'),
 'static_audit_ref':ref(HERE/'static-audit.json'),'tool_diagnostics_ref':diagnostics,'new_failure_origin_refs':origins,
 'before_ref':ref(HERE/'inputs.before.json'),'after_ref':ref(HERE/'inputs.after.json'),'final_rehash_ref':ref(HERE/'public-inputs.final.json'),
 'prior_failures_preserved_no_recount':inherit,'new_selectors':{'top':1,'leaf_proposals':24,'executed':0,'status':'NOT_RUN'},
 'open':['I02 complete full-source admission/materialization/final/journal positive fixtures','C02/I01 full initial qualification profile predicates fixed refusal','unclassified unrelated SDK receipt association fixed refusal','prior R1/R2/native/historical OPEN boundaries','explicit driver Innocuous fork/pin and physical SQLite qualification'],
 'source_accepted':False,'sql24_adoption_allowed':False,'formal_increment':0,
 'Go_gofmt_compile_SQL_HTTP_SDK_model_calls':0,'manifest':'manifest.json; includes this handoff; self excluded; exact ref supplied separately',
 'required_non_author_review':'Review C01 graph and conservative unrelated-receipt boundary; do not infer full evaluator completion or permission to install SQL24.'})
files=[ref(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='manifest.json']
manifest=write('manifest.json',{'schema':'researchos.receipt-manifest.v1','files':files,'self_excluded':True})
print(json.dumps({'handoff':handoff,'manifest':manifest,'files':len(files),'origins':origins,'writer':'STOPPED'},ensure_ascii=False))
