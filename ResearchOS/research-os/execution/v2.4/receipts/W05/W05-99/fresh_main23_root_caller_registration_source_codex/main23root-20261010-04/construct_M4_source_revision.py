from __future__ import annotations
import ast, copy, ctypes, difflib, hashlib, json, msvcrt, ntpath, os, sys
from ctypes import wintypes
from pathlib import Path
Q=Path(__file__).resolve().parent
B=Q.parent.parent
M3=Q.parent/'main23root-20261009-03'
REVIEW=B/'main23_qualification_time_contract_independent_review_codex/review-20261010-01'
ACTOR='codex:/root/backup_regression_resources'
THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084'
def need(value,code):
    if not value:raise ValueError(code)
def pin(path,raw=None):
    path=Path(path)
    if raw is None:raw=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,raw):
    p=Q/name
    with p.open('xb') as f:f.write(raw)
    return pin(p)
def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def save_json(name,value):return save(name,encoded(value))
class Guard:
    def __init__(self):self.held=[]
    def read(self,path,expected):
        path=Path(path).resolve(strict=True)
        api=ctypes.WinDLL('kernel32',use_last_error=True)
        api.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
        api.CreateFileW.restype=wintypes.HANDLE
        handle=api.CreateFileW(str(path),0x80000000,1,None,3,0x80,None)
        if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
        stream=os.fdopen(msvcrt.open_osfhandle(int(handle),os.O_RDONLY|os.O_BINARY),'rb')
        before=os.fstat(stream.fileno());raw=stream.read();actual=pin(path,raw)
        self.held.append((stream,actual,(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)))
        assert (actual['sha256'],actual['bytes'])==(expected['sha256'],expected['bytes'])
        return raw,actual
    def close(self):
        rows=[]
        try:
            for stream,ref,before in self.held:
                stream.seek(0);raw=stream.read();after=os.fstat(stream.fileno())
                assert before==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
                assert hashlib.sha256(raw).hexdigest()==ref['sha256']
                rows.append({'ref':ref,'volume_device_decimal':str(after.st_dev),'file_identity_decimal':str(after.st_ino),
                    'mtime_ns_decimal':str(after.st_mtime_ns),'end_identity_bytes_equal':True})
        finally:
            for stream,_,_ in self.held:stream.close()
        return {'schema':'researchos.finite-independent-source-guard.v1','records':rows,'all_handles_closed':all(x.closed for x,_,_ in self.held),'retained_handles':0,'live_Canon_handles':0}
