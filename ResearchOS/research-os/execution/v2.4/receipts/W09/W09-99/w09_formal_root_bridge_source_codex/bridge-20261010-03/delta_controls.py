"""Source-only two-finding controls. Main stages and dispatcher are never executed."""
import ast,hashlib,json,os,sys,types
from pathlib import Path
N=Path(__file__).resolve().parent;R=Path('D:/作品集/ResearchOS/research-os')
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def module(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
m=module(N/'w09_root_bridge.source.py');checks=[]
def check(name,ok):assert ok,name;checks.append(name)
def reject(name,fn):
 try:fn()
 except (ValueError,FileNotFoundError):checks.append(name);return
 raise AssertionError(name)
check('fixed-canonical-backend-map',m.AUTHOR=='codex:'+m.AUTHOR_BACKEND)
resource=m.resource_environment()
check('actual-readonly-resource-root-host-marker',len(resource['refs'])==5 and len(resource['audit_ranges'])==3)
for bad in ('C:/','C:\\Users\\yqyyds\\AppData\\Local\\Temp','D:\\temp',
 'C:\\Users\\yqyyds\\AppData\\Local\\ResearchOS\\w09-native-v4','C:\\Users\\yqyyds\\.researchos\\other'):
 reject('reject-temp-'+bad,lambda value=bad:m.environment_directory(value))
reject('general-ref-still-rejects-C-marker',lambda:m.checked(m.RESOURCE_OWNER_REF))
check('physical-C-exact',m.environment_directory(str(m.PUBLIC_TEMP)).resolve(strict=True)==m.PUBLIC_TEMP)
tree=ast.parse((N/'w09_root_bridge.source.py').read_bytes())
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
common=next(n for n in functions['propose'].body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='common' for t in n.targets))
q={k:dict(path='CONTROL_ONLY',sha256='0'*64,bytes=0) for k in ('bridge_source_ref','source_hdf_ref','source_mf_ref','source_review_ref','resource_parent_ref','resource_audit_ref')}
q.update(current4=[],bridge_temp_parent=str(m.PUBLIC_TEMP),resource_owner_sha256=m.RESOURCE_OWNER_REF['sha256'])
scope={**m.__dict__,'req':q}
exec(compile(ast.Module(body=[common],type_ignores=[]),'<scope metadata expression only>','exec'),scope)
check('Scope-raw-author-and-canonical-metadata',scope['common']['source_actor']==m.AUTHOR_BACKEND and scope['common']['source_author_canonical']==m.AUTHOR)
check('Scope-current-generation-package-binding',scope['common']['generation']==m.BRIDGE_GENERATION and scope['common']['source_hdf_ref']==q['source_hdf_ref'])
# Evaluate Main's exact peer-author predicate against a genuine historical peer capture.
auditpath=m.W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.public21-source-review-v2.actual-audit.root.json'
audit=json.loads(auditpath.read_bytes());capture=Path(audit['original_capture_ref']['path'])
if not capture.is_absolute():capture=R/capture
records=[json.loads(line) for line in capture.read_bytes().splitlines()]
profile=ast.parse((R/'execution/v2.4/formal_profile_w09.py').read_bytes())
role=next(n for n in profile.body if isinstance(n,ast.FunctionDef) and n.name=='_role_audit')
branch=next(n for n in role.body if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and any(isinstance(c,ast.Constant) and c.value=='codex:/root' for c in n.test.comparators))
predicate=branch.orelse[0]
def main_peer(actor):
 env=dict(call=records[1],result=records[2],payload=records[2]['payload'],proof={'actor_id':actor},
  api=types.SimpleNamespace(require=lambda ok,*args:m.need(ok,'MAIN_EXACT_PEER_PREDICATE')))
 exec(compile(ast.Module(body=[predicate],type_ignores=[]),'<Main exact peer predicate only>','exec'),env)
