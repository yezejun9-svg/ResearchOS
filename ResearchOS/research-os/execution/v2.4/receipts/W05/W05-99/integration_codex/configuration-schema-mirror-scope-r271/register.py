import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
CP, OW, ST, CM = [ROOT / ("execution/v2.4/" + name) for name in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


def enc(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def save(name, value):
    with (OUT / name).open("xb") as stream:
        stream.write(enc(value))


def ref(relative, expected=None):
    value = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if expected:
        assert value == expected, relative
    return {"path": relative, "sha256": value}


before = {path: path.read_bytes() for path in [CP, OW, ST, CM]}
cp, ow = json.loads(before[CP]), json.loads(before[OW])
assert cp["revision"] == 270 and ow["revision"] == 98 and len(cp["failure_counters"]) == 203
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "396287cc5427eb125aaedb8a2b7fadf63e6b9322"
for path, raw in before.items():
    with (OUT / (path.stem + ".original.json")).open("xb") as stream:
        stream.write(raw)
prior_ref = ref(BASE + "integration_codex/configuration-upgrade-scope-r270/scope_registration.json", "1dcb4a47472752f15d4db8db0d0de3d12af53d6c0496e9b0fe2477ed641485e0")
prior = json.loads((ROOT / prior_ref["path"]).read_bytes())
wt = ROOT / prior["worktree"]
assert wt.is_dir()
review_ref = ref(BASE + "host_configuration_schema_mirror_scope_review_codex/98cce1a4-5b1a-4361-8fb7-4d6b979481df/scope_review.json", "2749e4d0021f4ac53c3da04fdb9a99399a5e142159b0e8f272938287b43777c2")
review = json.loads((ROOT / review_ref["path"]).read_bytes())
assert review["decision"] == "SOURCE_SCOPE_READY_EXACT2_IMMUTABLE_SCHEMA_MIRRORS" and len(review["exact_additions"]) == 2
author_prefix = BASE + "host_configuration_upgrade_executor_codex/implementation-df2b17aedb254da9b0fb902ca7f8575f/"
author_refs = []
for name, expected in [("schema_mirror_scope_proposal", "9f780cf9e38e554b40a969ab188f0521d003447be6370cf4ace2cb862c91e9aa"), ("schema_mirror_scope_supplement", "6f2e221f4c8b9c5408fab093c08583d37e8a1e30c37804b0041f4ad3ae50f1e0")]:
    path = wt / (author_prefix + name + ".json")
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    destination = OUT / (name + ".original.json")
    with destination.open("xb") as stream:
        stream.write(raw)
    author_refs.append(ref(destination.relative_to(ROOT).as_posix(), expected))
mirrors = review["exact_additions"]
for item in mirrors:
    for root in [ROOT, wt]:
        source = root / item["source"]
        assert source.is_file() and source.stat().st_size == item["bytes"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item["source_sha256"]
        assert not (root / item["target"]).exists()
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
scope = copy.deepcopy(prior)
scope.update(schema="researchos.root.configuration-upgrade-exact10-source-scope.v1", registered_at=now, amended_by="codex:/root", prior_exact8_scope_ref=prior_ref, original_exact8_scope_remains=True, exact2_mirror_scope_review_ref=review_ref, exact2_author_proposal_refs=author_refs, immutable_schema_mirrors=mirrors, mirror_mandatory_guards=review["mandatory_guards"])
scope["paths"] += [item["target"] for item in mirrors]
assert len(scope["paths"]) == len(set(scope["paths"])) == 10
scope["source_only_authority"] = "Same isolated original8 prerequisites plus exact2 byte mirrors only; current API/schema/loader originals unchanged. Scope guards and all12 original gates still mandatory; no public handler/SQL24/LIVE qualification."
save("scope_registration.json", scope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
handoff_ref = ref(BASE + "cli_read_interrupt_executor_codex/freeze-r270/handoff.json")
handoff = json.loads((ROOT / handoff_ref["path"]).read_bytes())
assert handoff["candidate_commit"] == "f565599af3679fef6d5233fe27d16b8c92a61db2" and handoff["actual_changed_paths"] == 178
full_ref = ref(handoff["full_result_ref"]["path"], "7461e91449c9820b3945911881b91a0973aa45cc22884b6e49bce5dfa83b926d")
mapping_ref = ref(BASE + "integration_codex/configuration-handler-readonly-r270/read_mapping.json")
subs = ow["card_path_bindings"]["W05-99"]["subtasks"]
sub = subs["host_configuration_upgrade_prerequisites"]
assert sub["scope_ref"] == prior_ref
sub.setdefault("scope_amendments", []).append({"at": now, "previous_scope_ref": prior_ref, "new_scope_ref": scope_ref, "added_paths": [item["target"] for item in mirrors], "independent_review_ref": review_ref})
sub.update(paths=scope["paths"], scope_ref=scope_ref, state="REGISTERED_EXACT10_SCHEMA23_PREREQUISITES_IMMUTABLE_MIRRORS_MAIN_HOLD", exact2_scope_review_ref=review_ref, immutable_schema_mirrors=mirrors)
subs["cli_read_interruption"].update(state="EXACT4_FROZEN_CURRENT_FULL234_PASS_INDEPENDENT_REVIEW_PENDING", candidate_commit=handoff["candidate_commit"], candidate_handoff_ref=handoff_ref, current_full_result_ref=full_ref)
subs["provider_transport_reasoning_binding"]["iteration_chain_state"] = "EXECUTOR_REPORTED_HISTORY_REJECTION_CHAIN_LIMIT_EXCEEDED_NO_FURTHER_AUTHOR_QUALIFICATION_RETRIES; sealed original origins pending Root import; latest PASS candidate remains unaccepted"
observations = [
    {"origin_key": "W05-99/root/r270-git-info-attributes-read-locator", "tool_chunk": "8e382c", "actual_aggregate_exit": 1, "actual_rg_error": "os error2", "failed_path": ".git/info/attributes", "existing_attributes": ".gitattributes: * -text", "source_mutation": False},
    {"origin_key": "W05-99/root/r270-contract-reader-path-locator", "tool_chunk": "6941bc", "actual_aggregate_exit": 0, "actual_rg_error": "os error2", "failed_paths": ["internal/contracts", "internal/api/client_protocol.go"], "corrected_strategy": "actual directories internal/domain and internal/api, observed client_protocol_schema.go and api/v2.go", "source_mutation": False},
    {"origin_key": "W05-99/root/r270-powershell-rg-file-glob-locator", "tool_chunk": "4f4af2", "actual_aggregate_exit": 1, "actual_rg_error": "os error123", "failed_path": "internal/domain/client_protocol*.go", "corrected_strategy": "directory search with rg --glob; actual correctedd0eae1 exit0", "source_mutation": False}
]
save("root_observations.json", {"schema": "researchos.root.actual-observations.v1", "at": now, "observations": observations, "raw_policy": "Tool session observations with exact chunks retained; no invented subprocess raw/invocation files."})
observations_ref = ref((OUT / "root_observations.json").relative_to(ROOT).as_posix())
old = copy.deepcopy(cp["failure_counters"])
for item in observations:
    assert item["origin_key"] not in {entry.get("origin_key") for entry in old}
    cp["failure_counters"].append({"origin_key": item["origin_key"], "attempts": 1, "retries_used": 0, "status": "ACTUAL_READ_ONLY_TOOL_ERROR_PRESERVED", "evidence_ref": observations_ref, "detail": item, "counter_reset": False, "formal_increment": 0})
assert len(cp["failure_counters"]) == 206 and cp["failure_counters"][:203] == old
cp.update(revision=271, expected_previous_revision=270, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=99, amended_at=now, amended_by="codex:/root")
cp["next_command"] = "Independent frozen L02 exact4 f565599 original oversize replay/full current closure; schema23 prerequisites exact10 includes only2 immutable schema mirrors/all12gates in original isolated WT, MAIN23hold. Provider9 different-root-cause controls/regressions only, original history rejection chain stopped after reported cumulative limit exceeded; sealed failures await import and latest PASS unaccepted. Root integrates only after nonself/source/current-composition review;W04/W07 revalidate final source;22/42CURRENT required."
cp["note"] = "L02 fresh fullCLI234 assertions/67top PASS0fail0skip,39061sourceinputs stable, frozen4code+174publicreceiptsf565599 awaits independent review. Schema23 exact8 expanded by reviewed exact2 bytewise schema mirrors only; API originals and foundation5 protected, all12 gates unchanged, no SQL24/host.configure/LIVE acceptance. New readonly public host.configure callgraph exposes remaining public gaps with no source edits.206failure origins preserve203prefix+3actualRootread diagnostics. Provider author reports original same-history failure chain exceeded limit; further retries stopped, no finalPASS erasure, structured origins pending. Formal0/42 unchanged."
cp["work_in_progress"].update(status="L02_FROZEN_CURRENT234_PENDING_NONSELF_PROVIDER9_LIMIT_PRESERVED_SCHEMA23_EXACT10_ISOLATED", next_action=cp["next_command"], host_configuration_upgrade_prerequisites_scope_ref=scope_ref, host_configuration_schema_mirror_scope_review_ref=review_ref, cli_read_candidate_handoff_ref=handoff_ref, cli_read_current_full_result_ref=full_ref, configuration_public_handler_read_mapping_ref=mapping_ref)
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "FROZEN_CURRENT_CLI_READ_CAUSAL_SOURCE_AND_EXACT2_SCHEMA_MIRROR_SCOPE_AMENDMENT", "scope_ref": scope_ref, "cli_handoff_ref": handoff_ref, "failure_origins": [203,206], "formal_increment": 0})
for item in [scope_ref, review_ref, *author_refs, handoff_ref, full_ref, mapping_ref, observations_ref]:
    if item["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(item["path"])
save("record.json", {"schema": "researchos.root.resume-checkpoint.v1", "actor": "codex:/root", "at": now, "checkpoint": [270,271], "ownership": [98,99], "failure_origins": [203,206], "scope_ref": scope_ref, "cli_handoff_ref": handoff_ref, "state_registry_unchanged": True, "formal_cases_current": 0, "formal_increment": 0})
assert all(path.read_bytes() == raw for path,raw in before.items())
for path, value in [(CP,cp),(OW,ow)]:
    temporary = path.with_name(path.name + ".root271.tmp")
    with temporary.open("xb") as stream:
        stream.write(enc(value))
    assert path.read_bytes() == before[path]
    os.replace(temporary,path)
assert ST.read_bytes() == before[ST] and CM.read_bytes() == before[CM]
print(json.dumps({"checkpoint":271,"ownership":99,"failure_origins":206,"scope_ref":scope_ref,"record_ref":ref((OUT/"record.json").relative_to(ROOT).as_posix()),"formal_increment":0}))
