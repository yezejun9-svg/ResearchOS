import hashlib,json,sys,traceback,types
from pathlib import Path
Q=Path(__file__).resolve().parent
def main():
    src=Q/'review_actual_nf5.v7.py';raw=src.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='536d8fe75e527e4055d29156838714cffe0a2765191a3e592ed560fc221ec7a2'
    m=types.ModuleType('actual_fact_argv_delta');m.__file__=str(src);exec(compile(raw,str(src),'exec'),m.__dict__)
    bundle=m.R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/nf5-four-closed-actual-input02.root.json'
    packet=m.decode(bundle.read_bytes());choice=m.decode((m.BASE/'source.choice.json').read_bytes())
    callfile=Q/'Root-call-gate-fields.json';calls=m.decode(callfile.read_bytes())
    refs=[m.pin(src),m.pin(bundle),m.pin(callfile),m.pin(m.BASE/'source.choice.json'),m.pin(m.GUARD),*[row['producer_closed_ref']for row in packet['groups'].values()]]
    gm=types.ModuleType('known_read_guard');gm.__file__=str(m.GUARD);graw=m.GUARD.read_bytes();assert m.digest(graw)==m.GUARD_SHA;exec(compile(graw,str(m.GUARD),'exec'),gm.__dict__)
    guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);checks=[];primary=None
    try:
        guard.acquire(refs)
        for name,row in packet['groups'].items():
            c=dict(choice['common'],**choice['selectors'][name]);closed=m.decode(m.read_ref(row['producer_closed_ref']));request=closed['request_ref']
            for stage in('prepare','run'):
                observed=calls[name][stage]['actual_call_input'];value=m.verify_original_Root_command(observed,c,request,stage)
                checks.append(dict(selector=name,stage=stage,actual_Root_argv=value['argv'],PASS=True,Root_called=False))
        name='W09-G01';c=dict(choice['common'],**choice['selectors'][name]);r=m.decode(m.read_ref(packet['groups'][name]['producer_closed_ref']))['request_ref']
        for kind,bad in [('changedSHA',dict(r,sha256='0'*64)),('changedBytes',dict(r,bytes=r['bytes']+1))]:
            rejected=False
            try:m.verify_original_Root_command(calls[name]['run']['actual_call_input'],c,bad,'run')
            except ValueError:rejected=True
            assert rejected;checks.append(dict(kind=kind,PASS=True,rejected=True))
    except BaseException as exc:primary=exc
    finally:
        cleanup=guard.close()
        with(Q/'observed-Root-argv-delta.guard.closed.json').open('xb')as f:f.write((json.dumps(cleanup,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    if primary is not None:raise primary
    m.guard_receipt(cleanup)
    result=dict(schema='researchos.actual-Root-argv-delta-controls.v1',checks=checks,passed=len(checks),guard_ref=m.pin(Q/'observed-Root-argv-delta.guard.closed.json'),Source_only=True,new_Root_calls=0,new_Native_calls=0,new_Go_calls=0,formal_acceptance=False)
    with(Q/'observed-Root-argv-delta.controls.json').open('xb')as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(passed=len(checks),controls_ref=m.pin(Q/'observed-Root-argv-delta.controls.json'),guard_ref=result['guard_ref']),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