main_peer(m.AUTHOR_BACKEND);check('genuine-history-raw-backend-predicate',True)
reject('canonical-peer-author-rejected',lambda:main_peer(m.AUTHOR))
# Only process-environment/cache behavior is stubbed; no temp file is created.
prior_temp=sys.modules.get('tempfile');fake_temp=types.ModuleType('tempfile');fake_temp.gettempdir=lambda:str(m.PUBLIC_TEMP)
sys.modules['tempfile']=fake_temp
old_os=m.os;m.os=types.SimpleNamespace(environ={'TEMP':str(m.PUBLIC_TEMP),'TMP':str(m.PUBLIC_TEMP)})
try:
 check('matching-process-temp-cache',m.require_process_temp()==m.PUBLIC_TEMP)
 fake_temp.gettempdir=lambda:'C:\\wrong'
 reject('reject-preexisting-wrong-cache',m.require_process_temp)
 fake_temp.gettempdir=lambda:str(m.PUBLIC_TEMP)
 m.os.environ['TMP']='D:\\wrong';reject('reject-mismatched-TMP',m.require_process_temp)
finally:
 m.os=old_os
 if prior_temp is None:sys.modules.pop('tempfile',None)
 else:sys.modules['tempfile']=prior_temp
# Launcher executes only a runpy spy. The original dispatcher is never loaded.
launcher=module(N/'consumer_launch.source.py')
prior_temp=sys.modules.get('tempfile');prior_runpy=sys.modules.get('runpy')
fake_temp=types.ModuleType('tempfile');fake_temp.gettempdir=lambda:str(m.PUBLIC_TEMP)
fake_runpy=types.ModuleType('runpy');dispatch_calls=[]
fake_runpy.run_path=lambda path,run_name:dispatch_calls.append(dict(path=path,run_name=run_name,argv=list(sys.argv),TEMP=os.environ.get('TEMP'),TMP=os.environ.get('TMP')))
old_env={k:os.environ.get(k) for k in ('TEMP','TMP')};oldargv=list(sys.argv);oldpath=list(sys.path)
try:
 sys.modules['tempfile']=fake_temp;sys.modules['runpy']=fake_runpy
 os.environ['TEMP']=os.environ['TMP']=str(m.PUBLIC_TEMP)
 source=ref(N/'w09_root_bridge.source.py')
 launcher.main([source['sha256'],str(source['bytes']),'test.retrieval','','C19'])
 check('consumer-same-process-explicit-TEMP',len(dispatch_calls)==1 and dispatch_calls[0]['TEMP']==dispatch_calls[0]['TMP']==str(m.PUBLIC_TEMP))
 check('unchanged-dispatcher-product-argv',dispatch_calls[0]['argv']==[str(R/'execution/command_dispatcher/dispatch.py'),'test.retrieval','--task-id','W09','--case-id','C19','--spec','v2.4'])
 reject('launcher-wrong-Source-pin',lambda:launcher.main(['0'*64,str(source['bytes']),'test.retrieval','','C19']))
 os.environ['TEMP']='D:\\wrong'
 reject('launcher-wrong-environment-before-dispatch',lambda:launcher.main([source['sha256'],str(source['bytes']),'test.retrieval','','C19']))
 check('rejected-launcher-never-dispatches',len(dispatch_calls)==1)
finally:
 sys.argv=oldargv;sys.path[:]=oldpath
 for k,v in old_env.items():
  if v is None:os.environ.pop(k,None)
  else:os.environ[k]=v
 for name,prior in (('tempfile',prior_temp),('runpy',prior_runpy)):
  if prior is None:sys.modules.pop(name,None)
  else:sys.modules[name]=prior
inverse=json.loads((N/'exact-inverse.json').read_bytes());restored=(N/'w09_root_bridge.source.py').read_bytes().decode()
for edit in reversed(inverse['changes']):restored=restored.replace(edit['after'],edit['before'])
check('complete-original-byte-inverse',restored.encode()==Path(inverse['base_ref']['path']).read_bytes())
report=dict(schema='researchos.bridge03-source-delta-controls.v1',count=len(checks),passed=len(checks),failed=0,checks=checks,
 subject=ref(N/'w09_root_bridge.source.py'),launcher=ref(N/'consumer_launch.source.py'),
 actual_resource_readonly_refs=resource['refs'],synthetic_scope_expression_only=True,Main_peer_predicate_only=True,
 launcher_runpy_spy_only=True,process_cache_stub_only=True,actual_bridge_stages=0,actual_dispatcher_calls=0,
 actual_Main_module_calls=0,actual_Native_Go_SQL_model_TP_calls=0,old_18_and_24_controls_rerun=False)
(N/'delta-controls.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='BRIDGE03_DELTA_PASS',passed=len(checks),report_ref=ref(N/'delta-controls.json')),ensure_ascii=False))

