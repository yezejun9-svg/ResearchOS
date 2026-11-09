"""Append truthful pending originals; never alter Canon or historical receipts."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os, types, sys

R = Path(r'D:\作品集\ResearchOS\research-os')
N = Path(__file__).resolve().parent
B = R / 'execution/v2.4/receipts/W05/W05-99'
W = R / 'execution/v2.4/receipts/W09/W09-99'
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT = Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree = ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
functions = ast.Module(body=[v for v in tree.body if isinstance(v, ast.FunctionDef) and v.name in ('pin','exact','save','outputs','capture')], type_ignores=[])
exec(compile(functions, 'prior_root_helpers_only', 'exec'), globals())

canonical = [exact(R/'execution/v2.4'/name, sha, size) for name, sha, size in (
    ('checkpoint.json','667f1515a5b62e2d7ee4948bf17055b7f9a0cce6391ad66c76ea70dde99255ba',4533514),
    ('path_ownership.json','4e294919209b1d65b5f869f613ada3a706a16ccaa8fb194dfca1d8982ddb7d3a',211140),
    ('step_state.json','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),
    ('commands.json','28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968))]
identity = exact(R/'execution/project_identity.json','03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec',420)
cp = json.loads(Path(canonical[0]['path']).read_bytes())
assert cp['revision']==371 and len(cp['failure_counters'])==1021 and cp['work_in_progress']['root_next_failure_ordinal_live']==1024

rows=[]
def row(ordinal, path, description, outer, python=None, binding=None, native=None, completeness='ACTUAL_HOST_ORIGINAL_PAIR'):
    rows.append(dict(ordinal=ordinal,origin_ref=pin(path),origin_selector='$',description=description,
        capture_completeness=completeness,capture_binding_ref=pin(binding) if binding else None,
        actual_outer_exit=outer,actual_python_exit=python,actual_native_exit=native,
        actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))

qr=W/'w09_profile_registry_compat_independent_source_review_codex/review-20261009-01'
row(1024,qr/'original-failure-1024.full-tool-pair.json','Independent Source control incorrectly required mixed newline bytes in the unchanged Index; Source repair retained the original failure.',1,1,completeness='SOURCE_REENCODED_FULL_ORIGINAL_HOST_PAIR')
assignment=json.loads((N/'public22.v4.original1025.assignment.root.json').read_bytes())
row(1025,Path(assignment['original_capture_ref']['path']),'Actual public22 original: four Native children exited0; verify22 Source oracle rejected required recovery trigger and credential revocation. Original failed case retained.',0,0,Path(assignment['capture_binding_ref']['path']),native=0)
rows[-1]['successful_native_children']=4
rows[-1]['first_failure_assignment_ref']=pin(N/'public22.v4.original1025.assignment.root.json')
nf=W/'full_w09_main_native_producer_source_codex/fullw09-20261009-01'
nd=json.loads((nf/'original-diagnostics.json').read_bytes())
captures={v['chunk_id']:v for v in nd['actual_original_captures']}
for ordinal,chunk,outer,description in (
    (1026,'dd1744',1,'Source author guessed absent retrieval test file. No actual runtime.'),
    (1029,'168169',0,'Source read included absent candidate directory in rg; individual rg exit unknown, later read succeeded.')):
    value=captures[chunk]
    row(ordinal,Path(value['raw_ref']['path']),description,outer,binding=Path(value['binding_ref']['path']))
pa=B/'public22_actual_independent_review_codex/actual-01a1210b'
for ordinal,label,outer,python,description in (
    (1027,'diagnostic-rg',0,None,'Independent actual reviewer guessed wrong registrar filename; rg inner exit unobserved.'),
    (1028,'diagnostic-caller-path',0,None,'Independent actual reviewer guessed absent caller.closed.json; original caller-return retained.'),
    (1030,'diagnostic-review-recursion',1,1,'Reviewer seal followed an old deleted historical business ref; stopped before guard and any product operation. Historical Canon now treated as byte archive.')):
    row(ordinal,pa/(label+'.actual-host.raw.jsonl'),description,outer,python,pa/(label+'.actual-host.binding.json'))
m2=B/'fresh_main23_root_caller_registration_source_codex/main23root-20261009-02'
for ordinal,chunk,description in (
    (1031,'eb048f','Source revision constructor rejected ambiguous inverse substring before candidate write.'),
    (1032,'2ae9b6','Source revision constructor incorrectly expected AST breadth-first order to equal source order; no candidate write.'),
    (1037,'e8d701','Source hostpair extractor incorrectly unpacked an already unwrapped actual-host value.'),
    (1038,'d93af2','Source hostpair extractor tool-name filter did not match observed bare exec name.')):
    row(ordinal,m2/('original-'+chunk+'.full-tool-pair.json'),description,1,1,completeness='SOURCE_REENCODED_FULL_ORIGINAL_HOST_PAIR')
l3=B/'genuine_schema22_public_upgrade_runner_source_codex/s22public-20261009-01-v3'
for ordinal,callordinal in zip(range(1033,1037),(6794,6801,6815,6829)):
    rawpath=l3/('v3-review-failure-actual-call-'+str(callordinal)+'.jsonl')
    binding=l3/('v3-review-failure-actual-call-'+str(callordinal)+'.binding.json')
    bd=json.loads(binding.read_bytes());assert bd['actual_exit_code']==1
    raw=rawpath.read_bytes()
    parser_error=b'ParserError' in raw
    row(ordinal,rawpath,'Leaf v3 diagnostic extraction or parser failure; all original controls/results retained; no product child.',1,None if parser_error else 1,binding)
    rows[-1]['source_call_ordinal']=callordinal
for ordinal,chunk,description in (
    (1039,'97b161','Root guessed a markdown leaf contract filename before the actual directory listing; correct contract.json subsequently read.'),
    (1040,'d6db89','Root read included absent execution/AGENTS.md with SilentlyContinue; canonical project AGENTS.md successfully read.')):
    def match(call,result,chunk=chunk):return any(v.get('chunk_id')==chunk for v in outputs(result['payload'].get('output')))
    captured=capture(AUDIT,ordinal,match,root=True);assert captured
    row(ordinal,Path(captured[0]['path']),description,0,binding=Path(captured[1]['path']))
    rows[-1]['console_output_complete']=ordinal!=1040
rows.sort(key=lambda v:v['ordinal'])
assert [v['ordinal'] for v in rows]==list(range(1024,1041))
assert len({v['ordinal'] for v in rows})==len(rows)
for v in rows:
    assert pin(Path(v['origin_ref']['path']))==v['origin_ref']
    if v['capture_binding_ref']:assert pin(Path(v['capture_binding_ref']['path']))==v['capture_binding_ref']
pendingref=save('pending-diagnostics.cp371.live1041.root.json',dict(schema='researchos.root-diagnostic-pending.v2',
    issued_by='codex:/root',source_cutoff=dict(highest_ordinal=1023,next_failure_ordinal=1024),
    next_original_failure_ordinal=1041,pending=rows,automatic_retry=False,counter_reset=False,Canon_written=False))
prior=json.loads((N/'RESUME.cp371-public22-stopped.live1026.root.json').read_bytes())
prior.update(created_utc=datetime.now(timezone.utc).isoformat(),
    prior_resume_ref=pin(N/'RESUME.cp371-public22-stopped.live1026.root.json'),
    canonical_refs=canonical,project_identity_ref=identity,next_original_failure_ordinal_live=1041,
    pending_diagnostics_ref=pendingref,pending_diagnostic_originals=list(range(1024,1041)),
    public22_actual_independent_hdf_ref=pin(pa/'HDF.resolved.json'),
    public22_actual_independent_mf_ref=pin(pa/'MF.resolved.json'),
    public22_actual_independent_decision_ref=pin(pa/'decision.resolved.json'),
    public22_leaf_v3_hdf_ref=pin(l3/'HDF.json'),public22_leaf_v3_mf_ref=pin(l3/'MF.json'),
    full_w09_native_source_hdf_ref=pin(nf/'HDF.json'),full_w09_native_source_mf_ref=pin(nf/'MF.json'),
    W05_public22_root_caller_status='ACTUAL_REGISTRATION_QUALIFIED_ORIGINAL1025_FAILED_ORACLE_RETAINED_LEAF_V3_UNDER_INDEPENDENT_SOURCE_REVIEW',
    W05_current_Main23_root_caller_status='V2_SOURCE_REPAIR_FINALIZING_PENDING_INDEPENDENT_REVIEW',
    W09_full_native_source_status='SOURCE_SEALED_69_CONTROLS_PENDING_NONAUTHOR_REVIEW_NO_ACTUAL_RUN',
    next_ready='Root-reviewed fresh Source integration; no old Native children rerun; preserve original1025 and all original diagnostics',
    whole_goal_status='ACTIVE',current_formal_accepted=0,formal_acceptance=False,parent_acceptance=False,Canon_written=False)
resumeref=save('RESUME.cp371-source-sealed.live1041.root.json',prior)
assert [pin(Path(v['path'])) for v in canonical]==canonical
print(json.dumps(dict(resume_ref=resumeref,pending_ref=pendingref,original_ordinals=[v['ordinal'] for v in rows],
    next_original=1041,checkpoint_revision=371,ownership_revision=175,canonical_unchanged=True,
    current_formal_accepted=0,whole_goal_status='ACTIVE'),ensure_ascii=False),flush=True)
