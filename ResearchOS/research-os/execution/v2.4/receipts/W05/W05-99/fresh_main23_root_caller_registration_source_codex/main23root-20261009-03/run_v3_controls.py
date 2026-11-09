import sys
sys.dont_write_bytecode=True
import ast
import contextlib
import copy
import io
import json
from pathlib import Path
import traceback
import types
Q=Path(__file__).resolve().parent
def main():
    sink=io.StringIO()
    with contextlib.redirect_stdout(sink):
        exec(compile((Q/'source_controls.py').read_bytes(),str(Q/'source_controls.py'),'exec'),{'__file__':str(Q/'source_controls.py'),'__name__':'source_controls_only'})
    original=json.loads(sink.getvalue());assert len(original['controls'])==22 and all(x['pass'] for x in original['controls'])
    sink=io.StringIO()
    with contextlib.redirect_stdout(sink):
        code=(Q/'source_controls_v3.py').read_bytes()
        controls_globals={'__file__':str(Q/'source_controls_v3.py'),'__name__':'source_controls_v3_only'}
        exec(compile(code,str(Q/'source_controls_v3.py'),'exec'),controls_globals)
        controls_globals['main']()
    targeted=json.loads((Q/'source-controls.v3.final.json').read_text(encoding='utf-8'))
    assert targeted['passed']==45 and targeted['failed']==0
    m=types.ModuleType('main23_v3_real_identity_controls');m.__file__=str(Q/'main23_root.source.py')
    source=(Q/'main23_root.source.py').read_bytes();exec(compile(source,m.__file__,'exec'),m.__dict__)
    raw=(Q/'real-Root-peer.raw.original.jsonl').read_bytes();lines=raw.splitlines(keepends=True);rows=[json.loads(x) for x in lines]
    import hashlib
    rawref=m.pin(Q/'real-Root-peer.raw.original.jsonl')
    binding={'schema':'researchos.root-actual-peer-capture-binding.v2','issued_by':m.ROOT,'root_thread_id':m.ROOT_THREAD,
        'original_capture_ref':rawref,'original_line_sha256':[hashlib.sha256(x).hexdigest() for x in lines],
        'source_line_bytes':[len(x) for x in lines],'source_line_offsets':[0,262908277,262908411],
        'source_prefix_size_observed':264174347,'source_audit_path':m.ROOT_AUDIT_LOG}
    first,last=m.original_capture_rows(binding,raw,peer=True)
    assert first==rows[1] and last==rows[2]
    fn=next(x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef) and x.name=='validate_peer_delivery')
    condition=next(x.args[0] for x in ast.walk(fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='need'
        and len(x.args)>1 and isinstance(x.args[1],ast.Constant) and x.args[1].value=='ACTUAL_PEER_DELIVERY_REQUIRED')
    gate=compile(ast.Expression(condition),'actual-peer-admission-condition','eval')
    peer=m.BUILDER_AUTHOR
    def admitted(first,last,actor):return eval(gate,m.__dict__,{'first':first,'last':last,'payload':last['payload'],'peer_actor':actor})
    assert admitted(first,last,peer) is True
    assert admitted(first,last,'codex:/root/other_peer') is False
    forged=copy.deepcopy(last);forged['metadata']['client_authored']=True
    assert admitted(first,forged,peer) is False
    bad=dict(binding,root_thread_id='wrong-root-thread')
    try:m.original_capture_rows(bad,raw,peer=True)
    except ValueError as error:assert str(error)=='EXTERNAL_ROOT_CAPTURE_IDENTITY'
    else:raise AssertionError('fake Rootthread accepted')
    # Actual Native backend observation establishes identity syntax, not role qualification.
    try:m.validate_peer_delivery(None,[],m.BUILDER_AUTHOR,'SOURCE_REVIEW_WITNESS')
    except ValueError as error:assert str(error)=='ACTUAL_NONAUTHOR_PEER_REQUIRED'
    else:raise AssertionError('builder Source author qualified by identity mapping')
    value={'schema':'researchos.main23-v3-actual-root-peer-source-controls.v1','authority':'NONE',
        'original22_passed':22,'preserved45_synthetic_controls_passed':45,
        'actual_original_Root_peer_envelope_source_condition_passed':True,
        'actual_peer_author':last['payload']['author'],'canonical_actor':peer,
        'controls':['actual source rows exactly match pinned Root original bytes',
            'actual /root task author matches canonical actor through exact prefix removal',
            'wrong peer rejected','fake Rootthread rejected','client_authored true rejected',
            'Native builder Source author remains unqualified for Main23 peer role'],
        'original_real_mapping_ref':m.pin(Q/'real-Root-peer-mapping.control.json'),
        'caller_ref':m.pin(Q/'main23_root.source.py'),'future_qualification_ref':None,'actual_registration_ref':None,
        'Native_Go_SQLite_dispatcher_model':None,
        'limits':'Real frozen backend envelope is tested only through exact original-row and admission-expression conditions. It is not a Main23 typed reviewer delivery or runtime qualification; 45 full-chain controls remain synthetic and nonauthoritative.'}
    with (Q/'source-controls.real-peer.final.json').open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({'original22':22,'preserved45':45,'real_mapping_controls':6,'caller_ref':value['caller_ref'],
        'actual_runtime_qualification':False,'retained_handles':0,'authority':'NONE'},ensure_ascii=False))
if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
