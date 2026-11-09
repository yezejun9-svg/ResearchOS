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
    raw = (ROOT / p).read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    if expected:
        assert h == expected, p
    return {"path": p, "sha256": h, "bytes": len(raw)}


before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert (cp["revision"], ow["revision"], len(cp["failure_counters"])) == (285, 113, 245)
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "2cdb0d43d5a600eef13c8f1735946a9adf52d079"
arch_ref = ref(BASE + "integration_codex/source-evidence-archive-r285/completed.json")
arch = json.loads((ROOT / arch_ref["path"]).read_bytes())
assert arch["head"] == head and arch["changed_paths"] == 760 and arch["source_changed"] is False
proposal_ref = ref(BASE + "host_configuration_handler_scope_revision_codex/8f972b92afae45c5ac96ca679d623975/scope_proposal.json", "9881250323d511b813dab6215fe30fd3ad984ba1682f74033ad448d482bae39f")
prior_decision_ref = ref(BASE + "host_configuration_handler_scope_revision_codex/8f972b92afae45c5ac96ca679d623975/root_interface_decision.record.json", "bd8ac5516fad6d1f2cd144e5edbd6a00ba56150f182c9b956de789a00c8554df")
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
decision = {"schema": "researchos.root.handler-interface-decisions.v2", "actor": "codex:/root", "at": now, "card": "W05-99", "actual_main_head": head, "prior_nine_decisions_ref": prior_decision_ref, "prior_exact16_proposal_ref": proposal_ref, "status": "DESIGN_DECISIONS_ONLY_EXACT18_NONAUTHOR_REVIEW_REQUIRED_BEFORE_SOURCE_WRITES", "add_exact_paths": [{"path": "internal/domain/backup_host_configuration.go", "bounds": "Only global identity original-response verification: strict new private original-request metadata and conditional legal REJECTED missing Session. All successful/ACK/derived-session existing proof stays strict; legacy empty headers remain original strict behavior."}, {"path": "internal/domain/backup_host_configuration_test.go", "bounds": "New public CreateBackup/Restore/replay/rebackup of authenticated legal REJECTED unknown/cross-project Session, strict request/response/header corruption controls, preserve all original assertions."}], "original_request_anchor": {"sole_storage": "New original idempotency INSERT.headers, private metadata only; no new table/response authority/public schema field and no headers UPDATE/legacy backfill.", "format": {"schema": "researchos.private-command-envelope.v1", "encoding": "base64", "raw_envelope_base64": "Exact original retained request bytes encoded with canonical base64.StdEncoding"}, "strict_reader": "Existing client_command_identity.go private helper: strict duplicate/unknown/type/UTF-8/private schema decoding, maxEncoded bound derived from raw1MiB plus fixed three-key overhead; strict base64 decode and exact re-encode equality (reject CRLF and noncanonical bits); raw length1..1MiB and full fixed CommandEnvelope strict validation before normalization.", "hash_binding": "Preserve existing Envelope.ContentHash() canonical complete-envelope algorithm including sha256: prefix. Decode saved raw to same request and compare canonical ContentHash to both identity and journal request_hash. SHA256(raw bytes) is optional evidence integrity only, never protocol request_hash or a new hash algorithm.", "attribution": "Stored raw protocol/command/client/project/session/method/scope/payload must equal original global identity/journal locator/full response including new session.create derived response exception only after durable sameTx creation proof.", "rejected_exception": "Only strictly proven new original REJECTED request may reference unknown/cross-project SID without requiring a successful Session creation. RequestSID/fullcontent remain bound; no responseSID-as-request proof. Successful/ACK or missing new metadata retain Session existence/project checks. Full frozen CommandResponse/method result checks never weaken.", "privacy": "Only already-allowed durable protocol envelopes, never native-only credential intake/secret fields. This private SQLite headers record must never be forwarded as HTTP headers or returned to product clients. Existing v1 HTTP headers and all old rows stay byte-identical."}, "pc01_legacy": "Unproved old draft/noRun Session lacks original frozen profile evidence: preserve its original Session/Goal/task/history and read behavior; binding/execution may explicitly refuse missing original provenance. Do not infer legacy from absence/current head/timestamp/ref prefix. A current authorized Owner plus real original creation/workspace and sameTx actual settled Session may bind it to a new typed configuration, with new original scopedconfigure request/response chain; subsequent typed checks remain required. Real positively proven legacy keeps prior supported behavior. Exact additional caller paths must be reviewed before scope expansion.", "required_controls": ["Unknown SID and cross-project SID typed REJECTED: business/config/head/session/run/queue/budget0; identity1+journal1 then public backup/restore/exact replay/rebackup preserves exact bytes", "Tamper only saved raw SID/client/project/payload/command, duplicate key, oversized raw/encoded header, CRLF/noncanonical base64, hash/body locator mismatch: reject at declared proof boundary", "Tamper rejected responseSID/status to successful/ACK missing Session: backup rejects; full successful/derived Session proof remains", "Original legacy empty headers/hash/principal-prefix replay remains unchanged; no identity backfill", "Authentication/schema/SQL/commit failure allrollback and no orphan identity; business legal rejection keeps original identity+journal only", "Existing configuration23 full historical backup/upgrade controls still pass with all original assertions; SQL23/schema/SDK/budget unchanged"], "execution_authorized": False, "source_changes": 0, "formal_increment": 0}
save("interface_decisions.json", decision)
decision_ref = ref((OUT / "interface_decisions.json").relative_to(ROOT).as_posix())
failure = {"origin_key": "W05-99/Root/handler-headers-discovery/c88140", "attempts": 1, "retries_used": 0, "status": "ACTUAL_READONLY_WINDOWS_LITERALGLOB_EXIT1_TRANSCRIPT_ONLY", "actual_outer_exit": 1, "tool_output_chunk": "c88140", "command_fragment": "rg headers patterns internal/domain/backup*.go --glob *.go", "actual_error": "Literal Windows wildcard path os error123", "original_raw_locator": "functions exec tool output chunk c88140", "native_stderr_file": None, "product_test_run": False, "source_mutation": False, "counter_reset": False, "formal_increment": 0}
save("failure_origin.json", failure)
failure_ref = ref((OUT / "failure_origin.json").relative_to(ROOT).as_posix())
assert failure["origin_key"] not in {r.get("origin_key") for r in cp["failure_counters"]}
cp["failure_counters"].append(dict(failure, evidence_ref=failure_ref))
assert len(cp["failure_counters"]) == 246
cp.setdefault("preserved_unindexed_tool_diagnostics", []).append({"tool_output_chunk": "ff316e", "actual_outer_exit": 1, "observation": "Correct directory/glob search returned ordinary no-match status1 for header-length patterns, with no read/IO error. Not a failed product check or failed invocation assertion.", "product_failure": False})
for p, raw in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(raw)
cp.update(revision=286, expected_previous_revision=285, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=114, amended_at=now, amended_by="codex:/root")
cp["work_in_progress"].update(configuration_handler_interface_decisions_ref=decision_ref, configuration_handler_scope_state="EXACT18_PROPOSED_NONAUTHOR_REVIEW_PENDING_NO_SOURCE_WRITES", main_source_head=head, next_action="Complete nonauthor exact18 handler scope proof, then Root register source lease/new isolated worktree. Provider distinct typed-route attempt3 currently bounded; old failures/history5 preserved. F08 serial later.")
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "HANDLER_EXACT18_INTERFACE_PRIVATE_ORIGINAL_REQUEST_DECISIONS_RECORDED_SOURCE_NOT_YET_AUTHORIZED", "decision_ref": decision_ref, "archive_ref": arch_ref, "source_unchanged_after_receipt_commit": True, "failure_origins": [245, 246], "formal_increment": 0})
for r in [decision_ref, failure_ref, arch_ref]:
    cp["evidence_index"].append(r["path"])
save("record.json", {"checkpoint": [285, 286], "ownership": [113, 114], "failure_origins": [245, 246], "decision_ref": decision_ref, "source_execution_authorized": False, "formal_increment": 0})
assert all(p.read_bytes() == raw for p, raw in before.items())
for p, v in zip(CANON[:2], [cp, ow]):
    tmp = p.with_name(p.name + ".root286.tmp")
    with tmp.open("xb") as f:
        f.write(enc(v))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({"checkpoint": 286, "ownership": 114, "failure_origins": 246, "decision_ref": decision_ref, "source_execution_authorized": False, "formal_increment": 0}))
