"""Root appends once-only immutable observations without changing Canon."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os,sys
R=Path(r'D:\作品集\ResearchOS\research-os')
N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
W=R/'execution/v2.4/receipts/W09/W09-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
names={'pin','exact','save','outputs','capture'}
functions=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names]
assert {x.name for x in functions}==names
exec(compile(ast.Module(body=functions,type_ignores=[]),'<original-Root-capture-helpers>','exec'),globals())
def doc(path):return json.loads(Path(path).read_bytes())
def verify(ref):
    actual=pin(ref['path']);assert (actual['sha256'],actual['bytes'])==(ref['sha256'],ref['bytes'])
    return ref
before=doc(N/'pending-diagnostics.cp371.live1043.root.json')
assert before['next_original_failure_ordinal']==1043
rows=list(before['pending'])
assert [x['ordinal'] for x in rows]==list(range(1024,1043))
def add(number,raw,binding,description,outer,python,selector='$',member=None):
    verify(raw);verify(binding)
    original_binding=doc(binding['path'])
    if member is not None:original_binding=original_binding['captures'][member]
    # Preserve the entire Source binding untouched, then normalize only this Root reference envelope.
    wrapper=save('original%d.standard-binding.live1058.root.json'%number,dict(
        schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',
        original_capture_ref=raw,original_source_binding_ref=binding,original_source_binding_selector='$' if member is None else '$.captures[%d]'%member,
        original_ordinal=number,original_bytes_unchanged=True,formal_authority=False))
    rows.append(dict(ordinal=number,origin_ref=raw,origin_selector=selector,description=description,
        capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',capture_binding_ref=wrapper,
        actual_outer_exit=outer,actual_python_exit=python,actual_native_exit=None,
        actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
rc=B/'public22_existing_observation_root_caller_source_codex/recheckroot-20261009-01'
rcd=doc(rc/'original1043-diagnostic.json')
pair=next(x for x in rcd['original_captures'] if x['chunk_id']=='72e203')
add(1043,pair['raw_ref'],pair['binding_ref'],'Source runtime gate rejected two omitted loaded modules. One original invocation: start7e23a1/session61695/completion72e203. Complete initial manifest and command retained; no product child.',1,1)
nf=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-02'
aggregate=pin(nf/'actual-hostpairs.binding.json')
captures=doc(aggregate['path'])['captures']
for number,index,outer,py,text in (
    (1044,3,1,1,'Source original capture adapter missed real output shape; preserved 073ed3 assertion failure before repaired capture input.'),
    (1045,4,0,None,'PowerShell read-only diagnostic called Substring on array; actual wrapper0, Python not invoked.')):
    add(number,captures[index]['actual_capture_ref'],aggregate,text,outer,py,member=index)
m3r=B/'fresh_main23_root_caller_registration_independent_source_review_codex/review-20261010-03'
entries=doc(m3r/'complete-hostpair-seal.json')['original_failures']
lookup={x['chunk']:x for x in entries}
for number,chunk,outer,py,text in (
    (1046,'8e1773',0,None,'Independent Source reader guessed legacy decision filename; real outer0 and Python not invoked.'),
    (1048,'4eeb48',1,1,'Independent Source sealer original adapter missed Promise.value. Failed original input retained; no product.'),
    (1049,'7a6d99',1,1,'Independent Source sealer original adapter could not locate forwarded output without chunk ID. Failed original input retained.'),
    (1050,'479ae0',1,None,'PowerShell OpenText on live audit caused sharing error; same invocation secondary reader errors retained. Python not invoked.')):
    x=lookup[chunk];add(number,x['capture_ref'],x['binding_ref'],text,outer,py)
nr=W/'full_w09_main_native_producer_independent_source_review_codex/review-fullw09-20261010-02'
lookup={x['name']:x for x in doc(nr/'source-review-decision.json')['actual_hostpairs']}
for number,name,outer,py,text in (
    (1047,'original1047-unknown-exit-read-diagnostic',None,None,'Reviewer guessed peer control filename. Original wrapper forwarded output only; numeric exit remains UNKNOWN/NULL.'),
    (1051,'168ba0',1,1,'Independent Source review script SyntaxError before guard acquisition; original failed script and actual host IO retained.'),
    (1052,'f2df44',1,1,'Real Source package rejected incompatible HDF status; reviewer failed full-SHA delivery lookup on abbreviated actual author Final. Guard closed0.'),
    (1053,'11a21f',1,1,'Independent in-memory authority-shape continuation lacked hashlib in fixture globals; original failed script retained, guard closed0. No real grant.')):
    x=lookup[name];add(number,x['raw_ref'],x['binding_ref'],text,outer,py)
tr=B/'fresh_main23_runtime_resource_independent_review_codex/runtime-20261010-03-isolated'
for number,stem,outer,py,text in (
    (1054,'original-review-interface-error',1,1,'Independent resource reviewer passed Path to string-only canonical path interface; original interface failure preserved.'),
    (1055,'original-nonisolated-rejection',0,0,'Independent resource qualification rejected 25 extra startup resources under non-isolated Python launch. Original REJECTED retained; corrected locked isolated launch passed without weakening gate.')):
    add(number,pin(tr/(stem+'.actual-host.raw.jsonl')),pin(tr/(stem+'.actual-host.binding.json')),text,outer,py)
rr=B/'public22_existing_observation_root_caller_independent_source_review_codex/review-20261010-01'
origin=doc(rr/'failure-origin.1056.json')
add(1056,origin['actual_host_raw_ref'],origin['actual_host_binding_ref'],'Independent caller reviewer report guessed third original case field. Actual immutable request is case_id/output_root/end_version=22; original report error preserved.',1,1)
def failed_root_capture(call,result):
    return any(x.get('chunk_id')=='599b63' for x in outputs(result['payload'].get('output')))
pair=capture(AUDIT,1057,failed_root_capture,root=True)
assert pair is not None
add(1057,pair[0],pair[1],'Root original provenance adapter attempted JSON decode before removing exact backend FINAL envelope; actual assertion1/1 preserved. New v2 finite adapter captured exact original records.',1,1)
rows.sort(key=lambda x:x['ordinal'])
assert [x['ordinal'] for x in rows]==list(range(1024,1058))
canonical=[]
for name,sha,size in (
('checkpoint.json','667f1515a5b62e2d7ee4948bf17055b7f9a0cce6391ad66c76ea70dde99255ba',4533514),
('path_ownership.json','4e294919209b1d65b5f869f613ada3a706a16ccaa8fb194dfca1d8982ddb7d3a',211140),
('step_state.json','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),
('commands.json','28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968)):
    canonical.append(exact(R/'execution/v2.4'/name,sha,size))
pending=save('pending-diagnostics.cp371.live1058.root.json',dict(before,pending=rows,
    next_original_failure_ordinal=1058,registered_in_current_canon=False,counter_reset=False))
resume=save('RESUME.cp371-time-contract-live1058.root.json',dict(
    schema='researchos.root-execution-resume.v1',issued_by='codex:/root',root_thread_id=THREAD,
    created_utc=datetime.now(timezone.utc).isoformat(),canonical_refs=canonical,
    expected_revisions=dict(checkpoint=371,path_ownership=175,step_state=None,commands=39),
    next_original_failure_ordinal=1058,pending_ref=pending,counter_reset=False,
    formal_cases_current_accepted=0,formal_cases_required=42,parent_tasks_required=22,
    identity_ref=exact(R/'execution/project_identity.json','03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec',420),
    original_public22_status='STOPPED_AT_FIRST_FAILURE_ORIGINAL1025_RETAINED',
    Main23=dict(source='M3_SOURCE_REVIEW_ACCEPTED',runtime_resources='ISOLATED_145_RESOURCE_REVIEW_ACCEPTED',
        actual_build='NOT_STARTED',remaining='Independent review of actual time contract and backend typed FINAL envelope; preserve all actual review/scope provenance.',
        provenance_ref=pin(N/'main23.v3.original-provenance.index.root.json')),
    W09=dict(source='V3_PUBLISHED_PACKAGE_REFS_PASS_PENDING_INDEPENDENT_REVIEW',actual_three_groups='NOT_STARTED'),
    public22_readonly_caller=dict(source='SOURCE_ACCEPTED_PENDING_ROOT_REGISTRATION',original_native_children='FOUR_ALREADY_FINISHED_NO_RERUN'),
    future_execution_grant=False,parent_acceptance=False,goal_status='ACTIVE',
    prior_resume_ref=pin(N/'RESUME.cp371-peer-source-changes-required.live1043.root.json')))
print(json.dumps(dict(pending_ref=pending,resume_ref=resume,rows=len(rows),next_original_failure_ordinal=1058,Canon_unchanged=True),ensure_ascii=False,indent=2))

