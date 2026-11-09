"""Writes new receipt templates only; AST parse is not import/execution."""
import ast,hashlib,json,pathlib,difflib
P=pathlib.Path(__file__).resolve().parent
OLD=P.parents[1]/'finite_controller_preparation_codex/2098f8232b5a4331b0cac70eccd32ce0'
def data(p):return p.read_text(encoding='utf-8')
def put(n,text):
 with (P/n).open('xb') as f:f.write(text.encode('utf-8'))
def save(n,obj):put(n,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
common=data(OLD/'controller_common.py')
a=common.index('def validate_grant(');b=common.index('def require_job(',a)
common=common[:a]+data(P/'authorization_contract.py.txt')+'\n\n'+common[b:]
common=common.replace('import base64, hashlib, json, os, re, stat, sys, time, types','import base64, contextlib, hashlib, json, os, re, stat, sys, time, types')
a=common.index('def trusted_module(');b=common.index('AUTHORIZATION_PATHS=',a)
common=common[:a]+'''def trusted_module(path,expected):
 verify(expected)
 if str(path)!=expected['path']:raise Stop('Helper path mismatch')
 raw=Path(path).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected['sha256'] or len(raw)!=expected['bytes']:raise Stop('Helper drift before raw compile')
 mod=types.ModuleType(Path(path).stem);mod.__file__=str(path)
 sys.modules['w09_receipt_'+Path(path).stem]=mod
 exec(compile(raw,str(path),'exec'),mod.__dict__)
 return mod

def existing_ref(path):
 return file_ref(path) if path is not None and Path(path).is_file() else None

'''+common[b:]
put('controller_common.v2.py',common);commonpin=ref(P/'controller_common.v2.py')
bootstrap='''import sys
sys.dont_write_bytecode=True
import argparse, contextlib, hashlib, io, json, os, re, stat, time, types
from pathlib import Path
# Hash actual source bytes BEFORE compile; no importlib loader and no pyc read for controller modules.
_common_path=Path(__file__).resolve().parent/'controller_common.v2.py'
_common_raw=_common_path.read_bytes()
if hashlib.sha256(_common_raw).hexdigest()!=COMMON_SHA:raise RuntimeError('Pinned common source mismatch before import')
if not sys.flags.isolated or not sys.flags.no_site or sys._xoptions.get('utf8') is not True:raise RuntimeError('Pinned -I -S -X utf8 required')
_common=types.ModuleType('w09_common_v2');_common.__file__=str(_common_path);sys.modules[_common.__name__]=_common
exec(compile(_common_raw,str(_common_path),'exec'),_common.__dict__)
globals().update({k:v for k,v in _common.__dict__.items() if not k.startswith('__')})
'''.replace('COMMON_SHA',repr(commonpin['sha256']))
oldcontroller=data(OLD/'controller.py');facts=oldcontroller[oldcontroller.index('def json_stream('):oldcontroller.index('class Controller:')]
init=oldcontroller[oldcontroller.index('class Controller:'):oldcontroller.index(' def run(')]
init=init.replace('self.serial=0;self.tests=0;self.ledger','self.serial=0;self.tests=0;self.results=[];self.attempts=[];self.ledger')
init=init.replace("  self.normal=trusted_module", "  self.ledger.add(g['_authorization_paths'],'consumed-immutable-Root-authorization-chain')\n  write_json(out/'runtime.source.before.json',runtime_source_snapshot(g['resource_files']))\n  self.normal=trusted_module")
init=init.replace("CGO_ENABLED='0',GOFLAGS", "CGO_ENABLED='0',GOOS='windows',GOARCH='amd64',GOAMD64='v1',GOEXPERIMENT='',GODEBUG='',GOFLAGS")
build=oldcontroller[oldcontroller.index(' def build('):oldcontroller.index(' def resources(')]
build=build.replace("'CGO_ENABLED','GOWORK'","'CGO_ENABLED','GOWORK','GOOS','GOARCH','GOAMD64','GOEXPERIMENT','GODEBUG'")
build=build.replace("  self.ledger.check('compile-complete')",'''  generated_mains=[p for p in walk_files(self.out/'gotmpdir') if p.name=='_testmain.go']
  importcfgs=[p for p in walk_files(self.out/'gotmpdir') if p.name.startswith('importcfg')]
  archives={}
  for cfg in importcfgs:
   for line in cfg.read_text(encoding='utf-8',errors='strict').splitlines():
    if line.startswith('packagefile '):
     path=no_alias(line.split('=',1)[1]);pin=file_ref(path)
     if pin['path'].casefold() not in self.ledger.rows:raise Stop('Actual compiler archive outside final full vector')
     archives[pin['path']]=pin
  if len(generated_mains)<2 or not importcfgs or not archives:raise Stop('Actual generated compiler provenance incomplete')
  write_json(self.out/'compiler-derived.json',{'generated_testmain_refs':[file_ref(p) for p in generated_mains],'importcfg_refs':[file_ref(p) for p in importcfgs],'archive_refs':list(archives.values()),'testexe_refs':self.executables,'all_WORK_ref':file_ref(self.out/'compiled-inputs.frozen.json')})
  self.ledger.check('compile-complete')''')
cases=oldcontroller[oldcontroller.index(' def cases('):oldcontroller.index('\ndef main():')]
cases=cases.replace('  result=[]','  result=self.results')
# New native/case proofs remain incrementally reachable even if later facts fail.
cases=cases.replace("result.append({'id':label,'selector':selected,'state':'NOT_RUN_RESOURCE_HOLD','requirements':required,'actual_native_exit':None});continue", "result.append({'id':label,'selector':selected,'state':'NOT_RUN_RESOURCE_HOLD','requirements':required,'actual_native_exit':None});write_json(self.out/('progress-%02d.json'%len(result)),result);continue")
entries=data(P/'entry_bodies.py.txt');launch=entries.split('# === LAUNCH ===\n',1)[1].split('# === WORKER ===\n',1)[0];worker=entries.split('# === WORKER ===\n',1)[1].split('# === CONTROLLER_MAIN ===\n',1)[0];main=entries.split('# === CONTROLLER_MAIN ===\n',1)[1]
topguard='''if __name__=='__main__':
 try:main()
 except BaseException as e:
  # Pre-authority/pre-output failures remain on actual stderr for the Root-owned caller.
  print(json.dumps({'schema':'researchos.w09.entry-failure.v2','error_type':type(e).__name__,'message':str(e),'actual_child_native_exit':None,'counter_reset':False},ensure_ascii=False),file=sys.stderr)
  raise
'''
def guarded(s):return s.replace("if __name__=='__main__':main()",topguard)
put('controller.v2.py',bootstrap+'\n'+facts+init+data(P/'controller_methods.py.txt')+'\n'+build+cases+'\n'+guarded(main))
put('launch.v2.py',bootstrap+'\n'+guarded(launch))
put('case_worker.v2.py',bootstrap+'\n'+guarded(worker))
sealer=data(P/'sealer_body.py.txt')
sealer=sealer.replace("'graph-domain.json','graph-adapter.json'", "'graph-domain.json','graph-adapter.json','compiler-derived.json'")
sealer=sealer.replace("  if not (root/name).is_file():raise Stop('Missing compiled provenance '+name)",'''  if not (root/name).is_file():raise Stop('Missing compiled provenance '+name)
 source_export=raw_json((root/'source-export.json').read_bytes());catalog=read_bound(g['source_catalog_ref'])
 if source_export.get('catalog_ref')!=g['source_catalog_ref'] or source_export.get('complete_before_any_Go') is not True or len(source_export['files'])!=catalog['file_count']:raise Stop('Public export proof')
 for pin,row in zip(source_export['files'],catalog['files']):
  if pin['path']!=str(root/'source'/row['path']) or (pin['sha256'],pin['bytes'])!=(row['sha256'],row['bytes']):raise Stop('Exported public input differs')
  verify(pin)
 derived=raw_json((root/'compiler-derived.json').read_bytes())
 if len(derived['generated_testmain_refs'])<2 or not derived['archive_refs'] or not derived['importcfg_refs']:raise Stop('Compiler generated/archive closure')
 for pin in derived['generated_testmain_refs']+derived['archive_refs']+derived['importcfg_refs']+list(derived['testexe_refs'].values()):
  verify(pin)
  if pin['path'] not in frozenpaths:raise Stop('Derived compiler input not frozen')
 for label in ['domain','adapter']:
  graph=raw_json((root/('graph-'+label+'.json')).read_bytes())
  if not graph or len(graph)>4096 or any(x.get('Error') or x.get('DepsErrors') or x.get('Incomplete') for x in graph):raise Stop('Actual full Go graph failed')''')
sealer=sealer.replace(" members=[file_ref(p) for p in walk_files(root)+walk_files(outerdir)]",''' members=[];links=[]
 permitted_links={str(root/'symlink-prerequisite/A/outside'):root/'symlink-prerequisite/B',str(root/'junction-resource/A/outside'):root/'junction-resource/B'}
 for base in [root,outerdir]:
  for current,dirs,files in os.walk(base,followlinks=False):
   for name in list(dirs)+files:
    path=Path(current)/name;st=path.lstat()
    if stat.S_ISLNK(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400:
     if str(path) not in permitted_links or path.resolve()!=permitted_links[str(path)].resolve():raise Stop('Unexpected evidence alias')
     links.append({'path':str(path),'resolved_target':str(path.resolve()),'file_attributes':getattr(st,'st_file_attributes',None),'mode':st.st_mode,'followed':False})
     if name in dirs:dirs.remove(name)
    elif path.is_file():members.append(file_ref(path))''')
sealer=sealer.replace("'only_self_excluded':True", "'only_self_excluded':True,'owned_links_not_followed':links")
put('seal_readonly.v2.py',bootstrap+'\n'+facts+'\n'+guarded(sealer))
for name in ['windows_debug_job_tree.py']:
 with (P/name).open('xb') as f:f.write((OLD/name).read_bytes())
with (P/'windows_owned_process.py').open('xb') as f:f.write((OLD/'inputs/2-windows_owned_process.py').read_bytes())
save('finite-roster.json',json.loads((OLD/'finite-roster.json').read_bytes()))
s=json.loads((OLD/'spec.json').read_bytes());s['schema']='researchos.w09.finite-controller-spec.v2';s['future_output_parent']=str(P)
files=['controller_common.v2.py','controller.v2.py','launch.v2.py','case_worker.v2.py','seal_readonly.v2.py','windows_debug_job_tree.py','windows_owned_process.py']
s['controller_refs']=[ref(P/n) for n in files]
for key,name in [('controller_ref','controller.v2.py'),('case_worker_ref','case_worker.v2.py'),('launcher_ref','launch.v2.py'),('sealer_ref','seal_readonly.v2.py'),('normal_helper_ref','windows_owned_process.py'),('debug_helper_ref','windows_debug_job_tree.py')]:s[key]=ref(P/name)
s['source_catalog_ref']=ref(P/'public-source-catalog.v2.json');s['roster_ref']=ref(P/'finite-roster.json')
s.update(expected_registration=None,combined_source_closure_ref=None,actual_compilation_closure=None,runtime_catalog_ref=None,resource_catalog_ref=None,execution_authorized=False,selected_controller_executed=False,root_scope_ref=None)
s['old_preparation_refs']=[ref(OLD/n) for n in ['spec.json','manifest.json','handoff.json']]
s['fixes']=['CTRL-01','CTRL-02','CTRL-03','CTRL-04','CTRL-05','CTRL-06']
save('spec.v2.json',s)
grant={'schema':'researchos.w09.finite-controller-root-grant.v2','actor':None,'authorized':False,'actual_registration_completed':False,'status':'PREPARATION_ONLY_NOT_EXECUTABLE','source_commit':s['source_commit'],'base_commit':s['base_commit'],'spec_ref':ref(P/'spec.v2.json'),'caps':s['caps'],'controller_refs':s['controller_refs'],'source_catalog_ref':s['source_catalog_ref']}
for k in ['scope_ref','controller_review_ref','registration_review_ref','registration_audit_ref','registration_intent_ref','registration_invocation_ref','registration_manifest_ref','registration_register_ref','registration_wrapper_ref','canonical_original_refs','canonical_desired_refs','canonical_copy_refs','resource_catalog_ref','runtime_catalog_ref','resource_files','source_compile_basis','combined_source_closure_ref','run_nonce','output_root','output_parent','tools','goroot','module_cache','go_tool_images','git_images','resources','normal_helper_ref','debug_helper_ref']:grant[k]=None
save('root-grant.UNAUTHORIZED.v2.template.json',grant)
scope={'schema':'researchos.w09.finite-root-scope.v2','actor':None,'status':'PREPARATION_ONLY_NOT_REGISTERED','spec_ref':ref(P/'spec.v2.json'),'source_commit':s['source_commit'],'base_commit':s['base_commit'],'caps':s['caps'],'controller_refs':s['controller_refs'],'source_catalog_ref':s['source_catalog_ref'],'expected_before':None,'expected_after':None,'controller_review_actor':None,'source_compile_basis':None,'combined_source_closure_ref':None,'resource_catalog_ref':None,'runtime_catalog_ref':None,'resources':None,'output_parent':str(P),'os_hold_policy':{'not_granted':'HOLD','granted_unexpected_failure':'STOP'},'checkpoint_binding_keys':{'scope':None,'review':None},'actual_invocation_contract':{'argv_pointer':None,'exact_argv':None,'native_exit_pointer':None,'outer_exit_pointer':None}}
save('root-scope.UNREGISTERED.v2.template.json',scope)
astrows=[]
for name in files:
 text=data(P/name);tree=ast.parse(text,filename=str(P/name));astrows.append({'ref':ref(P/name),'AST_PARSE':'PASS','candidate_imported':False,'executed':False,'functions':len([x for x in ast.walk(tree) if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))])})
save('ast-audit.json',{'actual_ast_parse_only':True,'files':astrows,'actual_controller_helper_native_SQL_Go_Node_HTTP_MODEL_calls':0})
for new,old in [('controller_common.v2.py','controller_common.py'),('controller.v2.py','controller.py'),('launch.v2.py','launch.py'),('case_worker.v2.py','case_worker.py'),('seal_readonly.v2.py','seal_readonly.py')]:put(new+'.diff',''.join(difflib.unified_diff(data(OLD/old).splitlines(True),data(P/new).splitlines(True),fromfile=str(OLD/old),tofile=str(P/new))))
print(json.dumps({'status':'PREPARATION_ONLY_NOT_RUN','AST_files':len(astrows),'roster_rows':len(s['roster']),'files':s['controller_refs']},ensure_ascii=False))
