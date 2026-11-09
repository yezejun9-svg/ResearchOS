import pathlib,json,hashlib,gzip,datetime,subprocess
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[6]
MAIN=pathlib.Path('D:/作品集/ResearchOS/research-os')
DRAFT=HERE.parent/'typed-route-5188793d240a4f1197f92bbc510ad9e1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def ref(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def write(name,v):
    with (HERE/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def require(ok,msg):
    if not ok:raise RuntimeError(msg)
summary=read(HERE/'execution-summary.json')
require(summary['actual_cases']==64 and summary['planned_cases']==64,'case count')
require(not summary['source_drift'] and not summary['input_drift'],'execution drift')
before=read(HERE/'before-first-case.json')['files']
current={p:ref(pathlib.Path(p)) for p in before}
require(current==before,'final current input drift')
write('current-inputs.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':current,'comparison':'EXACT_EQUALS_BEFORE_FIRST_CASE','count':len(current)})
diffnames=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT).decode().splitlines()
require(sorted(diffnames)==['internal/domain/runtime_model_verification.go','internal/domain/runtime_provider_binding_windows_test.go'],'unexpected source mutation')
prior=read(HERE.parent/'epoch-correction-69a52b78d491456792bf394b01629e02'/'before-first-case.json')['files']
source9=read(HERE/'source9.freeze.json')
protected={name:entry['current'] for name,entry in source9.items() if name not in diffnames}
for name,v in protected.items():require(prior[str(ROOT/name)]==v,'protected provider source drift '+name)
write('protected-source7.json',{'source_before':ref(HERE.parent/'epoch-correction-69a52b78d491456792bf394b01629e02'/'before-first-case.json'),'files':protected,'drift':[]})
cases=[];pass_count=0;skip_count=0
for outcome in summary['outcomes']:
    name=outcome['case'];inv=read(HERE/(name+'.result.json'))
    events=[json.loads(line) for line in (HERE/(name+'.stdout.raw')).read_text(encoding='utf-8').splitlines()]
    passed=[e for e in events if e.get('Action')=='pass' and e.get('Test')]
    skipped=[e for e in events if e.get('Action')=='skip']
    require(inv['exit']==0 and len(passed)==1 and not skipped,'case exit/assertion/skip '+name)
    pass_count+=len(passed);skip_count+=len(skipped)
    actual=read(HERE/(name+'-evidence')/'actual.json')
    row={'name':name,'result':ref(HERE/(name+'.result.json')),'actual':ref(HERE/(name+'-evidence')/'actual.json'),'test':passed[0]['Test'],'exit':0,'skip':0}
    if name.startswith('case-'):
        spec=read(HERE/(name+'.json'))
        v1=json.loads(gzip.decompress((HERE/(name+'-evidence')/'semantic-before.json.gz').read_bytes()))
        v2=json.loads(gzip.decompress((HERE/(name+'-evidence')/'semantic-after.json.gz').read_bytes()))
        require(not actual['test_failed'],'test cleanup failure '+name)
        require(v1['schema']==v2['schema'] and set(v1['tables'])==set(v2['tables']),'schema/table drift '+name)
        changed=sorted(k for k in v1['tables'] if v1['tables'][k]!=v2['tables'][k])
        require(set(changed)<=set(spec['allowed_mutation_tables']),'unregistered mutation '+name)
        require(actual['original_triggers']==actual['triggers_after'],'trigger drift '+name)
        if spec['mutation']=='none':require(v1==v2 and actual['semantic_equal'],'unmutated semantic drift '+name)
        row.update({'label':actual['mode'],'mutation':spec['mutation'],'expected_error':spec['want_error'],'required_cause':spec['required_cause'],'inventory_error':actual['inventory_error'],'stream_backup_error':actual['stream_backup_error'],'inventory_count':actual['inventory_count'],'original_effect_key_counts':actual['original_effect_key_counts'],'semantic_tables':len(v1['tables']),'schema_rows':v1['schema']['row_count'],'semantic_equal':v1==v2,'changed_tables':changed,'input_sha256':actual['input_sha256'],'closed_db_sha256':actual['closed_db_sha256'],'byte_identical':actual['input_sha256']==actual['closed_db_sha256'],'semantic_before':ref(HERE/(name+'-evidence')/'semantic-before.json.gz'),'semantic_after':ref(HERE/(name+'-evidence')/'semantic-after.json.gz'),'closed_db':ref(HERE/(name+'-evidence')/'case.sqlite')})
    cases.append(row)
