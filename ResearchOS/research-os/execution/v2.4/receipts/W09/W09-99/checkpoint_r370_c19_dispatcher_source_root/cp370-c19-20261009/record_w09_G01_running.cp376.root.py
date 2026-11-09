"""Persist the actual in-flight one-shot selector without asserting completion."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
N=Path(__file__).resolve().parent;R=Path(r'D:\作品集\ResearchOS\research-os')
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,d):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
prior_ref=pin(N/'RESUME.cp376-w09-native-registered.live1117.root.json');prior=json.loads(Path(prior_ref['path']).read_bytes())
current=prior['canonical_refs'];assert all(pin(Path(x['path']))==x for x in current)
resume=save('RESUME.cp376-w09-G01-running.live1117.root.json',dict(prior,
    created_utc=datetime.now(timezone.utc).isoformat(),prior_resume_ref=prior_ref,
    W09='G01_PREPARE_COMPLETED_ALL_GUARDS_CLOSED_ACTUAL_RUN_STARTED_FINAL_EXIT_PENDING_G02_A06_NOT_STARTED',
    native_processes=dict(G01=dict(prepare_initial_chunk='cfcbd5',prepare_session_id=62390,prepare_final_chunk='7f9ae8',
        actual_prepare_outer_exit=0,actual_prepare_python_exit=0,actual_run_initial_chunk='c18f37',actual_run_session_id=84073,
        actual_run_outer_exit=None,actual_run_python_exit=None,actual_Go_test_exit=None,one_shot_run_started=True,
        automatic_retry=False),G02=dict(started=False),A06=dict(started=False)),
    next_actions=['Resume existing session84073 to its real final exit; do not start a second G01 run.',
                  'Read durable raw Go/list/test streams and closure proof after completion.',
                  'Prepare/run G02 then A06 once under their existing scopes, without Canon mutation.']))
handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=handoff.read_bytes()
with (N/'historical.HANDOFF.before-G01-running.cp376.root.md').open('xb') as f:f.write(old);f.flush();os.fsync(f.fileno())
prefix=('# Current Root continuation: CP376 / OW180 / CM40 / live next1117\n\n'
    'G01 prepare completed outer/Python0 with all guards and jobs closed. Its one-shot actual run is in flight in existing session84073, final exit unknown; do not start another G01 run. G02/A06 not started. Goal ACTIVE; formal0/42.\n\n'
    'Current resume: '+resume['path']+'\nSHA256 '+resume['sha256']+' bytes '+str(resume['bytes'])+'\n\n').encode()
with handoff.open('wb') as f:f.write(prefix+old);f.flush();os.fsync(f.fileno())
assert all(pin(Path(x['path']))==x for x in current) and handoff.read_bytes().endswith(old)
print(json.dumps(dict(resume_ref=resume,actual_running_session=84073,actual_exit=None,Canon_unchanged=True,formal_acceptance=False),ensure_ascii=False,indent=2))
