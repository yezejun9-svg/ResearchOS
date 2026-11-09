"""Verify actual immutable diagnostic pairs and issue the complete Root suffix."""
from pathlib import Path
import hashlib, json, os, re, types

R=Path('D:/作品集/ResearchOS/research-os'); V=R/'execution/v2.4'
W=V/'receipts/W09/W09-99'; B=V/'receipts/W05/W05-99'; N=Path(__file__).resolve().parent
P=B/'schema21_public_bootstrap_actual_independent_review_codex/source-diagnostic-supplement-20261010-01'
Q=W/'full_w09_nf5_actual_independent_review_codex/review-actual-nf5-20261010-01'
C=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-01'
A=W/'c19_order_Main_actual_independent_review_codex/review-20261010-01'
Z=B/'public22_to_main23_continuation_independent_review_codex/review-20261010-01'
REG=W/'w09_nf6_root_registration_source_codex/register-20261010-01'
ROOT='codex:/root'; START=1162; STOP=1183

def pin(p):
    p=Path(p); raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def checked(ref):
    assert type(ref) is dict and set(ref)=={'path','sha256','bytes'}
    assert pin(ref['path'])['sha256']==ref['sha256'] and pin(ref['path'])['bytes']==ref['bytes']
    return Path(ref['path']).read_bytes()

def doc(ref): return json.loads(checked(ref))

def save(name,value):
    p=N/name; raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with p.open('xb') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return pin(p)

def docs(value):
    if isinstance(value,dict):
        yield value
        for child in value.values(): yield from docs(child)
    elif isinstance(value,list):
        for child in value: yield from docs(child)
    elif isinstance(value,str):
        try: yield from docs(json.loads(value))
        except ValueError: pass

