"""Future Root-owned outer only. No implicit grant generation or retry.
Usage: -I -S -X utf8 THIS phase scope scopeSHA grant grantSHA.
Preparation of this text does not authorize its execution.
"""
import hashlib
import json
import os
import sys
import traceback
import types
from pathlib import Path

ROOT=Path('D:/作品集/ResearchOS/research-os')
def need(ok,why):
    if not ok:raise RuntimeError(why)
def strict(raw):
    def pairs(rows):
        d={}
        for k,v in rows:need(k not in d,'DUPLICATE_KEY');d[k]=v
        return d
    return json.loads(raw.decode('utf8'),object_pairs_hook=pairs)
def rawref(r):
    need(isinstance(r,dict) and set(r)=={'path','sha256','bytes'},'REF')
    p=Path(r['path']);need(p.is_absolute() and p.resolve()==p,'CANONICAL_PATH')
    raw=p.read_bytes();need(len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'PIN');return raw
def load(r,name):
    raw=rawref(r);m=types.ModuleType(name);m.__file__=r['path'];sys.modules[name]=m
    exec(compile(raw,r['path'],'exec'),m.__dict__);return m
def save(p,v):
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def main():
    out=None;first=None;secondary=[];result=None;helper=None;u=None;allowed=None
    try:
        need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,'I_S_UTF8_REQUIRED');sys.dont_write_bytecode=True
        need(len(sys.argv)==6,'phase scope sha grant sha');phase,sp,sh,gp,gh=sys.argv[1:]
        raw=Path(sp).read_bytes();need(hashlib.sha256(raw).hexdigest()==sh,'SCOPE_PIN');s=strict(raw)
        need(s['preparation_only'] is False and phase in ('prepare','execute'),'NO_EXECUTION_SCOPE')
        need(s['authority_validator_ref'] is not None,'OPEN_ACTUAL_ROOT_VALIDATOR')
        gate=load(s['authority_validator_ref'],'driver18_launch_authority');auth=gate.validate_grant(sp,sh,gp,gh)
        need(auth['scope']==s and auth['phase']==phase and auth['actor']=='codex:/root' and auth['actual_registration_completed'] is True,'ROOT_ACTUAL_AUTHORITY')
        for ref in auth['authorization_input_refs']:rawref(ref)
        u=load(s['utility_ref'],'driver18_launch_utilities')
        candidate=u.safe(s[phase+'_launcher_output_root'],ROOT/'execution/v2.4/receipts/W05/W05-99',True)
        candidate.mkdir();out=candidate
        resources=strict(rawref(s['resource_catalog_ref']))
        controls=[s[k] for k in ('controller_ref','launcher_ref','authority_validator_ref','utility_ref','owned_helper_ref','debug_helper_ref')]
        allowed=resources['files']+controls
        for ref in allowed:rawref(ref)
        need(u.pin(sys.executable)==resources['python'],'ACTUAL_PYTHON_PIN')
        need(u.pin(Path(__file__))==s['launcher_ref'],'ACTUAL_LAUNCHER_PIN')
        helper=load(s['owned_helper_ref'],'driver18_launch_owned')
        save(out/'python-os.before.json',u.module_observation(allowed,helper));save(out/'authorization.json',auth)
        env=dict(s['public_environment']);need(set(env)<=set(['SystemRoot','WINDIR','ComSpec','PATH','PATHEXT']),'PUBLIC_ENV_ONLY')
        argv=[resources['python']['path'],'-I','-S','-X','utf8',s['controller_ref']['path'],phase,sp,sh,gp,gh]
        save(out/'requested.json',{'argv':argv,'cwd':str(ROOT),'env':env,'timeout':3600,'automatic_retry':False})
        need(s['caps']['outer_seconds']==3600,'OUTER_BOUND')
        with (out/'stdout.raw').open('xb') as so,(out/'stderr.raw').open('xb') as se:
            result=helper.run_owned(argv,str(ROOT),env,so,se,3600)
        u.job_ok(result,False)
    except BaseException as e:
        first={'stage':'LAUNCH_OR_INNER','error':repr(e),'traceback':traceback.format_exc(),
               'actual_stage_native_exit':None,'actual_inner_result':result,'automatic_retry':False,'counter_reset':False}
    finally:
        if out is not None:
            if helper:
                try:save(out/'python-os.after.json',u.module_observation(allowed,helper))
                except BaseException as e:secondary.append({'stage':'runtime-after','error':repr(e)})
            if first is None and secondary:first={'stage':'EVIDENCE_FINALIZATION','error':secondary[0],'actual_stage_native_exit':None}
            try:
                save(out/'inner.invocation.json',{'result':result,'actual_native_exit':result.get('actual_exit') if result else None})
                if first:save(out/'failure.origin.json',first)
                save(out/'completed.json',{'error':first,'secondary':secondary,'reported_exit':1 if first else 0,'source_acceptance':False})
                save(out/'manifest.json',{'files':[u.pin(p) for p in u.files(out)],'excluded_only_self':True})
            except BaseException as e:
                secondary.append({'stage':'FINAL_RECEIPT_WRITE','error':repr(e)});first=first or secondary[-1]
        if first:sys.stderr.write(json.dumps({'first_cause':first,'secondary':secondary},ensure_ascii=False)+'\n')
    return 1 if first else 0
if __name__=='__main__':raise SystemExit(main())
