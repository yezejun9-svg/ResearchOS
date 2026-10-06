import datetime,hashlib,json,pathlib,subprocess
R=pathlib.Path('D:/作品集/ResearchOS/research-os');O=pathlib.Path(__file__).resolve().parent;B=O.parent
F='67ee53661f267c0b7a2441cfd58117fbd0b39b30'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];refs={}
def check(name,ok,detail=None):
 checks.append({'id':name,'ok':bool(ok),'detail':detail});assert ok,name
def ref(p):
 refs[str(p)]=sha(p);return refs[str(p)]
def manifest(folder,expected=None):
 p=folder/'manifest.json';h=ref(p);m=read(p)
 check(folder.name+'-manifest',not expected or h==expected)
 check(folder.name+'-all-files',all(sha(folder/name)==value for name,value in m.items()),len(m))
 return h
prep=read(O/'preparation.json');base=read(B/'integration_codex/binding_baseline_codex.json')
idxpath=B/'integration_codex/exact_parent_dispatch_results.json';idx=read(idxpath);ref(idxpath)
registry=read(R/'execution/v2.4/commands.json');paths=read(R/'execution/v2.4/path_ownership.json')
check('final-source-and-registry',subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==F==idx['source_head'] and registry['revision']==36 and paths['revision']==45 and sha(R/'execution/v2.4/commands.json')==idx['registry_sha256'])
check('other30-registry-entries-preserved',len(registry['commands'])==31 and all(registry['commands'][k]==v for k,v in base['v24_decoded_commands'].items() if k!='build.check'))
check('protected-sources-preserved',all(sha(R/p)==h for p,h in base['protected_source_hashes'].items()) and sha(R/'execution/commands.json')==base['legacy_registry_sha256'])
fix=read(B/'ast_projection_fix_handoff_codex.json')
check('final-frozen-repair-sources',all(sha(B/name)==value for name,value in fix['sources'].items()))
entry=registry['commands']['build.check']
check('exact-wrapper-registered',entry['argv']==['-B','execution/v2.4/receipts/W02/W02-99/dispatch_parent_exact.py'])
check('prior-internal-only-index-preserved',sha(B/'integration_codex/exact_dispatch_results.json')==idx['earlier_internal_only_index_sha256'])
gates=[];runs={};gate_templates={x['check_id']:x for x in prep['frozen_gates']}
for item in idx['actual_registered_selectors']:
 selector=item['selector'];mirror=R/item['mirror_path'];dp=mirror/'receipt.json';d=read(dp);ref(dp)
 check(selector+'-dispatcher-current-exact',sha(dp)==item['dispatcher_receipt_sha256'] and item['exit_code']==d['exit_code']==d['child_exit_code']==0 and d['status']=='PASS' and d['assertion_ids']==[selector] and d['selectors']=={'task_id':'W02','check_id':selector,'case_id':''} and d['code_revision']==F and d['registered_command_revision']==idx['registry_sha256'])
 check(selector+'-dispatcher-raw-streams',all(sha(mirror/(k+'.txt'))==d[k]['sha256']==sha(R/d[k]['path']) for k in ['stdout','stderr']))
 stdout=read(mirror/'stdout.txt');child=pathlib.Path(item['child_receipt']);report=read(child);runs[selector]=child.parent;ref(child)
 check(selector+'-exact-output-internal-separation',stdout['assertion_ids']==[selector] and type(stdout['assertions']) is int and stdout['assertions']==1 and stdout['internal_assertion_ids']==report['assertion_ids']==item['internal_assertion_ids'] and stdout['internal_assertion_count']==len(report['assertion_ids']) and stdout['receipt_sha256']==sha(child)==item['child_receipt_sha256'])
 check(selector+'-child-mode-status-scope',report['check_id']==selector and report['mode']==gate_templates[selector]['mode'] and report['status']=='PASS' and report['owned_acceptance_ids']==report['formal_cases_accepted']==[] and report['whole_card_accepted'] is False and report['assertions']==len(report['assertion_ids']) and [c['id'] for c in report['checks']]==report['assertion_ids'] and all(c['ok'] is True for c in report['checks']))
 manifest(child.parent,item['child_manifest_sha256'])
 pp=pathlib.Path(item['projection_receipt']);projection=read(pp);ref(pp)
 check(selector+'-projection-audit',sha(pp)==item['projection_receipt_sha256']==stdout['projection_receipt_sha256'] and projection['assertion_ids']==[selector] and projection['child_exit_code']==0 and projection['status']=='PASS' and all(sha(B/n)==h for n,h in projection['source_sha256'].items()))
 manifest(pp.parent,item['projection_manifest_sha256'])
 check(selector+'-projection-child-raw',read(pp.parent/'child.command.json')['exit_code']==0 and read(pp.parent/'child.stdout.txt')['assertion_ids']==report['assertion_ids'])
 gate={'check_id':selector,'mode':gate_templates[selector]['mode'],'frozen_check':gate_templates[selector]['check'],'frozen_expected':gate_templates[selector]['expected'],'decision':'ACCEPT','invocation_id':d['invocation_id'],'dispatcher_receipt':str(dp),'dispatcher_receipt_sha256':sha(dp),'assertion_ids':[selector],'child_exit_code':0,'child_receipt':str(child),'child_receipt_sha256':sha(child),'child_manifest_sha256':item['child_manifest_sha256'],'projection_receipt':str(pp),'projection_receipt_sha256':sha(pp),'projection_manifest_sha256':item['projection_manifest_sha256'],'aggregation_assertions':1,'current_child_internal_assertion_ids':report['assertion_ids'],'current_child_internal_count':len(report['assertion_ids'])}
 if selector!='W02-G02':
  replay=read(child.parent/'revalidation.json');ref(child.parent/'revalidation.json')
  n=17 if selector=='W02-G01' else 21
  historical=[x for x in replay['validated_inputs_and_raw'] if x['kind']=='historical_partial_driver_not_archived']
  check(selector+'-historical-unavailable-driver-explicit',all(x['sha256']=='c6712a634ad186523f68cbbe702a5e7d5a393e1bad580e4dee7d30f33c3e8d0f' and 'no source-archive claim' in x['limit'] for x in historical),historical)
  check(selector+'-original-current-raw-and-inputs',len(replay['source_assertion_ids'])==n and set(replay['recomputed_conditions'])==set(replay['source_assertion_ids']) and all(v is True for v in replay['recomputed_conditions'].values()) and all(sha(pathlib.Path(x['path']))==x['sha256'] for x in replay['validated_inputs_and_raw'] if x not in historical),len(replay['validated_inputs_and_raw'])-len(historical))
  original=B/replay['source_run'];gate.update(original_internal_assertion_ids=replay['source_assertion_ids'],original_internal_count=n,original_receipt=str(original/'receipt.json'),original_receipt_sha256=replay['source_receipt_sha256'],original_manifest_sha256=replay['source_manifest_sha256'],current_execution='Read-only revalidation and exact parent-ID projection; original product/build/fixture commands not rerun.')
 else:gate.update(original_internal_assertion_ids=report['assertion_ids'],original_internal_count=13,current_execution='Actual current registry/path checks and four synthetic dispatcher probes; 434 route rows are intercepted/static routing checks, not old product execution.')
 gates.append(gate)
