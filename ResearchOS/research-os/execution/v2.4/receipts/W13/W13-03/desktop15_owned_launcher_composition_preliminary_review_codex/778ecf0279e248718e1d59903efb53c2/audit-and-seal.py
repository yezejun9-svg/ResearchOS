from pathlib import Path
import ast,json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
B=R/'execution/v2.4/receipts/W13/W13-03/desktop15_root_scope_binding_executor_codex/8792799f829a23452ae5d89a59e1b0cf'
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return pin(O/n)
s=json.loads((B/'scope.bound.proposed.json').read_bytes());check=[]
def ck(v,label):check.append({'check':label,'passed':bool(v)})
ck(pin(B/'scope.bound.proposed.json')['sha256']=='0672885b089a13beae915a87dc57aeaa978e92eaccd8870aad16af143d36e9a2','unchanged bound proposal')
src={}
for name in ['launcher_ref','controller_ref','owned_process_helper_ref','runtime_resources_ref']:
 ref=s[name];p=Path(ref['path']);actual=pin(p);ck(actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes'],'actual '+name);src[name]=p.read_text(encoding='utf-8')
launcher=src['launcher_ref'];controller=src['controller_ref'];runtime=json.loads(src['runtime_resources_ref']);catalog={str(Path(x['path'])).casefold():x for x in runtime['files']}
ck(len(catalog)==len(runtime['files'])==1212,'1212 unique runtime paths')
outer=dict(catalog);inner=dict(catalog)
for name in ['launcher_ref','controller_ref','owned_process_helper_ref']:outer[str(Path(s[name]['path'])).casefold()]=s[name]
for name in ['controller_ref','owned_process_helper_ref']:inner[str(Path(s[name]['path'])).casefold()]=s[name]
for name in ['launcher_ref','controller_ref','owned_process_helper_ref']:ck(outer[str(Path(s[name]['path'])).casefold()]==s[name],'outer dynamic exact '+name)
for name in ['controller_ref','owned_process_helper_ref']:ck(inner[str(Path(s[name]['path'])).casefold()]==s[name],'inner dynamic exact '+name)
imports={}
for name in ['launcher_ref','controller_ref','owned_process_helper_ref']:
 tree=ast.parse(src[name]);items=[]
 for n in tree.body:
  if isinstance(n,ast.Import):items.extend(x.name for x in n.names)
  elif isinstance(n,ast.ImportFrom):items.append(n.module)
 imports[name]=sorted(set(items))
ck(set(imports['controller_ref'])<=set(imports['launcher_ref']),'imported controller no new top-level stdlib relative launcher')
root=Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64')
expectedpaths=[root/'Lib'/n for n in ['argparse.py','datetime.py','hashlib.py','json/__init__.py','os.py','traceback.py','types.py','pathlib/__init__.py','urllib/parse.py','ctypes/__init__.py','ctypes/wintypes.py','subprocess.py']]+[root/'DLLs/_ctypes.pyd',root/'python.exe',root/'python314.dll']
for p in expectedpaths:ck(str(p).casefold() in catalog,'known static import resource '+str(p))
ck("types.ModuleType('desktop15_authority_readonly')" in launcher and "controller.__file__=s['controller_ref']['path']" in launcher and "sys.modules[controller.__name__]=controller" in launcher,'outer imported controller exact path identity')
ck("exec(compile(source,controller.__file__,'exec'),controller.__dict__)" in launcher and "controller.grant_check(s,sref,g)" in launcher,'cached verified source only; pure grant_check before child')
ck("if __name__=='__main__':" in controller and "controller=types.ModuleType('desktop15_authority_readonly')" in launcher,'import name does not execute controller main')
ck("controller.DEADLINE=DEADLINE;controller.BASE=s['expected_cli43_head']" in launcher,'pure authority read gets deadline and explicit base')
ck("sref['path']=g['scope_ref']['path']" in launcher and "grant['scope_ref']==sref" in controller,'serialized scope ref spelling preserved')
ck("s['launcher_ref']['path']==str(Path(__file__).resolve())" in launcher and s['launcher_ref']['path']==str(Path(s['launcher_ref']['path']).resolve()),'launcher exact identity matches actual scope')
ck("for n in ['scope','scope-sha256','grant','grant-sha256']" in launcher and "for name in ['scope','scope-sha256','grant','grant-sha256']" in controller,'four CLI flags match')
ck("argv=[python['path'],'-I','-S','-X','utf8',s['controller_ref']['path']" in launcher,'pinned Python launches actual selected controller')
ck(launcher.count('helper.run_owned(')==1 and 'subprocess.run(' not in launcher,'sole source child ownedJob')
ck("timeout=min(1200,max(0,DEADLINE-time.monotonic()))" in launcher and "DEADLINE=time.monotonic()+900" in controller,'outer remaining1200 inner900 unchanged')
ck("observe('runtime.source.before_import',False)" in launcher and "observe('runtime.source.prehelper',False)" in launcher and "runtime('runtime.before')" in launcher,'runtime observations before embedded import/helper/child')
ck("'__file__','__cached__'" in launcher and 'helper.runtime_resource_paths()' in launcher and 'Unpinned outer Python/OS runtime' in launcher,'unknown loaded paths fail closed source+cached+DLL')
ck("copies=controller.grant_check(s,sref,g)" in launcher and "cli43_bounded_qualification_gate(scope['cli43_bounded_qualification_refs'], document, verify, bounded)" in controller,'new held2 gate reached before source child')
ck("for item in copies:require(raw(ROOT/item['canonical_path'])==verify(item['ref'])" in launcher,'outer post-child canonical equality')
ck("for item in protected:verify(item)" in controller and "scope['old_deleted_paths']" in controller and "'commit_attempt_cap':1,'apply_attempt_cap':1" in controller,'inner fullprotected/old11D/source once')
ck('No retry or existing output' in launcher and 'candidate.mkdir(exist_ok=False);out=candidate' in launcher,'exclusive owned output no clobber')
ck("'actual_native_controller_exit':result.get('actual_exit') if isinstance(result,dict) else None" in launcher and "'current_phase_native_exit':None" in launcher,'last child distinct from nullable finalization phase')
ck("attempt('runtime.after'" in launcher and "attempt('invocation.final'" in launcher and "attempt('failure.origin'" in launcher,'finalization evidence paths guarded')
ck(s['exact_paths']==15 and s['union_paths']==58 and len(s['old_deleted_paths'])==11 and s['product_tests_HTTP_SQL_models']==0,'unchanged source-only bounds')
ar=save('audit.json',{'checks':check,'count':len(check),'failed':[x for x in check if not x['passed']],'static_imports':imports,'scope_dynamic_expected_paths':{'outer':[s[k] for k in ['launcher_ref','controller_ref','owned_process_helper_ref']],'inner':[s[k] for k in ['controller_ref','owned_process_helper_ref']]},'target_imports_or_executions':0,'new_failure_origins':[]})
rr=save('review.json',{'schema':'researchos.desktop15-owned-launcher-composition-preliminary-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'PRELIMINARY_COMPOSITION_CHECKED_AWAIT_ACTUAL_SCOPE_AND_GRANT' if all(x['passed'] for x in check) else 'REQUEST_CHANGES','requested_changes':[x for x in check if not x['passed']],'actual_launcher_executed':False,'execution_authorized':False,'final_READY_issued':False,'bound_proposal_ref':pin(B/'scope.bound.proposed.json'),'launcher_ref':s['launcher_ref'],'controller_ref':s['controller_ref'],'runtime_ref':s['runtime_resources_ref'],'helper_ref':s['owned_process_helper_ref'],'audit_ref':ar,'checks_passed':sum(x['passed'] for x in check),'reused_review_ref':pin(R/'execution/v2.4/receipts/W13/W13-03/desktop15_current_bound_scope_independent_review_codex/251396ba3c064b66a823489d7fece242/review.json'),'findings':'No deterministic missing path or producer/consumer field mismatch found in this narrow static composition. Named embedded controller and helper __file__ values are included through explicit dynamic expected refs; catalog1212 remains public partial prediction, not actual future loaded module closure.','remaining':['Actual active scope/sealed registration/current4/grant refs and exact Root launch command must be checked after metadata phases close.','Parent executor/grant directories require safe Root preparation; execution UUID and outer UUID leaves must remain absent.','Loaded Python/pyc/DLL membership is enforced at runtime; no assurance of complete future OS lifecycle or time-fit.','Root must preserve stopped partial source/index state on any error; no retry/reset.','Only exact15 source patch/one commit; no Desktop runtime, Go/Node/SQL/network/SDK/model/formal acceptance.'],'observational_parent_exists':Path(s['new_output_root']).parent.is_dir(),'new_failure_origins':[],'status':'STOPPED'})
hr=save('handoff.json',{'schema':'researchos.public-review-handoff.v1','review_ref':rr,'decision':'PRELIMINARY_COMPOSITION_CHECKED_AWAIT_ACTUAL_SCOPE_AND_GRANT','manifest_path':str(O/'manifest.json'),'actual_target_executions':0,'new_failure_origins':[],'status':'STOPPED'})
rows=[pin(p) for p in sorted(O.iterdir()) if p.is_file()];mr=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','count':len(rows),'entries':rows,'self_excluded':True})
print(json.dumps({'review':rr,'manifest':mr,'handoff':hr,'checks':len(check),'failed':[x for x in check if not x['passed']]},ensure_ascii=False))
