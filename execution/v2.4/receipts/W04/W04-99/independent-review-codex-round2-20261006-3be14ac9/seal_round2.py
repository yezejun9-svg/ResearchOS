"""Independent changed-input review only; never runs a product or dispatcher."""
import pathlib,json,hashlib,datetime,ast,copy
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W04/W04-99';I=B/'integration_codex';O=pathlib.Path(__file__).parent
checked={};checks=[]
def sha(p):
 p=pathlib.Path(p).resolve();h=hashlib.sha256(p.read_bytes()).hexdigest()
 if str(p) in checked:assert checked[str(p)]==h,('changed_during_review',str(p))
 checked[str(p)]=h
 return h
def rd(p):sha(p);return json.loads(pathlib.Path(p).read_bytes())
def rf(p):return {'path':pathlib.Path(p).relative_to(R).as_posix(),'sha256':sha(p)}
def resolve(x):
 p=(R/x['path']).resolve();assert p.is_relative_to(R.resolve()) and sha(p)==x['sha256'];return p
def doc(x):return rd(resolve(x))
def ck(name,value):assert value,name;checks.append(name)
def save(p,d):
 with pathlib.Path(p).open('x',encoding='utf8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
old_dir=B/'independent-review-codex-final-20261006-61a0d2e7'
old=rd(old_dir/'audit_result.json')
old_public=R/'execution/v2.4/formal_case_index.py'
for name,h in old['input_hashes'].items():
 p=pathlib.Path(name)
 ck('reused_input_'+name,sha(p)==('26ade1e6c23e43d4ca5f26bd39313aa5fdf747350a872bf7bf8de71edda4a776' if p.resolve()==old_public.resolve() else h))
freeze=rd(I/'registration_repair_freeze_codex.json')
ck('root_frozen_commit',freeze['source_head']=='47a0fe198fadedcf8db000adf9608a5cf6fe8f69')
for item in freeze['source_refs']:resolve(item)
old_review_path=B/'independent_review_codex.json'
ck('old_review_preserved',sha(old_review_path)=='0a647a472966eba5f929cb990a775766956cbdec86272c0911edf57a962c3792')
pairs=[(I/'validator_before_registration_repair.py',B/'formal_validator_codex/validate.py','5add6b0044da783d009b52cdaac3402be053303006691ec337eac767d247e894','008759e428d993da3a277cb915818ebcac67fd4b73027d732413271d6e81cb96'),(I/'formal_index_before_registration_repair.py',old_public,'101241f1f06c2e0b8c472ced25fbaebe046e87e62dd58620fd08e46865af77b1','26ade1e6c23e43d4ca5f26bd39313aa5fdf747350a872bf7bf8de71edda4a776')]
new_dispatch_nodes=[]
for before,after,bh,ah in pairs:
 ck('before_source_hash_'+before.name,sha(before)==bh);ck('after_source_hash_'+after.name,sha(after)==ah)
 nodes=[]
 for path in [before,after]:
  tree=ast.parse(path.read_text('utf8'));nodes.append({n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))})
 ck('only_registered_dispatch_function_changed_'+after.name,[k for k in nodes[0].keys()|nodes[1].keys() if nodes[0].get(k)!=nodes[1].get(k)]==['registered_dispatch'])
 new_dispatch_nodes.append(nodes[1]['registered_dispatch'])
ck('two_reader_repair_AST_identical',new_dispatch_nodes[0]==new_dispatch_nodes[1])
controls_root=B/'formal_validator_codex/registration-repair-controls/runs'
success_path=controls_root/'controls-dd45f568eefa4a978e2467defcef3646/receipt.json'
failure_path=controls_root/'controls-523201990f284c369f582182574b3050/receipt.json'
control_docs=[]
for p,h in [(success_path,'d34cc8d0f17bed0e842f23090373672ac4d5f4f84c1f195e895c35d99d731b85'),(failure_path,'e64d2be066c078a51d275ec880f6a9f6e05b9169a2d93b0f7b1e92c16e483266')]:
 d=rd(p);ck('control_receipt_hash_'+p.parent.name,sha(p)==h)
 raw=resolve(d['stdout']).read_text('utf8');err=resolve(d['stderr']).read_text('utf8')
 snap=doc(d['source_snapshot_ref'])
 for s in snap['sources']:ck('snapshot_original_hash_'+p.parent.name+s['original_ref']['path'],s['original_ref']['sha256']==s['snapshot_ref']['sha256']);resolve(s['snapshot_ref'])
 ck('actual_locked_control_tool_'+p.parent.name,sha(d['locked_python']['path'])==d['locked_python']['sha256'])
 observations=[json.loads(l.split(' ',1)[1]) for l in raw.splitlines() if l.startswith('REGISTRATION_REPAIR_CONTROL ')]
 ck('control_observations_count_'+p.parent.name,len(observations)==d['control_count'])
 if p==success_path:
  ck('actual_new_controls_pass',d['status']=='PASS' and type(d['exit_code']) is int and d['exit_code']==0 and d['source_unchanged_during_run'] and d['control_roster_complete'])
  expected={(r,s) for r in ['local','public'] for s in ['dispatcher_not_in_product_vector','wrong_native_hash','changed_current_bytes','post_read_change','child_input_unpinned']}
  ck('exact_10_control_roster',len(observations)==10 and {(x['reader'],x['scenario']) for x in observations}==expected and all(x['status']=='PASS' for x in observations))
  ck('actual_suite_result', 'Ran 10 tests in ' in err and err.rstrip().endswith('OK'))
  for n,h2 in d['source_hashes'].items():ck('new_control_current_source_'+n,sha(R/n)==h2)
 else:
  ck('historical_harness_failure_retained',d['status']=='FAIL' and d['exit_code']==1 and "KeyError: 'input_hashes'" in err and err.rstrip().endswith('FAILED (errors=5)') and len(observations)==5 and all(x['reader']=='public' for x in observations))
 control_docs.append({'receipt':rf(p),'observations':observations})
