"""Generate receipt-only controller revision; AST parsing only, no candidate import."""
import ast,difflib,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
O=ROOT/'execution/v2.4/receipts/W13/W13-03/desktop_exact15_integration_preparation_codex/f5ac31fcc8884b43ba7d25fc4fc75735'
R=ROOT/'execution/v2.4/receipts/W13/W13-03/desktop_exact15_integration_static_independent_review_codex/71ce8cd4985f4ed1bb1fb73ea21d5c78'
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,b):
 with (N/name).open('xb') as f:f.write(b)
 return ref(N/name)
def doc(name,d):return write(name,(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
orig=(O/'integrate_desktop15.py').read_text(encoding='utf-8')
if ref(O/'integrate_desktop15.py')['sha256']!='dd774a02ee6f496a781451b68eceac1f6738deabe7fd443422f5b59974e29b2f':raise RuntimeError('Old controller pin')
start=orig.index('def execute(args):');body_start=orig.index("        hr=scope['owned_process_helper_ref']",start)
end=orig.index('    except BaseException as exc:\n        save(out,\'failure.origin.json\'',body_start)
pre=orig[start:body_start]
pre=pre[pre.index('    raw=read(args.scope)'):]
needle="    out.mkdir();phase='PRE_NATIVE';last=None;applied=False;commit_attempted=False;steps=0\n    try:\n"
if not pre.endswith(needle):raise RuntimeError('Exact pretry boundary')
pre=pre[:-len(needle)]
pre=pre.replace("    out=bounded(scope['new_output_root'],False)","    candidate=bounded(scope['new_output_root'],False)")
pre=pre.replace('out.parent','candidate.parent').replace('out.name','candidate.name').replace('os.path.lexists(out)','os.path.lexists(candidate)')
pre=''.join('    '+line if line.strip() else line for line in pre.splitlines(True))
pre+="        candidate.mkdir(exist_ok=False);out=candidate;phase='PRE_NATIVE'\n"
body=orig[body_start:end]
run_start=body.index('        def run(');run_end=body.index('        def guards():',run_start)
newrun='''        def run(name,argv,timeout=30):
            nonlocal phase,last,phase_native,steps
            budget();steps+=1;require(steps<=80,'Git80 step cap');phase=name;last=None;phase_native=None;error=None;start=now()
            try:
                with (out/(name+'.stdout.raw')).open('xb') as so,(out/(name+'.stderr.raw')).open('xb') as se:
                    last=helper.run_owned(prefix+argv,str(ROOT),env,so,se,timeout)
                phase_native=last.get('actual_exit') if isinstance(last,dict) else None
                job_ok(last)
            except BaseException as exc:error=exc
            finally:
                try:
                    save(out,name+'.invocation.json',{'argv':prefix+argv,'cwd':str(ROOT),'environment':env,'started_at':start,
                         'ended_at':now(),'process_observation':last,'wrapper_error':repr(error) if error else None,
                         'actual_native_exit':last.get('actual_exit') if isinstance(last,dict) else None,'automatic_retry':False})
                except BaseException as seal_error:
                    if error is None:error=seal_error;phase=name+'-invocation-evidence';phase_native=None
                    else:secondary.append({'phase':name+'-invocation-evidence','error':repr(seal_error),'actual_native_exit':None})
            if error is not None:raise error
            phase='GUARD_AFTER_'+name;phase_native=None;budget()
            return raw_file(out/(name+'.stdout.raw'))
'''
body=body[:run_start]+newrun+body[run_end:]
rt_start=body.index('        def runtime(name):');rt_end=body.index("        bundle=scope['main_runtime_bundle_ref']",rt_start)
newruntime='''        def runtime(name):
            expected=runtime_expected()
            paths=set(helper.runtime_resource_paths())|{sys.executable}
            for module in list(sys.modules.values()):
                for field in ['__file__','__cached__']:
                    p=getattr(module,field,None)
                    if p and Path(p).is_file():paths.add(p)
            actual=[]
            for p in sorted(paths):
                k=str(Path(p).absolute()).casefold();require(k in expected,'Unpinned controller runtime')
                verify(expected[k]);actual.append(ref(p))
            save(out,name+'.json',{'kind':'ACTUAL_POINT_IN_TIME_NOT_LIFECYCLE','files':actual})
        runtime_after=runtime
'''
body=body[:rt_start]+newruntime+body[rt_end:]
needle="        helper=types.ModuleType('desktop15_owned_job');helper.__file__=str(path(hr['path']))\n"
insert='''        def runtime_expected():
            expected={str(path(x['path']).absolute()).casefold():x for x in document(scope['runtime_resources_ref'])['files']}
            for item in [scope['controller_ref'],hr]:expected[str(path(item['path']).absolute()).casefold()]=item
            return expected
        Path(__file__).resolve().as_uri()
        expected=runtime_expected();source_paths={sys.executable}
        for module in list(sys.modules.values()):
            for field in ['__file__','__cached__']:
                p=getattr(module,field,None)
                if p and Path(p).is_file():source_paths.add(p)
        observed=[]
        for p in sorted(source_paths):
            k=str(Path(p).absolute()).casefold();require(k in expected,'Unpinned Python source before helper load')
            verify(expected[k]);observed.append(ref(p))
        save(out,'runtime.source.before_import.json',{'kind':'ACTUAL_POINT_IN_TIME_NOT_LIFECYCLE','files':observed})
        helper=types.ModuleType('desktop15_owned_job');helper.__file__=str(path(hr['path']));sys.modules[helper.__name__]=helper
'''
if body.count(needle)!=1:raise RuntimeError('Exact helper-load boundary')
body=body.replace(needle,insert)
body=body.replace("        save(out,'completed.json',{'actor'","        completion={'actor'")
needle="'source_acceptance':False,'formal_increment':0})\n"
if body.count(needle)!=1:raise RuntimeError('Exact completed boundary')
body=body.replace(needle,"'source_acceptance':False,'formal_increment':0}\n")
opening='''def execute(args):
    global BASE
    out=None;phase='READ_SCOPE_AND_AUTHORITY';last=None;phase_native=None;applied=False;commit_attempted=False;steps=0
    first=None;secondary=[];exact=[];runtime_after=None;completion=None
    def attempt(label,fn):
        nonlocal first
        try:return fn()
        except BaseException as error:
            detail={'phase':label,'error':repr(error),'traceback':traceback.format_exc(),'actual_native_exit':None}
            if first is None:first=detail
            else:secondary.append(detail)
            print(json.dumps({'first_error':first,'secondary_error':detail},ensure_ascii=False),file=sys.stderr)
    try:
'''
closing='''    except BaseException as exc:
        first={'phase':phase,'error':repr(exc),'traceback':traceback.format_exc(),'actual_native_exit':phase_native}
        print(json.dumps({'first_error':first,'last_child_observation':last,'safe_output':str(out) if out else None,
             'automatic_retry':False,'rollback':False,'counter_reset':False},ensure_ascii=False),file=sys.stderr)
    finally:
        if out is not None:
            if runtime_after is not None and not (out/'runtime.after.json').exists():
                attempt('runtime.after',lambda:runtime_after('runtime.after'))
            if first is not None:
                def observations():
                    evidence=[]
                    for p in [ROOT/'.git/HEAD',ROOT/'.git/index']+[ROOT/x['path'] for x in exact]:
                        try:
                            raw=raw_file(p);evidence.append({'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
                        except BaseException as error:evidence.append({'path':str(p),'error':repr(error),'actual_native_exit':None})
                    save(out,'after_failure.readonly_observations.json',evidence)
                attempt('after-failure-observation',observations)
                attempt('inputs-after-failure',lambda:save(out,'immutable-inputs.after_failure.json',list(READS.values())))
            if first is None and completion is not None:attempt('completed',lambda:save(out,'completed.json',completion))
            if first is not None:
                attempt('failure-origin',lambda:save(out,'failure.origin.json',{'first_error':first,'secondary_errors':secondary,
                     'last_child_observation':last,'current_phase_native_exit':None,'apply_attempted':applied,
                     'commit_attempted':commit_attempted,'automatic_retry':False,'rollback':False,'counter_reset':False}))
            def manifest():
                rows=[]
                for p in sorted(out.rglob('*')):
                    bounded(p)
                    if p.is_file():
                        b=raw_file(p);rows.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
                save(out,'manifest.json',{'count':len(rows),'entries':rows,'excluded_only':str(out/'manifest.json')})
            attempt('manifest',manifest)
        if first is not None:
            print(json.dumps({'first_error':first,'secondary_errors':secondary,'last_child_observation':last,
                 'apply_attempted':applied,'commit_attempted':commit_attempted,'automatic_retry':False,'rollback':False,'counter_reset':False},ensure_ascii=False),file=sys.stderr)
    if first is not None:raise RuntimeError('Desktop integration stopped; first error preserved above')


'''
tail=orig[orig.index('def main():',end):]
new=orig[:start]+opening+pre+body+closing+tail
ast.parse(new,filename='integrate_desktop15.v2.py')
control=write('integrate_desktop15.v2.py',new.encode('utf-8'))
launcher=ref(N/'launch_desktop15.v2.py');ast.parse((N/'launch_desktop15.v2.py').read_text(encoding='utf-8'))
write('controller.unified.diff',''.join(difflib.unified_diff(orig.splitlines(True),new.splitlines(True),fromfile='old/integrate_desktop15.py',tofile='new/integrate_desktop15.v2.py')).encode('utf-8'))
oldlauncher=(O/'launch_desktop15.py').read_text(encoding='utf-8');newlauncher=(N/'launch_desktop15.v2.py').read_text(encoding='utf-8')
write('launcher.unified.diff',''.join(difflib.unified_diff(oldlauncher.splitlines(True),newlauncher.splitlines(True),fromfile='old/launch_desktop15.py',tofile='new/launch_desktop15.v2.py')).encode('utf-8'))
scope=json.loads((O/'scope.final.v2.proposed.json').read_bytes())
scope['controller_ref']=control;scope['launcher_ref']=launcher
scope['preparation_revision']={'status':'PREPARATION_ONLY_NOT_EXECUTABLE','old_scope_ref':ref(O/'scope.final.v2.proposed.json'),'review_ref':ref(R/'review.json'),'fixes':['D15-CTRL-01','D15-CTRL-02'],'actual_execution':False,'current_root_tuple_guessed':False,'native_unknown':None,'runtime_claim':'BEFORE_IMPORT_SOURCE_PINS_AND_ACTUAL_POINT_IN_TIME_ONLY','first_error_preserved':True,'last_child_is_not_phase_native':True}
for key in ['expected_registration','expected_before_registration','registration_namespace','operation_uuid','new_output_root','expected_cli43_head','expected_main_branch','protected_source_vector_ref','desktop_source_review_ref']:
 if scope[key] is not None:raise RuntimeError('Future authority field became concrete '+key)
if scope['authorized'] is not False:raise RuntimeError('Preparation authorized unexpectedly')
doc('scope.v3.proposed.json',scope)
original=ast.parse(orig);revised=ast.parse(new)
kept=[]
for node in original.body:
 if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name not in ['execute']:
  partner=next(x for x in revised.body if isinstance(x,type(node)) and x.name==node.name)
  if ast.dump(node,include_attributes=False)!=ast.dump(partner,include_attributes=False):raise RuntimeError('Unrelated top-level function changed '+node.name)
  kept.append(node.name)
doc('static.audit.json',{'schema':'researchos.desktop15-controller-preparation-revision-audit.v1','status':'PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','review_ref':ref(R/'review.json'),'AST_modules':2,'candidate_imports':0,'candidate_executions':0,'product_source_changes':0,'Git_mutations':0,'Go_Node_SQL_HTTP_Model':0,'unchanged_top_level_function_AST':kept,'new_failure_origins':[],'source_before':[ref(O/x) for x in ['integrate_desktop15.py','launch_desktop15.py','scope.final.v2.proposed.json','manifest.json']],'future_grant':False,'future_registration_and_Main43':None,'bounds':{'paths':15,'combined_paths':58,'Git_steps':80,'apply':1,'commit':1,'controller_seconds':900,'outer_seconds':1200,'cleanup_seconds':5}})
print(json.dumps({'controller':control,'launcher':launcher,'scope':ref(N/'scope.v3.proposed.json')},ensure_ascii=False))