check('three-unique-exact-parent-gates',set(runs)==set(gate_templates) and len({x['invocation_id'] for x in gates})==3)
g02=read(runs['W02-G02']/'receipt.json');folder=runs['W02-G02']
check('G02-current-inputs',all(sha(pathlib.Path(p))==h for p,h in g02['source_inputs_sha256'].items()),len(g02['source_inputs_sha256']))
inventory=read(folder/'command-inventory.json')
check('G02-real-command-artifact-paths',len(inventory)==31 and sum(x['registry_state']=='BOUND' for x in inventory)==23 and all(not x['issues'] and all((R/p['path']).is_file() and sha(R/p['path'])==p['sha256'] for p in x['paths']) for x in inventory))
pathinv=read(folder/'path-inventory.json');check('G02-actual-paths',all((R/x['path']).exists() for x in pathinv if x['kind']=='actual') and len({x['path'] for x in pathinv})==len(pathinv))
special=paths['special_paths'];check('G02-restricted-unbound-separation',special['verifier_restricted_store']['path'] is None and special['verifier_restricted_store']['status']=='UNBOUND' and special['verifier_restricted_store']['access_class']=='VERIFIER_ONLY')
cases=read(folder/'dispatcher-cases.json')
for case in cases:
 p=folder/case['receipt'];d=read(p);ref(p)
 check('G02-current-probe-'+case['label'],sha(p)==case['receipt_sha256'] and d['status']==case['expected_status']==case['actual_status'] and d['exit_code']==case['expected_exit']==case['actual_exit'] and all(sha(folder/'dispatcher-fixture'/d[k]['path'])==d[k]['sha256'] for k in ['stdout','stderr']))
