from __future__ import annotations
import ast,copy,hashlib,json,types
from datetime import timedelta
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    r=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def save(n,v):
    p=Q/n
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    b=json.loads((Q/'source-inputs.basis.json').read_bytes());gr=b['references'][2];gm=types.ModuleType('Task79_control_guard');gm.__file__=gr['path'];exec(compile(Path(gr['path']).read_bytes(),gm.__file__,'exec'),gm.__dict__);guard=gm.Guard();closed=False
    try:
        inv=json.loads((Q/'Task79-exact-inverse.json').read_bytes())
        for r in b['references']+[inv['candidate_ref'],b['actual_Task76_observation_ref'],b['actual_Task76_raw_ref'],b['legacy_Task68_observation_ref'],b['legacy_Task68_raw_ref'],pin(Q/'run_Task79_time_delta_controls.py')]:guard.read(r['path'],r)
        m=types.ModuleType('Task79_time_Source_control');m.__file__=str(Q/'old21_root.source.py');source=Path(m.__file__).read_bytes();exec(compile(source,m.__file__,'exec'),m.__dict__)
        obs=json.loads(Path(b['actual_Task76_observation_ref']['path']).read_bytes());raw=Path(b['actual_Task76_raw_ref']['path']).read_bytes();rows=[json.loads(x) for x in raw.splitlines()];first,last=rows[1:]
        actor=obs['peer_actor'];text=last['payload']['content'][0]['text'];envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+actor.removeprefix('codex:')+'\nPayload:\n';delivered=m.strict(text[len(envelope):] if text.startswith(envelope) else text)
        assert delivered['schema']=='researchos.old21-peer-review-delivery.v2' and delivered['operation']=='SOURCE_REVIEW_WITNESS'
        active_obs=obs;active_raw=raw;active_first=copy.deepcopy(first);active_last=copy.deepcopy(last)
        m.doc=lambda ref:copy.deepcopy(active_obs);m.checked=lambda ref:active_raw;m.original_capture_rows=lambda binding,raw,peer=False:(copy.deepcopy(active_first),copy.deepcopy(active_last))
        results=[]
        def decode():return m.validate_peer_delivery(b['actual_Task76_observation_ref'],delivered['review_refs'],actor,'SOURCE_REVIEW_WITNESS')
        def test(name,fn,code=None,mode='SYNTHETIC_TIME_DELTA_SOURCE_UNIT'):
            try:fn()
            except ValueError as e:assert code is not None and str(e)==code,(name,str(e),code);results.append(dict(name=name,observed='REJECT',code=str(e),mode=mode,Source_PASS=True))
            else:assert code is None,(name,'not rejected');results.append(dict(name=name,observed='DECODE_SOURCE_UNIT_ONLY',mode=mode,Source_PASS=True))
        test('actual Task76 metadata1ms earlier adjacent Full Final decoder',decode,mode='ACTUAL_DELIVERY_DECODE_ONLY_ROOT_ISSUER_GATE_NOT_EXECUTED')
        finaltime=m.when(last['timestamp'])
        for name,delta,code in [('equal timestamps',0,None),('one second inclusive',1,None),('one second plus one ms',1.001,'ACTUAL_PEER_DELIVERY_REQUIRED'),('metadata after Final1ms',-0.001,'ACTUAL_PEER_DELIVERY_REQUIRED')]:
            active_first=copy.deepcopy(first);active_first['timestamp']=(finaltime-timedelta(seconds=delta)).isoformat().replace('+00:00','Z');test(name,decode,code)
        active_first=copy.deepcopy(first);active_last=copy.deepcopy(last);active_last['ordinal']+=1
        test('nonadjacent ordinal still rejects',decode,'ACTUAL_PEER_DELIVERY_REQUIRED')
        active_last=copy.deepcopy(last);active_last['metadata']['client_authored']=True
        test('client authored still rejects',decode,'ACTUAL_PEER_DELIVERY_REQUIRED')
        active_last=copy.deepcopy(last);active_last['payload']['author']='/root/not_full'
        test('wrong backend actor still rejects',decode,'ACTUAL_PEER_DELIVERY_REQUIRED')
        # One necessary compatibility observation for the exact legacy Task68 Source pin, not the old39 suite.
        active_obs=json.loads(Path(b['legacy_Task68_observation_ref']['path']).read_bytes());active_raw=Path(b['legacy_Task68_raw_ref']['path']).read_bytes();legacyrows=[json.loads(x) for x in active_raw.splitlines()];active_first,active_last=legacyrows[1:]
        test('exact Task68 legacy raw message time pin remains accepted',lambda:m.validate_peer_delivery(b['legacy_Task68_observation_ref'],list(b['known_builder_Source_review_refs'].values()),active_obs['peer_actor'],'BUILDER_SOURCE_REVIEW_WITNESS'),mode='ACTUAL_LEGACY_DECODE_ONLY_ROOT_ISSUER_GATE_NOT_EXECUTED')
        before=ast.parse(Path(b['base_caller_ref']['path']).read_bytes());after=ast.parse(source);bm={n.name:ast.dump(n,include_attributes=False) for n in before.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};am={n.name:ast.dump(n,include_attributes=False) for n in after.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};changed=sorted(k for k in bm if bm[k]!=am[k]);assert changed==['validate_peer_delivery']
        assert bm['failure_rows']==am['failure_rows'] and bm['projection']==am['projection'] and bm['original_capture_rows']==am['original_capture_rows']
        results.append(dict(name='single predicate inverse all other Source including counters and original Root bytes gate unchanged',mode='AST_AND_EXACT_BYTE_INVERSE',Source_PASS=True))
        closure=save('Task79-time-delta-controls.guard.closed.json',guard.close());closed=True
        result=save('Task79-time-delta-controls.json',dict(schema='researchos.old21-caller-Task79-time-delta-controls.v1',caller_ref=pin(Q/'old21_root.source.py'),controls=results,passed=len(results),failed=0,exact_changed_functions=changed,guard_ref=closure,actual_Task76_observation_ref=b['actual_Task76_observation_ref'],actual_Task76_raw_ref=b['actual_Task76_raw_ref'],Source_decode_controls_only=True,Root_issuer_gate_NOT_EXECUTED=True,Root_observation_is_witness=False,Scope_or_qualification_created=False,Go_Native_SQL_TP_model_calls=0,live_Canon_reads=0,old39_59_853_14782_not_reexecuted=True,execution_grant=False,formal_acceptance=False))
        print(json.dumps(dict(controls_ref=result,guard_ref=closure,passed=len(results),failed=0),ensure_ascii=False))
    finally:
        if not closed and any(not s.closed for s,_,_ in guard.held):save('Task79-controls-attempt-failure.guard.closed.json',guard.close())
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