write('case-audit.json',{'cases':cases,'test_pass':pass_count,'skip':skip_count,'product_or_model_calls':0})
inputs=read(HERE/'original-inputs.before.json')
for name,r in inputs.items():
    require(ref(pathlib.Path(r['original']['path']))==r['original'],'original DB changed '+name)
    require(ref(pathlib.Path(r['copy']['path']))==r['copy'],'sealed input copy changed '+name)
write('original-inputs.after.json',inputs)
write('failure-history.json',{'issue':'P9-P12-SR01','prior_cumulative_issue_failures':3,'author_source_attempt':3,'new_failed_case_invocations':0,'current_cumulative_issue_failures':3,'old_model_history_failures':5,'held_positive_tests':'NOT_RUN; original C10 remains held and does not establish qualification of current code','automatic_retry':False,'old_case02':'Byte changed and no original paired semantic evidence; NOT retroactively credited','precase_draft':ref(DRAFT/'precase-draft-status.json'),'previous_failure_origins':[ref(HERE.parent/'causal-repair-481c0dc455c643f5a2e70b7178c97fe2'/'failure_origins.json'),ref(HERE.parent/'epoch-correction-69a52b78d491456792bf394b01629e02'/'failure_origins.json')],'diagnostic_errors':read(HERE/'attempt.json')['precase_diagnostic_errors'],'no_counter_reset':True})
groups={'R01':[0],'R02':[1],'R03':[2],'R04':[3,6],'R05':[4,5],'R06':[7,8],'R07':[9,10,11],'R08':list(range(12,21)),'R09':list(range(21,54))}
handoff={'status':'SOURCE_EXECUTION_REPORTED_PENDING_NONAUTHOR_REVIEW','actor':'codex:/root/command_queue_impl','issue':'P9-P12-SR01','author_attempt':3,'scope':ref(MAIN/'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-typed-route-scope-r285/scope_registration.json'),'source2':{name:ref(ROOT/name) for name in diffnames},'source9':ref(HERE/'source9.freeze.json'),'current_complete_vector':ref(HERE/'current-inputs.json'),'compiled_inputs':ref(HERE/'compiled-inputs.before.json'),'test_executable':ref(HERE/'domain.test.exe'),'execution':ref(HERE/'execution-summary.json'),'case_audit':ref(HERE/'case-audit.json'),'groups':{g:[cases[i]['name'] for i in indexes] for g,indexes in groups.items()},'actual_tests':64,'pass':64,'fail':0,'skip':0,'current_vector_count':len(current),'compiled_file_count':len(read(HERE/'compiled-inputs.before.json')['files']),'source_drift':0,'original_input_drift':0,'models':0,'workers':0,'HTTP':0,'paid':0,'public_backup_restore':'NOT_RUN_OPTIONAL: all 64 registered zero-model controls used; internal validator results are not public restore proof','generic_fixture_without_original_revision':'COMPATIBILITY_BLOCKED, no current/latest/profile guessing','synthetic_scope':'Only counterfactual copied fixtures and synthetic provenance/epoch controls; never actual historical qualification','acceptance':'No self acceptance, LIVE qualification, Main integration, W05/A04 or parent increment','failures':ref(HERE/'failure-history.json'),'precase_draft_preserved':str(DRAFT),'copy_scope':'Only these two public receipt namespaces and exact2 source. Original seven DBs contain authorized synthetic fixture data, no private Host/Vault/holdout. Other namespaces remain unchanged.'}
write('handoff.json',handoff)
print(json.dumps({'pass':64,'fail':0,'skip':0,'current_files':len(current),'handoff':ref(HERE/'handoff.json')},ensure_ascii=False))
