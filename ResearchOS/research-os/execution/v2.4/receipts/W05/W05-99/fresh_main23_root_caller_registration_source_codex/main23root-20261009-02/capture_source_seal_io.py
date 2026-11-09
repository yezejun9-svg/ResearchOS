import sys
sys.dont_write_bytecode=True
import hashlib
import json
from pathlib import Path
import stat
import traceback
Q=Path(__file__).resolve().parent
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
def pin(path):
    path=Path(path).resolve(strict=True);raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value,raw=False):
    path=Q/name;data=value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as stream:assert stream.write(data)==len(data)
    path.chmod(path.stat().st_mode & ~stat.S_IWRITE)
    return pin(path)
def dictionaries(value):
    rows=[]
    def visit(v,depth=0):
        if depth>24:return
        if type(v) is dict:
            rows.append(v)
            for x in v.values():visit(x,depth+1)
        elif type(v) is list:
            for x in v:visit(x,depth+1)
        elif type(v) is str:
            seen=set()
            for text in [v]+v.splitlines():
                text=text.strip()
                if text in seen or not text.startswith(('{','[')):continue
                seen.add(text)
                try:visit(json.loads(text),depth+1)
                except json.JSONDecodeError:continue
    visit(value)
    return rows
def main():
    hdf=pin(Q/'HDF.json');mf=pin(Q/'MF.json')
    assert (hdf['sha256'],hdf['bytes'])==('c3175d8c8563e55d9350a9259b4d094d8707f4693460de99cc0fc33e41e34c5e',13007)
    assert (mf['sha256'],mf['bytes'])==('f3e43400199925ec491f46b97befbbbdb084a177206fab434bdf710b6e182ba5',31730)
    expected=json.loads((Q/'source-seal.actual-tool-pair.json').read_text(encoding='utf-8'))['response']
    calls={};matches=[];prefix=AUDIT.stat().st_size
    with AUDIT.open('rb') as stream:
        header_raw=stream.readline();header=json.loads(header_raw)
        assert header['type']=='session_meta' and header['payload']['id']=='01a11cee-bf59-7a01-be0e-9f799f9b1084'
        assert header['payload']['parent_thread_id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
        assert header['payload']['agent_path']=='/root/backup_regression_resources'
        while stream.tell()<prefix:
            offset=stream.tell();raw=stream.readline()
            if offset+len(raw)>prefix:break
            row=json.loads(raw);payload=row.get('payload',{})
            if row.get('type')!='response_item' or type(payload) is not dict:continue
            call_id=payload.get('call_id')
            if payload.get('type') in ('custom_tool_call','function_call') and payload.get('name') in ('exec','functions.exec'):
                calls[call_id]=(offset,raw,row)
            elif payload.get('type') in ('custom_tool_call_output','function_call_output') and call_id in calls and b'996413' in raw:
                for value in dictionaries(payload.get('output')):
                    if value==expected:matches.append((calls[call_id],(offset,raw,row)))
    assert len(matches)==1
    call,output=matches[0];records=[(0,header_raw,header),call,output]
    rawref=save('source-seal.actual-source-hostpair.jsonl',b''.join(x[1] for x in records),True)
    binding=save('source-seal.actual-source-hostpair.binding.json',{
        'schema':'researchos.actual-source-seal-hostpair-binding.v1','authority':'NONE',
        'source_author':'codex:/root/backup_regression_resources','author_session_id':header['payload']['id'],
        'root_parent_thread_id':header['payload']['parent_thread_id'],'actual_agent_path':header['payload']['agent_path'],
        'source_audit_path':str(AUDIT),'source_prefix_size_observed':prefix,
        'source_line_offsets':[x[0] for x in records],'source_line_ordinals':[x[2]['ordinal'] for x in records],
        'source_line_bytes':[len(x[1]) for x in records],'source_line_sha256':[hashlib.sha256(x[1]).hexdigest() for x in records],
        'actual_call_id':call[2]['payload']['call_id'],'actual_outer_exit':0,'actual_Python_exit':0,
        'actual_go_native_sqlite_dispatcher_model_exit':None,'raw_original_capture_ref':rawref,
        'HDF_ref':hdf,'MF_ref':mf,'all_selected_original_lines_match':True})
    members=json.loads((Q/'MF.json').read_text(encoding='utf-8'))['members']
    assert all(pin(x['path'])==x for x in members)
    assert all(not (Path(x['path']).stat().st_mode & stat.S_IWRITE) for x in members+[hdf,mf])
    summary=save('source-seal.closed-summary.json',{
        'schema':'researchos.main23-v2-source-seal-closed-summary.v1','HDF_ref':hdf,'MF_ref':mf,
        'members':len(members),'all_immutable_member_pins_equal':True,'all_members_readonly':True,
        'actual_seal_tool_pair_ref':pin(Q/'source-seal.actual-tool-pair.json'),
        'actual_seal_raw_hostpair_ref':rawref,'actual_seal_binding_ref':binding,
        'guard_ref':pin(Q/'finite-source-guard.final.closed.json'),'retained_handles':0,'live_Canon_handles':0,
        'actual_future_qualification_ref':None,'actual_registration_ref':None,'actual_grant_ref':None,
        'formal_acceptance':False,'authority':'NONE','author_STOP':True,
        'postseal_exclusion':'These self-referential seal receipts were predeclared in immutable MF; no member/HDF/MF was changed.'})
    print(json.dumps({'summary_ref':summary,'raw_hostpair_ref':rawref,'binding_ref':binding,
        'member_count':len(members),'pins_unchanged':True,'retained_handles':0,'STOP':True},ensure_ascii=False))
if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
