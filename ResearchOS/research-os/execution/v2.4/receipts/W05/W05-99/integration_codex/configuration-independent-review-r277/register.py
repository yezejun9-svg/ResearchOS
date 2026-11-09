import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
CANON = [ROOT / ("execution/v2.4/" + n) for n in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


def enc(v):
    return (json.dumps(v, ensure_ascii=False, indent=2) + "\n").encode()


def save(n, v):
    with (OUT / n).open("xb") as f:
        f.write(enc(v))


def ref(p, expected=None):
    h = hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
    if expected:
        assert h == expected, p
    return {"path": p, "sha256": h}


before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert cp["revision"] == 276 and ow["revision"] == 104 and len(cp["failure_counters"]) == 232
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "26e1043751c989d4e6016a76f113e343c9e38382"
for p, raw in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(raw)
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
config = ow["card_path_bindings"]["W05-99"]["subtasks"]["host_configuration_upgrade_prerequisites"]
assert len(config["paths"]) == 11 and config["owner"] == "codex:/root/sources_parent_impl"
scope = {"schema": "researchos.root.independent-source-review-scope.v1", "actor": "codex:/root", "reviewer": "codex:/root/command_queue_impl", "executor": config["owner"], "parent": "W05", "card": "W05-99", "at": now, "review_namespace": "execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_source_review_codex/<new-uuid>/**", "source_writes": 0, "canonical_writes": 0, "frozen10_candidate": "125ea34ca0878f18c4dce47f9259ab5e9e77c2eb", "immutable_foundation": "fef0ee2d56351e74ceed11b0b37d3f87e9c83494", "base_source": "396287cc5427eb125aaedb8a2b7fadf63e6b9322", "main_comparison_only": head, "exact_source11": config["paths"], "scope_refs": {"exact10": ref(BASE + "integration_codex/configuration-schema-mirror-scope-r271/scope_registration.json", "b630bb18181934f1c4dbac37179be976fc0b25f447b46a9b7f8e89a30c86750f"), "one_test": ref(BASE + "integration_codex/configuration-test-and-p12-resource-r276/test_scope_registration.json", "f3f74be44cfe1a515a6c1f31c63f22aefb45cba04c42c0f055cd3125f3ed7338"), "all12_gates": config["independent_scope_review_ref"]}, "review_policy": "Reviewer did not author config10/foundation5/test1. Frozen10 only static audit now; no whole-source acceptance from pending test1. Final exact11 commit/handoff and complete compiler/source/tools/program/testbinary vectors required before actual nonself selectors. Source author cannot sign acceptance; Root alone integrates Main after separate current composition validation.", "before_final_test_freeze": "Only readonly Git/public frozen receipts/static scope audit; no compile/test invocation yet.", "after_final_test_freeze": "One appropriate targeted source replay covering fixed current23/historical22, real public backup/restore/upgrade/rollback/activequeue/old22writer and immutable schema mirrors. Preserve original negative/failure/zero-assertion facts. New readonly overlays/isolated checkout/cache/testbinary in own review namespace allowed. Pin current source and original SQL/API, Go/Node/executables/embeds and actual package graph before and after; stop first unexplained failure, no unregistered repair.", "g01": "Match actual old22 and target23 builds to captured source/release roots and program SHA. Public executable protocol has no arbitrary binary source self-attestation; judge external frozen release binding honestly, no claim of runtime source identity detection.", "g10": "Historic14 ActiveRecovery OPEN is separately inherited same base three-file bytes; fixed14CLI original artifact opt-in true execution does not qualify ActiveRecovery. Original hardpin failure preserved and newstrict23/historical22 controls required, not widened >= checks. Other guards and SQL1..23 unchanged.", "private_data_reads": 0, "paid_calls": 0, "actual_service_model_calls": 0, "provider_worker_starts": "0 unless separately scoped genuine loopback SDK regression is necessary; no held Provider9 positives authorized", "exclude": ["SQL24/F08", "host.configure/session handler implementation", "provider9 source changes or positive held history retries", "private Host/Vault/user DB", "Main/canonical state mutations", "formal acceptance"], "formal_increment": 0}
save("scope_registration.json", scope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
config.setdefault("independent_reviewer_history", []).append({"verifier": config["verifier"], "note": "Earlier scope review retained; nonself exact11 source reviewer reassigned after frozen10 to parallel independent P12 diagnostics."})
config.update(verifier="codex:/root/command_queue_impl", independent_source_review_scope_ref=scope_ref, frozen10_candidate=scope["frozen10_candidate"], final_test_supplement_state="IN_PROGRESS_SOURCE_ACCEPTANCE_PENDING")
cp.update(revision=277, expected_previous_revision=276, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=105, amended_at=now, amended_by="codex:/root")
cp["next_command"] = "Configuration exact10 frozen125ea+immutablefoundation5 nonauthor Cmd staticreview; sourceparent completesregistered1test strict23/historical22 supplement, final11freeze then independent actual replay. Main23hold/sourceRuntimeconfigurationnotimplemented. W05Review runs only registered P12 candidate zero-model copiedDBcontrols after causal public deps. Providerhistory5 held/noreset. F08 future14/configure14 onlyreadonlyscope. Requalify22parents/42CURRENT all required."
cp["work_in_progress"].update(status="CONFIGURATION_EXACT11_NONAUTHOR_SCOPE_REGISTERED_PENDING_TESTFREEZE_P12_ZERO_MODEL", next_action=cp["next_command"], configuration_independent_source_review_scope_ref=scope_ref)
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "NONAUTHOR_CONFIGURATION_EXACT11_SOURCE_REVIEWER_REGISTERED", "scope_ref": scope_ref, "failure_origins_unchanged": 232, "formal_increment": 0})
cp["evidence_index"].append(scope_ref["path"])
save("record.json", {"checkpoint": [276, 277], "ownership": [104, 105], "failure_origins": [232, 232], "scope_ref": scope_ref, "formal_increment": 0})
assert all(p.read_bytes() == b for p, b in before.items())
for p, v in zip(CANON[:2], [cp, ow]):
    tmp = p.with_name(p.name + ".root277.tmp")
    with tmp.open("xb") as f:
        f.write(enc(v))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({"checkpoint": 277, "ownership": 105, "failure_origins": 232, "scope_ref": scope_ref, "formal_increment": 0}))
