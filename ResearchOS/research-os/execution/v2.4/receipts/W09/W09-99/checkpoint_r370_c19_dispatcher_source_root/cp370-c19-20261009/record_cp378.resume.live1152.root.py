"""Persist current Root continuation without changing any canonical ledger."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os

R = Path('D:/作品集/ResearchOS/research-os')
V = R / 'execution/v2.4'
W = V / 'receipts/W09/W09-99'
B = V / 'receipts/W05/W05-99'
N = Path(__file__).resolve().parent
NF = W / 'full_w09_main_native_producer_source_codex/fullw09-20261010-05'
REG = W / 'w09_nf5_root_registration_root/967152d41cce4a879070dd73ad4ef49c'

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def save(name, value, raw=False):
    data = value if raw else (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    with (N / name).open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return pin(N / name)

current = [pin(V / (name + '.json')) for name in ('checkpoint', 'path_ownership', 'step_state', 'commands')]
assert [(ref['sha256'], ref['bytes']) for ref in current] == [
    ('1c938f55160baffee20d8bc00369346b3e332a72df0eb2dddcbf52540c4c75d0', 4843407),
    ('03c8e2ab4c003e89c521e6625d34312d891f379d4ee7765c3601b645fb0d102e', 244498),
    ('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149', 257446),
    ('12141a8ba01d34c7181ee35e054f4762732ca8627cbee87271610e65d6f28b97', 67323),
]
cp = json.loads(Path(current[0]['path']).read_bytes())
assert cp['revision'] == 378 and cp['work_in_progress']['root_next_failure_ordinal_live'] == 1149
run_ids = {
    'W09-G01': '3a37a137bede4d759d30cbf6cf9ca10d',
    'W09-G02': 'a0b1cf0a3e0e4048921077d6408e2f4c',
    'A06': '5eb3b491ef5f49ef9ae589c9f5ee712c',
    'C19': 'ed65b2f6b53447c1ad208a32e48a131b',
}
native = {}
for selector, run_id in run_ids.items():
    leaf = NF / ('actual-' + selector + '-' + run_id)
    native[selector] = dict(run_id=run_id, prepare_ref=pin(leaf / 'prepare.ready.json'),
                            native_request_ref=pin(REG / ('native.request.' + selector + '.json')),
                            prepare_actual_outer_exit=0, prepare_actual_python_exit=0)
native['W09-G02'].update(status='ACTUAL_NATIVE_CLOSED_PENDING_INDEPENDENT_REVIEW',
                        root_final_host_chunk='d7e6ce', root_actual_outer_exit=0,
                        root_actual_python_exit=0, all_guards_closed=True, all_owned_jobs_closed=True,
                        validation_closed_ref=pin(NF / ('actual-W09-G02-' + run_ids['W09-G02']) / 'producer/validation.closed.json'))
native['W09-G01'].update(status='ACTUAL_NATIVE_RUNNING_ONCE', root_initial_host_chunk='bb53aa',
                        active_exec_session_id=78839)
for selector in ('A06', 'C19'):
    native[selector].update(status='PREPARED_NOT_RUN', native_execution_started=False)
review = B / 'schema21_public_root_caller_independent_review_codex/review-public21-caller-20261010-02'
pending = {}
for ordinal in (1149, 1150, 1151):
    binding = review / ('original-' + str(ordinal) + '.binding.json')
    pending[str(ordinal)] = dict(status='ACTUAL_SOURCE_REVIEW_FAILURE_PENDING_CONTIGUOUS_REGISTRATION',
                                actual_outer_exit=1, actual_python_exit=1,
                                Native_exit=None, Go_exit=None, SQL_exit=None,
                                binding_ref=pin(binding) if binding.is_file() else None)
resume = dict(schema='researchos.root-continuation.v2', issued_by='codex:/root',
    root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98', created_utc=datetime.now(timezone.utc).isoformat(),
    prior_resume_ref=pin(N / 'RESUME.cp377-current-source-required.live1147.root.json'),
    canonical_refs=current, canonical_checkpoint_revision=378, canonical_ownership_revision=182,
    expected_revisions=dict(checkpoint=378,path_ownership=182,step_state=None,commands=40),
    registered_through_original_ordinal=1148, next_registered_original_ordinal=1149,
    next_original_failure_ordinal=1152, pending_original_ordinals=[1149,1150,1151],
    pending_diagnostics=pending, Goal_status='ACTIVE', active_parent_tasks=['W05','W09'],
    parent_tasks_required=22, formal_cases_required=42, formal_cases_currently_accepted=0,
    W09_current=dict(generation='fullw09-20261010-05', native_selectors=native,
        registration_activation_ref=pin(REG / 'activate.completed.json'),
        producer_independent_source_review_ref=pin(W / 'full_w09_nf5_independent_source_review_codex/review-nf5-20261010-01/producer/decision.json'),
        bridge03_independent_review_ref=pin(W / 'w09_formal_root_bridge_independent_review_codex/review-bridge-20261010-03/decision.json'),
        formal_consumers_current_CM40_run=0, formal_scope_created=False,
        actual_report_independent_review='BACKUP_REVIEWER_PREPARING_NO_QUALIFICATION_YET'),
    W05_public21_current=dict(
        source_caller02_hdf_ref=pin(B / 'schema21_public_root_caller_source_codex/s21public-caller-20261010-02/HDF.json'),
        source_caller02_actual_author_ref=pin(N / 'w09.public21-caller02-author.actual-audit.root.json'),
        source_review_status='TASK106_LAST_SOURCE_DELIVERY_PATH_COMPARISON_AND_SEAL_IN_PROGRESS',
        original1146_preserved=True, runtime_qualification_scope_created=False,
        runtime_manifest_created=False, public_bootstrap_started=False),
    no_failure_counter_reset=True, no_historical_receipt_replay=True,
    next_actions=[
        'Poll G01 session78839; do not repeat its one-shot run. Run prepared A06 and C19 once in sequence.',
        'Seal actual Root prepare/run call-return pairs and obtain independent current four-packet review.',
        'Keep CP378/OW182 byte stable while the four Native scopes consume this canonical vector.',
        'Finish Source Caller02 review, then issue actual public runtime resource qualification without reusing Caller01.',
        'Run six current CM40 formal consumers only after current Native qualification and a fresh formal Scope.',
        'Register pending original1149..1151 contiguously once; require true formal review and Main verify_owner/derive.',
    ])
ref = save('RESUME.cp378-nf5-native-running.live1152.root.json', resume)
handoff = V / 'HANDOFF_RESUME_PACK.md'
old = handoff.read_bytes()
save('historical.HANDOFF.before-cp378.live1152.root.md', old, True)
prefix = ('# Current Root continuation: CP378 / OW182 / CM40 / live next1152\n\n'
    'Registered through1148; original1149..1151 preserved pending contiguous merge. Formal0/42; Goal ACTIVE. '
    'NF5 all four preparations closed0. G02 actual GoList and GoTest closed0; pending independent report/mode review. '
    'G01 running once in exec session78839; A06/C19 prepared and not yet run. Keep Canon byte stable until all four Native scopes close. '
    'Bridge03 Source independently accepted; no current six formal consumers or formal Scope. '
    'Public21 Caller02 directory repair Source under final independent review; no resource Scope or bootstrap process.\n\n'
    'Current resume: ' + ref['path'] + '\nSHA256 ' + ref['sha256'] + ' bytes ' + str(ref['bytes']) + '\n\n').encode()
with handoff.open('wb') as stream:
    stream.write(prefix + old)
    stream.flush()
    os.fsync(stream.fileno())
assert handoff.read_bytes() == prefix + old
assert [pin(item['path']) for item in current] == current
print(json.dumps(dict(resume_ref=ref, canonical_unchanged=True, live_next=1152, formal_acceptance=False), ensure_ascii=False))
