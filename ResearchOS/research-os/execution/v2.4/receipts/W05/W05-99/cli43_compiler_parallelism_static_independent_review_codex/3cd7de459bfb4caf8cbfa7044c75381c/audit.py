from pathlib import Path
import json,hashlib,ast,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';C=P/'cli43_compiler_parallelism_preparation_codex/8ac0acd36c6047beaab455730692d078';T=P/'cli43_quiet_build_readonly_triage_codex/11fc59d13e2547ebbf71c593b46f596a';O=Path(__file__).parent
checks=[];refs=[]
def path(v):
 p=Path(v);return p if p.is_absolute() else R/p
def pin(p):
 p=path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(n,b):
 checks.append({'check':n,'passed':bool(b)})
 if not b:raise ValueError(n)
def read(p):return json.loads(path(p).read_bytes())
def verify(r):
 p=path(r['path']);a=pin(p);check('pin '+r['path'],a['sha256']==r['sha256'] and a['bytes']==r['bytes']);refs.append(r);return p
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
try:
 for p,h in [(C/'handoff.json','906e713f8ba9d6a0787b86d9b43b6d456f8b28d7784352df10e6d89f7543a605'),(C/'manifest.json','d7e74c8e1b3eea2264df682d03dcffa2ce0a5924e80180764a0065a0121de8c7'),(T/'handoff.json','4dc80e999a34359ff8eed34cbc8d819fc81fd71f4b04132ffede7c28714c99ba'),(T/'manifest.json','5c22be6bbb91ce5a67edcdf1d1003d085bc954d11786e8fed3a8f12137a76dd7')]:check('supplied '+str(p),pin(p)['sha256']==h)
 for p in [C/'manifest.json',T/'manifest.json']:
  m=read(p);check('self exclusion '+str(p),m['self_excluded_only'] is True)
  for r in m['members']:verify(r)
 h=read(C/'handoff.json');new=verify(h['candidate_ref']).read_bytes();old=verify(h['prior_v5']).read_bytes();verify(h['triage_handoff']);check('candidate precise SHA',hashlib.sha256(new).hexdigest()=='333d69e00a421efcbb08e9ddf06e1486e911cd82af4a0d46a8bb60c8203f2bea')
 substitutions=[(b"run('build-cli',[go,'build','-p=1','-mod=readonly'",b"run('build-cli',[go,'build','-mod=readonly'"),(b"run('build-test',[go,'test','-c','-p=1','-mod=readonly'",b"run('build-test',[go,'test','-c','-mod=readonly'")];inverse=new
 for a,b in substitutions:check('exact one site '+a.decode(),new.count(a)==1);inverse=inverse.replace(a,b)
 check('whole byte inverse',inverse==old);check('byte delta14',len(new)-len(old)==14);check('AST inverse',ast.dump(ast.parse(inverse.decode()),include_attributes=False)==ast.dump(ast.parse(old.decode()),include_attributes=False));ast.parse(new.decode())
 calls={}
 for x in ast.walk(ast.parse(new.decode())):
  if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='run' and x.args and isinstance(x.args[0],ast.Constant) and x.args[0].value in ['build-cli','build-test']:
   calls[x.args[0].value]={'line':x.lineno,'argv_ast':ast.dump(x.args[1]),'literal_argv':[z.value if isinstance(z,ast.Constant) else None for z in x.args[1].elts],'timeout_ast':ast.dump(x.args[3]),'remaining_call_ast':[ast.dump(z) for z in x.args[4:]]}
 check('exact2 build callsites',set(calls)=={'build-cli','build-test'});check('both timeouts600',all(x['timeout_ast']=='Constant(value=600)' for x in calls.values()))
 inputs=read(C/'inputs.before-after.json');check('author input drift0',inputs['drift']==[])
 for r in inputs['files']:verify(r)
 b=(C/'inputs/01-build.go').read_text();tf=(C/'inputs/02-testflag.go').read_text();cfg=(C/'inputs/03-cfg.go').read_text();exe=(C/'inputs/04-exec.go').read_text();helper=(T/'sources/12-windows_debug_job_tree.py').read_text()
 check('build registration', 'AddBuildFlags(CmdBuild, DefaultBuildFlags)' in b and 'cmd.Flag.IntVar(&cfg.BuildP, "p", cfg.BuildP, "")' in b)
 check('test c/p share command flagset','work.AddBuildFlags(CmdTest, work.OmitVFlag|work.OmitJSONFlag)' in tf and 'cf.BoolVar(&testC, "c", false, "")' in tf and 'cmdflag.ParseOne(&CmdTest.Flag, args)' in tf)
 check('worker consumer','par := cfg.BuildP' in exe and 'for i := 0; i < par; i++' in exe);check('default GOMAXPROCS','BuildP                 = runtime.GOMAXPROCS(0)' in cfg)
 check('helper active cap unchanged','limits.BasicLimitInformation.ActiveProcessLimit = min(process_cap, 16)' in helper and 'limits.BasicLimitInformation.LimitFlags' in helper)
 th=read(T/'handoff.json');facts=read(verify(th['facts_ref']));selection=read(verify(th['parent_selected_next_preparation_ref']));verify(th['original_diagnostic_plan_ref']);check('parent selection preparation only',selection['actual_execution_authorized'] is False and selection['original_one_stage_diagnostic_plan_preserved'] is True and selection['root_cause'] is None)
 actual=read(verify(facts['invocation_ref']));d=actual['result']['debug_capture'];live=set();timeline=[];peak=0
 for i,e in enumerate(d['events']):
  if e['code']==3:check('create unseen '+str(i),e['pid'] not in live);live.add(e['pid'])
  elif e['code']==5:check('exit existing '+str(i),e['pid'] in live);live.remove(e['pid'])
  else:continue
  peak=max(peak,len(live));timeline.append({'event_index':i,'code':e['code'],'pid':e['pid'],'live_after':len(live)})
 check('timeline exacttriage',timeline==facts['concurrency_timeline']);check('peak16/end0',peak==16==facts['peak_live_by_order'] and not live and facts['end_live']==0)
 check('triage preserves unknown cause',th['cause'] is None and th['actual_target_calls']==0 and th['original_underlying_failure_count']==1)
 oldreview=P/'cli43_failed_execution_independent_review_codex/f41d184815b341e086a26d2a750f0b60/review.json';check('reused failedclosure',pin(oldreview)['sha256']=='8cb8fb307dabe2668a736d7e964177a1fd67605a7f380d5f6e06d9268d59a6bb')
 save('audit.json',{'checks':checks,'verified_refs':refs,'changed_calls':calls,'event_reconstruction':{'peak_live':peak,'end_live':len(live),'timeline':timeline},'actual_target_execution':False,'full_resource_tree_rehashed':False})
 review={'schema':'researchos.cli43-compiler-parallelism-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_NEW_SCOPE_PREPARATION','requested_changes':[],'candidate_ref':pin(C/'runner.v6.proposed.py'),'candidate_manifest_ref':pin(C/'manifest.json'),'candidate_handoff_ref':pin(C/'handoff.json'),'prior_runner_ref':h['prior_v5'],'triage_handoff_ref':pin(T/'handoff.json'),'triage_manifest_ref':pin(T/'manifest.json'),'selection_supplement_ref':th['parent_selected_next_preparation_ref'],'prior_failed_execution_review_ref':pin(oldreview),'audit_ref':pin(O/'audit.json'),'changes':['Exactly -p=1 added to build-cli line464 and build-test line465; +14 bytes. Whole-file and AST inverse equals v5.','Pinned Go AddBuildFlags registers integer -p for build and test; test -c and -p=1 share CmdTest.Flag and occur before package arguments.','cfg.BuildP feeds build worker scheduling. This does not cap compile.exe internal -c threads, change test semantics, or prove absence of any other child creation.'],'triage_assessment':{'observed_CreateExit_processes':25,'reconstructed_peak_live':16,'end_live':0,'helper_active_process_limit':16,'quota_failure_observed':False,'failed_CreateProcess_error_code':None,'actual_GOMAXPROCS':None,'actual_interrupt_observed':None,'ordinary_build_StartSigHandlers_reachability_proven':False,'root_cause':None},'preserved':'Go-list/buildvcs, Job16/total2048, image/resource guards,600s build limits,3300/3600 enclosing bounds, HTTP caps, case roster, business instrumentation, assertions, first-stop and nullable exits are byte-identical outside the two additions. No permission or qualification cap is widened.','required_next':'Root must freeze a new actual scope, runtime/code references, fresh execution namespace/export/cache/compiler outputs and independently reviewed registration/CAS/seal/unique grant before one bounded changed-input run. This review authorizes preparation only. Prior r326 failure remains; no same-input retry or old-cache/exe reuse.','reused_scope_review':'9a02c0c42aa3d1fc4c4464171175416c450d2be4e52abfbe64c6c4c6f6b85fb3; narrow inverse review only, not repeated resource qualification.','actual_target_execution':False,'execution_authorized':False,'source_acceptance':False,'formal_increment':0,'new_failure_origins':[],'status':'STOPPED'}
 save('review.json',review);print(json.dumps({'checks':len(checks),'review':pin(O/'review.json')},ensure_ascii=True))
except BaseException:
 save('audit.failure.json',{'traceback':traceback.format_exc(),'checks':checks,'actual_target_execution':False});raise
