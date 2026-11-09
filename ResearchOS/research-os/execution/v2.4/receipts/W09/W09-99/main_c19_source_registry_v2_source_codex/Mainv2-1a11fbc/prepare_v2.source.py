"""Prepare Mainv2 Source only; immutable inputs, no adoption entrypoint execution."""
import ast
import base64
import difflib
import hashlib
import json
from pathlib import Path
import sys
import types

R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
B=R/'execution/v2.4/receipts/W05/W05-99'
N=Path(__file__).resolve().parent
OLD=W/'main_c19_source_registry_integration_codex/mainc19-1a11f84'
CP=B/'checkpoint_r367_scope_namespace_v3_source_root/cp367-scope-v3-20261009'
QR=B/'checkpoint_r367_scope_namespace_v3_independent_review_codex/cp367v3r-01a11fad'
GP=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'

def pin(p):
    p=Path(p).resolve(strict=True);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def save(name,value,raw=False):
    data=value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with (N/name).open('xb') as f:f.write(data)
    return pin(N/name)

def load(p):return json.loads(Path(p).read_bytes())

def inverse(before,after):
    spans=[]
    for op,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if op!='equal':spans.append(dict(before_start=a,before_end=b,after_start=c,after_end=d,
            before_base64=base64.b64encode(before[a:b]).decode(),after_base64=base64.b64encode(after[c:d]).decode()))
    restored=after
    for row in reversed(spans):
        assert restored[row['after_start']:row['after_end']]==base64.b64decode(row['after_base64'])
        restored=restored[:row['after_start']]+base64.b64decode(row['before_base64'])+restored[row['after_end']:]
    assert restored==before
    return dict(whole_before_base64=base64.b64encode(before).decode(),whole_after_base64=base64.b64encode(after).decode(),
        before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),spans=spans,
        complete_byte_inverse=True)