cases=[
 (1162,P/'original-1162.binding.json','2f488e',1,None,'Wrong public scope field name, rejected before SQL.'),
 (1163,P/'original-1163.binding.json','6c7d13',1,None,'Read of absent frozen Source path.'),
 (1164,Q/'original1164.binding.json','0a87ee',1,None,'Read-only rg regular expression quoting failure.'),
 (1165,P/'original-1165.binding.json','7034b1',1,1,'Historic CP379 ref checked against CP380 before SQL; corrected using archived refs.'),
 (1166,Q/'original1166.binding.json','d977ff',1,1,'SourceReadGuard rejected relative ref path before selector checks.'),
 (1167,P/'original-1167.binding.json','dd37ba',1,1,'Source ref slash spelling equality failed after successful SQL checks; successful prefix preserved.'),
 (1168,Q/'original1168.binding.json','784193',1,1,'Exact-single-host assumption rejected actual batched prepare audit.'),
 (1169,N/'original1169.actual-root.binding.json','7a5aef',0,None,'Suppressed missing-path read; following rg returned outer0.'),
 (1170,C/'original1170.binding.json','5b772b',0,None,'Wrong W05 caller search path; rg child2 followed by successful read outer0.'),
 (1171,C/'original1171.binding.json','5ce81a',1,None,'Read-only caller lookup used W09 instead of W05 prefix.'),
 (1172,Q/'original1172.corrected.binding.json','993be3',1,1,'Batched prepare host check refused; Guard3564 closed0 and successful prefix retained.'),
 (1173,Q/'original1173.binding.json','138dad',0,0,'Sealer emitted original ordinal1168 for actual1172; separately corrected without changing original bytes.'),
 (1174,C/'original1174.binding.json','f5366b',1,1,'Pure Source control used WindowsPath plus string before any Native call.'),
 (1175,C/'original1175.binding.json','9b1011',1,1,'Pure Source control used the wrong DB flag argument index.'),
 (1176,A/'original-6aeb06.binding.json','6aeb06',1,None,'Read-only command used project parent rather than repository root.'),
 (1177,A/'original-b80816.binding.json','b80816',1,None,'Second read-only command retained the wrong project root.'),
 (1178,A/'original-39fb10.binding.json','39fb10',0,None,'Nonterminating missing request.json read followed by successful read outer0.'),
 (1179,A/'original-24ae31.binding.json','24ae31',1,None,'Source review read HANDOFF.json rather than published HDF.json.'),
 (1180,A/'original-policy-cleanup.binding.json',None,None,None,'Automatic approval review rejected empty-directory cleanup before process creation; no retry or bypass.'),
 (1181,Z/'actual-9e5fbb.binding.json','9e5fbb',1,1,'Reviewer sealer over-required a direct caller ref in the actual author FINAL; actual contract and transitive HDF binding preserved.'),
 (1182,N/'original1182.actual-root.binding.json','de90b9',1,None,'Root read-only lookup used absent registration-contract.json; true filename located by independent inventory.'),
]
assert [x[0] for x in cases]==list(range(START,STOP))
raw=checked(dict(path=str(REG/'adoption_core.source.py'),sha256='2c99ef66d3ee2c25302858fef715ad46096c750bd5ebff58faa95f0cdd4ead4f',bytes=16396))
core=types.ModuleType('root_nf6_pending_pure_core'); exec(compile(raw,str(REG/'adoption_core.source.py'),'exec'),core.__dict__)
current=[pin(V/(name+'.json')) for name in ('checkpoint','path_ownership','step_state','commands')]
cp=doc(current[0]); assert cp['revision']==382 and cp['work_in_progress']['root_next_failure_ordinal_live']==START
rows=[]; verification=[]
for ordinal,path,chunk,outer,py,description in cases:
    source_ref=pin(path); binding=doc(source_ref); origin=binding['original_capture_ref']; original=checked(origin)
    lines=original.splitlines(keepends=True); assert len(lines)==3 and all(line.endswith(b'\n') for line in lines)
    assert [hashlib.sha256(line).hexdigest() for line in lines]==binding['original_line_sha256']
    if 'source_line_bytes' in binding: assert [len(line) for line in lines]==binding['source_line_bytes']
    offsets=binding['source_line_offsets']; assert len(offsets)==3 and offsets[0]==0 and offsets[1]<offsets[2]
    with Path(binding['source_audit_path']).open('rb') as source:
        for offset,line in zip(offsets,lines): source.seek(offset); assert source.readline()==line
    events=[json.loads(line) for line in lines]; call=events[1]['payload']; result=events[2]['payload']
    assert events[0]['type']=='session_meta'
    assert call['type'] in ('function_call','custom_tool_call') and result['type'] in ('function_call_output','custom_tool_call_output')
    assert call['call_id']==result['call_id']
    if chunk is None:
        assert 'blocked by policy' in str(result.get('output'))
        assert binding['tool_rejected_before_process'] is True and binding['actual_outer_exit'] is None
    else:
        hosts=[host for host in docs(result.get('output')) if host.get('chunk_id')==chunk]
        assert len(hosts)==1 and hosts[0]['exit_code']==outer
        markers=re.findall(r'ROOT(?:_ACTUAL|_SOURCE)?_PYTHON_EXIT=(-?\d+)',hosts[0].get('output',''))
        assert (int(markers[-1]) if markers else None)==py
    witnessed=save('pending-original.'+str(ordinal)+'.Root-binding.live'+str(STOP)+'.json',dict(
        schema='researchos.root-original-diagnostic-binding.v1',issued_by=ROOT,
        original_capture_ref=origin,original_source_binding_ref=source_ref,original_source_binding_selector='$',
        original_ordinal=ordinal,original_bytes_unchanged=True,formal_authority=False,
        actual_pair_and_source_offsets_verified=True,actual_host_chunk_id=chunk,
        original_source_thread_id=events[0]['payload']['id']))
    exits={key:None for key in core.EXIT_FIELDS}; exits['actual_outer_exit']=outer; exits['actual_python_exit']=py
    rows.append(dict(ordinal=ordinal,origin_ref=origin,origin_selector='call_id:'+call['call_id'],
        description=description,capture_binding_ref=witnessed,
        capture_completeness='ACTUAL_ORIGINAL_HEADER_CALL_RESULT_3LF_AND_LIVE_SOURCE_OFFSETS',**exits))
    verification.append(dict(ordinal=ordinal,source_binding_ref=source_ref,Root_binding_ref=witnessed,
        original_capture_ref=origin,actual_outer_exit=outer,actual_python_exit=py,source_offsets_reobserved=True))
pending=dict(schema='researchos.root-pending-diagnostics.v1',issued_by=ROOT,counter_reset=False,
    registered_in_current_canon=False,current_canonical_refs=current,source_cutoff_original_failure_ordinal=START-1,
    next_original_failure_ordinal=STOP,pending=rows)
merged,stop=core.merge_pending(cp,pending,current)
assert stop==STOP and merged[:len(cp['failure_counters'])]==cp['failure_counters']
assert [pin(ref['path']) for ref in current]==current
verification_ref=save('pending-diagnostics.cp382.live1183.verification.root.json',dict(
    schema='researchos.root-original-suffix-verification.v1',issued_by=ROOT,rows=verification,
    complete_contiguous_suffix=True,original_bytes_unchanged=True,counter_reset=False,Canon_written=False))
pending['original_suffix_verification_ref']=verification_ref
ref=save('pending-diagnostics.cp382.live1183.root.json',pending)
print(json.dumps(dict(pending_ref=ref,verification_ref=verification_ref,first=START,last=STOP-1,
    next_original_failure_ordinal=STOP,canonical_unchanged=True,registered=False,formal_acceptance=False),ensure_ascii=False))
