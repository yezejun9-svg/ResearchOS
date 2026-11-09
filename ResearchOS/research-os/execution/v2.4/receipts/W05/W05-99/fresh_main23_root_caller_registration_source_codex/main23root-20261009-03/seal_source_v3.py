import sys
sys.dont_write_bytecode=True
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import traceback
Q=Path(__file__).resolve().parent
BASE=Q.parent/'main23root-20261009-02'
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
AUTHOR='codex:/root/backup_regression_resources'
def pin(path):
    path=Path(path).resolve(strict=True);raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value,raw=False):
    path=Q/name;data=value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as stream:assert stream.write(data)==len(data)
    return pin(path)
def doc(name):return json.loads((Q/name).read_text(encoding='utf-8'))
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
    visit(value);return rows
def main():
    caller=pin(Q/'main23_root.source.py');assert (caller['sha256'],caller['bytes'])==('c72ba84cde5cbbc6cc55cd25322d2faa49b34981f5fd88ce7b746275d2af336b',56282)
    delta=doc('v3-inputs-and-delta.json');inverse=doc('exact-inverse.json')
    raw=(Q/'main23_root.source.py').read_bytes();off=inverse['offset_bytes'];new=inverse['new_utf8'].encode();old=inverse['old_utf8'].encode()
    assert raw[off:off+len(new)]==new
    restored=raw[:off]+old+raw[off+len(new):]
    assert restored==Path(inverse['base_caller_ref']['path']).read_bytes()
    old_tree,new_tree=ast.parse(restored),ast.parse(raw)
    old_f={x.name:ast.dump(x,include_attributes=False) for x in old_tree.body if isinstance(x,ast.FunctionDef)}
    new_f={x.name:ast.dump(x,include_attributes=False) for x in new_tree.body if isinstance(x,ast.FunctionDef)}
    assert set(old_f)==set(new_f) and [k for k in old_f if old_f[k]!=new_f[k]]==['validate_peer_delivery']
    assert (Q/'source_controls.py').read_bytes()==(BASE/'source_controls.py').read_bytes()
    assert doc('source-controls.v3.final.json')['passed']==45
    assert doc('source-controls.real-peer.final.json')['original22_passed']==22
    io=doc('complete-source-tool-dictionary-io.json')['items']
    expected={x['response']['chunk_id']:x['response'] for x in io if x['key'] in ('main23v3_prepare','main23v3_controls')}
    assert len(expected)==2
    calls={};found={};prefix=AUDIT.stat().st_size
    with AUDIT.open('rb') as stream:
        header_raw=stream.readline();header=json.loads(header_raw)
        assert header['payload']['id']=='01a11cee-bf59-7a01-be0e-9f799f9b1084' and header['payload']['agent_path']=='/root/backup_regression_resources'
        assert header['payload']['parent_thread_id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
        while stream.tell()<prefix:
            offset=stream.tell();line=stream.readline()
            if offset+len(line)>prefix:break
            row=json.loads(line);p=row.get('payload',{})
            if row.get('type')!='response_item' or type(p) is not dict:continue
            cid=p.get('call_id')
            if p.get('type') in ('custom_tool_call','function_call') and p.get('name') in ('exec','functions.exec'):calls[cid]=(offset,line,row)
            elif p.get('type') in ('custom_tool_call_output','function_call_output') and cid in calls and any(c in line.decode('utf-8') for c in expected):
                for v in dictionaries(p.get('output')):
                    if v.get('chunk_id') in expected and v==expected[v['chunk_id']]:
                        assert v['chunk_id'] not in found;found[v['chunk_id']]=(calls[cid],(offset,line,row),v)
    assert set(found)==set(expected)
    capture_refs=[]
    for chunk,(call,output,host) in found.items():
        lines=[(0,header_raw,header),call,output]
        rawref=save('actual-Source-'+chunk+'.jsonl',b''.join(x[1] for x in lines),True)
        binding=save('actual-Source-'+chunk+'.binding.json',{'schema':'researchos.actual-source-tool-pair-binding.v1',
            'source_author':AUTHOR,'author_thread_id':header['payload']['id'],'parent_root_thread_id':header['payload']['parent_thread_id'],
            'actual_agent_path':header['payload']['agent_path'],'source_audit_path':str(AUDIT),'source_prefix_size_observed':prefix,
            'source_line_offsets':[x[0] for x in lines],'source_line_ordinals':[x[2]['ordinal'] for x in lines],
            'source_line_bytes':[len(x[1]) for x in lines],'source_line_sha256':[hashlib.sha256(x[1]).hexdigest() for x in lines],
            'actual_call_id':call[2]['payload']['call_id'],'actual_outer_exit':host['exit_code'],
            'actual_python_exit':0 if 'ROOT_PYTHON_EXIT=0' in host['output'] else None,
            'Go_Native_SQLite_dispatcher_model':None,'original_capture_ref':rawref,'authority':'NONE'})
        capture_refs.append({'raw_ref':rawref,'binding_ref':binding})
    static=save('static-verification.json',{'schema':'researchos.main23-v3-exact-identity-static-verification.v1',
        'Source_author':AUTHOR,'full_inverse_to_v2':True,'only_changed_function':'validate_peer_delivery',
        'other_function_ASTs_equal':True,'original22_Source_byte_equal':True,'existing45_substantive_controls_preserved':True,
        'real_Root_peer_mapping_controls':6,'no_new_actor_admitted':True,'Root_or_Source_author_self_review_still_rejected':True,
        'future_qualification_ref':None,'authority':'NONE'})
    report=save('source-report.md',('''v3 仅修复 canonical codex:/root/<task> 到实际 backend /root/<task> 的精确身份映射。
唯一生产候选差分为 validate_peer_delivery 内 peer_actor.removeprefix("codex:")；所有其他函数与 v2 AST/bytes 保留。
v2 HDF/MF、45控件、inverse与全部历史1031/1032/1037/1038证据原件不变；本包没有新的机械失败。
作者仍为 backup；builder 作者 Native 不变，实际作者 thread/Root parent 见 actual-Source-*.binding.json。
原22控件 Source逐字节保留，45有限纯控件只把合成backend actor格式修正为 /root/task，全部通过。
真实 Root 原始三行在 offsets0/262908277/262908411、ordinal60317 已逐字节验证。
6项真实来源条件控制覆盖真实映射、错peer、假Rootthread、client_authored以及 Native角色拒绝。
Native的真实旧消息只证明身份格式；它不是 Main23 typed delivery，也不赋予 Main23运行资格。
原完整HDF/MF/decision refs、Root原审计、peer typed交付、非作者角色、scope/lease、资源pins、Root发行次序与阈值都不变。
Source_only，authority=NONE；未来 qualification/request/registration/grant均NULL。
Main/Canon/旧Source/T*写入0；没有Go/native/SQLite/dispatcher/model执行。
等待非作者新审查与 Root 新Scope/真实runtime资格；封存后 STOP。
''').encode('utf-8'),True)
    spec=importlib.util.spec_from_file_location('v3_source_guard',BASE/'read_inputs.py');lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
    guard=lib.Guard();closed=False
    try:
        for path in sorted(p for p in Q.rglob('*') if p.is_file()):
            data,ref=guard.read(path,pin(path))
            if path.suffix=='.py':ast.parse(data);compile(data,str(path),'exec')
        for ref in [delta['base_hdf_ref'],delta['base_mf_ref'],inverse['base_caller_ref']]:guard.read(ref['path'],ref)
        closure=guard.close();closed=True;closure.update(authority='NONE',live_Canon_handles=0)
        guardref=save('finite-source-guard.final.closed.json',closure)
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()
    members=sorted((pin(p) for p in Q.rglob('*') if p.is_file()),key=lambda x:x['path'])
    mf=save('MF.json',{'schema':'researchos.immutable-source-manifest.v1','source_author':AUTHOR,'authority':'NONE','members':members,
        'excluded_postseal_files':['source-seal.actual-tool-pair.json'],'excluded_reason':'Self-referential final seal actual tool pair is recorded after immutable pins; no member changes.'})
    hdf=save('HDF.json',{'schema':'researchos.main23-root-caller-registration-source-hdf.v3','status':'SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING',
        'source_author':AUTHOR,'source_thread_id':header['payload']['id'],'parent_root_thread_id':header['payload']['parent_thread_id'],
        'actual_agent_path':header['payload']['agent_path'],'builder_source_author':'codex:/root/native_temp_independent_review',
        'manifest_ref':mf,'caller_ref':caller,'registrar_ref':caller,'contract_ref':pin(Q/'root-calling-contract.source.json'),
        'source_inputs_ref':pin(Q/'source-inputs.json'),'report_ref':report,'static_verification_ref':static,'Source_guard_ref':guardref,
        'base_hdf_ref':delta['base_hdf_ref'],'base_mf_ref':delta['base_mf_ref'],'inverse_ref':pin(Q/'exact-inverse.json'),
        'actual_source_hostpairs':capture_refs,'real_Root_peer_mapping_ref':pin(Q/'real-Root-peer-mapping.control.json'),
        'controls_real_mapping_ref':pin(Q/'source-controls.real-peer.final.json'),'controls45_ref':pin(Q/'source-controls.v3.final.json'),
        'controls22_ref':pin(Q/'source-controls.final.json'),'v2_original_failures_unchanged':delta['v2_failure_origins_unchanged'],
        'created_utc':datetime.now(timezone.utc).isoformat(),'Source_only':True,'authority':'NONE',
        'actual_future_qualification_ref':None,'actual_request_ref':None,'actual_registration_ref':None,'actual_grant_ref':None,
        'Main_Canon_oldSource_T_writes':0,'Go_Native_SQLite_dispatcher_model':None,'live_Canon_held_handles':0,
        'formal_acceptance':False,'parent_acceptance':False,'author_STOP_after_seal':True})
    for ref in members+[mf,hdf]:
        assert pin(ref['path'])==ref
        path=Path(ref['path']);path.chmod(path.stat().st_mode & ~stat.S_IWRITE)
    print(json.dumps({'HDF_ref':hdf,'MF_ref':mf,'members':len(members),'caller_ref':caller,
        'contract_ref':pin(Q/'root-calling-contract.source.json'),'report_ref':report,'guard_ref':guardref,
        'Source_controls':{'original22':22,'preserved45':45,'real_mapping6':6},'retained_handles':0,
        'future_qualification_ref':None,'actual_registration':False,'authority':'NONE','STOP':True},ensure_ascii=False))
if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
