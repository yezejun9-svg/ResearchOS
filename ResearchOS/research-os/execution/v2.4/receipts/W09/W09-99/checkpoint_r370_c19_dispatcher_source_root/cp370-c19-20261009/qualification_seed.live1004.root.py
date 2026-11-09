"""Root actual seed observation after independent registrar definition review."""
from datetime import datetime, timezone
from pathlib import Path
import copy, hashlib, json, os

N = Path(__file__).resolve().parent
W = N.parent.parent
S = W/'checkpoint_r369_native_source_root/cp369-c19-20261009'
RV = W/'cp370_registrar_v3_independent_review_codex/regr3-01a120ab'
V3 = W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v3'
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
EXITS = ('actual_outer_exit', 'actual_python_exit', 'actual_native_exit', 'actual_dispatcher_exit', 'actual_model_exit')

def pin(path):
    path = path.resolve(strict=True); raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def read(ref):
    assert set(ref) == {'path', 'sha256', 'bytes'} and pin(Path(ref['path'])) == ref
    return Path(ref['path']).read_bytes()

def exact(path, sha, size):
    ref = dict(path=str(path.resolve(strict=True)), sha256=sha, bytes=size); read(ref); return ref

def save(path, value):
    with path.open('xb') as file:
        file.write((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode()); file.flush(); os.fsync(file.fileno())
    return pin(path)

reviews = [exact(RV/name, sha, size) for name, sha, size in (
    ('HDF.json', '7744cbc0da801ccde4b4fb4c0e48b1f7df8b6e32844b6f17e4489b4aeef15d42', 2327),
    ('MF.json', '9b4a1f967c39c891c51eb40a1c3e9868157ddd3090d8a6bca8df50fb4de1b253', 2485),
    ('source-decision.json', '5550766b0cc7a9a05530ba604ce28aef4181a474f70ee2b6db0bacd58cbc61ac', 3222))]
rh, rm, decision = [json.loads(read(ref)) for ref in reviews]
assert decision['decision'] == 'ACCEPTED_SOURCE_ONLY' and decision['actor_id'] == 'codex:/root/attach_fixture_source_review'
assert decision['actor_role'] == 'INDEPENDENT_NON_AUTHOR' and decision['actual_registration'] is False
assert decision['formal_acceptance'] is False and decision['parent_acceptance'] is False
assert rh['manifest_ref'] == reviews[1] and rh['source_decision_ref'] == reviews[2] and reviews[2] in rm['members']
assert decision['source_hdf_ref'] == exact(V3/'HDF.json', '246a870b96519fedcafe2840ef23bb778f01631236a205d6b08a4a15f124457a', 3388)
assert decision['source_mf_ref'] == exact(V3/'MF.json', '1c8754af40371f08711d2356def2ba626a04c2b8e9249de3a79386a7f77aaba6', 8749)
resume = json.loads((S/'RESUME.cp369-main-profile-adopted.live1004.root.json').read_bytes())
for ref in [resume['identity_ref'], *resume['canonical_refs']]: read(ref)
pending_ref = exact(S/'pending-diagnostics.live1004.root.json', '29f635f5d59aa8d3e9514f9d81598afefb5c5f65af2b5a613ad1a25dbe6aae90', 31622)
pending = json.loads(read(pending_ref))['pending']
prior_ref = exact(N/'original-diagnostic-qualifications.seed.live996.root.json', '29ccebbd4fa089e2bb579b8cbbfe7253b14d5b2364f1c5f26895e7cbbe91f81d', 55750)
prior = json.loads(read(prior_ref))
assert [row['ordinal'] for row in pending] == list(range(966, 1004))
assert len(prior['rows']) == 30 and prior['before_canonical_refs'] == resume['canonical_refs']
rows = copy.deepcopy(prior['rows'])
for row, source in zip(rows, pending[:30]):
    assert all(row[key] == source[key] for key in ('ordinal', 'origin_ref', 'description'))
    read(row['origin_ref']); row['exit_qualification']['diagnostic_source_ref'] = pending_ref
for source in pending[30:]:
    read(source['origin_ref']); read(source['capture_binding_ref'])
    number = source['ordinal']
    row = {key: source[key] for key in ('ordinal', 'origin_ref', 'origin_selector', 'description', *EXITS)}
    row['capture_completeness'] = source['origin_capture_completeness']
    row['exit_qualification'] = dict(schema='researchos.root-original-exit-qualification.v1', authority='ROOT_OBSERVED_DIAGNOSTIC_ONLY', unknown_is_null=True,
        source_capture_ref=source['origin_ref'], source_capture_selector=source['origin_selector'], diagnostic_source_ref=pending_ref,
        diagnostic_source_selector='pending[ordinal='+str(number)+']')
    assert all(row[key] is None or type(row[key]) is int for key in EXITS)
    rows.append(row)
identities = [(row['origin_ref']['sha256'], row['origin_selector']) for row in rows]
assert len(identities) == len(set(identities)) == 38
now = datetime.now(timezone.utc).isoformat()
qualification = dict(schema='researchos.root-cp370-original-invocation-qualification.v1', issued_by='codex:/root', root_thread_id=THREAD, created_utc=now,
    source_pending_ref=pending_ref, before_canonical_refs=resume['canonical_refs'], source_cutoff={'highest_ordinal':965, 'next_failure_ordinal':966},
    next_original_failure_ordinal=1004, rows=rows, formal_acceptance=False, parent_acceptance=False, counter_reset=False)
qualification_ref = save(N/'original-diagnostic-qualifications.seed.live1004.root.json', qualification)
resume.update(created_utc=now, Root_original_qualification_ref=qualification_ref,
              CP370_status='REGISTRAR_V3_DEFINITION_SOURCE_ACCEPTED_ROOT_SEED_CREATED', current_original_qualification_status='ROOT_ACTUAL_SEED_OBSERVED_NONFORMAL',
              CP370_registrar_v3_independent_hdf_ref=reviews[0], CP370_registrar_v3_independent_mf_ref=reviews[1], CP370_registrar_v3_independent_decision_ref=reviews[2])
for ref in resume['canonical_refs']: read(ref)
resume_ref = save(S/'RESUME.cp369-main-profile-adopted.seed.live1004.root.json', resume)
print(json.dumps(dict(resume_ref=resume_ref, pending_ref=pending_ref, qualification_ref=qualification_ref,
                     next_original=1004, Canonical_unchanged=True, formal_delta=0), ensure_ascii=False), flush=True)
