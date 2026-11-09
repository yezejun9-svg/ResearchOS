from __future__ import annotations
import ast, copy, hashlib, importlib.util, json, ntpath, sys, types
from datetime import datetime, timedelta, timezone
from pathlib import Path
Q=Path(__file__).resolve().parent
ACTOR='codex:/root/backup_regression_resources'
def need(v,c):
    if not v:raise ValueError(c)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    p=Q/name
    with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def load(p,name):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def pure_parts(m,tree):
    fn={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    runtime=fn['runtime_review_chain']
    projection=next(n for n in runtime.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='projected' for t in n.targets))
    checks={n.value.args[-1].value:n for n in runtime.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='need' and isinstance(n.value.args[-1],ast.Constant)}
    tf=ast.FunctionDef(name='M4_pure_time_binding',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=x) for x in ('qualification','payload','scope','review','received','root_binding')],vararg=None,kwonlyargs=[],kw_defaults=[],kwarg=None,defaults=[]),body=[copy.deepcopy(projection),copy.deepcopy(checks['QUALIFICATION_PAYLOAD_EXACT_BINDING']),copy.deepcopy(checks['RUNTIME_ORIGINAL_REVIEW_ISSUANCE_TIME_ORDER'])],decorator_list=[])
    peer=fn['validate_peer_delivery'];start=next(i for i,n in enumerate(peer.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='text' for t in n.targets))
    end=next(i for i,n in enumerate(peer.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and n.value.args and isinstance(n.value.args[-1],ast.Constant) and n.value.args[-1].value=='PEER_REVIEW_REF_BINDING')
    pf=ast.FunctionDef(name='M4_pure_peer_content',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=x) for x in ('payload','expected_refs','peer_actor','operation')],vararg=None,kwonlyargs=[],kw_defaults=[],kwarg=None,defaults=[]),body=[copy.deepcopy(peer.body[0]),*copy.deepcopy(peer.body[start:end+1]),ast.Return(value=ast.Name(id='delivered',ctx=ast.Load()))],decorator_list=[])
    module=ast.fix_missing_locations(ast.Module(body=[tf,pf],type_ignores=[]));ns=dict(m.__dict__);exec(compile(module,str(Q/'main23_root.source.py')+'#PURE_SOURCE_EXPRESSIONS_ONLY','exec'),ns)
    return ns['M4_pure_time_binding'],ns['M4_pure_peer_content'],ast.unparse(module)
