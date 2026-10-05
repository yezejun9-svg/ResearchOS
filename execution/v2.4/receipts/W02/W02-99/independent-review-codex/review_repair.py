import datetime,hashlib,json,pathlib,subprocess,sys,types
R=pathlib.Path('D:/作品集/ResearchOS/research-os');O=pathlib.Path(__file__).resolve().parent;B=O.parent
F='6f858d7bb78aaed95878cf89bf2f7792560e872e';P='execution/v2.4/receipts/W02/W02-99/'
blob=lambda p:subprocess.check_output(['git','show',F+':'+P+p],cwd=R)
digest=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
checks=[];refs={}
def check(name,ok,detail=None):
 checks.append({'id':name,'ok':bool(ok),'detail':detail});assert ok,name
handoff=json.loads(blob('ast_projection_fix_handoff_codex.json'))
for name,h in handoff['sources'].items():
 check('frozen-source-'+name,digest(blob(name))==h);refs[F+':'+P+name]=h
for group in ['ast_tests','projection_tests']:
 item=handoff['latest_receipts'][group];rel=item['path'].replace('\\','/').removeprefix(P);folder=rel.rsplit('/',1)[0]
 check(group+'-receipt-pin',digest(blob(rel))==item['sha256'])
 manifest=json.loads(blob(folder+'/manifest.json'));check(group+'-manifest-pin',digest(blob(folder+'/manifest.json'))==item['manifest_sha256'])
 check(group+'-all-raw-pins',all(digest(blob(folder+'/'+p))==h for p,h in manifest.items()),len(manifest))
 report=json.loads(blob(rel));check(group+'-nonempty-all-success',report['status']=='PASS' and len(report['checks'])==report['check_count'] and all(x['ok'] is True for x in report['checks']),report['check_count'])
 check(group+'-actual-helper-pin',report['helper_sha256']==handoff['sources']['evidence_reuse.py'])
 refs[F+':'+P+rel]=item['sha256'];refs[F+':'+P+folder+'/manifest.json']=item['manifest_sha256']
# Run the fixed AST validator against the exact independently archived original
# counterexample. Neither the current driver nor any mutant is imported.
m=types.ModuleType('evidence_reuse');m.__file__=str(B/'evidence_reuse.py');exec(compile(blob('evidence_reuse.py'),m.__file__,'exec'),m.__dict__)
original=B/'run-20261005T204515Z-b2910479b670/driver-sources/parent_driver.py'
try:m.verify_driver_ast(original,O/'g02_default_expression_mutant.txt');reason='ACCEPT'
except m.Refused as e:reason=str(e)
check('original-independent-default-counterexample-now-refused',reason=='G02_DEFINITION_CHANGED',reason)
check('original-counterexample-unchanged',digest((O/'ast_boundary_probe.json').read_bytes())==handoff['existing_failure_reference']['sha256'] and digest((O/'g02_default_expression_mutant.txt').read_bytes())==handoff['existing_failure_reference']['mutant_sha256'])
CB=R/'.local/worktrees/codex-w0299'/P
check('frozen-candidate-current-helper',digest((CB/'evidence_reuse.py').read_bytes())==handoff['sources']['evidence_reuse.py'])
check('g02-body-only-current-positive',bool(m.verify_driver_ast(original,CB/'parent_driver.py')))
# Exercise projection validation on an actual immutable successful reuse receipt.
# Imports are compiled from the frozen Git objects; no child process is launched.
sys.modules['evidence_reuse']=m
bridge=types.ModuleType('dispatch_parent');bridge.__file__=str(CB/'dispatch_parent.py');exec(compile(blob('dispatch_parent.py'),bridge.__file__,'exec'),bridge.__dict__);sys.modules['dispatch_parent']=bridge
w=types.ModuleType('independent_exact_projection');w.__file__=str(CB/'dispatch_parent_exact.py');exec(compile(blob('dispatch_parent_exact.py'),w.__file__,'exec'),w.__dict__)
item=handoff['latest_receipts']['G01_source_reuse'];path=R/'.local/worktrees/codex-w0299'/item['path'];report=read(path)
payload={'status':'PASS','check_id':'W02-G01','assertions':report['assertions'],'assertion_ids':report['assertion_ids'],'receipt':str(path)}
encode=lambda x:json.dumps(x).encode('utf-8')
positive=w.verify_child(encode(payload),'W02-G01')
check('independent-real-reuse-exact-projection',positive['assertion_ids']==['W02-G01'] and positive['assertions']==1 and positive['reused_original_assertion_count']==17 and positive['receipt_sha256']==digest(path.read_bytes()))
mutations=[('bool-count',{'assertions':True},'ASSERTION_COUNT_MISMATCH'),('duplicate',{'assertions':2,'assertion_ids':report['assertion_ids']*2},'DUPLICATE_IDS'),('zero',{'assertions':0,'assertion_ids':[]},'EMPTY_OR_INVALID_IDS'),('wrong-selector',{'check_id':'W02-G03'},'STDOUT_CHECK_ID_MISMATCH'),('wrong-id',{'assertion_ids':['W02-G03-FAKE']},'STDOUT_SELECTOR_MISMATCH'),('non-pass',{'status':'FAIL'},'CHILD_NOT_PASS'),('outside-card',{'receipt':str(O/'preparation.json')},'RECEIPT_OUTSIDE_CARD')]
for name,changes,expected in mutations:
 try:w.verify_child(encode(dict(payload,**changes)),'W02-G01');actual='ACCEPT'
 except m.Refused as e:actual=str(e)
 check('independent-projection-'+name,actual==expected,actual)
result={'schema':'researchos.independent-repair-review.v1','repair_commit':F,'status':'PASS_REPAIR_PENDING_FINAL_REGISTERED_GATES','checks':checks,'reference_hashes':refs,'old_counterexample':'ast_boundary_probe.json','old_raw_preserved':True,'new_product_Go_GUI_provider_service_calls':0,'new_projection_validator_child_processes':0,'new_in_process_projection_cases':8,'mutants_executed':False,'card_accepted':False,'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (O/'repair_6f858_review.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':result['status'],'checks':len(checks),'sha256':digest((O/'repair_6f858_review.json').read_bytes())}))
