"""Task58: finite Source-only time conditions and two original peer envelopes."""
import ast
import hashlib
import json
import os
from pathlib import Path
import types

R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W05/W05-99'
S=W/'fresh_main23_root_caller_registration_source_codex/main23root-20261009-03'
T=W/'fresh_main23_runtime_resource_independent_review_codex/runtime-20261010-03-isolated'
D=Path(__file__).resolve().parent
ACTOR='codex:/root/full_w09_source_review'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
ROOT_LOG=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
G=W/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
def pin(p):
    raw=Path(p).read_bytes()
    return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(name,value):
    with (D/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(D/name)
def check(ok,code):
    if not ok:raise AssertionError(code)
def exact_pin(ref):
    actual=pin(ref['path'])
    check(actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes'],'INPUT_PIN_'+ref['path'])
    return actual
def main():
    src=doc(S/'HDF.json'); task55=doc(T/'HDF.json')
    inputs=[pin(S/'HDF.json'),exact_pin(src['manifest_ref']),exact_pin(src['caller_ref']),exact_pin(src['contract_ref']),
        pin(T/'HDF.json'),exact_pin(task55['manifest_ref']),exact_pin(task55['decision_ref']),pin(G)]
    check(inputs[0]['sha256']=='6ea62e31e8a8b50ac1685bee9e19b639e7df1417a1a18421fc755a0bd4b0525b','EXACT_M3_HDF')
    check(inputs[4]['sha256']=='f11318a7bc0f8bac31e2a7417167e7a8499e0f07148959b222dc95b3d7f853ee','EXACT_TASK55_HDF')
    check(inputs[-1]['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85' and inputs[-1]['bytes']==11404,'SOURCE_GUARD_PIN')
    gm=types.ModuleType('task58_source_guard');gm.__file__=str(G)
    exec(compile(G.read_bytes(),str(G),'exec'),gm.__dict__)
    guard=gm.SourceReadGuard()
    try:
        guard.acquire(inputs)
        text=(S/'main23_root.source.py').read_text(encoding='utf-8')
        tree=ast.parse(text)
        funcs={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
        selected=[funcs[k] for k in ('need','strict','structured_documents')]
        # Functions must share globals; only these three inert AST functions execute.
        ns={'json':json}
        exec(compile(ast.Module(body=selected,type_ignores=[]),str(S/'main23_root.source.py'),'exec'),ns)
        chain=funcs['runtime_review_chain']
        projection=next(x for x in chain.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='projected' for t in x.targets))
        excluded=next(x for x in ast.walk(projection) if isinstance(x,ast.Set))
        check(ast.literal_eval(excluded)=={'schema','payload_ref','root_issuance_binding_ref'},'EXACT_M3_PROJECTION')
        time_stmt=next(x for x in chain.body if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call)
            and any(isinstance(a,ast.Constant) and a.value=='RUNTIME_ORIGINAL_REVIEW_ISSUANCE_TIME_ORDER' for a in x.value.args))
        time_expr=compile(ast.Expression(time_stmt.value.args[0]),str(S/'main23_root.source.py'),'eval')
        source_evidence=save('exact-source-time-and-format.json',dict(input_refs=inputs,
            source_projection_lines=[projection.lineno,projection.end_lineno],source_projection=ast.get_source_segment(text,projection),
            exact_binding_lines=[321,322],time_order_lines=[time_stmt.lineno,time_stmt.end_lineno],time_order=ast.get_source_segment(text,time_stmt),
            structured_documents_lines=[funcs['structured_documents'].lineno,funcs['structured_documents'].end_lineno],
            peer_delivery_lines=[funcs['validate_peer_delivery'].lineno,funcs['validate_peer_delivery'].end_lineno],
            contract_payload_rule=doc(S/'root-calling-contract.source.json')['runtime_qualification']['payload_rule'],
            contract_time_order=doc(S/'root-calling-contract.source.json')['runtime_qualification']['time_order'],
            Task55_verdict=doc(T/'decision.json')['verdict'],Task55_reviewed_utc=task55['reviewed_utc'],
            Task55_formal_acceptance=task55['formal_acceptance'],Task55_execution_grant=task55['execution_grant']))
        checks=[]
        def m3_case(name,p,c,r,w,expected_binding,expected_time,expected_causal):
            # Ordered integer coordinates only; no qualification/payload artifact or future UTC is created.
            qualification={'schema':'CONDITION_MODEL_ONLY','created_utc':w,'payload_ref':None,'root_issuance_binding_ref':None,'same_data':7}
            payload={'schema':'CONDITION_MODEL_ONLY','created_utc':p,'same_data':7}
            projected={k:v for k,v in qualification.items() if k not in ast.literal_eval(excluded)}
            binding={k:v for k,v in payload.items() if k!='schema'}==projected
            order=eval(time_expr,{'when':lambda x:x},dict(scope={'created_utc':0},review={'reviewed_utc':1},received=2,
                root_binding={'tool_call_timestamp':c,'tool_result_timestamp':r},qualification=qualification))
            causal=2<=p<c<r<w
            check((binding,order,causal)==(expected_binding,expected_time,expected_causal),name)
            checks.append(dict(name=name,payload_coordinate=p,call_coordinate=c,result_coordinate=r,wrapper_coordinate=w,
                exact_projection_passes=binding,M3_time_comparison_passes=order,strict_actual_creation_order_passes=causal,
                evidence_kind='FINITE_INTEGER_CONDITION_ONLY'))
        m3_case('M3_real_payload_time_bound_into_wrapper',3,4,5,3,True,False,False)
        m3_case('M3_true_post_output_wrapper_time',3,4,5,6,False,True,True)
        m3_case('M3_preselected_future_payload_time_is_causally_invalid',6,4,5,6,True,True,False)
        m3_case('M3_weak_numeric_equality_is_not_strict_causality',3,3,3,3,True,True,False)
        def corrected(p,c,r,w,peer=2,scope=0,review=1,now=10,data_equal=True):
            return data_equal and scope<=review<=peer<=p<=c<=r<=w<=now
        for name,args,expected in [
            ('M4_separate_true_payload_and_wrapper_times',(3,4,5,6),True),
            ('M4_payload_created_after_Root_call',(5,4,6,7),False),
            ('M4_wrapper_created_before_tool_output',(3,4,6,5),False),
            ('M4_reject_future_wrapper_coordinate',(3,4,5,11),False),
            ('M4_payload_before_peer',(1,4,5,6),False)]:
            value=corrected(*args);check(value==expected,name)
            checks.append(dict(name=name,expected=expected,observed=value,evidence_kind='FINITE_INTEGER_CONDITION_ONLY'))
        check(corrected(3,4,5,6,data_equal=False) is False,'M4_EXACT_DATA_BINDING_REQUIRED')
        checks.append(dict(name='M4_exact_payload_data_binding_required',expected=False,observed=False,evidence_kind='FINITE_INTEGER_CONDITION_ONLY'))
        # Extract exact 3-row captures from a fixed observed Root audit prefix.
        prefix=ROOT_LOG.stat().st_size
        with ROOT_LOG.open('rb') as f:
            head=f.readline();f.seek(max(len(head),prefix-32*1024*1024))
            if f.tell()!=len(head):f.readline()
            offset=f.tell();tail=f.read(prefix-offset)
        check(json.loads(head)['payload']['id']==ROOT_THREAD,'ACTUAL_ROOT_HEADER')
        targets={60921,60922,60969,60970};rows={}
        for line in tail.splitlines(keepends=True):
            try:item=json.loads(line)
            except (ValueError,UnicodeDecodeError):offset+=len(line);continue
            if item.get('ordinal') in targets:rows[item['ordinal']]=(offset,line,item)
            offset+=len(line)
        check(set(rows)==targets,'ROOT_ORIGINAL_FINAL_ROWS_PRESENT')
        observed=[]
        peer_actor='codex:/root/attach_fixture_source_review'
        for ordinal,operation in ((60922,'RUNTIME_QUALIFICATION_ISSUANCE'),(60970,'SOURCE_REVIEW_WITNESS')):
            first,last=rows[ordinal-1],rows[ordinal]
            first_obj,last_obj=first[2],last[2];payload=last_obj['payload']
            identity=(first_obj['type']=='inter_agent_communication_metadata' and type(first_obj['payload'].get('trigger_turn')) is bool
                and last_obj['type']=='response_item' and last_obj['ordinal']==first_obj['ordinal']+1
                and first_obj['timestamp']==last_obj['timestamp'] and payload['type']=='agent_message'
                and payload['author']==peer_actor.removeprefix('codex:') and payload['recipient']=='/root'
                and last_obj['metadata']['client_authored'] is False and len(payload['content'])==1
                and set(payload['content'][0])=={'type','text'} and payload['content'][0]['type']=='input_text')
            check(identity,'ACTUAL_PEER_IDENTITY_'+str(ordinal))
            raw=head+first[1]+last[1]
            with ROOT_LOG.open('rb') as stream:
                for off,line in ((0,head),(first[0],first[1]),(last[0],last[1])):
                    check(off+len(line)<=prefix,'ROOT_CAPTURE_PREFIX');stream.seek(off)
                    check(stream.read(len(line))==line,'ROOT_CAPTURE_ACTUAL_BYTES')
            raw_path=D/('actual-peer-'+str(ordinal)+'.raw.jsonl')
            with raw_path.open('xb') as stream:stream.write(raw)
            raw_ref=pin(raw_path)
            binding_ref=save('actual-peer-'+str(ordinal)+'.binding.json',dict(
                schema='researchos.main23-time-contract-source-review.capture.v1',review_author=ACTOR,
                source_audit_path=str(ROOT_LOG),Root_thread_id=ROOT_THREAD,source_prefix_size_observed=prefix,
                source_line_offsets=[0,first[0],last[0]],source_line_bytes=[len(head),len(first[1]),len(last[1])],
                original_line_sha256=[hashlib.sha256(x).hexdigest() for x in (head,first[1],last[1])],
                original_capture_ref=raw_ref,actual_peer_actor=peer_actor,actual_message_id=payload['id'],
                actual_received_at=last_obj['timestamp'],actual_metadata_ordinal=ordinal-1,actual_message_ordinal=ordinal,
                formal_acceptance=False,execution_grant=False,qualifying_root_binding=False))
            body=payload['content'][0]['text']
            docs=ns['structured_documents'](body)
            typed=[x for x in docs if x.get('schema')=='researchos.main23-peer-review-delivery.v2']
            expected_prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+peer_actor.removeprefix('codex:')+'\nPayload:\n'
            check(body.startswith(expected_prefix),'EXACT_OBSERVED_BACKEND_ENVELOPE_'+str(ordinal))
            stripped=ns['strict'](body[len(expected_prefix):])
            check(type(stripped) is dict and stripped['schema']=='researchos.main23-peer-review-delivery.v2'
                and stripped['operation']==operation and stripped['review_author']==peer_actor
                and stripped['root_thread_id']==ROOT_THREAD and stripped['verdict']=='ACCEPTED_SOURCE_ONLY'
                and stripped['formal_acceptance'] is False and stripped['execution_grant'] is False,'STRIPPED_COMPLETE_TYPED_BODY')
            check(type(stripped['review_refs']) is list and len(stripped['review_refs'])==3,'DELIVERED_THREE_COMPLETE_REFS')
            for ref in stripped['review_refs']:exact_pin(ref)
            check(len(typed)==0,'EXACT_M3_STRUCTURED_DOCUMENTS_REJECTS_ENVELOPE')
            def proposed_peer_body(candidate):
                if candidate.startswith('Message Type:'):
                    check(candidate.startswith(expected_prefix),'EXACT_BACKEND_FINAL_ENVELOPE_REQUIRED')
                    candidate=candidate[len(expected_prefix):]
                value=ns['strict'](candidate)
                check(type(value) is dict and value.get('schema')=='researchos.main23-peer-review-delivery.v2','ONE_COMPLETE_TYPED_PEER_JSON')
                return value
            check(proposed_peer_body(body)==stripped,'M4_ACTUAL_ENVELOPE_STRICT_JSON')
            plain=body[len(expected_prefix):]
            check(proposed_peer_body(plain)==stripped,'M4_EXISTING_COMPLETE_PLAIN_JSON_COMPATIBILITY')
            checks.append(dict(name='M4_actual_final_and_plain_JSON_'+str(ordinal),expected=True,observed=True,
                evidence_kind='ACTUAL_ORIGINAL_PEER_BODY_PLUS_FINITE_PARSER_ONLY'))
            for label,candidate in [
                ('wrong_sender',body.replace('Sender: /root/attach_fixture_source_review','Sender: /root/foreign',1)),
                ('wrong_recipient_task',body.replace('Task name: /root\n','Task name: /root/foreign\n',1)),
                ('wrong_message_type',body.replace('Message Type: FINAL_ANSWER','Message Type: MESSAGE',1)),
                ('unanchored_envelope','arbitrary prefix\n'+body),
                ('extra_JSON_document',body+'\n{}'),
                ('duplicate_JSON_key',expected_prefix+'{"schema":"researchos.main23-peer-review-delivery.v2","schema":"researchos.main23-peer-review-delivery.v2"}')]:
                rejected=False
                try:proposed_peer_body(candidate)
                except (ValueError,TypeError,AssertionError):rejected=True
                check(rejected,'M4_REJECT_'+label+'_'+str(ordinal))
                checks.append(dict(name='M4_reject_'+label+'_'+str(ordinal),expected_rejected=True,observed_rejected=True,
                    evidence_kind='FINITE_BODY_MUTATION_ONLY_NOT_ACTUAL_PEER'))
            observed.append(dict(ordinal=ordinal,operation=operation,raw_ref=raw_ref,binding_ref=binding_ref,
                exact_envelope_prefix=expected_prefix,original_body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                M3_complete_documents_found=len(docs),M3_typed_deliveries_found=len(typed),M3_rejection='PEER_TYPED_DELIVERY_REQUIRED',
                exact_envelope_stripped_strict_JSON_passes=True,actual_identity_and_original_offsets_verified=True,
                observed_delivered_refs=stripped['review_refs']))
        result_ref=save('finite-source-checks.json',dict(schema='researchos.main23-time-contract-independent-source-checks.v1',
            review_author=ACTOR,reviewer_thread_id=os.environ['CODEX_THREAD_ID'],status='CHANGES_REQUIRED_SOURCE_ONLY',
            source_evidence_ref=source_evidence,checks=checks,actual_peer_observations=observed,
            conclusion='M3 is not implementable with honest separate sequential creation timestamps and rejects both observed normal FINAL envelopes.',
            numeric_formula_alone_unsatisfiable=False,strict_real_causal_creation_cycle=True,
            model_only_no_qualification_created=True,actual_Go_runs=0,actual_Native_jobs=0,actual_SQL_runs=0,actual_dispatcher_runs=0,
            actual_model_calls=0,Canon_written=False,Source_written=False,formal_acceptance=False,execution_grant=False))
    finally:
        closed=guard.close();guard_ref=save('Source-guard.closed.json',closed)
    check(closed['closed'] is True and closed['retained_handles_count']==0 and not closed['errors'],'ALL_SOURCE_HANDLES_CLOSED')
    print(json.dumps(dict(status='CHANGES_REQUIRED_SOURCE_ONLY',finite_checks_ref=result_ref,Source_guard_ref=guard_ref,
        checks=len(checks),actual_peer_captures=observed,Source_guard_closed=True,retained_handles_count=0,
        products_started=0,qualification_created=False),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
