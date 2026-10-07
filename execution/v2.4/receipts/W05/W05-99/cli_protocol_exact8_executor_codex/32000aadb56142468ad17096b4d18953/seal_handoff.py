from pathlib import Path
import hashlib,json,subprocess,re,datetime

W=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
N=Path(__file__).resolve().parent
D=N/'final-freeze'
B=N/'build-aba1462acb4a49b081e1bf06fd419a91'
M=Path('D:/作品集/ResearchOS/research-os')
P=M/'execution/v2.4/receipts/W05/W05-99/cli_contract_exact_fix_scope_codex/f12c3e1bc23b42fc9c4018e85f8f849d'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
 p=Path(p);return {'path':p.relative_to(W).as_posix() if p.is_relative_to(W) else str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(name,value):
 p=D/name
 assert not p.exists(),p
 p.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
 return ref(p)

scope=load(N/'cli_implementation_scope.json')
commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
paths=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',commit],text=True).splitlines()
assert len(paths)==8
sources=[]
for p in paths:
 blob=subprocess.check_output(['git','show',commit+':'+p])
 assert blob==(W/p).read_bytes()
 sources.append(dict(ref(W/p),git_blob=subprocess.check_output(['git','rev-parse',commit+':'+p],text=True).strip(),base_sha256=hashlib.sha256(subprocess.check_output(['git','show',scope['base_commit']+':'+p])).hexdigest()))
source_ref=save('source-manifest.json',{'base':scope['base_commit'],'source_commit':commit,'paths':sources,'diff_ref':ref(D/'source.diff'),'protected_audit':ref(N/'protected-source-audit-current.json'),'source_acceptance':False})
symbols=[]
for p in paths:
 if p.endswith('_test.go'):
  for i,line in enumerate((W/p).read_text(encoding='utf-8').splitlines(),1):
   m=re.match(r'func (Test\w+)\(',line)
   if m:symbols.append({'path':p,'line':i,'test':m[1]})
save('test-symbols.json',{'method':'top-level Go test function declaration scan, not execution count','symbols':symbols})

allruns=[];current=[];index={}
for p in sorted(N.glob('run-*/result.json'),key=lambda p:p.stat().st_mtime):
 x=load(p);iscurrent=any(str(B/'cli.test.exe')==a for a in x.get('actualargv',[]))
 allruns.append({'result_ref':ref(p),'exit_code':x['exit_code'],'current_executable':iscurrent,'leaf_events':x['leaf_events'],'event_counts_including_parent':x['event_counts_including_parent']})
 if iscurrent:
  assert x['exit_code']==0 and not x['source_drift'] and not x['event_counts_including_parent']['skip']
  current.append((p,x))
  for event in x['leaf_events']:index[event['test']]={'status':event['action'].upper(),'result_ref':ref(p),'stdout_ref':x['stdout_ref']}

inventory=load(N/'finite-inventory-r305.json');new=[]
for row in inventory['new_leaves']:
 selector=row['selector'];out=dict(row)
 out.pop('state',None)
 if selector in index:out.update(index[selector])
 else:out.update(status='HOLD_NOT_RUN_CURRENT',reason='Frozen handler session.list accepts nonnull request SID then response identity fails HTTP500. No unchanged rerun, no client workaround promoted as producer fix.')
 if '/full-method-results/' in selector or 'AttachCompletionBarrier/' in selector:out['actual_layer']='COMPILED_TEST_EXE_REAL_LOOPBACK_HTTP_PRIVATE_CLI_CALL_PATH'
 elif '/real-' in selector:out['actual_layer']='COMPILED_CLI_REAL_API_CLOSED_SQLITE_SYNTHETIC_RUNTIME'
 else:out['actual_layer']='COMPILED_CLI_TYPED_LOOPBACK_FIXTURE'
 new.append(out)
assert sum(x['status']=='PASS' for x in new)==99
assert sum(x['status']=='HOLD_NOT_RUN_CURRENT' for x in new)==2
reg=[]
for exact in scope['approved_exact_regression_selectors']:
 group=exact[1:-1]
 matches=[(p,x) for p,x in current if '-test.run='+exact in x['actualargv']]
 assert len(matches)==1,(group,len(matches))
 p,x=matches[0]
 reg.append({'selector':exact,'result_ref':ref(p),'exit_code':0,'leaf_count':len(x['leaf_events']),'leaf_events':x['leaf_events'],'event_counts_including_parent':x['event_counts_including_parent']})
coverage_ref=save('current-leaf-coverage.json',{'build_ref':ref(B/'build-result.json'),'new_inventory_ref':ref(N/'finite-inventory-r305.json'),'new_leaf_count':101,'new_pass':99,'new_hold':2,'new_skip':0,'regression_groups':21,'regression_leaf_pass':sum(r['leaf_count'] for r in reg),'regression_skip':0,'new_leaves':new,'regressions':reg,'all_current_results':[ref(p) for p,x in current],'no_formal_acceptance':True})
save('all-cohort-results.json',{'note':'Historical failed and pre-amendment cohorts remain immutable; not added to current pass totals. Parent and leaf failure events do not create extra failure origins.','runs':allruns})

case_source=load(P/'future_case_matrix.json');case_map={}
def add(k,selectors,notes='',status='OBSERVED_CONTROLS'):
 case_map[k]={'selectors':selectors,'notes':notes,'status':status}
I='TestCLIProtocolInteractiveAuthority/';A='TestCLIProtocolAttachCompletionBarrier/';V='TestCLIProtocolStrictResponse/';E='TestCLIProtocolExitClassification/'
add('P01-01',[I+'real-existing-open-readonly'],'Actual earlier HTTP500, raw request presentation only; future hook preserves exact bytes.','HOLD_PRODUCER_DEFECT')
add('P01-02',[I+'real-existing-self-send'],'Not run after first unexpected common list producer failure.','HOLD_PRODUCER_DEFECT')
add('P01-03',[I+'fixture-foreign-writer'],'Typed protocol fixture only. Proposed real API foreign-writer resource path not executed because existing-session list producer remains blocked.','PARTIAL_LAYER_GAP')
add('P01-04',[I+'real-new-created-owned-send'],'CAS305 supersedes redundant attach rule only for COMPLETED newly created valid own lease; actual API durable one send returns BLOCKED3 without MODEL.')
add('P01-05',[I+'new-two-multiline-turns'])
add('P01-06',[I+'fixture-invalid-list'])
add('P01-07',[I+'fixture-list-other-item'])
add('P01-08',[I+'fixture-slash-read-only','TestW05CLIInteractiveBeforeEOFAndSlash'])
for i,names in enumerate([['ack-then-completed'],['permanent-ack'],['ack-then-conflict'],['ack-cancel'],['false-acquired'],['foreign-writer','expired-writer'],['caller-epoch-not-authority'],['typed-cancel-ack']],1):
 add('P03-A%02d'%i,[A+n for n in names],'Compiled test executable calls actual private CLI path through loopback HTTP; not an independent production CLI child. Real domain attach completion remains HOLD.')
vnames=[['protocol','command','method'],['valid-null','missing-session','foreign-session'],['valid-null','valid-zero','missing-revision','fraction','overflow','large-exact'],['client'],['snapshot-project','snapshot-session','snapshot-revision','snapshot-missing-writer','snapshot-fraction-epoch'],['full-method-results/'],['ack-empty','ack-snapshot','ack-null'],['rejected-no-error','error-code-mismatch'],['duplicate','escaped-duplicate','nested-duplicate'],['invalid-utf8','surrogate','trailing-value'],['near-integer','fraction','large-exact','overflow'],['top-in-progress','top-not-implemented']]
for i,names in enumerate(vnames,1):
 sels=[]
 for name in names:sels.extend([s for s in index if s.startswith(V+name)] if name.endswith('/') else [V+name])
 add('P03-V%02d'%i,sels,'Method-shape controls reject invalid arbitrary method_confirmed results; they do not claim positive execution of all methods.' if i==6 else '')
add('P03-V13',[r['selector'][1:-1] for r in reg[:4]])
add('P03-V14',[r['selector'][1:-1] for r in reg[4:13]])
add('P03-V15',['TestW05CLIFollowRefusesIncompleteExecution','TestW05CLIGoalDraftAndExecutionOutcomes'])
add('P03-V16',[V+'invalid-last-reply'])
add('P04-01',[E+'NOT_IMPLEMENTED'],'Root resource-category ruling; legal typed REJECTED only.')
add('P04-02',[E+'illegal-top'])
add('P04-03',[E+'FORBIDDEN',E+'MODEL_UNAVAILABLE',E+'INVALID_REQUEST'])
add('P04-04',[E+'INTERNAL_ERROR',E+'http503'])
add('P04-05',['TestCLIReadStatusActualWindowsConsoleSignal'],'Actual hidden Windows console signal in protected test; its TempDir child binary was not retained, original trace/build inputs remain, do not claim retained child exe.')
cases=[]
for old in case_source['cases']:
 row={'id':old['id'],'original_expected':old['expected'],'original_layer':old['layer']}
 if old['id'] in case_map:
  row.update(case_map[old['id']]);refs=[]
  for s in row['selectors']:
   for name,e in index.items():
    if name==s or name.startswith(s+'/'):
     if e['result_ref'] not in refs:refs.append(e['result_ref'])
  row['actual_result_refs']=refs
 else:row.update(status='HOLD_NOT_RUN',selectors=[],actual_result_refs=[],notes='Original full harness/native bootstrap/P02 requirements preserved; source compilation and literal-ID audit are not execution.')
 cases.append(row)
save('scenario-coverage.json',{'original_matrix_ref':ref(P/'future_case_matrix.json'),'rows':41,'immediate_rows':37,'original_hold_rows':4,'cases':cases,'qualification':'Observed controls are evidence, not whole-scenario product acceptance. Actual layers override original planned layers; explicit gaps remain.'})
save('old26-and-checkids.json',{'old26_ledger_ref':ref(P/'old26_revision_ledger.json'),'original_ids_ref':ref(P/'original_ids_preserved.json'),'current_static_audit_ref':ref(N/'protected-source-audit-current.json'),'formal_harness_executions_this_scope':0,'original_report':'69 recorded successful check IDs; 26 failure entries. Neither is a current aggregate PASS count.','full_harness_status':'HOLD','harness_build_only_ref':ref(B/'harness-build-only.invocation.json')})

dbs=[ref(p) for p in N.rglob('*.db')]
save('sqlite-artifacts.json',{'artifacts':dbs,'note':'Owned fixture snapshots only. Preserve each original path; only explicit cleanup/close trace establishes closed status, a .db suffix alone does not.'})
oldhandoffs=[]
for p in N.glob('r305-*/handoff.json'):oldhandoffs.append(ref(p))
oldhandoffs.append(ref(N/'pre-amendment-handoff/handoff.json'))
save('failure-history-links.json',{'sealed_origin_handoffs':oldhandoffs,'new_nonzero_origins_since_goal_supplement':0,'counters':'Root is sole canonical counter owner. No reset or retrospective invented outer exit.','raw_history_included':True})
save('git-source-commit.json',{'actual_argv':['git','commit','-m','fix(cli): validate typed replies and preserve completion barriers'],'actual_outer_exit':0,'actual_chunk':'b92174','commit':commit,'paths':paths,'receipt_commit':'separate later commit'})
save('handoff.json',{'status':'IMPLEMENTATION_AND_FINITE_VALIDATION_REPORTED_NOT_SELF_ACCEPTED','executor':'codex:/root/sources_parent_impl','source_commit':commit,'base_commit':scope['base_commit'],'source_manifest_ref':source_ref,'current_coverage_ref':coverage_ref,'current_inputs_ref':ref(D/'inputs.current.json'),'closure_ref':ref(D/'closure.json'),'compiled_archives_after_ref':ref(D/'compiled-archives.after.json'),'build_ref':ref(B/'build-result.json'),'cli_binary_ref':ref(B/'researchos-cli.exe'),'test_binary_ref':ref(B/'cli.test.exe'),'harness_binary_build_only_ref':ref(B/'cli-contract.exe'),'new_tests':{'inventory':101,'pass':99,'held':2,'skip':0},'regressions':{'groups':21,'leaf_pass':sum(r['leaf_count'] for r in reg),'skip':0},'scenario_matrix_ref':ref(D/'scenario-coverage.json'),'failure_history_ref':ref(D/'failure-history-links.json'),'production_source_edits':8,'SDK_MODEL_EXTERNAL_PAID_CALLS':0,'holds':['Frozen22752 session.list nonnull SID accepted then original response identity mismatch HTTP500; two existing real API leaves held','P01-03 real API foreign writer scenario has typed fixture only','Real domain attach(true) acknowledgement has no COMPLETED producer; acquisition/renewal completion not fabricated','P02 actual checkpoint resume and full formal harness remain held','Original old26 harness failures unchanged; source compile not claim fixed aggregate','Independent source review and Root integration not performed by executor'],'evidence_limits':['23 generic method response controls and 10 attach controls run private CLI call path inside compiled test.exe through actual loopback, not standalone CLI child','Old failed existing API request JSON is reformatted presentation; exact original request bytes not reconstructed','Protected native Windows signal test deletes its temporary child exe after return; retained transcript and compiler closure do not replace missing historical binary'],'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print('SOURCE',commit,'NEW_PASS',99,'REGRESSION_LEAF',sum(r['leaf_count'] for r in reg),'HANDOFF',sha(D/'handoff.json'))
