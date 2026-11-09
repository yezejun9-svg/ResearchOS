"""Root issues a complete suffix from immutable actual diagnostic inputs."""
from pathlib import Path
import copy, hashlib, json, os, sys, types
R=Path("D:/作品集/ResearchOS/research-os")
V=R/"execution/v2.4";W=V/"receipts/W09/W09-99"
N=Path(__file__).resolve().parent
D=W/"pending_diagnostic_inputs_source_codex/pending1134-1146-20261010-01"
REG=W/"w09_nf4_root_registration_source_codex/register-20261010-02"
corepath=REG/"adoption_core.source.py"
raw=corepath.read_bytes()
assert len(raw)==16407 and hashlib.sha256(raw).hexdigest()=="05cc0bf92d94372ebfcdb19322b2b90fb93aab27e288331413710d1d89d41e1d"
core=types.ModuleType("Root_existing_pending_core")
exec(compile(raw,str(corepath),"exec"),core.__dict__)
def pin(p):
    p=Path(p);b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def checked(ref):
    core.ref_shape(ref)
    assert pin(ref["path"])==ref
    return Path(ref["path"]).read_bytes()
def read(ref): return json.loads(checked(ref))
def save(name,value):
    p=N/name
    with p.open("xb") as f:
        f.write(core.encoded(value));f.flush();os.fsync(f.fileno())
    return pin(p)
draft_ref=pin(D/"pending-diagnostic-inputs.draft.json")
assert draft_ref["sha256"]=="b559e6308d61da66cf833906eaa59956182d515d404615cca0b9c31627014fc1" and draft_ref["bytes"]==39823
draft=read(draft_ref)
assert draft["Root_issued"] is False and draft["Root_counter_authority"] is False
rows=copy.deepcopy(draft["pending"])
assert [r["ordinal"] for r in rows]==list(range(1134,1147))
verification_ref=pin(D/"verification.json")
assert verification_ref["sha256"]=="b10e6cc36ad88bf69efa75cb1ac3dfa6ee732c5c007db1c46b187251336a87d4"
checked(verification_ref)
# The additional actual reviewer diagnostic is supplied after its original seal.
addon_ref=pin(sys.argv[1])
addon=read(addon_ref)
assert addon["issued_by"]=="codex:/root" and addon["schema"]=="researchos.root-pending-diagnostic-additions.v1"
rows+=addon["pending"]
stop=addon["next_original_failure_ordinal"]
assert type(stop) is int and [r["ordinal"] for r in rows]==list(range(1134,stop))
out=[]
for row in rows:
    assert all(k in row and (row[k] is None or type(row[k]) is int) for k in core.EXIT_FIELDS)
    checked(row["origin_ref"])
    checked(row["capture_binding_ref"])
    for ref in row.get("source_fact_refs",[]): checked(ref)
    original_source_binding=row["capture_binding_ref"]
    binding=save("pending-original."+str(row["ordinal"])+".Root-binding.live"+str(stop)+".json",dict(
        schema="researchos.root-original-diagnostic-binding.v1",issued_by="codex:/root",
        original_capture_ref=row["origin_ref"],original_source_binding_ref=original_source_binding,
        original_source_binding_selector=row.get("origin_json_pointer") or "$",
        original_ordinal=row["ordinal"],original_bytes_unchanged=True,formal_authority=False,
        original_host_binding_verified_input_ref=row.get("verification_ref",verification_ref),source_draft_ref=draft_ref,
        source_additions_ref=addon_ref))
    value={k:copy.deepcopy(row[k]) for k in ("ordinal","origin_ref","origin_selector","description",*core.EXIT_FIELDS)}
    value.update(capture_binding_ref=binding,capture_completeness="ACTUAL_HOST_ORIGINAL_PAIR_WITH_IMMUTABLE_SOURCE_FACT")
    out.append(value)
current=[pin(V/(n+".json")) for n in ("checkpoint","path_ownership","step_state","commands")]
cp=read(current[0])
assert cp["revision"]==377 and cp["work_in_progress"]["root_next_failure_ordinal_live"]==1134
pending=dict(schema="researchos.root-pending-diagnostics.v1",issued_by="codex:/root",counter_reset=False,
    registered_in_current_canon=False,current_canonical_refs=current,source_cutoff_original_failure_ordinal=1133,
    next_original_failure_ordinal=stop,pending=out,source_draft_ref=draft_ref,source_additions_ref=addon_ref)
merged,next_ordinal=core.merge_pending(cp,pending,current)
assert next_ordinal==stop and merged[:len(cp["failure_counters"])]==cp["failure_counters"]
ref=save("pending-diagnostics.cp377.live"+str(stop)+".root.json",pending)
assert [pin(r["path"]) for r in current]==current
print(json.dumps(dict(pending_ref=ref,canonical_unchanged=True,registered=False,
                     first=1134,last=stop-1,next_original_failure_ordinal=stop,formal_acceptance=False),ensure_ascii=False))
