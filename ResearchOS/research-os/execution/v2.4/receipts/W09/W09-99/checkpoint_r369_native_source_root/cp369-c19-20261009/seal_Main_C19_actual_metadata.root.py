"""Read actual results losslessly; emit refs and aggregate metadata only."""
import hashlib,json,os
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W09/W09-99/w09_c19_main_root_producer_v2_source_codex/mainc19p2-1a11fe4'
actual=P/'actual-main-root';stage=actual/'producer'
def pin(p):
    p=p.resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
ready_ref=pin(actual/'prepare.ready.json');closed_ref=pin(stage/'validation.closed.json')
ready=json.loads(Path(ready_ref['path']).read_bytes());closed=json.loads(Path(closed_ref['path']).read_bytes())
assert ready['status']=='PREPARED_ALL_GUARDS_CLOSED' and closed['status']=='MAIN_C19_NATIVE_PACKET_CLOSED_PENDING_INDEPENDENT_REVIEW'
assert ready['all_guards_closed'] is True and closed['all_guards_closed'] is True and closed['all_owned_jobs_closed'] is True
assert closed['cleanup_errors']==[] and closed['formal_case_accepted_delta']==0
vector=json.loads((N/'Main-C19-current-canonical-vector.actual.root.json').read_bytes())
assert [pin(Path(ref['path'])) for ref in vector['refs']]==vector['refs']
meta=dict(schema='researchos.root-main-c19-actual-handoff.v1',issued_by='codex:/root',status=closed['status'],prepare_ready_ref=ready_ref,producer_closed_ref=closed_ref,native_packet_ref=closed['native_packet_ref'],request_ref=closed['request_ref'],vector_ref=pin(N/'Main-C19-current-canonical-vector.actual.root.json'),source_handoff_ref=pin(P/'HDF.json'),source_manifest_ref=pin(P/'MF.json'),source_root=str(R),run_id='9e912dfc1058454da08ae7f93f4de24d',actual_invocation_refs=closed['invocation_refs'],original_tool_io_refs=[pin(N/name) for name in ('Main-C19-vector.original-tool-io.root.json','Main-C19-prepare.original-tool-io.root.json','Main-C19-run.original-tool-io.root.json')],all_guards_closed=True,all_owned_jobs_closed=True,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,individual_unobserved_native_exits=None,Native_Mode_independent_review='PENDING')
out=N/'Main-C19-actual-handoff.root.json'
with out.open('xb') as f:f.write((json.dumps(meta,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));f.flush();os.fsync(f.fileno())
print(json.dumps(dict(actual_handoff_ref=pin(out),prepare_ready_ref=ready_ref,producer_closed_ref=closed_ref,native_packet_ref=closed['native_packet_ref'],invocation_count=len(closed['invocation_refs']),canonical_unchanged=True,formal_delta=0),ensure_ascii=False),flush=True)
