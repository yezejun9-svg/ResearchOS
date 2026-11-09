"""Read existing complete returned observation; no product or SQLite call."""
from pathlib import Path
import hashlib,json
R=Path(r'D:\作品集\ResearchOS\research-os')
B=R/'execution/v2.4/receipts/W05/W05-99/integration_codex'
case=B/'schema22-public-89c0459006654891bf3c540af6b525aa'
caller=B/'schema22-public-caller-89c0459006654891bf3c540af6b525aa'
def pin(path):
    raw=path.read_bytes();return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
record=json.loads((caller/'caller-return.root.json').read_bytes())
state=json.loads((caller/'runner-returned-state.root.json').read_bytes())
calls=[]
for call in state['calls']:
    observed=call.get('observation',{})
    calls.append(dict(phase=call['phase'],actual_exit=call['actual_exit'],
        owned_child_pid=observed.get('owned_child_pid'),
        creation_time_100ns_decimal=str(observed.get('creation_time_100ns')),
        job_cleanup=observed.get('job_cleanup'),stdout_ref=call.get('stdout_ref'),
        stderr_ref=call.get('stderr_ref'),result_ref=call.get('result_ref')))
print(json.dumps(dict(caller_record_ref=pin(caller/'caller-return.root.json'),
    returned_state_ref=pin(caller/'runner-returned-state.root.json'),
    state_keys=list(state),status=state['status'],phase=state['phase'],
    first_failure=state.get('first_failure'),caller_error=record.get('caller_error'),
    calls=calls,closed_receipt=state.get('closed_receipt'),
    guard_cleanup={k:record['source_guard_cleanup'].get(k) for k in ('closed','retained_handles_count','errors')},
    observations={k:v for k,v in state.items() if k not in ('calls','source_guard_cleanup','source_resources') and
                  ('schema' in k or 'table' in k or 'baseline' in k or 'restore' in k or 'retained' in k)},
    existing_case_json_files=[str(p.relative_to(case)) for p in case.rglob('*.json') if 'private' not in p.parts],
    original_ordinal=1025,next_original=1026,formal_acceptance=False),ensure_ascii=False),flush=True)
