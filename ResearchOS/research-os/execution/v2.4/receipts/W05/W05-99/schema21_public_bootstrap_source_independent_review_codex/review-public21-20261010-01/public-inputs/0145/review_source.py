import pathlib,json,hashlib,types,sys,ast,re
R=pathlib.Path(r'D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';O=pathlib.Path(__file__).resolve().parent
S=B/'genuine_schema21_public_bootstrap_runner_source_codex/s21public-20261010-01'
def pin(path):
 p=pathlib.Path(path).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(path):return json.loads(pathlib.Path(path).read_bytes())
def save(name,value):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def refs(value):
 if isinstance(value,dict):
  if all(k in value for k in ('path','sha256','bytes')):yield {k:value[k] for k in ('path','sha256','bytes')}
  for v in value.values():yield from refs(v)
 elif isinstance(value,list):
  for v in value:yield from refs(v)
h=read(S/'HDF.json');mf=read(S/'MF.json');contract=read(S/'contract.json');inputs=read(S/'input-manifest.json')
assert pin(S/'HDF.json')['sha256']=='257c702cc43df27e845d353f2909f5c01a4db545b7aff1819796c24e94618068'
assert pin(S/'MF.json')['sha256']=='b0707bead1519ca12fa5541ca75ce828553a32e6e1ef6cfe996114f1d1cc1050'
expected=list(refs(h))+list(refs(mf))+list(refs(contract))+list(refs(inputs))+[pin(S/'HDF.json'),pin(S/'MF.json')]
supplement=[pathlib.Path(contract['old21_root'])/p for p in ['apps/control/private_windows.go','apps/control/replay_command.go','internal/domain/contracts.go']]
expected += [pin(p) for p in supplement]+[pin(__file__)]
unique={}
for ref in expected:
 n=dict(path=str(pathlib.Path(ref['path']).resolve()),sha256=ref['sha256'].removeprefix('sha256:'),bytes=ref['bytes']);key=n['path'].casefold()
 if key in unique:assert unique[key]==n,(unique[key],n)
 unique[key]=n
before=[dict(expected=x,actual=pin(x['path']),matched=pin(x['path'])==x) for x in unique.values()]
save('input-pins.json',dict(refs=before,all_matched=all(x['matched'] for x in before)));assert all(x['matched'] for x in before)
gp=contract['source_guard'];graw=pathlib.Path(gp['path']).read_bytes();assert hashlib.sha256(graw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
module=types.ModuleType('public21_review_guard');module.__file__=gp['path'];sys.modules[module.__name__]=module;exec(compile(graw,gp['path'],'exec'),module.__dict__)
guard=module.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=1024*1024*1024);guard.acquire(list(unique.values()))
checks=[]
def check(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail))
try:
 def raw(p):return guard.get_buffer(str(pathlib.Path(p).resolve()))
 def held(p):return json.loads(raw(p))
 source=raw(S/'public21_runner.py').decode();tree=ast.parse(source)
 functions={x.name:x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
 run=functions['run_registered_case'];calls=list(ast.walk(run));ordered=sorted([x for x in calls if isinstance(x,ast.Call)],key=lambda x:(x.lineno,x.col_offset))
 called=[(ast.unparse(x.func),x.lineno) for x in ordered]
 check('78 source members and exact 80-file namespace closure',mf['member_count']==len(mf['members'])==78 and len([p for p in S.rglob('*') if p.is_file()])==80 and {str(pathlib.Path(x['path']).resolve()).casefold() for x in mf['members']}=={str(p.resolve()).casefold() for p in S.rglob('*') if p.is_file() and p.name not in ['HDF.json','MF.json']})
 check('contract and HDF have no runtime grant or self acceptance',not h['execution_grant'] and not h['formal_acceptance'] and not h['Source_self_acceptance'] and not contract['runtime_grant'] and not contract['scope_registration'] and not contract['formal_acceptance'] and all(v is None for k,v in contract.items() if k.startswith('future_')))
 programme=held(contract['old21_qualification_ref']['path'])
 check('root bound genuine old21 programme exact',pin(contract['old21_qualification_ref']['path'])['sha256']=='8b5d6565586e51be741fa25b2f79cf41c55d0f8733c43d0f6a60f2ebca738a70' and programme['source_schema_version']==21 and programme['source_commit']==contract['source_commit'] and programme['source_tree']==contract['source_tree'] and programme['program_refs']['control']==contract['old21_control'] and programme['program_refs']['backup']==contract['old21_backup'] and programme['programme_qualification'] and not programme['execution_grant'])
 # Paths in programme bindings may use different slash spelling; compare physical pins independently below.
 def comparable(ref):return (str(pathlib.Path(ref['path']).resolve()).casefold(),ref['sha256'],ref['bytes'])
 check('qualified control and backup pins included in source guard',all(comparable(programme['program_refs'][role])==comparable(contract['old21_'+role]) for role in ['control','backup']) and all(str(pathlib.Path(contract['old21_'+role]['path']).resolve()).casefold() in unique for role in ['control','backup']))
 numbered={int(pathlib.Path(relative).name[:4]):ref for relative,ref in contract['frozen_runtime_refs'].items() if re.fullmatch(r'[0-9]{4}_.+\.sql',pathlib.Path(relative).name)}
 actual=sorted(int(p.name[:4]) for p in (pathlib.Path(contract['old21_root'])/'migrations/sqlite').iterdir() if re.fullmatch(r'[0-9]{4}_.+\.sql',p.name))
 check('true frozen SQL membership1through21 plus nonnumbered addon',sorted(numbered)==actual==list(range(1,22)) and 'migrations/sqlite/next_v24_sessions.sql' in contract['frozen_runtime_refs'])
 main=raw(pathlib.Path(contract['old21_root'])/'apps/control/main.go').decode()
 store=raw(pathlib.Path(contract['old21_root'])/'internal/domain/store.go').decode()
 private=raw(supplement[0]).decode()
 check('public finite bootstrap branch exits before HTTP and credentials only private file',main.index('if *bootstrapOwner {')<main.index('http.Server') if 'http.Server' in main else main.index('if *bootstrapOwner {')<main.index('ListenAndServe'),dict(bootstrap_line=110))
 check('real constructor applies numbered SQL and session addon in same transaction','next_v24_sessions.sql' in store and 'installClientSessionFence(context.Background(), tx, false)' in store and 'INSERT OR IGNORE INTO schema_migrations(version)' in store and 'tx.Commit()' in store)
 check('generated Owner bytes written only to private fd with Windows DACL','json.NewEncoder(f).Encode' in main and 'windows.SetNamedSecurityInfo' in private and '15*time.Minute' in main and 'owner.read' not in source and 'read_bytes(owner' not in source)
 check('exact child flags and direct child call count','--bootstrap-owner' in ast.get_source_segment(source,functions['compile_case']) and '--credential-file' in ast.get_source_segment(source,functions['compile_case']) and sum(name=='job_module.run_owned' for name,_ in called)==1 and not any(name in ['subprocess.run','subprocess.Popen','os.system'] for name,_ in called),called)
 check('new Root scope runtime authority explicitly delegated before reads','PUBLIC21_BOOTSTRAP_ONLY'==contract['scope_key'] and next(line for name,line in called if name=='root_scope.require_registered')<next(line for name,line in called if name=='read_exact') and len(contract['Root_caller_mandatory_contract'])>=8 and 'require_resources' in contract['Root_scope_interface'])
 helpers=raw(contract['public22_helpers_ref']['path']).decode();owned=raw(contract['owned_job']['path']).decode()
 check('pinned helpers gate0 PIDFILETIME and complete job closure before oracle','actual_exit' in helpers and 'creation_time_100ns' in helpers and 'job_idle_confirmed' in helpers and 'active_processes_last_observed' in helpers and source.index('helpers.closed_job(observed)')<source.index('helpers.readonly_database_observation(db)'))
 check('baseline guarded readonly immutable oracle and no SQL writer in new leaf','mode=ro&immutable=1' in helpers and 'PRAGMA query_only=ON' in helpers and 'connection.close()' in helpers and 'baseline_guard.acquire([baseline_ref])' in source and 'sqlite3' not in source and 'connection.execute' not in source and 'readonly_attribute=True' in source)
 check('OwnedJob suspended assign before resume and bounded finally closure',owned.index("stage = 'ASSIGN_SUSPENDED_CHILD'")<owned.index("stage = 'RESUME_ASSIGNED_CHILD'") and 'finally:' in owned and 'for handle in reversed(handles)' in owned and '90,creation_flags=0x08000000' in source)
 check('source and baseline guards always have finally close','finally:' in ast.get_source_segment(source,run) and "for name,guard in (('baseline',baseline_guard),('source',source_guard))" in source and 'audit=guard.close()' in source)
 author_controls=held(S/'source-controls.json');check('56 author controls retained and not rerun',len(author_controls['checks'])==author_controls['passed']==56 and author_controls['failed']==0 and all(x['passed'] for x in author_controls['checks']))
 closefacts=[]
 for name in ['source-preparation.guard.closed.json','source-controls.guard.closed.json','source-full-closure.guard.closed.json']:
  g=held(S/name);closefacts.append(dict(file=name,entries=len(g['entries']),closed=g['closed'],retained=g['retained_handles_count'],errors=g['errors'],verification=g['verification']))
 check('all three author source guards closed',all(x['closed'] and x['retained']==0 and not x['errors'] and x['verification']=='PASSED' for x in closefacts),closefacts)
 author=held(S/'source-author-audit.json');host_checks=[]
 for pair in author['completed_tool_pairs']:
  bind=held(pair['binding_ref']['path']);capture=raw(pair['raw_ref']['path']);lines=capture.splitlines(keepends=True);records=[json.loads(x) for x in lines]
  hashes=[hashlib.sha256(x).hexdigest() for x in lines]
  copied=(len(lines)==3 and hashes==bind['source_line_sha256'] and [len(x) for x in lines]==bind['source_line_bytes'])
  identity=(records[0]['payload']['id']==author['actual_thread'] and records[0]['payload']['parent_thread_id']==author['actual_parent_thread'] and records[0]['payload']['agent_path']=='/root/backup_regression_resources')
  pair_match=(records[1]['payload']['call_id']==records[2]['payload']['call_id']==pair['call_id']==bind['actual_call_id'])
  original_matches=[]
  with pathlib.Path(bind['source_audit_path']).open('rb') as f:
   for offset,size,line in zip(bind['source_line_offsets'],bind['source_line_bytes'],lines):
    f.seek(offset);original_matches.append(f.read(size)==line)
  host_checks.append(dict(call_id=pair['call_id'],three_line_copy_exact=copied,actual_author_identity=identity,paired_original_call_output=pair_match,original_offset_bytes_match=all(original_matches),no_Root_authority=not bind['Root_issuer'] and not bind['execution_grant'] and not bind['formal_acceptance']))
 check('29 completed source host pairs match original exact offsets and author identity',len(host_checks)==author['completed_pair_count']==29 and all(all(v is True for k,v in x.items() if k!='call_id') for x in host_checks))
 save('author-provenance-checks.json',dict(pairs=host_checks,inflight_sealer_claim=author['inflight_sealer_result_capture'],future_result_not_fabricated=True))
 # The only new pure control executes one existing AST statement, with in-memory values.
 statement=next(n for n in ast.walk(run) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='invocation.update')
 assert statement.lineno==173
 code=compile(ast.fix_missing_locations(ast.Module(body=[statement],type_ignores=[])),str(S/'public21_runner.py')+'#line173-only','exec')
 injections=[]
 for fail_at in [1,2]:
  invocation=dict(actual_exit=None,observation=None)
  observed=dict(actual_exit=0,job_cleanup=dict(handles_closed=True,job_idle_confirmed=True,primary_exit_confirmed=True,active_processes_last_observed=0,errors=[]),synthetic_pure_control=True)
  seen=[]
  def fail_ref(path):
   seen.append(path)
   if len(seen)==fail_at:raise OSError('INJECTED_PUBLIC_OUTPUT_READ_FAILURE')
   return dict(path='synthetic-only',sha256='0'*64,bytes=0)
  scope=dict(invocation=invocation,observed=observed,observed_ref=fail_ref,stdout='synthetic_stdout',stderr='synthetic_stderr',time=types.SimpleNamespace(time_ns=lambda:1))
  try:exec(code,scope);error=None
  except OSError as exc:error=str(exc)
  lost=invocation['actual_exit'] is None and invocation['observation'] is None
  injections.append(dict(fail_at_output='stdout' if fail_at==1 else 'stderr',expected_fault_caught=error=='INJECTED_PUBLIC_OUTPUT_READ_FAILURE',returned_job_observation_was_available=True,actual_returned_exit_synthetic=observed['actual_exit'],recorded_exit_after_failure=invocation['actual_exit'],recorded_job_observation_after_failure=invocation['observation'],data_loss_reproduced=lost,run_registered_case_called=False,Root_scope_created=False,product_native_SQL_Go_calls=0))
 check('new uncovered postchild artifact failure loses already returned actual job evidence',all(x['expected_fault_caught'] and x['data_loss_reproduced'] for x in injections),injections)
 save('uncovered-output-failure-control.json',dict(schema='researchos.independent-pure-source-counterexample.v1',source_ref=pin(S/'public21_runner.py'),source_lines=[173,173],exact_statement=ast.get_source_segment(source,statement),method='One original AST statement executed with in-memory synthetic job data and injected OSError; no full runner/caller/native/SQL invocation',controls=injections,author56_not_rerun=True,finding='PUBLIC21-OBSERVATION-001',actual_exit_0_is_synthetic_not_native=True))
 copies=[]
 for i,ref in enumerate(unique.values()):
  # Exact input pins remain primary; binaries/build.closed are not duplicated.
  if ref['bytes']>2*1024*1024:continue
  p=pathlib.Path(ref['path']);dest=O/'public-inputs'/str(i).zfill(4)/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(raw(p))
  copies.append(dict(original_ref=ref,copy_ref=pin(dest)))
 save('public-copy-index.json',copies)
 save('source-review-checks.json',dict(checks=checks,all_verification_checks_passed=all(x['passed'] for x in checks),sourceguard_entries=len(unique),copied_public_inputs=len(copies),source_member_count=78,decision='REQUEST_CHANGES_SOURCE_ONLY',product_execution_count=0,Go_SQL_native_model_TP_calls=0,Root_issuer_created=False,author_controls_rerun=False,new_pure_controls=2,blocking_findings=['PUBLIC21-OBSERVATION-001'],counter_reset=False))
finally:
 closed=guard.close();save('sourceguard.closed.json',closed);assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
after=[dict(expected=x,actual=pin(x['path']),matched=pin(x['path'])==x) for x in unique.values()]
save('closing-pins.json',dict(refs=after,all_unchanged=all(x['matched'] for x in after)))
print(json.dumps(dict(decision='REQUEST_CHANGES_SOURCE_ONLY',all_verification_checks_passed=all(x['passed'] for x in checks),failed_verification_checks=[x for x in checks if not x['passed']],finding='PUBLIC21-OBSERVATION-001',new_pure_control_cases=2,sourceguard_entries=len(closed['entries']),closed=closed['closed'],all_pins_unchanged=all(x['matched'] for x in after),new_mechanical_failures=0),ensure_ascii=False))