check('G02-probes-unique-clean',len(cases)==4 and len({c['invocation_id'] for c in cases})==4 and read(folder/'cleanup.json')['absent'] is True and not pathlib.Path(read(folder/'cleanup.json')['target']).exists())
for name,count in [('frozen_raw_review.json',69),('reuse_f327_review.json',13),('repair_6f858_review.json',28)]:
 p=O/name;report=read(p);ref(p);check(name+'-completed-prior-review',len(report['checks'])==count and all(x['ok'] is True for x in report['checks']))
for p in [O/'ast_boundary_probe.json',O/'g02_default_expression_mutant.txt',B/'build_identity_supplement_codex.json',B/'renderer_reuse_closure_codex.json',B/'integration_codex/binding_baseline_codex.json',R/'execution/v2.4/path_ownership.json',R/'execution/v2.4/commands.json',B/'ast_projection_fix_handoff_codex.json'] :ref(p)
meaning=[
 ('W02-G02','Current commands36/path45: 31 real registered keys, 23 bound/8 explicit unbound; concrete artifact paths, owner mapping, locked executable/argv/env names/timeout/platform and exact wrapper observed in actual dispatch.'),
 ('W02-G01/W02-G03','Two actual clean Go builds and six post-repair commands; five already-passed source-matched commands retained, including three real nonempty Go tests and 12 static frozen-spec checks. Current dispatcher rejects UNBOUND/zero assertions. Static schema/package checks do not accept full A03 runtime.'),
 ('W02-G02/W02-G03','Three exact registered logical-key parent calls now emit singleton frozen IDs. Actual unknown/unbound/platform/selector refusals and preserved legacy transport prevent guessed commands and zero-case success.'),
 ('W02-G03','Actual synthetic-credential dispatcher probes cover missing credentials, secret-in-argv rejection, controlled environment names, no implicit environment and raw/JSON-escaped stream redaction; no real provider secret used.'),
 ('W02-G02','Actual evaluation adapter, current renderer design-token import and development receipt paths bound. Verifier store remains explicitly null/UNBOUND and VERIFIER_ONLY pending W17; no candidate checkout designated formal holdout storage.'),
 ('W02-G01/W02-G02','Existing MU_FORK renderer and 18 matched inputs plus design-token import closure retained; 15 dependency entries/locks inventoried; Node tooling does not change sole Go business authority.'),
 ('W02-G01/W02-G02','Existing shared Go core, actual CLI binaries, native Desktop source/build/startup entries and client protocol map retained. 23 methods/14 events are structural coverage; PLANNED labels remain historical. Existing W01 sample evidence reused only for exact matching source, not new GUI execution.'),
 ('W02-G01/W02-G02','One selected MU_FORK composition; 5083 tracked source hashes verified, component/patch/lock evidence preserved, QM not required and fallback not triggered; no new runner installation.'),
 ('W02-G01/W02-G02','Recorded core-265137d9566c derives from actual control buildinfo revision 265137d9566c8f56d793ad75c6f16877176924a1 and matched implementation hash. Actual CLI binary hash/command reports researchos-client/2 and version0.2.4-w0203. Desktop build/start entries recorded. core_build_id_runtime_observed=false; no new host/GUI observation claimed. Unsupported CLI command actually exits3 NOT_IMPLEMENTED.')]