actual_preflight=rd(I/'repair_reviewed_integrity_invocation_codex.json')
ck('actual_preflight_frozen_source',actual_preflight['validator']['sha256']==pairs[0][3]);resolve(actual_preflight['validator']);resolve(actual_preflight['current_context'])
preflight=doc(actual_preflight['stdout']);resolve(actual_preflight['stderr'])
ck('actual_new_preflight_pass',type(actual_preflight['exit_code']) is int and actual_preflight['exit_code']==0 and preflight['integrity']=='PASS' and set(preflight['eligible_owned_cases'])=={'C03','C04','A01'} and preflight['formal_accepted_count']==0)
oldfail=rd(I/'reviewed_integrity_invocation_codex.json');oldfailresult=doc(oldfail['stdout']);resolve(oldfail['stderr'])
ck('original_registration_failure_retained',oldfail['exit_code']==1 and oldfailresult['reason_code']=='DISPATCHER_CHANGED')
state=rd(R/'execution/v2.4/step_state.json');owner=next(x for x in state['steps'] if x['id']=='W04-99')
ck('no_canonical_acceptance_yet',owner['status']=='IN_PROGRESS')
ck('old_review_not_registered',not any(x.get('path','').endswith('/independent_review_codex.json') for x in owner.get('evidence',[])))
original=rd(old_review_path);ctx=doc(original['current_context_ref']);index=doc(original['evidence_index_ref'])
ck('unchanged_current_context',original['current_context_ref']['sha256']=='8615cc89a48146241674dbfc56ccfa68396fc44f4327f01cfe8d1131370cf101')
dispatcher=R/'execution/command_dispatcher/dispatch.py';dh=sha(dispatcher)
ck('native_dispatcher_unchanged',dh=='69c94d63050fb2274a4d995742e934e85c52bd43e9afd5bf9640a5f3404061e4')
for entry in ctx['registered_dispatches']:
 d=doc(entry['receipt_ref']);ck('native_dispatcher_pin_'+d['invocation_id'],d['dispatcher_sha256']==dh);resolve(d['stdout']);resolve(d['stderr'])
for name,h in checked.items():assert hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest()==h,('changed_before_issue',name)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
review=copy.deepcopy(original);review['issued_at']=now
for case in review['owned_case_verdicts']:
 case['semantic_review']['statement'] += ' Round2 independently confirms continued validity after the bounded registration-reader repair: real native dispatcher hashes and reader finish/CAS tracking replace only the erroneous demand to include the later dispatcher in the original Go product vector. Product code/input/raw and these business verdicts are unchanged. This is a new issuance before canonical registration; the earlier unregistered review and failed registration attempt remain preserved.'
companion={'schema':'researchos.w04.independent-round2-review.v1','scope':'REGISTRATION_INTEGRITY_REPAIR_AND_UNCHANGED_PRODUCT_EVIDENCE_REVALIDATION','status':'PASS','issued_at':now,'verifier_id':'codex:/root/w1702_review','source_head':freeze['source_head'],'check_count':len(checks),'checks':checks,'input_hashes':checked,
 'previous_unregistered_review_ref':rf(old_review_path),'previous_review_preserved_not_canonical_supersession':True,
 'earlier_full_semantic_review':rf(old_dir/'static_review_and_scope.json'),'earlier_full_audit':rf(old_dir/'audit_result.json'),
 'repair_freeze':rf(I/'registration_repair_freeze_codex.json'),'actual_preflight':rf(I/'repair_reviewed_integrity_invocation_codex.json'),
 'original_registration_failure':rf(I/'reviewed_integrity_invocation_codex.json'),'control_runs':control_docs,
 'resolved_origin':'Real registration read DISPATCHER_CHANGED C03 caused by demanding registration dispatcher membership in an earlier product vector, not actual dispatcher drift.',
 'minimal_repair':'Two identical registered_dispatch blocks use Reader.ref on the fixed canonical dispatcher path and actual native receipt hash; this preserves validation and finish/CAS dependency tracking. Child inputs still require their original product pins. No other function AST changed.',
 'new_control_harness_failure':'One control-harness origin, not five product failures: initial local controls expected a public-only input_hashes return key. Fixed observer calls the real Reader.finish and records its dependency map; all ten new controls then pass.',
 'reused_product_evidence':'All previous audited input hashes match except the specifically reviewed public formal reader change. 29 Go tests/subtests, original two source invocations, eleven native registration receipts, 10 formal assertions and five gates are reused with unchanged applicable product bytes.',
 'testing_boundary':'65/30/2 historical suites were preserved, not rerun or claimed as execution on the repair. Ten new targeted controls and the actual changed-input root read preflight provide repair validation. No Go, dispatcher, provider or GUI was rerun.',
 'formal_count_before_root_registration':0,'product_business_acceptance_created':False,'open_blockers':[]}
save(O/'review_detail.json',companion)
save(B/'independent_review_codex_round2.json',review)
save(O/'manifest.json',{'schema':'researchos.independent-review-manifest.v1','issued_at':now,'review_ref':rf(B/'independent_review_codex_round2.json'),'files':[rf(p) for p in sorted(O.iterdir()) if p.is_file()],'status':'PASS','product_commands_executed':0})
print(json.dumps({'review':rf(B/'independent_review_codex_round2.json'),'issued_at':now,'detail':rf(O/'review_detail.json'),'manifest':rf(O/'manifest.json'),'checks':len(checks),'input_files':len(checked)},ensure_ascii=False,indent=2))

