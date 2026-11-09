"""Preserve current completed/in-flight execution and unregistered diagnostics."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os

N = Path(__file__).resolve().parent
R = Path(r'D:\作品集\ResearchOS\research-os')
W = R / 'execution/v2.4/receipts/W09/W09-99'

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def save(name, value):
    path = N / name
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())
        stream.flush()
        os.fsync(stream.fileno())
    return pin(path)

prior_ref = pin(N / 'RESUME.cp376-w09-G01-running.live1117.root.json')
prior = json.loads(Path(prior_ref['path']).read_bytes())
current = prior['canonical_refs']
assert all(pin(ref['path']) == ref for ref in current)
source = W / 'w09_formal_consumer_readiness_readonly_codex/readiness-20261010-01'
diagnostics = []
for ordinal, raw_hash, raw_size, binding_hash, binding_size in [
    (1117, 'bd788658ed7abdf5f4e2a302947a174529b459661d6ddb12c0ed15db38cf7d0f', 39587,
     '6ba66ceb09bc605f0c95e763544115726092bb0b17df3f1f53c89686510acc80', 1881),
    (1118, '4a685912d46769438815dfe8f37b675065f17f01c11822500abcf4465d2f1529', 32436,
     'c6f88b1d1f5046499d2407ed01275e86b015b9d9754db8724173df9ea4b12294', 7146),
]:
    raw_ref = pin(source / f'original-{ordinal}.raw.jsonl')
    binding_ref = pin(source / f'original-{ordinal}.binding.json')
    assert (raw_ref['sha256'], raw_ref['bytes']) == (raw_hash, raw_size)
    assert (binding_ref['sha256'], binding_ref['bytes']) == (binding_hash, binding_size)
    diagnostics.append(dict(original_ordinal=ordinal, source_actor='codex:/root/full_w09_source_review',
                            original_raw_ref=raw_ref, source_binding_ref=binding_ref,
                            registered_in_Canon=False))
pending_ref = save('pending-diagnostics.cp376.live1119.root.json', dict(
    schema='researchos.root-pending-source-diagnostics.v1',
    created_utc=datetime.now(timezone.utc).isoformat(), canonical_revision=376,
    already_registered_through=1116, next_original_failure_ordinal=1119,
    diagnostics=diagnostics, no_counter_reset=True,
    expected_normal_rg_no_matches_are_not_failure_ordinals=True,
    Canon_mutation_deferred_until_three_Native_runs_closed=True))
g01_root = W / ('full_w09_main_native_producer_source_codex/fullw09-20261010-03/'
                'actual-W09-G01-4fd62ca511684dc39d62c5571d8ddaf5/producer')
closed_ref = pin(g01_root / 'validation.closed.json')
assert (closed_ref['sha256'], closed_ref['bytes']) == (
    '75d948b2d172d4d77d56de2588c16dc00eb33ee9d0f2d753f675e1ca2bbf971d', 1689718)
closed = json.loads(Path(closed_ref['path']).read_bytes())
assert closed['error'] is None and not closed['cleanup_errors']
assert closed['all_guards_closed'] and closed['all_owned_jobs_closed']
assert closed['summary']['native_test_exit'] == 0
assert closed['formal_case_accepted_delta'] == 0
resume_ref = save('RESUME.cp376-w09-G02-running.live1119.root.json', dict(
    prior, created_utc=datetime.now(timezone.utc).isoformat(), prior_resume_ref=prior_ref,
    next_original_failure_ordinal=1119, pending_diagnostics_ref=pending_ref,
    W09='G01_ACTUAL_NATIVE_CLOSED_PENDING_REVIEW_G02_ACTUAL_RUNNING_A06_NOT_STARTED',
    native_processes=dict(
        G01=dict(actual_final_chunk='8d91e4', actual_outer_exit=0, actual_python_exit=0,
                 actual_Go_test_exit=0, validation_closed_ref=closed_ref,
                 summary=closed['summary'],
                 actual_final_capture_ref=pin(N/'w09.G01-native-run-final.actual-audit.root.json'),
                 all_guards_closed=True, all_owned_jobs_closed=True, automatic_retry=False,
                 formal_acceptance=False),
        G02=dict(actual_prepare_initial_chunk='784eee', actual_prepare_session_id=9313,
                 actual_prepare_final_chunk='8a210f', actual_prepare_outer_exit=0,
                 actual_prepare_python_exit=0, actual_run_initial_chunk='175ec0',
                 actual_run_session_id=86213, actual_run_outer_exit=None,
                 actual_run_python_exit=None, actual_Go_test_exit=None,
                 one_shot_run_started=True, automatic_retry=False),
        A06=dict(started=False)),
    next_actions=[
        'Resume existing G02 session86213; do not start another G01/G02 run.',
        'Prepare and run A06 once under its registered finite Native scope.',
        'After all Native jobs close, obtain independent actual review and implement the missing Caller using the existing Main formal engine.',
        'Register diagnostics1117/1118 exactly once after current Native vector no longer needs Canon376.']))
handoff = R / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
old = handoff.read_bytes()
with (N/'historical.HANDOFF.before-G02-running.cp376.live1119.root.md').open('xb') as stream:
    stream.write(old)
    stream.flush()
    os.fsync(stream.fileno())
prefix = ('# Current Root continuation: CP376 / OW180 / CM40 / live next1119\n\n'
          'G01 actual Native returned outer/Python/Go test0 with all guards and jobs closed; independent review pending. G02 actual run is in existing session86213; final exit unknown. A06 not started. Goal ACTIVE; formal0/42. Diagnostics1117/1118 sealed pending; old counters preserved.\n\n'
          'Current resume: '+resume_ref['path']+'\nSHA256 '+resume_ref['sha256']+
          ' bytes '+str(resume_ref['bytes'])+'\n\n').encode()
with handoff.open('wb') as stream:
    stream.write(prefix+old)
    stream.flush()
    os.fsync(stream.fileno())
assert handoff.read_bytes().endswith(old) and all(pin(ref['path']) == ref for ref in current)
print(json.dumps(dict(resume_ref=resume_ref, pending_ref=pending_ref,
                      G02_existing_session=86213, Canon_unchanged=True,
                      formal_acceptance=False), ensure_ascii=False))
