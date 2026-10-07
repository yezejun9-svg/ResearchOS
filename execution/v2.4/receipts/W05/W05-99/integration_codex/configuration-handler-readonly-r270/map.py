"""Record current public configuration callgraph; grants no new source scope."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
FOUNDATION = ROOT / ".local/worktrees/codex-w0599-host-configuration-upgrade"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("xb") as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


names = ["internal/domain/client_protocol.go", "internal/domain/client_protocol_sessions.go", "internal/domain/client_protocol_journal.go", "internal/domain/client_protocol_schema.go", "internal/domain/runtime_sessions_windows.go", "internal/domain/runtime_goal_bindings_windows.go", "internal/api/v2.go", "internal/api/contracts/client.protocol.schema.json", "internal/api/contracts/domain.schema.json", "internal/host/host.go", "internal/host/model_credential.go", ".local/worktrees/v24-continuation/spec/v2.4/22_CLIENT_INTERFACE_DETAILS.md"]
inputs = {str(ROOT / name): sha(ROOT / name) for name in names}
for name in ["internal/domain/client_configuration.go", "internal/domain/client_command_identity.go", "migrations/sqlite/0023_host_model_configuration.sql"]:
    inputs[str(FOUNDATION / name)] = sha(FOUNDATION / name)
schema = json.loads((ROOT / "internal/api/contracts/client.protocol.schema.json").read_bytes())
definitions = schema.get("$defs", schema.get("definitions", {}))
save("source_before.json", inputs)
save("typed_configuration_contract.json", {"source_sha256": inputs[str(ROOT / "internal/api/contracts/client.protocol.schema.json")], "method": schema["x-method-contracts"]["host.configure"], "payload": definitions["ConfigurePayload"], "result": definitions["ConfigureResult"]})
save("read_mapping.json", {"schema": "researchos.root.configuration-handler-readonly-callgraph.v1", "actor": "codex:/root", "at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "main_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(), "mode": "READ_ONLY_SOURCE_INFERENCE_NOT_EXECUTED_NOT_ACCEPTED", "source_inputs": len(inputs), "foundation": "fef0ee2d56351e74ceed11b0b37d3f87e9c83494 immutable private storage only; MAIN lacks23", "observations": [
    {"path": "internal/domain/client_protocol.go", "fact": "DecodeEnvelope requires writer_epoch for host.configure containing provider_id/model_id even when session_id is null. Frozen contract permits default-only configuration with null project/session/revision/epoch.", "status": "SOURCE_OBSERVED_DEFAULT_CONFIGURATION_GAP_NO_NEW_TEST_EXECUTED"},
    {"path": "internal/domain/client_protocol.go", "fact": "host.configure is absent from writeMethods and has no implemented read/write handler; current dispatch returns NOT_IMPLEMENTED. This is a real missing public method, not evidence of storage foundation failure.", "status": "PUBLIC_HANDLER_NOT_IMPLEMENTED"},
    {"path": "internal/api/v2.go", "fact": "ClientHostInfo.ConfigRevision is initialized0; API default instanceID uses PID. Durable configuration owner must instead derive current verified Host.InstanceID from protected directory and OS principal, supplied through trusted host composition.", "status": "TRUSTED_HOST_CONFIGURATION_COMPOSITION_REQUIRED"},
    {"path": "internal/domain/client_configuration.go (isolated foundation)", "fact": "stageClientConfiguration only supports default-only envelopes; caller owns authentication, global identity join, original typed response insertion, final semantic read and full transaction rollback. No session switching or runtime qualification is implemented there.", "status": "FOUNDATION_ALONE_DOES_NOT_IMPLEMENT_HOST_CONFIGURE"},
    {"path": "internal/domain/runtime_sessions_windows.go", "fact": "sessionModel matches exact immutable model_config.ref in current host RuntimeRegistration/profile and route; a newly generated mc- storage ref does not itself create an admitted runtime, provider connection or credential authority.", "status": "RUNTIME_BINDING_AND_QUALIFICATION_SEPARATE_REQUIRED"},
    {"path": "internal/host/model_credential.go", "fact": "ModelCredential is private trusted coordinator only, checks original credential ref/revision/provider/revocation then opens protected material. Configure/probe/models cannot expose key or use client-supplied readiness.", "status": "PRESERVE_PRIVATE_CREDENTIAL_AUTHORITY"}],
    "next_design_requirements": ["Only after independently verified schema23 public backup/upgrade/current composition, review exact handler source scope; no immediate new source authority.", "Default-only and settled-session configuration must obey exact typed envelope, principal/verified stable host, global command identity and original single response authority; concurrent revisions/foreign owner/replays fail or replay consistently.", "Configuration save performs no network/model call. Sessions/runs keep immutable model versions; live or UNKNOWN run and unresolved queue reject session rebind before mutation; no silent fallback.", "Host status must read real durable configuration and credential metadata; saved credentials and profiles are not proof of provider/model qualification.", "Provider models/probe are separate bounded capabilities with explicit authorization and original project BudgetLedger; live B01 remains blocked independently.", "Do not create SQL24 or alter root canonical state/API schema/SDK/source from this read-only map."], "source_changes": 0, "product_test_executions": 0, "paid_calls": 0, "private_host_reads": 0, "formal_increment": 0})
assert inputs == {path: sha(Path(path)) for path in inputs}
save("source_after.json", inputs)
save("result.json", {"actual_exit": 0, "source_inputs": len(inputs), "source_drift": False, "source_edits": 0, "formal_increment": 0})
print(json.dumps({"actual_exit": 0, "source_inputs": len(inputs), "source_drift": False, "formal_increment": 0}))