def actual_peer(observation):
    binding=read(observation['binding_ref']['path']);raw=Path(observation['raw_ref']['path']).read_bytes();lines=raw.splitlines(keepends=True);rows=[json.loads(v) for v in lines]
    need(binding['qualifying_root_binding'] is False,'NO_SOURCE_CAPTURE_ROOT_AUTHORITY')
    need(len(lines)==3 and binding['source_line_bytes']==[len(v) for v in lines] and binding['original_line_sha256']==[hashlib.sha256(v).hexdigest() for v in lines],'REAL_CAPTURE_PINS')
    with Path(binding['source_audit_path']).open('rb') as f:
        for off,line in zip(binding['source_line_offsets'],lines):
            need(off+len(line)<=binding['source_prefix_size_observed'],'REAL_PREFIX');f.seek(off);need(f.read(len(line))==line,'REAL_ROOT_ORIGINAL_BYTES')
    head,first,last=rows;p=last['payload'];actor=binding['actual_peer_actor']
    need(head['type']=='session_meta' and head['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98','FIXED_ROOT_PARENT')
    need(first['type']=='inter_agent_communication_metadata' and first['ordinal']+1==last['ordinal']==observation['ordinal'] and first['timestamp']==last['timestamp'],'REAL_METADATA_ADJACENCY')
    need(p['type']=='agent_message' and p['author']==actor.removeprefix('codex:') and p['recipient']=='/root' and last['metadata']['client_authored'] is False,'REAL_PEER_IDENTITY')
    need(p['id']==binding['actual_message_id'] and last['timestamp']==binding['actual_received_at'],'REAL_MESSAGE_TIME_ID')
    return p,actor
def main():
    constructor=load(Q/'construct_M4_source_revision.py','M4_guard_no_main');guard=constructor.Guard();closed=False;refs={}
    result=read(Q/'construction-result.json');inputs=read(Q/'source-inputs.json')
    def hold(ref):
        key=ntpath.normcase(ntpath.normpath(ref['path']))
        if key in refs:need((refs[key]['sha256'],refs[key]['bytes'])==(ref['sha256'],ref['bytes']),'CONFLICT');return
        guard.read(ref['path'],ref);refs[key]=ref
    try:
        for ref in [*inputs['references'],result['caller_ref'],result['contract_ref'],result['source_inputs_ref'],result['inverse_ref'],pin(__file__),pin(Q/'construct_M4_source_revision.py'),dict(path=sys.executable,sha256='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b',bytes=106328)]:hold(ref)
        module=types.ModuleType('M4_inert_Source_only');module.__file__=str(Q/'main23_root.source.py');raw=Path(module.__file__).read_bytes();exec(compile(raw,module.__file__,'exec'),module.__dict__)
        tree=ast.parse(raw);timecheck,peercheck,extracted=pure_parts(module,tree);save('extracted-pure-source-expressions.json',dict(status='SYNTHETIC_SOURCE_ONLY_NOT_RUNTIME_QUALIFICATION',source_ref=result['caller_ref'],expressions=extracted))
        rows=[]
        def passcheck(name,fn):
            fn();rows.append(dict(name=name,status='PASS_SOURCE_ONLY'))
        def reject(name,fn):
            try:fn()
            except (ValueError,TypeError,KeyError) as e:rows.append(dict(name=name,status='PASS_EXPECTED_REJECTION',error_type=type(e).__name__,error=str(e)))
            else:raise AssertionError('EXPECTED_REJECTION:'+name)
        inverse=read(Q/'exact-inverse.json')
        passcheck('full_original_byte_inverse_and_only_two_changed_logic_functions',lambda:need(inverse['full_original_byte_inverse'] and set(inverse['changed_top_level_functions'])=={'validate_peer_delivery','runtime_review_chain'},'EXACT_TWO'))
        passcheck('Root_tool_structured_documents_byte_unchanged',lambda:need(inverse['Root_tool_structured_documents_byte_unchanged'],'NO_ROOT_STDOUT_CHANGE'))
        base=datetime.now(timezone.utc)-timedelta(seconds=180);times=[base+timedelta(seconds=10*i) for i in range(7)]
        def fixture(stamps=times):
            s,rv,rcv,pc,c,o,w=stamps
            q={'schema':'researchos.root-main23-qualified-runtime.v2','issued_by':'codex:/root','review_author':'codex:/root/synthetic_test_peer','payload_created_utc':pc.isoformat(),'created_utc':w.isoformat(),'payload_ref':'SYNTHETIC_NOT_A_REF','root_issuance_binding_ref':'SYNTHETIC_NOT_A_REF','resource_refs':['SYNTHETIC_ONLY']}
            p={k:copy.deepcopy(v) for k,v in q.items() if k not in ('schema','payload_ref','root_issuance_binding_ref','created_utc')};p['schema']='researchos.root-main23-runtime-qualification-payload.v2'
            return [q,p,{'created_utc':s.isoformat()},{'reviewed_utc':rv.isoformat()},rcv,{'tool_call_timestamp':c.isoformat(),'tool_result_timestamp':o.isoformat()}]
        passcheck('distinct_actual-causal-shaped_payload_and_wrapper_times_synthetic',lambda:timecheck(*fixture()))
        for i,label in enumerate(('scope_after_review','review_after_peer','peer_after_payload','payload_after_Root_call','Root_call_after_Root_output','Root_output_after_wrapper')):
            t=list(times);t[i]=t[i+1]+timedelta(seconds=1)
            reject(label,lambda t=t:timecheck(*fixture(t)))
        t=list(times);t[6]=datetime.now(timezone.utc)+timedelta(seconds=120)
        reject('wrapper_future_time_rejected',lambda:timecheck(*fixture(t)))
        f=fixture();f[1]['payload_created_utc']=(times[3]+timedelta(seconds=1)).isoformat()
        reject('payload_created_utc_exact_binding_changed',lambda:timecheck(*f))
        f=fixture();f[1]['created_utc']=f[0]['created_utc']
        reject('old_payload_created_utc_wrapper_circular_field_rejected',lambda:timecheck(*f))
        f=fixture();f[1]['resource_refs']=['CHANGED_SYNTHETIC_RESOURCE']
        reject('all_other_payload_resource_fields_still_exact',lambda:timecheck(*f))
        f=fixture();del f[0]['payload_created_utc'];del f[1]['payload_created_utc']
        reject('missing_payload_created_utc_rejected',lambda:timecheck(*f))
        f=fixture();f[0]['created_utc']=f[0]['created_utc'].split('+')[0]
        reject('naive_wrapper_time_rejected',lambda:timecheck(*f))
        decision=read(result['Task58_decision_ref']['path']);observations=next(x for x in decision['findings'] if x['id']=='M3-PEER-FINAL-02')['actual_peer_observations']
        examples=[]
        for observation in observations:
            p,actor=actual_peer(observation);expected=observation['observed_delivered_refs'];op=observation['operation'];ordinal=observation['ordinal']
            passcheck('actual_'+str(ordinal)+'_complete_FINAL_envelope_Source_entry',lambda p=p,a=actor,e=expected,o=op:peercheck(p,e,a,o))
            prefix=observation['exact_envelope_prefix'];plain=copy.deepcopy(p);plain['content'][0]['text']=p['content'][0]['text'][len(prefix):]
            passcheck('actual_'+str(ordinal)+'_complete_plain_JSON_compatibility',lambda p=plain,a=actor,e=expected,o=op:peercheck(p,e,a,o))
            examples.append(dict(ordinal=ordinal,raw_ref=observation['raw_ref'],binding_ref=observation['binding_ref'],actual_peer_actor=actor,actual_backend_author=p['author'],whole_body_Source_entry_passed=True,real_original_offsets_verified=True,qualification_or_Root_issuance_authority=False))
        p,actor=actual_peer(observations[0]);ob=observations[0];prefix=ob['exact_envelope_prefix'];expected=ob['observed_delivered_refs'];op=ob['operation'];body=p['content'][0]['text'];plain=body[len(prefix):];decoded=module.strict(plain)
        def changedtext(text):
            v=copy.deepcopy(p);v['content'][0]['text']=text;return v
        negatives={'wrong_message_type':body.replace('Message Type: FINAL_ANSWER','Message Type: MESSAGE',1),'wrong_task_recipient':body.replace('Task name: /root\n','Task name: /root/other\n',1),'wrong_backend_sender':body.replace('Sender: '+p['author'],'Sender: /root/wrong_peer',1),'unanchored_extra_text':'unrelated text\\n'+body,'trailing_text':body+'\\nextra','trailing_JSON':body+'\\n{}','duplicate_JSON_key':prefix+'{"schema":"researchos.main23-peer-review-delivery.v2",'+plain.lstrip()[1:]}
        for name,text in negatives.items():reject(name,lambda text=text:peercheck(changedtext(text),expected,actor,op))
        for field,value in [('review_author','codex:/root/wrong_peer'),('root_thread_id','wrong-thread'),('operation','wrong-operation'),('verdict','REJECTED'),('formal_acceptance',True),('execution_grant',True)]:
            d=copy.deepcopy(decoded);d[field]=value;reject('wrong_typed_'+field,lambda d=d:peercheck(changedtext(prefix+json.dumps(d)),expected,actor,op))
        for field,value in [('path','D:/wrong/path'),('sha256','0'*64),('bytes',expected[0]['bytes']+1)]:
            d=copy.deepcopy(decoded);d['review_refs'][0][field]=value;reject('wrong_full_ref_'+field,lambda d=d:peercheck(changedtext(prefix+json.dumps(d)),expected,actor,op))
        reject('Source_author_selfreview_still_rejected',lambda:peercheck(p,expected,module.CALLER_AUTHOR,op))
        reject('unknown_actor_syntax_still_rejected',lambda:peercheck(p,expected,'codex:/unknown-peer',op))
        closure=guard.close();closed=True;cref=save('finite-M4-controls.guard.closed.json',closure)
        rr=save('finite-M4-source-controls.json',dict(schema='researchos.main23-M4-finite-source-controls.v1',source_author=ACTOR,status='PASS_SOURCE_ONLY',controls=rows,count=len(rows),actual_peer_examples=examples,pure_expressions_extracted_from_candidate=True,synthetic_time_controls=True,old_controls_and14782_14670_not_rerun=True,guard_ref=cref,retained_handles=0,live_Canon_handles=0,actual_qualification_created=False,actual_Scope_created=False,actual_lease_created=False,actual_Root_grant_created=False,Go_runs=0,Native_jobs=0,SQL_runs=0,TP_runs=0,dispatcher_runs=0,model_calls=0,formal_acceptance=False,execution_grant=False))
        print(json.dumps(dict(result_ref=rr,guard_ref=cref,controls_count=len(rows),actual_peer_ordinals=[x['ordinal'] for x in examples],retained_handles=0,actual_qualification_created=False),ensure_ascii=False),flush=True)
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1',flush=True);raise
    print('ROOT_PYTHON_EXIT=0',flush=True)