def main():
    assert N==W/'main_c19_source_registry_v2_source_codex/Mainv2-1a11fbc'
    assert pin(OLD/'HDF.json')['sha256']=='ba6898a98c3bbd62eb8447938122ace9f95b6baad73b0cff9d1ebe597ed590eb'
    assert pin(OLD/'MF.json')['sha256']=='1087530d763b1f601509d568957d59a820ad6f385d01fef4d724da00caead004'
    inputs={}
    def add(ref):
        assert pin(ref['path'])==ref
        key=ref['path'].casefold();assert key not in inputs or inputs[key]==ref
        inputs[key]=ref
    for ref in load(OLD/'source-input-pins.original.json')['refs']:add(ref)
    for home in (OLD,CP,QR):
        add(pin(home/'HDF.json'));add(pin(home/'MF.json'))
        h=load(home/'HDF.json');assert h['manifest_ref']==pin(home/'MF.json')
        for ref in load(home/'MF.json')['members']:add(ref)
    facts=load(CP/'checkpoint.execution.facts.json')
    def discover(v):
        if isinstance(v,dict):
            if set(v)=={'path','sha256','bytes'}:add(v)
            else:
                for x in v.values():discover(x)
        elif isinstance(v,list):
            for x in v:discover(x)
    discover(facts)
    for name in ('checkpoint','path_ownership','step_state','commands'):add(pin(R/'execution/v2.4'/f'{name}.json'))
    add(pin(GP));add(pin(Path(sys.executable)))
    assert pin(GP)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    gm=types.ModuleType('mainv2_source_guard');gm.__file__=str(GP)
    exec(compile(GP.read_bytes(),str(GP),'exec'),gm.__dict__)
    guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    try:
        guard.acquire(list(inputs.values()))
        for ref in inputs.values():assert pin(ref['path'])==ref
        original=(OLD/'adopt_main_c19.source.py').read_bytes()
        before=original.decode()
        old_ns="main_c19_source_registry_integration_codex/mainc19-1a11f84"
        new_ns="main_c19_source_registry_v2_source_codex/Mainv2-1a11fbc"
        assert before.count(old_ns)==1
        old="""    require(scope['formal_case_accepted_delta']==0 and all(scope[k] is False for k in
        ('formal_dispatcher','formal_acceptance','producer_rerun','copy_native_packet','new_Go_SQL_API_model_calls',
         'checkpoint_write','ownership_write','step_state_write')),'ROOT_SOURCE_ONLY_BOUNDARY')"""
        new="""    require(all(scope[k] is False for k in
        ('formal_dispatcher','formal_acceptance','producer_rerun','copy_native_packet',
         'checkpoint_write','ownership_write','step_state_write')),'ROOT_SOURCE_ONLY_BOUNDARY')
    require(all(type(scope[k]) is int and scope[k]==0 for k in
        ('formal_case_accepted_delta','new_Go_SQL_API_model_calls')),'ROOT_STRICT_INTEGER_ZERO_BOUNDARY')"""
        assert before.count(old)==1
        after=before.replace(old_ns,new_ns).replace(old,new).encode()
        assert after.decode().replace(new,old).replace(new_ns,old_ns).encode()==original
        ast.parse(after);compile(after,str(N/'adopt_main_c19.source.py'),'exec')
        save('adopt_main_c19.source.py',after,True)
        inv=inverse(original,after)
        inv.update(schema='researchos.main-c19-v2-caller-byte-inverse.v1',original_ref=pin(OLD/'adopt_main_c19.source.py'),
            proposed_ref=pin(N/'adopt_main_c19.source.py'),authorized_changes=['fixed_namespace','strict_typed_scope_boundary'])
        save('caller.complete-byte-inverse.json',inv)
        for name in ('before.0.raw','before.1.raw','before.2.raw','before.6.raw','commands.proposed.json','commands.complete-byte-inverse.json'):
            save(name,(OLD/name).read_bytes(),True)
        def rebind(v):
            if isinstance(v,dict):
                if set(v)=={'path','sha256','bytes'} and Path(v['path']).is_relative_to(OLD):
                    return pin(N/Path(v['path']).relative_to(OLD))
                return {k:rebind(x) for k,x in v.items()}
            if isinstance(v,list):return [rebind(x) for x in v]
            if isinstance(v,str):return v.replace(str(OLD),str(N)).replace(OLD.as_posix(),N.as_posix())
            return v
        change=rebind(load(OLD/'change-set.json'));save('change-set.json',change)
        contract=rebind(load(OLD/'root-calling-contract.json'))
        contract['scope_boolean_false_fields']=['formal_dispatcher','formal_acceptance','producer_rerun','copy_native_packet','checkpoint_write','ownership_write','step_state_write']
        contract['scope_strict_integer_zero_fields']=['formal_case_accepted_delta','new_Go_SQL_API_model_calls']
        contract['scope_integer_zero_rejects']=['boolean_false','boolean_true','float_zero','nonzero_integer','string_zero','null']
        contract['after_adoption_required']=['New Main-root native packet and independent mode review: original candidate absolute owned pins cannot relocate unchanged.',
            'New explicit Root dispatch scope and actual dispatcher receipts.',
            'Independent current applicability review and production W09 formal profile before any CURRENT formal claim.']
        save('root-calling-contract.json',contract)
        save('metadata.complete-byte-inverse.json',dict(schema='researchos.main-c19-v2-metadata-byte-inverse.v1',files=[dict(name=name,
            original_ref=pin(OLD/name),proposed_ref=pin(N/name),inverse=inverse((OLD/name).read_bytes(),(N/name).read_bytes()))
            for name in ('change-set.json','root-calling-contract.json')]))
        save('source-input-pins.original.json',dict(refs=list(inputs.values()),count=len(inputs),historical_471_not_v2_results=True))
        save('fix-origin.json',dict(finding_id='CP367-V3-P1-CROSS-CALLER-INT-BOOL',review_handoff_ref=pin(QR/'HDF.json'),
            review_manifest_ref=pin(QR/'MF.json'),findings_ref=pin(QR/'findings.json'),registration_caller_ref=pin(CP/'register_cp367.v2.source.py'),
            previous_handoff_ref=pin(OLD/'HDF.json'),previous_manifest_ref=pin(OLD/'MF.json'),old_source_review_preserved=True,
            historical_control_count=471,historical_controls_reused_as_v2_pass=False,actual_execution=False))
        for ref in inputs.values():assert pin(ref['path'])==ref
    finally:
        cleanup=guard.close();save('source-preparation.guard.cleanup.actual.json',cleanup)
    assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
    print(json.dumps(dict(status='SOURCE_PREPARED',input_count=len(inputs),caller_ref=pin(N/'adopt_main_c19.source.py'),actual_adoption=False)))

if __name__=='__main__':main()
