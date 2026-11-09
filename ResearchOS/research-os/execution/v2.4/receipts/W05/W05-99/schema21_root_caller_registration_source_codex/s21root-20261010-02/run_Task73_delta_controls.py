from __future__ import annotations
import ast,copy,hashlib,json,types
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
    p=Q/n
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    basis=json.loads((Q/'source-inputs.basis.json').read_bytes());mf=json.loads(Path(basis['base_mf_ref']['path']).read_bytes());gr=next(r for r in mf['members'] if Path(r['path']).name=='read_Task69_basis_revision.py')
    gm=types.ModuleType('Task73_control_guard');gm.__file__=gr['path'];exec(compile(Path(gr['path']).read_bytes(),gm.__file__,'exec'),gm.__dict__);guard=gm.Guard();closed=False
    try:
        inv=json.loads((Q/'Task73-exact-inverse.json').read_bytes())
        for r in basis['references']+[inv['candidate_ref'],pin(Q/'run_Task73_delta_controls.py')]:guard.read(r['path'],r)
        m=types.ModuleType('Task73_Source_control');m.__file__=str(Q/'old21_root.source.py');raw=Path(m.__file__).read_bytes();exec(compile(raw,m.__file__,'exec'),m.__dict__)
        results=[]
        def test(name,fn,code=None,mode='SYNTHETIC_SOURCE_UNIT'):
            try:fn()
            except ValueError as e:
                assert code is not None and str(e)==code,(name,str(e),code)
                results.append(dict(name=name,observed='REJECT',code=str(e),mode=mode,Source_PASS=True))
            else:
                assert code is None,(name,'no rejection',code)
                results.append(dict(name=name,observed='ALLOW_SOURCE_UNIT_ONLY',mode=mode,Source_PASS=True))
        original={k:getattr(m,k) for k in ('doc','checked','original_capture_rows')}
        start=100
        cp=dict(revision=373,workers=[],failure_counters=[dict(original_payload=dict(immutable_origin_ref=dict(sha256='0'*64),origin_selector='old'),counted_once=True,counter_reset=False)],work_in_progress=dict(root_next_failure_ordinal_live=start,later_diagnostics_observed_after_cutoff=[],old_scope='preserved'))
        ow=dict(revision=177,card_path_bindings={'W05-99':dict(subtasks=dict(old_scope=dict(value='preserved')))})
        rr=lambda label,n:dict(path=str(Q/('NOT_WRITTEN_SYNTHETIC_'+label)),sha256=str(n)*64,bytes=0)
        scope,ownerref,workerref,facts=[rr(k,n) for k,n in [('scope',1),('owner',2),('worker',3),('facts',4)]]
        owner=dict(scope_ref=scope,owner=m.ROOT,selected_worker_id=m.ROOT)
        worker=dict(scope_ref=scope,owner=m.ROOT,worker_id=m.ROOT,selected_owner_ref=ownerref)
        def pending(n,rows=None):return dict(issued_by=m.ROOT,counter_reset=False,pending=[] if rows is None else rows,next_original_failure_ordinal=n)
        def row(n,sha):return dict(ordinal=n,origin_ref=rr('origin'+str(n),sha),origin_selector='synthetic'+str(n),description='Source unit only; no original runtime failure',actual_outer_exit=None,actual_python_exit=None,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
        active=None;m.doc=lambda ref:copy.deepcopy(active);m.checked=lambda ref:b'SYNTHETIC_CONTROL_ONLY'
        def checked_rows(v):
            nonlocal active
            active=v;return m.failure_rows('SYNTHETIC_NO_ROOT_PENDING_FILE',cp)
        def projected(v):return m.projection(cp,ow,scope,ownerref,workerref,facts,owner,worker,v,'2026-10-10T00:00:00Z')
        for name,n in [('backwards',99),('negative',-1),('bool',True),('string','100')]:
            v=pending(n)
            test('failure_rows empty '+name,lambda v=v:checked_rows(v),'PENDING_CONTIGUOUS_CURRENT_COUNTER')
            test('projection empty '+name,lambda v=v:projected(v),'PENDING_CONTIGUOUS_CURRENT_COUNTER')
        empty=pending(start)
        test('failure_rows empty next equals actual start',lambda:checked_rows(empty))
        def equal_projection():
            beforecp=m.encoded(cp);beforeow=m.encoded(ow);a,b=projected(empty)
            assert m.encoded(cp)==beforecp and m.encoded(ow)==beforeow and a['failure_counters']==cp['failure_counters'] and a['work_in_progress']['root_next_failure_ordinal_live']==start
            assert b['card_path_bindings']['W05-99']['subtasks']['old_scope']==ow['card_path_bindings']['W05-99']['subtasks']['old_scope']
        test('empty normal projection preserves all old failure/Scope and full inverse',equal_projection)
        continuous=pending(102,[row(100,5),row(101,6)])
        test('failure_rows normal continuous two rows with unknown exits NULL',lambda:checked_rows(continuous))
        def normal_projection():
            a,b=projected(continuous)
            assert a['failure_counters'][:1]==cp['failure_counters'] and len(a['failure_counters'])==3 and a['work_in_progress']['root_next_failure_ordinal_live']==102
            assert all(x['original_payload']['actual_python_exit'] is None and x['counter_reset'] is False for x in a['failure_counters'][1:])
            assert b['card_path_bindings']['W05-99']['subtasks']['old_scope']==ow['card_path_bindings']['W05-99']['subtasks']['old_scope']
        test('normal continuous projection preserves history and NULL rule',normal_projection)
        for name,v in [('gap',pending(102,[row(100,5)])),('duplicate ordinal',pending(102,[row(100,5),row(100,6)])),('bool ordinal',pending(101,[dict(row(100,5),ordinal=True)]))]:
            test('failure_rows '+name,lambda v=v:checked_rows(v),'PENDING_CONTIGUOUS_CURRENT_COUNTER')
            test('projection '+name,lambda v=v:projected(v),'PENDING_CONTIGUOUS_CURRENT_COUNTER')
        cp['work_in_progress']['root_next_failure_ordinal_live']=1
        bool_equal_integer=pending(2,[dict(row(1,5),ordinal=True)])
        test('failure_rows bool ordinal equals int1 rejected by type',lambda:checked_rows(bool_equal_integer),'PENDING_CONTIGUOUS_CURRENT_COUNTER')
        test('projection bool ordinal equals int1 rejected by type',lambda:projected(bool_equal_integer),'PENDING_CONTIGUOUS_CURRENT_COUNTER')
        cp['work_in_progress']['root_next_failure_ordinal_live']=start
        for k,v in original.items():setattr(m,k,v)
        # Decode the actual Full delivery, with copied observation only. No Root-issued binding/grant is fabricated.
        obs=json.loads(Path(basis['actual_Task68_observation_ref']['path']).read_bytes());peerraw=Path(basis['actual_Task68_raw_ref']['path']).read_bytes();peerrows=[json.loads(x) for x in peerraw.splitlines()];first,last=peerrows[1:]
        assert obs['Root_witness'] is False and obs['Root_authorization'] is False and obs['issued_by_Root'] is False
        with Path(obs['source_audit_path']).open('rb') as f:
            for offset,line in zip(obs['source_line_offsets'],peerraw.splitlines(keepends=True)):f.seek(offset);assert f.readline()==line
        active_last=copy.deepcopy(last);active_raw=peerraw
        m.doc=lambda ref:copy.deepcopy(obs);m.checked=lambda ref:active_raw
        m.original_capture_rows=lambda binding,raw,peer=False:(copy.deepcopy(first),copy.deepcopy(active_last))
        refs=list(basis['known_builder_Source_review_refs'].values());actor=obs['peer_actor'];op='BUILDER_SOURCE_REVIEW_WITNESS'
        def decode(expected=refs,peer=actor,operation=op):return m.validate_peer_delivery(basis['actual_Task68_observation_ref'],expected,peer,operation)
        test('exact actual Task68 legacy Full envelope and builder three refs decode',lambda:decode(),mode='ACTUAL_DELIVERY_DECODE_ONLY_ROOT_ISSUER_GATE_NOT_EXECUTED')
        envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+actor.removeprefix('codex:')+'\nPayload:\n'
        body=last['payload']['content'][0]['text'];delivered=m.strict(body[len(envelope):] if body.startswith(envelope) else body)
        def setbody(value,plain=False):
            nonlocal active_last
            active_last=copy.deepcopy(last);active_last['payload']['content'][0]['text']=('' if plain else envelope)+json.dumps(value,ensure_ascii=False)
        # Plain whole JSON is an existing allowed representation, synthetically observed here only.
        setbody(delivered,True);test('legacy plain whole JSON decode retains strict original source pin',lambda:decode())
        for field,value,code in [('component','OLD21','EXACT_LEGACY_OLD21_BUILDER_DELIVERY'),('root_thread_id','WRONG_THREAD','PEER_REVIEW_REF_BINDING'),('operation','BUILDER_SOURCE_REVIEW_WITNESS','PEER_REVIEW_REF_BINDING'),('formal_acceptance',True,'PEER_REVIEW_REF_BINDING'),('execution_grant',True,'PEER_REVIEW_REF_BINDING')]:
            d=copy.deepcopy(delivered);d[field]=value;setbody(d);test('legacy wrong '+field,lambda:decode(),code)
        active_last=copy.deepcopy(last)
        wrongrefs=copy.deepcopy(refs);wrongrefs[0]['bytes']+=1
        test('legacy altered expected builder ref bytes',lambda:decode(wrongrefs),'EXACT_LEGACY_OLD21_BUILDER_DELIVERY')
        d=copy.deepcopy(delivered);d['review_refs'][0]['sha256']='f'*64;setbody(d)
        test('legacy altered delivered ref SHA',lambda:decode(),'PEER_REVIEW_REF_BINDING')
        active_last=copy.deepcopy(last)
        test('legacy cannot replace Caller SOURCE_REVIEW_WITNESS delivery',lambda:decode(operation='SOURCE_REVIEW_WITNESS'),'PEER_TYPED_DELIVERY_REQUIRED')
        test('legacy wrong backend Full actor',lambda:decode(peer='codex:/root/not_full'),'ACTUAL_PEER_DELIVERY_REQUIRED')
        for name,change in [('client authored',lambda r:r['metadata'].update(client_authored=True)),('wrong backend author',lambda r:r['payload'].update(author='/root/not_full')),('wrong Root recipient',lambda r:r['payload'].update(recipient='/other_root'))]:
            active_last=copy.deepcopy(last);change(active_last);test(name,lambda:decode(),'ACTUAL_PEER_DELIVERY_REQUIRED')
        for name,text in [('trailing JSON',body+'\n{}'),('wrong FINAL sender',body.replace('Sender: /root/full_w09_source_review','Sender: /root/not_full')),('duplicate JSON key',envelope+'{"schema":"researchos.main23-peer-review-delivery.v2","schema":"researchos.main23-peer-review-delivery.v2"}')]:
            active_last=copy.deepcopy(last);active_last['payload']['content'][0]['text']=text;test(name,lambda:decode(),'PEER_TYPED_DELIVERY_REQUIRED')
        active_last=copy.deepcopy(last);active_raw=peerraw+b' '
        test('legacy changed original raw bytes reject',lambda:decode(),'EXACT_LEGACY_OLD21_BUILDER_DELIVERY');active_raw=peerraw
        # Caller-specific old21 schema+SOURCE_REVIEW_WITNESS remains the unchanged supported route; synthetic body only.
        d=copy.deepcopy(delivered);d['schema']='researchos.old21-peer-review-delivery.v2';setbody(d)
        test('Caller old21 schema and SOURCE_REVIEW_WITNESS route retained',lambda:decode(operation='SOURCE_REVIEW_WITNESS'))
        for k,v in original.items():setattr(m,k,v)
        before=ast.parse(Path(basis['base_caller_ref']['path']).read_bytes());after=ast.parse(raw)
        bmap={n.name:ast.dump(n,include_attributes=False) for n in before.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};amap={n.name:ast.dump(n,include_attributes=False) for n in after.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        changed=sorted(k for k in bmap if bmap[k]!=amap[k]);assert changed==['failure_rows','projection','validate_peer_delivery']
        closure=save('Task73-delta-controls.guard.closed.json',guard.close());closed=True
        result=save('Task73-delta-controls.json',dict(schema='researchos.old21-caller-Task73-delta-controls.v1',caller_ref=pin(Q/'old21_root.source.py'),controls=results,passed=len(results),failed=0,exact_changed_functions=changed,guard_ref=closure,legacy_actual_original_root_bytes_seek_verified=True,actual_legacy_decode_Source_only=True,external_Root_issuer_binding_gate_test='NOT_EXECUTED; actual independent observation used under pure decode stub',Root_witness_created=False,actual_RootScope_created=False,actual_runtime_qualification_created=False,actual_builder_called=False,Go_Native_SQL_TP_model_calls=0,live_Canon_reads=0,old_853_14782_25_not_reexecuted=True,execution_grant=False,formal_acceptance=False))
        print(json.dumps(dict(controls_ref=result,guard_ref=closure,passed=len(results),failed=0),ensure_ascii=False))
    finally:
        if not closed and any(not s.closed for s,_,_ in guard.held):save('Task73-delta-controls-attempt-failure.guard.closed.json',guard.close())
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
