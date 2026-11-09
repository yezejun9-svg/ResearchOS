"""Seal the retained API originals using the exact published closed-receipt interface."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)
    and x.name in {'pin','exact','save','outputs','capture'}],type_ignores=[]),'Root_capture_functions_only','exec'),globals())
chunks=['7d4120','b59d51','88aab2','7e84a6','4af931','1359a8','2712c4','4011e4','5bd8be','461ccb']
pairs=[]
for number,chunk in enumerate(chunks,106017):
    binding_ref=pin(N/('original%d.actual-host.binding.root.json'%number))
    binding=json.loads(Path(binding_ref['path']).read_bytes());raw_ref=binding['original_capture_ref']
    raw=exact(Path(raw_ref['path']),raw_ref['sha256'],raw_ref['bytes'])
    lines=Path(raw_ref['path']).read_bytes().splitlines(keepends=True)
    assert len(lines)==3 and chunk in str(json.loads(lines[2])['payload']['output'])
    with AUDIT.open('rb') as f:
        for off,line,sha in zip(binding['source_line_offsets'],lines,binding['original_line_sha256']):
            f.seek(off);assert f.read(len(line))==line and hashlib.sha256(line).hexdigest()==sha
    pairs.append(dict(actual_chunk_id=chunk,raw_ref=raw_ref,binding_ref=binding_ref))
def failed(call,result):
    return any(x.get('chunk_id')=='5f6292' for x in outputs(result['payload'].get('output')))
raw,binding=capture(AUDIT,1067,failed,root=True)
standard=save('original1067.standard-binding.actual-main23.root.json',dict(
    schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',
    original_capture_ref=raw,original_source_binding_ref=binding,original_source_binding_selector='$',
    original_ordinal=1067,original_bytes_unchanged=True,formal_authority=False))
pending=save('pending-diagnostics.cp373.live1068.root.json',dict(
    schema='researchos.root-pending-diagnostics.v1',issued_by='codex:/root',counter_reset=False,
    source_cutoff_original_failure_ordinal=1066,next_original_failure_ordinal=1068,
    registered_in_current_canon=False,pending=[dict(
        ordinal=1067,origin_ref=raw,origin_selector='$',capture_binding_ref=standard,
        description='Root Main23 API sealing helper treated closed_receipt wrapper as a three-key ref; actual published Source uses closed_receipt.ref. Ten original API pairs retained; product build completed successfully with all five Go exits0.',
        capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=1,actual_python_exit=1,
        actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)]))
observed_ref=exact(N/'main23.v4.activation-after.current4.actual.root.json','f7cb3bd5a29eefb9eafb0e253caa705d5f0de173cf7b080c1df7e3496aecba23',3716)
observation=json.loads(Path(observed_ref['path']).read_bytes())
for ref in observation['current_canonical_refs']:
    exact(Path(ref['path']),ref['sha256'],ref['bytes'])
file_ref=exact(N/'main23.v4.actual-return-file-observation.root.json','613407ce3abc8ea74c634098a64c9977e1647e1ceaca9d93de78abfb2adae5b3',12791)
file_observation=json.loads(Path(file_ref['path']).read_bytes())
receipt=B/'integration_codex/fresh-main23-caller-3ef8ee61a94e4adca86a00f55a8b7a13'
state=json.loads((receipt/'builder-returned-state.root.json').read_bytes())
assert state['closed_receipt']['status']=='PUBLISHED'
closed_ref=state['closed_receipt']['ref']
exact(Path(closed_ref['path']),closed_ref['sha256'],closed_ref['bytes'])
seal=save('main23.v4.actual.complete-hostpair-seal-v2.root.json',dict(
    schema='researchos.root-main23-actual-hostpair-seal.v1',issued_by='codex:/root',root_thread_id=THREAD,
    created_utc=datetime.now(timezone.utc).isoformat(),actual_toolpairs=pairs,
    actual_start_chunk_id='2712c4',actual_session_id=39534,actual_completion_chunk_id='5bd8be',
    actual_outer_exit=0,actual_python_exit=0,actual_Go_exit_codes=[0]*5,
    returned_file_observation_ref=file_ref,full_persisted_return_refs=file_observation['full_persisted_return_refs'],
    build_closed_ref=closed_ref,current_canonical_observation_ref=observed_ref,
    complete_original_API_rows_retained=True,original_API_process_stdout_truncated=True,
    omitted_process_stdout_bytes_as_reported=8164529,original_process_stdout_complete_not_asserted=True,
    original_process_stdout_not_reconstructed=True,Go_raw_stdout_and_stderr_refs=file_observation['calls'],
    original_failure_ordinal_next=1068,pending_ref=pending,programme_qualification=None,
    formal_acceptance=False,parent_acceptance=False))
print(json.dumps(dict(seal_ref=seal,build_closed_ref=closed_ref,pending_ref=pending,actual_pairs=len(pairs),
    complete_API_rows_preserved=True,original_process_stdout_truncation_retained=True,
    programme_qualification=None),ensure_ascii=False,indent=2))