def main():
    need(sys.flags.isolated==1 and sys.flags.no_site==1 and sys.dont_write_bytecode and sys.flags.utf8_mode==1,'LOCKED_FLAGS')
    guard=Guard();closed=False;refs={}
    def hold(ref):
        key=ntpath.normcase(ntpath.normpath(ref['path']))
        if key in refs:
            need((refs[key]['sha256'],refs[key]['bytes'])==(ref['sha256'],ref['bytes']),'INPUT_CONFLICT');return Path(ref['path']).read_bytes()
        raw,actual=guard.read(ref['path'],ref);refs[key]=actual;return raw
    try:
        hold({'path':sys.executable,'sha256':'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b','bytes':106328})
        bh={'path':str(M3/'HDF.json'),'sha256':'6ea62e31e8a8b50ac1685bee9e19b639e7df1417a1a18421fc755a0bd4b0525b','bytes':13200}
        bm={'path':str(M3/'MF.json'),'sha256':'6ede7ac360b4f71f086872a8e1ee2e7097187dd16dd6618ddc17c8ea0d296872','bytes':9259}
        h=json.loads(hold(bh));mf=json.loads(hold(bm));need(h['manifest_ref']==bm,'BASE_MF')
        for ref in mf['members']:hold(ref)
        rh=pin(REVIEW/'HDF.json');review=json.loads(hold(rh));rm=review['manifest_ref'];reviewmf=json.loads(hold(rm))
        for ref in reviewmf['members']:hold(ref)
        rd=review['decision_ref'];decision=json.loads(hold(rd))
        need(decision['verdict']=='CHANGES_REQUIRED' and decision['review_author']=='codex:/root/full_w09_source_review' and decision['independent_non_author'] is True,'TASK58_NONAUTHOR')
        minimum={x['id']:x['minimum_revision'] for x in decision['findings']}
        need(minimum['M3-TIME-01']['wrapper_projection_exclusions']==['schema','payload_ref','root_issuance_binding_ref','created_utc'],'EXACT_MINIMUM')
        basecaller=h['caller_ref'];old=hold(basecaller);need(basecaller==decision['source_caller_ref'],'REVIEW_BASE_CALLER')
        oldcontractref=h['contract_ref'];contract=json.loads(hold(oldcontractref));need(oldcontractref==decision['source_contract_ref'],'REVIEW_BASE_CONTRACT')
        oldinputsref=h['source_inputs_ref'];oldinputs=json.loads(hold(oldinputsref))
        for ref in oldinputs['references']:hold(ref)
        for ref in oldinputs['creation_baseline']:hold(ref['snapshot_ref'])
        edits=[]
        old_peer=b'    text = payload["content"][0]["text"]\n    deliveries = [x for x in structured_documents(text) if x.get("schema") == "researchos.main23-peer-review-delivery.v2"]\n    need(len(deliveries) == 1, "PEER_TYPED_DELIVERY_REQUIRED")\n    delivered = deliveries[0]\n'
        new_peer=b'    text = payload["content"][0]["text"]\n    envelope = "Message Type: FINAL_ANSWER\\nTask name: /root\\nSender: " + peer_actor.removeprefix("codex:") + "\\nPayload:\\n"\n    try:\n        delivered = strict(text[len(envelope):] if text.startswith(envelope) else text)\n    except (ValueError, TypeError):\n        need(False, "PEER_TYPED_DELIVERY_REQUIRED")\n    need(type(delivered) is dict and delivered.get("schema") == "researchos.main23-peer-review-delivery.v2",\n         "PEER_TYPED_DELIVERY_REQUIRED")\n'
        old_projection=b'    projected = {k: v for k, v in qualification.items() if k not in {"payload_ref", "root_issuance_binding_ref", "schema"}}\n'
        new_projection=b'    projected = {k: v for k, v in qualification.items() if k not in {"payload_ref", "root_issuance_binding_ref", "schema", "created_utc"}}\n'
        old_time=b'    need(when(scope["created_utc"]) <= when(review["reviewed_utc"]) <= received\n         <= when(root_binding["tool_call_timestamp"]) <= when(root_binding["tool_result_timestamp"])\n         <= when(qualification["created_utc"]), "RUNTIME_ORIGINAL_REVIEW_ISSUANCE_TIME_ORDER")\n'
        new_time=b'    need(when(scope["created_utc"]) <= when(review["reviewed_utc"]) <= received\n         <= when(qualification["payload_created_utc"]) <= when(root_binding["tool_call_timestamp"])\n         <= when(root_binding["tool_result_timestamp"]) <= when(qualification["created_utc"])\n         <= datetime.now(timezone.utc), "RUNTIME_ORIGINAL_REVIEW_ISSUANCE_TIME_ORDER")\n'
        for label,before,after in [('anchored_exact_peer_FINAL_or_plain_JSON',old_peer,new_peer),('wrapper_only_created_utc_projection',old_projection,new_projection),('causal_payload_and_wrapper_time_order',old_time,new_time)]:
            need(old.count(before)==1,'UNIQUE_BYTE_SPAN_'+label);edits.append(dict(label=label,old_offset=old.index(before),before_hex=before.hex(),after_hex=after.hex()))
        cursor=0;parts=[]
        for edit in sorted(edits,key=lambda x:x['old_offset']):
            before=bytes.fromhex(edit['before_hex']);after=bytes.fromhex(edit['after_hex']);offset=edit['old_offset'];need(offset>=cursor,'NONOVERLAP')
            parts.append(old[cursor:offset]);edit['new_offset']=sum(len(x) for x in parts);parts.append(after);cursor=offset+len(before)
        parts.append(old[cursor:]);new=b''.join(parts);restored=new
        for edit in sorted(edits,key=lambda x:x['new_offset'],reverse=True):
            before=bytes.fromhex(edit['before_hex']);after=bytes.fromhex(edit['after_hex']);offset=edit['new_offset'];need(restored[offset:offset+len(after)]==after,'INVERSE_BYTE_SPAN');restored=restored[:offset]+before+restored[offset+len(after):]
        need(restored==old,'FULL_SOURCE_BYTE_INVERSE')
        oldast=ast.parse(old);newast=ast.parse(new)
        oldfunc={n.name:ast.get_source_segment(old.decode('utf-8'),n) for n in oldast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        newfunc={n.name:ast.get_source_segment(new.decode('utf-8'),n) for n in newast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        changed=[name for name in oldfunc if oldfunc[name]!=newfunc[name]]
        need(set(changed)=={'validate_peer_delivery','runtime_review_chain'} and set(oldfunc)==set(newfunc),'ONLY_TWO_LOGIC_FUNCTIONS')
        caller=save('main23_root.source.py',new)
        save('caller.M3-to-M4.diff',''.join(difflib.unified_diff(old.decode('utf-8').splitlines(keepends=True),new.decode('utf-8').splitlines(keepends=True),fromfile=str(M3/'main23_root.source.py'),tofile=str(Q/'main23_root.source.py'))).encode('utf-8'))
        inverse=save_json('exact-inverse.json',dict(schema='researchos.main23-M4-source-byte-inverse.v1',base_ref=basecaller,candidate_ref=caller,old_byte_sha256=hashlib.sha256(old).hexdigest(),inverse_sha256=hashlib.sha256(restored).hexdigest(),inverse_bytes=len(restored),full_original_byte_inverse=True,edits=edits,changed_top_level_functions=changed,unchanged_function_names=[name for name in oldfunc if name not in changed],Root_tool_structured_documents_byte_unchanged=oldfunc['structured_documents']==newfunc['structured_documents'],relative_N_unchanged=True))
        inputs=copy.deepcopy(oldinputs);inputs['schema']='researchos.main23-M4-source-inputs.v1';inputs['M4_base_hdf_ref']=bh;inputs['M4_base_mf_ref']=bm;inputs['Task58_hdf_ref']=rh;inputs['Task58_mf_ref']=rm;inputs['Task58_decision_ref']=rd;inputs['references']=[*oldinputs['references'],bh,bm,*mf['members'],rh,rm,*reviewmf['members']]
        inputs['creation_baseline_is_inherited_historical_only']=True;inputs['future_qualification_scope_lease_request_grant']=None;inputs['old_source_controls_reused_not_rerun']=[ref for ref in mf['members'] if Path(ref['path']).name in ('source-controls.final.json','source-controls.v3.final.json','source-controls.real-peer.final.json')]
        inp=save_json('source-inputs.json',inputs)
        contract['caller_ref']=contract['registrar_ref']=caller;contract['source_inputs_ref']=inp
        contract['future_binding_policy']='Inherited immutable Source baseline is historical CP371/OW175/CM39; it is not a future current4 grant. Root must obtain fresh actual current4 and exact dynamic CAS after new nonauthor review and M4 runtime resource qualification. No futureCP372 is assumed.'
        runtimecontract=contract['runtime_qualification'];runtimecontract['fields'].insert(runtimecontract['fields'].index('created_utc'),'payload_created_utc')
        runtimecontract['payload_rule']='Wrapper schema/payload_ref/root_issuance_binding_ref/created_utc are excluded. Every other wrapper field equals payload exactly except payload schema; payload uses payload_created_utc and contains no created_utc. All identities, source refs and resource refs remain exactly bound.'
        runtimecontract['time_order']=minimum['M3-TIME-01']['required_order'];runtimecontract['creation_rule']=minimum['M3-TIME-01']['creation_rule']
        runtimecontract['wrapper_created_utc_semantics']='Actual wrapper creation after actual Root output; wrapper-only, checked <= validating current UTC.'
        runtimecontract['payload_created_utc_semantics']='Actual immutable payload creation after actual peer receipt and before actual Root call; exactly bound in payload and wrapper.'
        contract['actual_peer_delivery']['content_rule']='Exactly one whole strict JSON dictionary, either complete plain JSON or starting with the exact anchored FINAL envelope derived from validated actual peer author: Message Type: FINAL_ANSWER\\nTask name: /root\\nSender: <peer_actor.removeprefix(codex:)>\\nPayload:\\n. Reject incorrect prefix, extra text, duplicate keys and trailing JSON. Root tool structured_documents is unchanged.'
        contract['M4_minimum_revision']=dict(base_hdf_ref=bh,base_mf_ref=bm,Task58_hdf_ref=rh,Task58_mf_ref=rm,Task58_decision_ref=rd,inverse_ref=inverse,only_changed_logic_functions=changed,Root_tool_structured_documents_unchanged=True,prior_identity_and_resource_gates_unchanged=True,future_qualification_scope_lease_request_grant=None)
        cref=save_json('root-calling-contract.source.json',contract)
        save('contract.M3-to-M4.diff',''.join(difflib.unified_diff(encoded(json.loads(hold(oldcontractref))).decode('utf-8').splitlines(keepends=True),encoded(contract).decode('utf-8').splitlines(keepends=True),fromfile=str(M3/'root-calling-contract.source.json'),tofile=str(Q/'root-calling-contract.source.json'))).encode('utf-8'))
        closure=guard.close();closed=True;gref=save_json('construction-input.guard.closed.json',closure)
        result=save_json('construction-result.json',dict(schema='researchos.main23-M4-source-construction.v1',status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW',source_author=ACTOR,source_thread_id=THREAD,base_hdf_ref=bh,base_mf_ref=bm,Task58_hdf_ref=rh,Task58_mf_ref=rm,Task58_decision_ref=rd,caller_ref=caller,contract_ref=cref,source_inputs_ref=inp,inverse_ref=inverse,input_guard_ref=gref,input_ref_count=len(refs),changed_logic_functions=changed,source_guards_closed=True,retained_handles=0,live_Canon_handles=0,qualification_created=False,Scope_created=False,lease_created=False,Root_grant_created=False,Go_runs=0,Native_runs=0,SQL_runs=0,TP_runs=0,dispatcher_runs=0,model_calls=0,formal_acceptance=False,execution_grant=False))
        print(json.dumps(dict(result_ref=result,caller_ref=caller,contract_ref=cref,inverse_ref=inverse,input_guard_ref=gref,changed_logic_functions=changed,retained_handles=0),ensure_ascii=False),flush=True)
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1',flush=True);raise
    print('ROOT_PYTHON_EXIT=0',flush=True)

