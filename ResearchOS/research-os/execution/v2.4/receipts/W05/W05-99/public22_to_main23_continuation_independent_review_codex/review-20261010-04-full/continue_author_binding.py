"""Unreached actual author proof and unchanged runtime-boundary checks only."""
from pathlib import Path
import ast,datetime,hashlib,json,re,types
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent;N=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-04'
OLD=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-03';PR=B/'public22_to_main23_continuation_independent_review_codex/review-20261010-03-full'
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
AUTHOR_AUDIT=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.public22-main23-continuation-source04.actual-audit.root.json'
s=types.ModuleType('support');s.__file__=str(HELPER);exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
h=json.loads((N/'HDF.json').read_bytes());author=json.loads(AUTHOR_AUDIT.read_bytes())
prefix=json.loads((D/'independent-delta-result.json').read_bytes());tail=json.loads((D/'tail-delta-result.json').read_bytes())
assert prefix['count']==prefix['passed']==7 and tail['passed']==12 and tail['checks'][-1]['passed'] is False
refs=[s.pin(__file__),s.pin(HELPER),s.pin(N/'HDF.json'),h['manifest_ref'],h['caller_ref'],h['source_inputs_ref'],h['calling_contract_ref'],
    h['predecessor_lineage_ref'],s.pin(OLD/'public22_to23_root.source.py'),s.pin(PR/'decision.json'),s.pin(AUTHOR_AUDIT),author['original_capture_ref']]
g=s.guard();checks=[];failure=None;prep=None
def check(name,ok,detail=None):
    checks.append(dict(name=name,passed=bool(ok),detail=detail))
    if not ok:raise ValueError(name)
