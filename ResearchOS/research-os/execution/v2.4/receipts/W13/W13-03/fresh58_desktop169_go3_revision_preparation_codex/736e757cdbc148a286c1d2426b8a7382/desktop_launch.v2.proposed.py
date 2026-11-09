"""Future one-shot Root launch only; currently no scope or authority is bound."""
import hashlib,json,os,sys,time,traceback,types
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
def need(v,m):
    if not v:raise RuntimeError(m)
def verify(r):
    need(type(r) is dict and set(r)=={'path','sha256','bytes'},'Exact immutable ref')
    p=Path(r['path']);need(p.is_absolute() and str(p.resolve())==str(p),'Canonical ref')
    b=p.read_bytes();need(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'Pinned input changed');return b
def doc(b):
    def pairs(items):
        d={}
        for k,v in items:need(k not in d,'Duplicate JSON');d[k]=v
        return d
    return json.loads(b.decode('utf-8'),object_pairs_hook=pairs)
def load(r,name):
    raw=verify(r);m=types.ModuleType(name);m.__file__=r['path'];sys.modules[name]=m;exec(compile(raw,r['path'],'exec'),m.__dict__);return m
def save(p,o):
    with p.open('xb') as f:f.write((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode())
def main():
    out=None;first=None;secondary=[];result=None;util=None;normal=None;allowed=[];phase='SCOPE';started=time.monotonic()
    try:
        need(sys.flags.isolated and sys.flags.no_site and len(sys.argv)==5,'Explicit isolated future Root launch')
        sys.dont_write_bytecode=True
        raw=Path(sys.argv[1]).read_bytes();need(hashlib.sha256(raw).hexdigest()==sys.argv[2],'Scope SHA');s=doc(raw)
        need(s['execution_authorized'] is True and s['preparation_only'] is False,'Preparation cannot launch')
        phase='ROOT_AUTHORITY';gate=load(s['authorization_verifier_ref'],'desktop58_launch_authority');auth=gate.validate_grant(*sys.argv[1:])
        need(auth['scope']==s and auth['registered_Root_scope_and_grant_verified'] is True and auth['fresh_current58_CLI2_qualified'] is True,'Root and current58 CLI2 authority')
        resources=doc(verify(s['resource_catalog_ref']));python=resources['tools']['python']
        need(str(Path(sys.executable).resolve())==python['path'],'Actual pinned Python');verify(python)
        for key in ['launcher_ref','controller_ref','utility_ref','owned_helper_ref']:verify(s[key])
        need(str(Path(__file__).resolve())==s['launcher_ref']['path'],'Actual launcher pin')
        util=load(s['utility_ref'],'desktop58_launch_util');normal=load(s['owned_helper_ref'],'desktop58_launch_owned')
        allowed=resources['files']+[s[k] for k in ['launcher_ref','controller_ref','utility_ref','owned_helper_ref','authorization_verifier_ref']]
        for r in allowed+auth['authorization_input_refs']:verify(r)
        initial_runtime=util.module_observation(allowed,normal)
        need(type(s['inner_seconds']) is int and s['inner_seconds']>0 and type(s['outer_seconds']) is int and
             type(s['launcher_evidence_reserve_seconds']) is int and s['launcher_evidence_reserve_seconds']>0 and
             s['outer_seconds']>s['inner_seconds']+25+5+s['launcher_evidence_reserve_seconds'],'Root complete outer phase allocation')
        outer_deadline=started+s['outer_seconds']
        need(outer_deadline-time.monotonic()>s['inner_seconds']+25+5+s['launcher_evidence_reserve_seconds'],'Outer preparation consumed allocation')
        phase='ALLOCATE';candidate=util.safe(s['outer_output_root'],ROOT/'execution/v2.4/receipts/W13/W13-03',True)
        need(candidate!=Path(s['output_root']) and not candidate.is_relative_to(Path(s['output_root'])) and not Path(s['output_root']).is_relative_to(candidate),'Distinct outer/inner outputs')
        candidate.mkdir();out=candidate
        save(out/'runtime.before.json',initial_runtime)
        argv=[python['path'],'-I','-S','-X','utf8',s['controller_ref']['path'],*sys.argv[1:]]
        remaining=outer_deadline-time.monotonic()
        effective_timeout=remaining-5-s['launcher_evidence_reserve_seconds']
        need(effective_timeout>s['inner_seconds']+25,'Root outer budget exhausted before owned child')
        env=dict(s['public_environment']);need(set(env)<=set(['SystemRoot','WINDIR','ComSpec','PATH','PATHEXT']),'Explicit public environment')
        phase='INNER';save(out/'request.json',{'argv':argv,'cwd':str(ROOT),'timeout':effective_timeout,'requested_outer_seconds':s['outer_seconds'],'remaining_before_start':remaining,'cleanup_reserve':5,'launcher_evidence_reserve':s['launcher_evidence_reserve_seconds'],'absolute_outer_deadline':outer_deadline,'automatic_retry':False,'counter_reset':False})
        with (out/'stdout.raw').open('xb') as so,(out/'stderr.raw').open('xb') as se:
            result=normal.run_owned(argv,str(ROOT),env,so,se,effective_timeout)
        save(out/'invocation.json',{'actual_native_exit':result.get('actual_exit'),'owned_result':result,'argv':argv,'cwd':str(ROOT)})
        util.job_ok(result)
    except BaseException as exc:first={'phase':phase,'error':repr(exc),'traceback':traceback.format_exc(),'actual_native_exit':None};traceback.print_exc()
    finally:
        if out is not None:
            if util is not None and normal is not None:
                try:save(out/'runtime.after.json',util.module_observation(allowed,normal))
                except BaseException as exc:
                    if first is None:first={'phase':'runtime-after','error':repr(exc),'actual_native_exit':None}
                    else:secondary.append({'phase':'runtime-after','error':repr(exc),'actual_native_exit':None})
            if time.monotonic()>outer_deadline:
                item={'phase':'outer-evidence-deadline','error':'Root outer budget exceeded','actual_native_exit':None}
                if first is None:first=item
                else:secondary.append(item)
            try:save(out/'result.json',{'first_error':first,'secondary_errors':secondary,'inner_result':result,'actual_native_inner_exit':result.get('actual_exit') if result else None,'actual_outer_native_exit':None,'elapsed_seconds':time.monotonic()-started,'source_acceptance':False})
            except BaseException:traceback.print_exc();return 1
            if time.monotonic()>outer_deadline:
                print('Root outer deadline exceeded after final result IO',file=sys.stderr);return 1
    return 1 if first else 0
if __name__=='__main__':raise SystemExit(main())
