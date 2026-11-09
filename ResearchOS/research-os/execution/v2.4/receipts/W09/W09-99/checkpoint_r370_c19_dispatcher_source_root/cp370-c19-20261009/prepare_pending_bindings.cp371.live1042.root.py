"""Normalize Root envelope bindings without changing original source captures."""
from pathlib import Path
import ast, hashlib, json, os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[v for v in t.body if isinstance(v,ast.FunctionDef) and v.name in ('pin','save','outputs')],type_ignores=[]),'prior_root_helpers_only','exec'),globals())
p=N/'pending-diagnostics.cp371.live1042.root.json';pending=json.loads(p.read_bytes())
summary=[]
for row in pending['pending']:
    ref=row.get('capture_binding_ref')
    if not ref:continue
    bd=json.loads(Path(ref['path']).read_bytes());raw=Path(row['origin_ref']['path']).read_bytes()
    assert pin(Path(ref['path']))==ref and pin(Path(row['origin_ref']['path']))==row['origin_ref']
    original=bd.get('original_capture_ref',bd.get('actual_capture_ref',bd.get('capture_ref')))
    assert original and original['sha256']==row['origin_ref']['sha256'] and original['bytes']==row['origin_ref']['bytes'] and Path(original['path']).resolve()==Path(row['origin_ref']['path']).resolve()
    if row['ordinal'] in (1033,1034,1035,1036):
        lines=raw.splitlines(keepends=True)
        assert len(lines)==4
        assert [len(v) for v in lines]==bd['source_line_bytes']
        assert [hashlib.sha256(v).hexdigest() for v in lines]==bd['original_line_sha256']
        header=json.loads(lines[0]);assert header['payload']['id']==bd['source_session_id']
        returned=[v for v in outputs(json.loads(lines[-1])['payload'].get('output')) if 'exit_code' in v]
        assert len(returned)==1 and returned[0]['exit_code']==1
        actual_output=returned[0]['output']
        row['actual_python_exit']=None if 'ParserError:' in actual_output else 1
        row['original_source_capture_binding_ref']=ref
        row['capture_binding_ref']=save('original'+str(row['ordinal'])+'.standard-binding.root.json',dict(
            schema='researchos.root-original-diagnostic-capture-binding.v1',issued_by='codex:/root',
            original_capture_ref=row['origin_ref'],original_source_binding_ref=ref,
            original_call_id=bd['original_call_id'],original_line_sha256=bd['original_line_sha256'],
            source_line_bytes=bd['source_line_bytes'],source_ordinals=bd['source_ordinals'],
            source_audit_path=bd['source_log'],source_session_id=bd['source_session_id'],
            tool_call_timestamp=bd['actual_call_timestamp'],tool_result_timestamp=bd['actual_result_timestamp'],
            actual_outer_exit=1,actual_python_exit=row['actual_python_exit'],
            original_raw_unchanged=True,source_offset_claim=None,formal_authority=False))
    elif not (bd.get('original_capture_ref') or bd.get('actual_capture_ref')):
        raise AssertionError('UNNORMALIZED_BINDING_'+str(row['ordinal']))
    summary.append(dict(ordinal=row['ordinal'],actual_python_exit=row['actual_python_exit'],standard_binding_ref=row['capture_binding_ref']))
pending['prior_pending_ref']=pin(p)
out=save('pending-diagnostics.cp371.registration-ready.live1042.root.json',pending)
print(json.dumps(dict(pending_ref=out,normalized_bindings=summary,originals_changed=False,Canon_written=False,next_original=1042),ensure_ascii=False),flush=True)