mapping=[dict(row=x['row'],requirement=x['requirement'],decision='ACCEPT_IN_W02_CONSTRUCTION_SCOPE',gates=y[0].split('/'),evidence_interpretation=y[1]) for x,y in zip(prep['frozen_development_checklist'],meaning)]
review={'schema':'researchos.independent-parent-review.v1','step_id':'W02-99','reviewer':'codex:/root/w1702_review','actual_model':'gpt-6-astra','reasoning_effort':'high','independent_of_executor':True,'source_revision':F,'commands_revision':36,'path_revision':45,'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'ACCEPT_W02_PARENT_CONSTRUCTION','technical_review':'PASS_IN_SCOPE','recommendation':'ACCEPT_W02-99_PARENT_GATES_ONLY','card_checks':{'W02-99-OUTPUT':'PASS','W02-99-NEGATIVE':'PASS','W02-99-EVIDENCE':'PASS'},'development_checklist_mapping':mapping,'gate_decisions':gates,'owned_acceptance_ids':[],'formal_cases_accepted':[],'formal_case_count_delta':0,'parent_counter_changes_by_reviewer':0,'state_changes_by_reviewer':0,'new_provider_calls':0,'new_GUI_runs':0,'new_Go_runs':0,'new_service_operations':0,'private_formal_label_reads':0,'independent_evidence':{'prior_raw_checks':69,'prior_reuse_checks':13,'repair_checks':28,'final_checks':len(checks),'new_in_process_projection_cases':8,'original_14_validator_negatives_rerun':False,'original_product_Go_GUI_fixtures_rerun':False},'checks':checks,'resolved_findings':[{'id':'W0299-AST-G02-IMPORT-SIDE-EFFECT','status':'CLOSED','original_counterexample':str(O/'ast_boundary_probe.json'),'original_counterexample_sha256':sha(O/'ast_boundary_probe.json'),'closure':'Fixed helper rejects the exact prior default-expression mutant; only g02 body may differ and ordered top-level structure/type/name/count are preserved. Frozen AST6 raw and independent counterexample closure verified.'},{'id':'W0299-EXACT-PARENT-ASSERTION-ID','status':'CLOSED','original_counterexample':str(B/'integration_codex/exact_dispatch_results.json'),'original_counterexample_sha256':sha(B/'integration_codex/exact_dispatch_results.json'),'closure':'commands36 real three registered calls emit exact [W02-G01/G02/G03]; internal17/13/21 retained separately. Strict wrapper validates nonempty unique int-count IDs, receipts/modes/checks/manifests/hash/scope and preserves nonzero child exits; original bridge and nonparent delegation unchanged.'}],'open_findings':[],'scope_qualifications':['Parent W02 construction acceptance only; A03 final owner W06 and A15 final owner W20 remain unaccepted here.','Historical first G01 top-level failure preserved; five successful prior subcommands rederived from raw and exact current inputs. Only that first original parent_driver source archive is unavailable; same-byte dispatch_parent and dispatcher_fixture archives verified separately.','Produced temporary binaries were measured and removed after execution; reports retain hashes/raw, not a claim that binaries remain on disk.','No new GUI, host, provider, service operation, W13/NVDA/W14 audit or private Verifier data inspection. W01 sample observations remain prior observations under exact source pins.','Current formal selector behavior is not universally observed. Eight later command keys remain UNBOUND; restricted store remains unprovisioned; existing C24/A12 formal limitations remain unaccepted.','No state, registry or counter written by reviewer. Integrator must register this independent receipt before changing step acceptance.'],'evidence_artifacts':[{'path':p,'sha256':h} for p,h in refs.items()]}
out=B/'independent_review_codex.json'
with out.open('x',encoding='utf-8') as f:json.dump(review,f,ensure_ascii=False,indent=2)
print(json.dumps({'verdict':review['verdict'],'prior_checks':110,'final_checks':len(checks),'development_rows':len(mapping),'gates':len(gates),'formal_case_delta':0,'sha256':sha(out)},ensure_ascii=False))
