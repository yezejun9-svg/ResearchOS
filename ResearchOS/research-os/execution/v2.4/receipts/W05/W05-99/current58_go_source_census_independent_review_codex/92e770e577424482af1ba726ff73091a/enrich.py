import pathlib,json,re,hashlib
O=pathlib.Path(__file__).parent;R=O.parents[7]
# Explicit root avoids assumptions about receipt nesting.
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
def load(p):return json.loads(pathlib.Path(p).read_bytes())
def ref(p):
 b=pathlib.Path(p).read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(n,x):
 with (O/n).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
c=load(O/'census.json');fs=load(O/'all-source-functions.json');sm=load(R/'execution/v2.4/receipts/W05/W05-99/whole58_terminal_evidence_gap_independent_review_codex/669dc830cf8b9f5360d36592c380f044/suite-map.json')
batches=[]
for b in sm['old_whole38_selected_batches']:
 d=b['package'].removeprefix('./');avail=sorted({t['name'] for t in c['tests'] if t['package_key'].split(':')[0]==d})
 selected=b.get('exact_top_selectors');rx=b.get('run_regex')
 if selected is None:selected=[n for n in avail if re.search(rx,n)]
 batches.append({'id':b['id'],'directory':d,'original_selector':b.get('run_regex',b.get('exact_top_selectors')),'current_exact_top_names':selected,'missing':[n for n in selected if n not in avail],'original_timeouts_are_historical_not_current_grant':{'test':b.get('test_timeout'),'outer':b.get('outer_timeout')},'current_qualified':False})
env=[];skips=[];constraints=[];regex_declarations=[]
for p in c['packages']:
 for f in p['go_files']:
  path=f['path'];s=(R/path).read_text(encoding='utf-8-sig');lines=s.splitlines()
  # Cross-check independent conventional declaration pattern; current source has no generic testing.T wrappers.
  if path.endswith('_test.go'):
   regex_declarations.extend((path,m.group(1)) for m in re.finditer(r'^func\s+(Test[^a-z\s(][\w]*)\s*\(\s*\w+\s+\*testing\.T\s*\)',s,re.M))
  for i,line in enumerate(lines):
   owner=[x['id'] for x in fs if x['path']==path and x['line']<=i+1<=x['end_line']]
   r={'path':path,'line':i+1,'text':line.strip(),'function_candidates':owner}
   if re.search(r'\.(?:Skip|Skipf|SkipNow)\(',line):skips.append(r|{'preceding_context':lines[max(0,i-3):i]})
   if re.search(r'os\.(?:Getenv|LookupEnv)\(',line):env.append(r|{'keys':re.findall(r'os\.(?:Getenv|LookupEnv)\("([^"]+)"',line)})
  if f['build_constraints'] or re.search(r'_(?:windows|linux|darwin|amd64|arm64)(?:_test)?\.go$',path):constraints.append(f)
actual={(t['path'],t['name']) for t in c['tests']};independent=set(regex_declarations)
cross={'lexical_count':len(actual),'independent_line_regex_count':len(independent),'only_lexical':sorted(actual-independent),'only_regex':sorted(independent-actual)}
matrix=[]
for t in c['tests']:
 sigs=t['reachable_local_signals'];text='\n'.join(x['text'] for x in sigs)
 flags=[]
 if any(k in text for k in ('RESEARCHOS_RUNTIME_LIVE','RESEARCHOS_C01_MODEL')):flags.append('EXPLICIT_REAL_MODEL_AUTHORIZATION_REQUIRED')
 if 'RESEARCHOS_MU_BUNDLE' in text:flags.append('ACTUAL_NODE_MU_BUNDLE_REQUIRED_LOCAL_FIXTURE_POSSIBLE')
 if any(k in text for k in ('W14_GO_TOOLCHAIN','RESEARCHOS_GO','CommandContext','exec.Command')):flags.append('NATIVE_CHILD_TOOL_RESOURCES_REQUIRE_SCOPE')
 if any(k in text for k in ('.Skip(','.Skipf(','.SkipNow(')):flags.append('SKIP_PATH_REACHABLE_STATIC')
 if any(k in text for k in ('NewServer','NewTLSServer')):flags.append('LOCAL_HTTP_FIXTURE_CONSTRUCTION_OBSERVED')
 matrix.append({'id':t['id'],'path':t['path'],'line':t['line'],'flags':flags or ['NO_SIGNAL_IN_LIMITED_LOCAL_SCAN_NOT_PROOF_OF_PURITY'],'referenced_signal_locations':list(dict.fromkeys(x['path']+':'+str(x['line']) for x in sigs)),'runtime_state':'NOT_RUN_IN_THIS_CENSUS'})
