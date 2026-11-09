"""Freeze the actual diagnostic suffix, without touching canonical state."""
from pathlib import Path
import hashlib, json, os
S=Path(__file__).resolve().parent;V=S.parents[4];W=S.parents[1];B=V/'receipts/W05/W05-99'
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
fixed={n:S/f'original{n}.fixed-actual.binding.root.json' for n in (1225,1226,1230)}
fixed.update({n:B/f'public23_to24_handoff_source_codex/handoff-20261010-01/diagnostic-appendix/original-{n}.binding.json' for n in (1227,1228)})
fixed[1229]=W/'w09_formal_root_bridge_source_codex/bridge-20261010-08/original-1229.binding.json'
descriptions={1225:'Read-only diagnosis reporter required two legal slash spellings to be raw-string equal; all 12 ranges and successful guard prefix retained.',1226:'Root read-only task selector placed global --plan after the subcommand; corrected selection passed without product calls.',1227:'Read-only inventory queried nonexistent cmd path after successful Git prefix; no product calls.',1228:'Read-only rg searched apps and returned no match; successful file-read prefix retained; public entry discovered in ops/backup.',1229:'Read-only query used W09 for an existing W05 Guard file after successful Main and diagnosis reads; no guard acquired.',1230:'Root read-only Get-Content guessed config.root.json instead of published configuration.root.json; last rg kept actual outer0; no product calls.'}
chunks={1225:'8d968a',1226:'400353',1227:'a27c9f',1228:'81ce7e',1229:'f5ac7c',1230:'ee077d'}
outer={1225:1,1226:2,1227:1,1228:1,1229:1,1230:0};py={1225:1,1226:2,1227:None,1228:None,1229:None,1230:None}
current=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert current[0]['sha256']=='39b39df749a254c0d7fec9d3681c9cbf8823020777b707703e16f6ffe53c2914'
rows=[]
for n,p in sorted(fixed.items()):
    br=pin(p);d=json.loads(p.read_bytes());rr=d.get('original_capture_ref',d.get('original_raw_ref'));assert pin(Path(rr['path']))==rr
    lines=Path(rr['path']).read_bytes().splitlines(keepends=True);assert len(lines)==3 and all(x.endswith(b'\n') for x in lines)
    digests=d.get('original_line_sha256',d.get('source_line_sha256'));assert [hashlib.sha256(x).hexdigest() for x in lines]==digests
    with Path(d['source_audit_path']).open('rb') as f:
        for off,line in zip(d['source_line_offsets'],lines):f.seek(off);assert f.readline()==line
    events=[json.loads(x) for x in lines];assert events[1]['payload']['call_id']==events[2]['payload']['call_id']
    assert d.get('actual_outer_exit',d.get('outer_exit'))==outer[n] and d.get('actual_python_exit',d.get('Python_exit'))==py[n]
    assert chunks[n] in lines[2].decode('utf-8')
    rows.append(dict(ordinal=n,origin_ref=rr,origin_selector='actual_host_chunk_id='+chunks[n],capture_binding_ref=br,description=descriptions[n],capture_completeness='ACTUAL_ORIGINAL_HEADER_CALL_RESULT_3LF_WITH_EXACT_SOURCE_OFFSETS',source_fact_refs=[br,rr],actual_outer_exit=outer[n],actual_python_exit=py[n],actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
d=dict(schema='researchos.root-pending-diagnostics.v1',issued_by='codex:/root',counter_reset=False,registered_in_current_canon=False,current_canonical_refs=current,source_cutoff_original_failure_ordinal=1224,next_original_failure_ordinal=1231,pending=rows)
p=S/'cp391-pending-diagnostics1225-1230.root.json';raw=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
assert current==[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
print(json.dumps(dict(pending_ref=pin(p),Canon_written=False,counter_reset=False,formal_acceptance=False),ensure_ascii=False))