try:
    g.acquire(refs)
    raw=g.get_buffer(h['caller_ref']['path']);old=g.get_buffer(str(OLD/'public22_to23_root.source.py'))
    i=json.loads(g.get_buffer(h['source_inputs_ref']['path']));lineage=json.loads(g.get_buffer(h['predecessor_lineage_ref']['path']))
    lines=g.get_buffer(author['original_capture_ref']['path']).splitlines(keepends=True)
    assert len(lines)==3 and all(line.endswith(b'\n') for line in lines)
    head,meta,final=[json.loads(line) for line in lines];payload=final['payload'];mp=meta['payload']
    check('actual_Attach_Final_backend_identity_adjacency_Root_parent',head['type']=='session_meta' and head['ordinal']==0
        and head['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
        and meta['type']=='inter_agent_communication_metadata' and final['type']=='response_item'
        and type(meta['ordinal']) is type(final['ordinal']) is int and final['ordinal']==meta['ordinal']+1
        and meta['timestamp']==final['timestamp']=='2026-10-10T01:52:52.500Z'
        and payload['type']=='agent_message' and payload['author']=='/root/attach_restore_independent_review'
        and payload['recipient']=='/root' and final['metadata']['client_authored'] is False
        and mp=={'trigger_turn':False})
    text=payload['content'][0]['text']
    envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/attach_restore_independent_review\nPayload:\n'
    rows=re.findall(r'^\| `([^`]+)` \| `([0-9a-f]{64})` \| ([0-9]+) \|$',text,re.M)
    expected=[s.pin(N/'HDF.json'),h['manifest_ref'],h['caller_ref'],h['calling_contract_ref']]
    check('actual_author_Markdown_full_pin_delivery_matches_Source_bytes',text.startswith(envelope)
        and ('目录：`'+str(N)+'`') in text
        and len(rows)==4 and all((Path(ref['path']).name,ref['sha256'],str(ref['bytes'])) in rows for ref in expected)
        and author['binding_sha256']==expected[0]['sha256'],dict(format='actual directory plus filename/fullSHA/bytes Markdown table',
            publication_evidence_only=True,not_a_typed_Root_review_witness=True))
    check('actual_author_capture_hashes_and_unique_offsets',author['original_line_sha256']==[hashlib.sha256(line).hexdigest() for line in lines]
        and author['source_line_offsets']==sorted(set(author['source_line_offsets'])) and author['source_line_offsets'][0]==0)
    with Path(author['source_audit_path']).open('rb') as f:
        for offset,line in zip(author['source_line_offsets'],lines):
            f.seek(offset);assert offset+len(line)<=author['source_prefix_size_observed'] and f.read(len(line))==line
    check('actual_author_Root_offset_original_bytes_readback',True)
    prior=json.loads(g.get_buffer(str(PR/'decision.json')))
    before=ast.parse(old);after=ast.parse(raw)
    def functions(tree):return {node.name:node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    a=functions(before);b=functions(after)
    check('Source03_runtime_and_business_closure_inherited_without_replay',prior['decision']=='ACCEPTED_SOURCE_ONLY'
        and prior['runtime_closure_reviewed'] is True and h['runtime_resources_ref']==prior['runtime_resources_ref']==i['runtime_resources_ref']
        and all(ast.dump(a[key],include_attributes=False)==ast.dump(b[key],include_attributes=False) for key in a if key!='projection')
        and ast.dump(ast.Module(body=[node for node in before.body if isinstance(node,(ast.Import,ast.ImportFrom))],type_ignores=[]),include_attributes=False)
            ==ast.dump(ast.Module(body=[node for node in after.body if isinstance(node,(ast.Import,ast.ImportFrom))],type_ignores=[]),include_attributes=False),
        dict(runtime_manifest_reused=149,runtime_actual_required_reused=144,Source03_full26_replayed=False,author19_replayed=False))
    observations=dict(complete_Source03_inverse_from_prefix=True,actual_source_author_audit_ref=s.pin(AUTHOR_AUDIT),
        archive_pair_refs=lineage['frozen_lineage']['after_archive_refs'],archive_revisions_only=[386,190],actual_live_CP387_OW191_read=False,
        Source_fixture_future_next=2000001,generation=dict(KEY='public22_to_main23_continuation_gen02',SLICE='PUBLIC22_TO_MAIN23_CONTINUATION_GEN02'),
        original1201_retained=True,original1025_retained=True,Root_Runtime_qualification_issued=False)
    prep=dict(source_hdf_ref=s.pin(N/'HDF.json'),source_mf_ref=h['manifest_ref'],
        **{key:h[key] for key in ('caller_ref','source_inputs_ref','calling_contract_ref','runtime_resources_ref','main23_bound_ref','existing22_decision_ref')},
        source_author=h['source_author'],runtime_boundary=prior['runtime_review_boundary'],runtime_closure_evidence_ref=prior['runtime_closure_evidence_ref'],
        inherited_review_ref=s.pin(PR/'decision.json'),actual_source_author_audit_ref=s.pin(AUTHOR_AUDIT),lineage_ref=h['predecessor_lineage_ref'],
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),observations=observations)
except BaseException as exc:
    failure=dict(type=type(exc).__name__,message=str(exc));raise
finally:
    guard_ref=s.write('author-tail-guard.closed.json',g.close())
    result_ref=s.write('author-tail-result.json',dict(checks=checks,count=len(checks),passed=sum(x['passed'] for x in checks),failure=failure,
        source_guard_ref=guard_ref,held_count=len(refs),reused_prefix_ref=s.pin(D/'independent-delta-result.json'),reused_tail_ref=s.pin(D/'tail-delta-result.json'),
        Source_only=True,product_calls=dict(Native=0,Go=0,SQL=0,dispatcher=0,TP=0,RootStage=0,model=0),execution_grant=False,formal_acceptance=False))
if prep is not None:s.write('review-preparation-context.json',prep)
print(json.dumps(dict(count=len(checks),passed=sum(x['passed'] for x in checks),failure=failure,source_guard_ref=guard_ref,result_ref=result_ref,
    Source_only=True,execution_grant=False,formal_acceptance=False),ensure_ascii=False))