changed=[{'path':f['path'],'tests':[t['name'] for t in c['tests'] if t['path']==f['path']]} for p in c['packages'] for f in p['go_files'] if f['in_combined58_delta']]
package_proposal=[]
for d in sorted({p['directory'] for p in c['packages']}):
 names=sorted({t['name'] for t in c['tests'] if t['package_key'].split(':')[0]==d})
 package_proposal.append({'package_directory':d,'all_platform_top_test_names':names,'proposed_exact_top_regex':'^('+'|'.join(names)+')$' if names else None,'target_platform_names':'MUST_DERIVE_FROM_FRESH_GO_GRAPH_BEFORE_GRANT','numeric_runtime_http_process_model_caps':None,'execution_authorized':False})
contracts=pathlib.Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/contracts');plan=load(contracts/'execution.plan.json');selected=[x for x in plan['steps'] if x['id'] in ('W05-99','W13-99','W20-99')]
write('old-batches.current-name-map.json',batches);write('skip-and-environment.json',{'skip_sites':skips,'environment_sites':env,'platform_constraints':constraints});write('test-resource-matrix.json',matrix);write('combined58-go-test-coverage.json',changed);write('census-parser-crosscheck.json',cross)
write('whole-suite.contract.proposal.json',{'schema':'researchos.current58-whole-go-suite-source-proposal.v1','source_commit':c['source_commit'],'status':'SOURCE_CENSUS_ONLY_NOT_ADOPTED','execution_authorized':False,'whole_suite_qualified':False,'formal_acceptance':False,'packages':package_proposal,'required_before_any_execution':['Freeze exact current source/head/canonical authority and explicit new scope','Fresh actual target-platform Go graph including generated/testmain/importcfg/link/archives/embed/toolchain/executables; test-name roster reconcile','Review transitive side effects; live-model/private evidence/historical executables held absent explicit separate scope','Pin native child/tool/OS/HTTP resources and numerical budgets, then independent scope/CAS/grant','Unexpected FAIL/SKIP/unknown module/closure drift stops qualification; preserve first cause and all actual exits','No arithmetic union of historical38, CLI2, DesktopGo3/Node169 creates whole-suite or formal acceptance'],'implementation_plan_ref':ref(contracts/'execution.plan.json'),'selected_plan_steps':selected,'signing_semantics':'Existing parent task and 42 formal acceptance contract remains authoritative; no new source acceptance sink invented'})
write('enrich-input-refs.json',[ref(contracts/n) for n in ('execution.plan.json','acceptance.json','tasks.json')])
print(json.dumps({'batches':[{ 'id':b['id'],'present':len(b['current_exact_top_names']),'missing':b['missing']} for b in batches],'crosscheck':cross,'skip_sites':len(skips),'env_sites':len(env),'changed_go_files':len(changed),'changed_go_top_tests':sum(len(x['tests']) for x in changed),'tests_with_live_flag':[x['id'] for x in matrix if 'EXPLICIT_REAL_MODEL_AUTHORIZATION_REQUIRED' in x['flags']]},ensure_ascii=False))
