"""Finite synthetic controls for two reviewed Source provenance gaps.

The temporary audit, reviewers, qualification and resources below are synthetic.
They test pure validators only and cannot register, qualify or execute a product.
"""
import sys
sys.dont_write_bytecode = True
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import traceback
import types

Q = Path(__file__).resolve().parent
CALLER = Q / 'main23_root.source.py'
RESULTS = []

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':'))+'\n').encode('utf-8')

def pin(path):
    raw = Path(path).read_bytes()
    return {'path':str(Path(path).resolve()), 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}

def put(path, value, raw=False):
    data = value if raw else encoded(value)
    with Path(path).open('xb') as stream:
        assert stream.write(data) == len(data)
    return pin(path)

def pass_case(name, fn):
    value = fn()
    assert value is not False, name
    RESULTS.append({'name':name,'status':'PASS','expectation':'synthetic valid input accepted by pure validator'})

def reject_case(name, fn, code=None):
    try:
        fn()
    except (ValueError, KeyError) as error:
        assert code is None or str(error) == code, (name, str(error), code)
        RESULTS.append({'name':name,'status':'PASS','expectation':'EXPECTED_REJECTION','observed':str(error)})
        return
    raise AssertionError(name+': invalid input accepted')

def changed(value, fn):
    result = copy.deepcopy(value)
    fn(result)
    return result

