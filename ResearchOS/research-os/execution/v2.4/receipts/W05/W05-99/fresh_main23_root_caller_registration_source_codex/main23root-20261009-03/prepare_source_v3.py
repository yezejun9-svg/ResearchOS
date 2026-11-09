import sys
sys.dont_write_bytecode=True
import ast
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import traceback
Q=Path(__file__).resolve().parent
BASE=Q.parent/'main23root-20261009-02'
R=Path('D:/作品集/ResearchOS/research-os')
PEER=R/'execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_independent_source_review_codex/review-fullw09-20261009-01'
ROOT_LOG=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
def pin(path,raw=None):
    path=Path(path).resolve(strict=True);raw=path.read_bytes() if raw is None else raw
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value,raw=False):
    path=Q/name;data=value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as stream:assert stream.write(data)==len(data)
    return pin(path,data)
def main():
    spec=importlib.util.spec_from_file_location('v2_finite_source_guard',BASE/'read_inputs.py')
    lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
    guard=lib.Guard();closed=False
    try:
        hraw,href=guard.read(BASE/'HDF.json',{'sha256':'c3175d8c8563e55d9350a9259b4d094d8707f4693460de99cc0fc33e41e34c5e','bytes':13007})
        mraw,mref=guard.read(BASE/'MF.json',{'sha256':'f3e43400199925ec491f46b97befbbbdb084a177206fab434bdf710b6e182ba5','bytes':31730})
        hdf=json.loads(hraw);mf=json.loads(mraw);members={Path(x['path']).name:x for x in mf['members']}
        values={}
        for name in ('main23_root.source.py','source_controls.py','source_controls_v2_observed.py','root-calling-contract.source.json','source-inputs.json','source-facts.json','static-verification.final.json'):
            raw,ref=guard.read(members[name]['path'],members[name]);values[name]=(raw,ref)
        source,source_ref=values['main23_root.source.py']
        old=b'payload.get("author") == peer_actor';new=b'payload.get("author") == peer_actor.removeprefix("codex:")'
        assert source.count(old)==1
        offset=source.index(old);candidate=source[:offset]+new+source[offset+len(old):]
        assert candidate[:offset]+old+candidate[offset+len(new):]==source
        ast.parse(candidate);compile(candidate,str(Q/'main23_root.source.py'),'exec')
        caller_ref=save('main23_root.source.py',candidate,True)
        save('caller.v2-to-v3.diff',''.join(difflib.unified_diff(source.decode('utf-8').splitlines(True),candidate.decode('utf-8').splitlines(True),fromfile='immutable-v2',tofile='candidate-v3')).encode('utf-8'),True)
        inverse_ref=save('exact-inverse.json',{'schema':'researchos.main23-peer-actor-v3-exact-byte-inverse.v1',
            'base_hdf_ref':href,'base_mf_ref':mref,'base_caller_ref':source_ref,'candidate_ref':caller_ref,
            'offset_bytes':offset,'old_utf8':old.decode(),'new_utf8':new.decode(),
            'full_inverse_to_immutable_v2_equal':True,'all_other_Source_bytes_equal':True})
        # Original22 exact Source retained. Existing45 only correct actual backend task-author fixture format.
        save('source_controls.py',values['source_controls.py'][0],True)
        controls=values['source_controls_v2_observed.py'][0]
        fixture_old=b"'payload':{'type':'agent_message','author':actor,"
        fixture_new=b"'payload':{'type':'agent_message','author':actor.removeprefix('codex:'),"
        assert controls.count(fixture_old)==1
        revised=controls.replace(fixture_old,fixture_new)
        revised=revised.replace(b"'source-controls.v2.current-final.json'",b"'source-controls.v3.final.json'")
        save('source_controls_v3.py',revised,True)
        save('controls.v2-to-v3.diff',''.join(difflib.unified_diff(controls.decode('utf-8').splitlines(True),revised.decode('utf-8').splitlines(True),fromfile='immutable-v2-45-controls',tofile='v3-synthetic-actual-task-author-format')).encode('utf-8'),True)
        br,bref=guard.read(PEER/'actual-Source-author-real-Root-peer.binding.json',{'sha256':'8b2de2f4010f2c5d11e40b305bca4cbc900b320a44d06c5decce911b50a16571','bytes':1147})
        rr,rref=guard.read(PEER/'actual-Source-author-real-Root-peer.raw.jsonl',{'sha256':'e7f9d0880969406fb1438f8d2ef038f4c6313a885d9eb8b730a814e34d7b128e','bytes':24290})
        save('real-Root-peer.binding.original.json',br,True);save('real-Root-peer.raw.original.jsonl',rr,True)
        lines=rr.splitlines(keepends=True);rows=[json.loads(x) for x in lines]
        assert len(rows)==3 and rows[0]['type']=='session_meta' and rows[0]['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
        assert rows[2]['ordinal']==60317 and rows[2]['payload']['author']=='/root/native_temp_independent_review'
        offsets=[0,262908277,262908411];prefix=264174347
        with ROOT_LOG.open('rb') as stream:
            for off,line in zip(offsets,lines):
                assert off+len(line)<=prefix
                stream.seek(off);assert stream.readline()==line
        canonical_actor='codex:/root/native_temp_independent_review'
        assert rows[2]['payload']['author']==canonical_actor.removeprefix('codex:')
        assert rows[2]['payload']['author']!='codex:/root/native_temp_independent_review'
        assert rows[2]['payload']['author']!='codex:/root/another_peer'.removeprefix('codex:')
        observation=save('real-Root-peer-mapping.control.json',{
            'schema':'researchos.main23-real-root-peer-actor-mapping-source-control.v1','status':'PASS_IDENTITY_MAPPING_ONLY',
            'actual_root_session_id':rows[0]['payload']['id'],'canonical_peer_actor':canonical_actor,
            'actual_task_author':rows[2]['payload']['author'],'actual_ordinal':rows[2]['ordinal'],
            'original_receipt_binding_ref':bref,'original_receipt_raw_ref':rref,'original_source_audit_path':str(ROOT_LOG),
            'source_line_offsets':offsets,'source_prefix_size_observed':prefix,
            'all_selected_original_source_bytes_match':True,'exact_actor_mapping':True,'wrong_peer_rejected':True,
            'not_Main23_typed_delivery':True,'not_Main23_runtime_qualification':True,
            'Native_remains_excluded_as_builder_Source_author':True,'authority':'NONE',
            'root_static_finding':'v2 canon actor compared directly to real backend /root task author; no new mechanical failure ordinal'})
        prior_contract=json.loads(values['root-calling-contract.source.json'][0]);prior_inputs=json.loads(values['source-inputs.json'][0])
        source_inputs=save('source-inputs.json',dict(prior_inputs,source_author='codex:/root/backup_regression_resources',
            references=prior_inputs['references']+[href,mref,source_ref,bref,rref],
            v3_base_hdf_ref=href,v3_base_mf_ref=mref,real_identity_mapping_receipt_refs=[bref,rref]))
        contract=dict(prior_contract,caller_ref=caller_ref,registrar_ref=caller_ref,source_inputs_ref=source_inputs)
        contract['actual_peer_delivery']['identity']='Canonical actor codex:/root/<task> maps exactly to actual backend agent_message.author /root/<task> using removeprefix(codex:); typed delivery.review_author and binding.peer_actor remain canonical. Peer Rootthread, original message provenance, issuer, independent role exclusions and every pin are unchanged.'
        contract['v3_identity_only_revision']={'base_hdf_ref':href,'base_mf_ref':mref,'inverse_ref':inverse_ref,
            'actual_mapping_control_ref':observation,'no_source_author_or_review_actor_reassignment':True,
            'real_Native_message_is_identity_evidence_only_not_Main23_qualification':True}
        contract_ref=save('root-calling-contract.source.json',contract)
        inputs=save('v3-inputs-and-delta.json',{'schema':'researchos.main23-v3-inputs-and-one-line-delta.v1',
            'base_hdf_ref':href,'base_mf_ref':mref,'source_author':'codex:/root/backup_regression_resources',
            'caller_ref':caller_ref,'contract_ref':contract_ref,'source_inputs_ref':source_inputs,
            'real_mapping_control_ref':observation,'v2_failure_origins_unchanged':json.loads(values['source-facts.json'][0])['failure_origins'],
            'old22_Source_byte_equal':True,'old45_substantive_controls_preserved':True,
            'v2_scope_role_lease_runtime_rules_preserved':True,'Native_Go_SQLite_dispatcher_model':None,'Main_Canon_oldSource_T_writes':0,
            'actual_future_qualification_ref':None,'actual_request_ref':None,'actual_registration_ref':None,'authority':'NONE'})
        closure=guard.close();closed=True;cref=save('input-source-guard.closed.json',closure)
        print(json.dumps({'inputs_ref':inputs,'caller_ref':caller_ref,'contract_ref':contract_ref,
            'real_mapping_control_ref':observation,'guard_ref':cref,'retained_handles':0,'authority':'NONE'},ensure_ascii=False))
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()
if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
