import hashlib,json,pathlib,subprocess,datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os');O=pathlib.Path(__file__).resolve().parent;B=O.parent
commit='f327ee10844810d8ada7a7b83aae05412d757c4a';prefix='execution/v2.4/receipts/W02/W02-99/'
blob=lambda p:subprocess.check_output(['git','show',commit+':'+prefix+p],cwd=R)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
handoff=json.loads(blob('reuse_handoff_codex.json'));refs={};checks=[]
def check(id,ok,detail=None):
 checks.append({'id':id,'ok':bool(ok),'detail':detail});assert ok,id
for name,h in handoff['sources'].items():
 actual=hashlib.sha256(blob(name)).hexdigest();check('frozen-source-'+name,actual==h);refs[commit+':'+prefix+name]=h
negative=handoff['latest_receipts']['negative_tests'];folder=B/negative['run']
check('14-negative-receipt-and-manifest',sha(folder/'receipt.json')==negative['receipt_sha256'] and sha(folder/'manifest.json')==negative['manifest_sha256'])
manifest=read(folder/'manifest.json');check('14-negative-raw-files',all(sha(folder/p)==h for p,h in manifest.items()),len(manifest));refs.update({str(folder/p):h for p,h in manifest.items()})
report=read(folder/'receipt.json');cases=report['negative_cases']
check('14-unique-actual-validator-negatives',report['status']=='PASS' and len(cases)==len({c['case'] for c in cases})==14 and all(c['exit_code']==3 and c['ok'] is True and read(folder/c['stdout']['path'])['reason']==c['expected_reason'] for c in cases),[c['case'] for c in cases])
check('test-helper-current-at-frozen-commit',report['helper_sha256']==handoff['sources']['evidence_reuse.py'] and report['test_source_sha256']==handoff['sources']['reuse_self_test.py'])
check('negative-fixture-no-product-calls',report['new_product_tests_executed']==report['new_dispatcher_fixture_children']==0 and report['new_validator_test_children']==14)
check('negative-owned-scratch-cleaned',read(folder/'cleanup.json')['exit_code']==0 and read(folder/'cleanup.json')['absent'] is True)
old=read(B/'run-20261005T204244Z-bef88e7b3cde/receipt.json');old_sources={pathlib.Path(p).name:h for p,h in old['source_inputs_sha256'].items() if pathlib.Path(p).name in ['parent_driver.py','dispatch_parent.py','dispatcher_fixture.py']}
available={}
for name in ['dispatch_parent.py','dispatcher_fixture.py']:
 p=B/'run-20261005T204515Z-b2910479b670/driver-sources'/name
 check('same-byte-cross-archive-'+name,sha(p)==old_sources[name]==handoff['partial_first_run_disclosure']['same_byte_archives_available'][name]['sha256'])
 available[name]={'path':str(p),'sha256':sha(p)}
assert old_sources['parent_driver.py']=='c6712a634ad186523f68cbbe702a5e7d5a393e1bad580e4dee7d30f33c3e8d0f'
result={'phase':'FROZEN_REUSE_F327_REVIEW','status':'PENDING_TWO_CONCRETE_FIXES','checks':checks,'reference_hashes':refs,'findings':[{'id':'W0299-AST-G02-IMPORT-SIDE-EFFECT','status':'OPEN_PENDING_PATCH','evidence':'ast_boundary_probe.json','detail':'Whole-g02 exemption accepts import-time default/decorator expressions; only body may differ. Root also requires sequence/count preservation to reject duplicate top-level definitions.'},{'id':'W0299-EXACT-PARENT-ASSERTION-ID','status':'OPEN_PENDING_PATCH','detail':'Frozen expected_assertion_ids require W02-G01/G02/G03; rev35 returns suffix/13 internal IDs. Parent check_id field is not the required assertion inventory. Root plans exact projection wrapper with original internal IDs preserved separately.'}],'historical_archive_precision':{'first_manifest_contains_driver_archive':False,'same_byte_sources_available_in_successful_run':available,'only_original_parent_driver_remains_unavailable':{'sha256':old_sources['parent_driver.py'],'interpretation':'Five passed prior commands independently rederived from pinned raw; original top-level FAIL remains.'},'previous_stage_review_immutable':'frozen_raw_review.json is preserved; this adds the exact cross-archive distinction.'},'new_Go_GUI_provider_service_calls':0,'card_accepted':False,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (O/'reuse_f327_review.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':result['status'],'checks':len(checks),'same_byte_old_driver_archives':len(available),'sha256':sha(O/'reuse_f327_review.json')}))