def main():
    module = types.ModuleType('main23_v2_synthetic_controls')
    module.__file__ = str(CALLER)
    exec(compile(CALLER.read_bytes(), str(CALLER), 'exec'), module.__dict__)
    m = module
    now = datetime.now(timezone.utc)
    times = [(now-timedelta(minutes=5)+timedelta(seconds=i*20)).isoformat() for i in range(8)]
    operation = 'SOURCE_REVIEW_WITNESS'
    peer = 'codex:/root/synthetic_independent_verifier'
    with tempfile.TemporaryDirectory(prefix='source-controls-synthetic-', dir=Q) as tmp:
        d = Path(tmp)
        m.N = d
        audit = d/'synthetic-audit.jsonl'
        m.ROOT_AUDIT_LOG = str(audit)
        header = {'type':'session_meta','ordinal':0,'payload':{'id':m.ROOT_THREAD},'timestamp':times[0]}
        header_raw = encoded(header)
        audit.write_bytes(header_raw)
        sequence = 0

        def capture(label, first, last, peer_capture=False):
            nonlocal sequence
            sequence += 1
            rawlines = [header_raw, encoded(first), encoded(last)]
            offsets = [0]
            with audit.open('ab') as stream:
                for line in rawlines[1:]:
                    offsets.append(stream.tell()); stream.write(line)
                prefix = stream.tell()
            raw = b''.join(rawlines)
            raw_ref = put(d/(label+'.jsonl'), raw, raw=True)
            binding = {
                'schema':'researchos.root-actual-peer-capture-binding.v2' if peer_capture else 'researchos.root-actual-tool-capture-binding.v1',
                'issued_by':m.ROOT,'root_thread_id':m.ROOT_THREAD,
                'source_audit_path':str(audit),'source_line_offsets':offsets,'source_prefix_size_observed':prefix,
                'original_capture_ref':raw_ref,'original_line_sha256':[hashlib.sha256(x).hexdigest() for x in rawlines],
                'source_line_bytes':[len(x) for x in rawlines],
                'tool_call_timestamp':first['timestamp'],'tool_result_timestamp':last['timestamp']}
            return binding, raw

        def root_capture(label, refs, op=operation, observed_changes=None, peer_binding=None):
            call_id = 'synthetic-call-'+label
            observed = {'schema':m.CAPTURE_RESULT_SCHEMA,'issued_by':m.ROOT,'observer_actor':m.ROOT,
                'root_thread_id':m.ROOT_THREAD,'operation':op,'source':'tools.exec_command',
                'formal_acceptance':False,'observed_refs':copy.deepcopy(refs),
                'peer_actor':peer if peer_binding else None}
            if observed_changes: observed_changes(observed)
            host = {'chunk_id':'synthetic-host-'+label,'exit_code':0,'output':encoded(observed).decode('utf-8')}
            first = {'type':'response_item','ordinal':100+sequence*4,'timestamp':times[4],
                'payload':{'type':'custom_tool_call','name':'functions.exec','call_id':call_id,
                    'input':'// MAIN23_CAPTURE_OPERATION:'+op+'\ntext(await tools.exec_command(SYNTHETIC_SOURCE_INPUT));'}}
            last = {'type':'response_item','ordinal':first['ordinal']+1,'timestamp':times[5],
                'payload':{'type':'custom_tool_call_output','call_id':call_id,'output':encoded(host).decode('utf-8')}}
            binding, raw = capture(label, first, last)
            binding.update(operation=op, original_call_id=call_id)
            if peer_binding: binding['peer_delivery_binding_ref'] = peer_binding
            return binding, raw

        def peer_capture(label, refs, op=operation, actor=peer, changes=None):
            delivered = {'schema':'researchos.main23-peer-review-delivery.v2','review_author':actor,
                'root_thread_id':m.ROOT_THREAD,'operation':op,'verdict':'ACCEPTED_SOURCE_ONLY',
                'formal_acceptance':False,'execution_grant':False,'review_refs':copy.deepcopy(refs)}
            if changes: changes(delivered)
            first = {'type':'inter_agent_communication_metadata','ordinal':50+sequence*4,
                'timestamp':times[3],'payload':{'trigger_turn':True}}
            last = {'type':'response_item','ordinal':first['ordinal']+1,'timestamp':times[3],
                'metadata':{'client_authored':False},'payload':{'type':'agent_message','author':actor,
                    'recipient':'/root','id':'synthetic-peer-'+label,
                    'content':[{'type':'input_text','text':encoded(delivered).decode('utf-8')}]}}
            binding, raw = capture(label, first, last, True)
            binding.update(peer_actor=actor,message_id=last['payload']['id'],received_at=times[3])
            return put(d/(label+'.binding.json'), binding), binding, raw

        refs = [put(d/('review-ref-'+str(i)+'.json'), {'synthetic':True,'index':i}) for i in range(3)]
        binding, raw = root_capture('valid-root', refs)
        pass_case('structured_full_path_sha_bytes_root_capture', lambda:m.validate_root_capture(binding,raw,refs,operation))
        pass_case('recursive_complete_json_ref_values', lambda:m.exact_ref_set(refs)==m.exact_ref_set(copy.deepcopy(refs)))
        for name, mutate, code in [
            ('wrong_root_thread',lambda b:b.__setitem__('root_thread_id','synthetic-other-thread'),'EXTERNAL_ROOT_CAPTURE_IDENTITY'),
            ('wrong_binding_operation',lambda b:b.__setitem__('operation','ACTIVATION_FACTS_CURRENT_FOUR'),'EXTERNAL_CAPTURE_OPERATION'),
            ('forged_timestamp',lambda b:b.__setitem__('tool_call_timestamp',times[0]),'EXTERNAL_PAIR_ORIGINAL_TIMESTAMPS'),
            ('bad_line_hash',lambda b:b['original_line_sha256'].__setitem__(1,'0'*64),'EXTERNAL_CAPTURE_LINE_PINS'),
            ('bad_line_bytes',lambda b:b['source_line_bytes'].__setitem__(1,1),'EXTERNAL_CAPTURE_LINE_PINS'),
            ('wrong_source_audit',lambda b:b.__setitem__('source_audit_path',str(d/'not-audit.jsonl')),'EXTERNAL_ORIGINAL_SOURCE_REQUIRED'),
            ('bad_source_offset',lambda b:b['source_line_offsets'].__setitem__(1,1),'EXTERNAL_ORIGINAL_SOURCE_BYTES'),
            ('source_prefix_too_short',lambda b:b.__setitem__('source_prefix_size_observed',1),'EXTERNAL_ORIGINAL_SOURCE_REQUIRED'),
        ]:
            bad = changed(binding, mutate)
            reject_case(name, lambda b=bad:m.validate_root_capture(b,raw,refs,operation),code)
        reject_case('missing_header_or_pair',lambda:m.validate_root_capture(binding,raw.split(b'\n',1)[1],refs,operation),'EXTERNAL_CAPTURE_BOUNDS')
        reject_case('extra_record',lambda:m.validate_root_capture(binding,raw+encoded({'extra':True}),refs,operation),'EXTERNAL_CAPTURE_BOUNDS')
        for name, mutate, code in [
            ('sha_text_substring',lambda o:o.__setitem__('observed_refs',[x['sha256'] for x in refs]),'EXACT_THREE_KEY_REF'),
            ('changed_complete_ref_path',lambda o:o['observed_refs'][0].__setitem__('path',str(d/'different.json')),'EXTERNAL_PAIR_DOES_NOT_BIND_REVIEW_REFS'),
            ('changed_complete_ref_bytes',lambda o:o['observed_refs'][0].__setitem__('bytes',refs[0]['bytes']+1),'EXTERNAL_PAIR_DOES_NOT_BIND_REVIEW_REFS'),
            ('changed_complete_ref_sha',lambda o:o['observed_refs'][0].__setitem__('sha256','0'*64),'EXTERNAL_PAIR_DOES_NOT_BIND_REVIEW_REFS'),
            ('missing_expected_ref',lambda o:o['observed_refs'].pop(),'EXTERNAL_PAIR_DOES_NOT_BIND_REVIEW_REFS'),
            ('duplicate_expected_ref',lambda o:o['observed_refs'].append(o['observed_refs'][0]),'CAPTURE_DUPLICATE_REFS'),
            ('changed_issuer',lambda o:o.__setitem__('issued_by',peer),'EXTERNAL_PAIR_DOES_NOT_BIND_REVIEW_REFS'),
            ('invented_return_source',lambda o:o.__setitem__('source','invented-json-string'),'EXTERNAL_PAIR_DOES_NOT_BIND_REVIEW_REFS'),
            ('unexpected_observer',lambda o:o.__setitem__('observer_actor',peer),'EXTERNAL_PAIR_DOES_NOT_BIND_REVIEW_REFS'),
        ]:
            b,r = root_capture(name,refs,observed_changes=mutate)
            reject_case(name,lambda b=b,r=r:m.validate_root_capture(b,r,refs,operation),code)

        pb, _, _ = peer_capture('valid-peer',refs)
        b,r = root_capture('valid-witness',refs,peer_binding=pb)
        pass_case('actual_peer_record_and_root_observer_bound',lambda:m.validate_root_capture(b,r,refs,operation,peer))
        for name, actor in [('root_self_review',m.ROOT),('caller_self_review',m.CALLER_AUTHOR),('builder_self_review',m.BUILDER_AUTHOR),('unknown_actor','unqualified-reviewer')]:
            reject_case(name,lambda actor=actor:m.validate_peer_delivery(pb,refs,actor,operation),'ACTUAL_NONAUTHOR_PEER_REQUIRED')
        reject_case('claimed_actor_differs_from_actual_peer',lambda:m.validate_peer_delivery(pb,refs,'codex:/root/other_verifier',operation),'ACTUAL_PEER_DELIVERY_REQUIRED')
        for name, mutate in [
            ('peer_changes_issuer_author',lambda v:v.__setitem__('review_author',m.ROOT)),
            ('peer_wrong_root_scope',lambda v:v.__setitem__('root_thread_id','wrong-root-thread')),
            ('peer_changes_complete_ref',lambda v:v['review_refs'][0].__setitem__('bytes',1)),
            ('peer_issues_execution_grant',lambda v:v.__setitem__('execution_grant',True)),
        ]:
            p,_,_ = peer_capture(name,refs,changes=mutate)
            reject_case(name,lambda p=p:m.validate_peer_delivery(p,refs,peer,operation),'PEER_REVIEW_REF_BINDING')
        bad = changed(b,lambda v:v.pop('peer_delivery_binding_ref'))
        reject_case('missing_peer_origin_ref',lambda:m.validate_root_capture(bad,r,refs,operation,peer),'ACTUAL_NONAUTHOR_PEER_REQUIRED')

        contract = {'synthetic_source_contract':True,'source_author':m.BUILDER_AUTHOR}
        contract_ref = put(d/'synthetic-builder-contract.json',contract)
        caller_ref = pin(CALLER)
        mf_ref = put(d/'MF.json',{'members':[caller_ref]})
        hdf_ref = put(d/'HDF.json',{'source_author':m.CALLER_AUTHOR,'manifest_ref':mf_ref,'caller_ref':caller_ref})
        resources = [put(d/'synthetic-python.txt',b'SOURCE ONLY; no executable\n',True),put(d/'synthetic-go.txt',b'SOURCE ONLY; no executable\n',True)]
        scope_ref = put(d/'synthetic-qualification-scope.json',{
            'schema':'researchos.root-main23-runtime-qualification-scope.v2','issued_by':m.ROOT,
            'root_thread_id':m.ROOT_THREAD,'slice_id':'MAIN23_RUNTIME_RESOURCE_QUALIFICATION',
            'formal_acceptance':False,'execution_grant':False,'source_hdf_ref':hdf_ref,'source_mf_ref':mf_ref,
            'caller_ref':caller_ref,'builder_contract_ref':contract_ref,'created_utc':times[0],
            'lease_expires_at':(now+timedelta(hours=1)).isoformat()})
        common = {'review_author':peer,'source_author':m.CALLER_AUTHOR,'builder_source_author':m.BUILDER_AUTHOR,
            'root_thread_id':m.ROOT_THREAD,'source_hdf_ref':hdf_ref,'source_mf_ref':mf_ref,'caller_ref':caller_ref,
            'builder_contract_ref':contract_ref,'qualification_scope_ref':scope_ref,
            'python_ref':resources[0],'go_ref':resources[1]}
        decision_ref = put(d/'synthetic-runtime-decision.json',dict(common,
            schema='researchos.main23-runtime-independent-review-decision.v2',
            independent_non_author=True,verdict='RUNTIME_CLOSURE_ACCEPTED',formal_acceptance=False,
            execution_grant=False,resource_refs=resources))
        review_mf_ref = put(d/'synthetic-review-MF.json',{'members':[decision_ref]})
        review_hdf_ref = put(d/'synthetic-review-HDF.json',dict(common,
            schema='researchos.main23-runtime-independent-review-hdf.v2',manifest_ref=review_mf_ref,
            decision_ref=decision_ref,reviewed_utc=times[1]))
        review_refs = [review_hdf_ref,review_mf_ref,decision_ref]
        peer_ref,_,_ = peer_capture('runtime-peer',review_refs,'RUNTIME_QUALIFICATION_ISSUANCE')
        flat = dict(common,issued_by=m.ROOT,status='QUALIFIED_FOR_MAIN23_BUILD',
            independent_non_author=True,formal_programme_qualification=False,formal_acceptance=False,
            review_hdf_ref=review_hdf_ref,review_mf_ref=review_mf_ref,review_decision_ref=decision_ref,
            review_hostpair_binding_ref=peer_ref,resource_refs=resources,created_utc=times[6])
        payload_ref = put(d/'synthetic-runtime-payload.json',dict(flat,schema='researchos.root-main23-runtime-qualification-payload.v2'))
        rb,rr = root_capture('runtime-root-issuance',[payload_ref,scope_ref]+review_refs+[peer_ref],'RUNTIME_QUALIFICATION_ISSUANCE')
        root_ref = put(d/'synthetic-runtime-root-binding.json',rb)
        qualification = dict(flat,schema='researchos.root-main23-qualified-runtime.v2',payload_ref=payload_ref,root_issuance_binding_ref=root_ref)
        qualification_ref = put(d/'synthetic-qualification.json',qualification)
        pass_case('runtime_actual_chain_source_scope_peer_and_root_pins',lambda:m.runtime_review_chain(qualification_ref,qualification,contract))
        for name, mutate, code in [
            ('runtime_v1_two_json_claim',lambda v:v.__setitem__('schema','researchos.root-main23-qualified-runtime.v1'),'QUALIFIED_RUNTIME_ACTUAL_REVIEW_CHAIN_REQUIRED'),
            ('runtime_wrong_root_thread',lambda v:v.__setitem__('root_thread_id','wrong-root-thread'),'QUALIFIED_RUNTIME_ACTUAL_REVIEW_CHAIN_REQUIRED'),
            ('runtime_changed_payload_field',lambda v:v.__setitem__('review_author','codex:/root/fake_verifier'),'QUALIFICATION_PAYLOAD_EXACT_BINDING'),
            ('runtime_changed_resource_sha',lambda v:v['resource_refs'][0].__setitem__('sha256','0'*64),'QUALIFICATION_PAYLOAD_EXACT_BINDING'),
            ('runtime_changed_source_bytes',lambda v:v['source_hdf_ref'].__setitem__('bytes',1),'QUALIFICATION_PAYLOAD_EXACT_BINDING'),
            ('runtime_missing_review_ref',lambda v:v.pop('review_hdf_ref'),'QUALIFICATION_PAYLOAD_EXACT_BINDING'),
            ('runtime_missing_peer_origin',lambda v:v.pop('review_hostpair_binding_ref'),'QUALIFICATION_PAYLOAD_EXACT_BINDING'),
        ]:
            bad = changed(qualification,mutate)
            reject_case(name,lambda v=bad:m.runtime_review_chain(qualification_ref,v,contract),code)
        reject_case('runtime_missing_root_issuance_proof',lambda:m.runtime_review_chain(qualification_ref,changed(qualification,lambda v:v.pop('root_issuance_binding_ref')),contract))
        altered = copy.deepcopy(qualification)
        altered['root_issuance_binding_ref'] = changed(root_ref,lambda v:v.__setitem__('bytes',1))
        reject_case('runtime_root_issuance_bytes_changed',lambda:m.runtime_review_chain(qualification_ref,altered,contract),'REF_BYTES_CHANGED')
        reject_case('runtime_builder_contract_changed',lambda:m.runtime_review_chain(qualification_ref,qualification,{'synthetic_source_contract':False}),'RUNTIME_REVIEW_SOURCE_PINS')
        changed_source = CALLER.read_bytes()
        assert pin(CALLER) == caller_ref and changed_source
    result = {'schema':'researchos.main23-caller-v2-targeted-source-controls.v1',
        'status':'SOURCE_SYNTHETIC_CONTROLS_COMPLETE','authority':'NONE','source_author':m.CALLER_AUTHOR,
        'caller_ref':pin(CALLER),'controls':RESULTS,'passed':len(RESULTS),'failed':0,
        'synthetic_audit_resources_deleted':not d.exists(),
        'actual_future_qualification_ref':None,'actual_request_ref':None,'actual_registration':False,
        'Native_Go_SQLite_model_execution':None,'formal_acceptance':False,
        'limits':'Pure validators only. Synthetic records and resource text files carry no Root, reviewer or runtime authority.'}
    ref = put(Q/'source-controls.v2.final.json',result)
    print(json.dumps({'result_ref':ref,'passed':len(RESULTS),'failed':0,'temporary_fixture_removed':not d.exists(),
        'actual_future_qualification_ref':None,'actual_registration':False,'Native_Go_SQLite_model':None},ensure_ascii=False))

if __name__ == '__main__':
    code = 0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
