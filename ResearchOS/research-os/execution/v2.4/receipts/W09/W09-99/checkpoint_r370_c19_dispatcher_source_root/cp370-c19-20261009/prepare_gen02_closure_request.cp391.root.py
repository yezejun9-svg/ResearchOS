"""Pin corrected peer acceptance and the actual contiguous diagnostic suffix."""
from pathlib import Path
import hashlib,json,os
S=Path(__file__).resolve().parent;V=S.parents[4];B=V/'receipts/W05/W05-99'
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(p,v):
    b=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    return pin(p)
p=json.loads((S/'cp391-pending-diagnostics1225-1230.root.json').read_bytes())
assert p['current_canonical_refs']==[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
extra={1231:(S/'original1231.platform-actual.binding.root.json',None,None,None,'Root orchestration parser SyntaxError before tool code ran; no host/Python/product process started.'),1232:(S/'original1232.fixed-actual.binding.root.json','fdf0ef',1,1,'Root platform capture expected a concatenated output rather than the actual separate text block; no artifact written; revised block boundary passed.'),1233:(S/'original1233.fixed-actual.binding.root.json','caacd8',0,0,'Independent A3 acceptance metadata cited nonexistent Source04 review-decision.json; actual query proves absence; A4 corrected only that path and derived metadata, preserving 30 actual checks.'),1234:(S/'original1234.fixed-actual.binding.root.json','380f18',1,1,'Root metadata preparation read context_seed_ref instead of published context_ref; same orchestration invocation then raised a TypeError after tool return. One original invocation, no Root stage calls.'),1235:(S/'original1235.fixed-actual.binding.root.json','dde746',1,1,'FREV Source control bad-resource fixture shared the consumer dictionary, mutating expected ref too; four successful control prefix and zero-closed Guard retained.'),1236:(S/'original1236.fixed-actual.binding.root.json','a03d66',1,1,'Root BR8 actual proposal request omitted lease_expires_at; stopped with zero closed Guard before archives, Scope, TP or Native. Seed retained.')}
for n,(f,chunk,outer,py,description) in extra.items():
    br=pin(f);d=json.loads(f.read_bytes());rr=d['original_capture_ref'];assert pin(Path(rr['path']))==rr
    lines=Path(rr['path']).read_bytes().splitlines(keepends=True);assert len(lines)==3
    assert [hashlib.sha256(x).hexdigest() for x in lines]==d['original_line_sha256']
    with Path(d['source_audit_path']).open('rb') as log:
        for off,line in zip(d['source_line_offsets'],lines):log.seek(off);assert log.readline()==line
    ev=[json.loads(x) for x in lines];assert ev[1]['payload']['call_id']==ev[2]['payload']['call_id']
    assert d['actual_outer_exit']==outer and d['actual_python_exit']==py
    p['pending'].append(dict(ordinal=n,origin_ref=rr,origin_selector='actual_host_chunk_id='+chunk if chunk else 'PLATFORM_PARSER_FAILURE_BEFORE_TOOL_CODE',capture_binding_ref=br,description=description,capture_completeness='ACTUAL_ORIGINAL_HEADER_CALL_RESULT_3LF_WITH_EXACT_SOURCE_OFFSETS',source_fact_refs=[br,rr],actual_outer_exit=outer,actual_python_exit=py,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
p['next_original_failure_ordinal']=1237;pr=save(S/'cp391-pending-diagnostics1225-1236.root.json',p)
a=B/'public22_to_main23_continuation_actual_independent_review_codex/actual-20261010-04'
q=dict(issued_by='codex:/root',formal_acceptance=False,expected_review_decision='QUALIFIED_COMPONENT_ONLY',review_decision_ref=pin(a/'review-decision.json'),review_hdf_ref=pin(a/'HDF.json'),review_mf_ref=pin(a/'MF.json'),review_delivery_audit_ref=pin(S/'w09.w05-gen02-corrected-component-review.actual-audit.root.json'),pending_diagnostics_ref=pr)
assert q['review_decision_ref']['sha256']=='f5a09c681afab822e201fa854611eb727d150b31e8d07dbf11c271f10017aa90'
qr=save(S/'cp391-gen02-closure.request.root.json',q)
print(json.dumps(dict(request_ref=qr,pending_ref=pr,Canon_written=False,formal_acceptance=False),ensure_ascii=False))
