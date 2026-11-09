"""Static Source sealing only: parse Python AST, inspect text, hash public files."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
B = ROOT.parent.parent
R = B.parents[4]
OLD = R / ".local/worktrees/codex-w0599-prepared-maintenance-native-52c5a209cfd34eca"
NATIVE = B / "prepared_abandonment_native_authority_source_codex/b1599aaf259c435db5a0a5313ab0ea65"
MIGRATION = B / "prepared_abandonment_schema_upgrade_source_codex/e841e7fcddaa45ecb115f84df9827af2"
HELPER = B / "native_private_stdin_helper_revision_codex/320740c9ef7c4dbaa6cae48633aa8e60"
CURRENT = B / "integration_codex/current-composition-full-domain-root-0d2a82e73b754a5f"
PREVIOUS = B / "integration_codex/native-authority-enrolled-v2-component-root-b0647419338d47ad"
FAILURE = B / "native_harness_read_failure_codex/798-1c3de11e13744710829920165c8"
assert B.name == "W05-99" and R.name == "research-os"

def ref(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def new(name, value):
    with (ROOT / name).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=True, indent=2)

def load(path):
    return Path(path).read_text(encoding="utf-8")

def jsonload(path):
    return json.loads(load(path))

pins = []
def pin(path, role, expected=None):
    actual = ref(path)
    if expected is not None:
        assert actual["sha256"] == expected["sha256"].removeprefix("sha256:"), (role,"hash drift")
        assert actual["bytes"] == expected["bytes"], (role,"length drift")
    pins.append({"role": role, **actual})
    return actual

for label, directory in [("native20",NATIVE),("migration10",MIGRATION)]:
    hdf = jsonload(directory/"HDF.json")
    pin(directory/"HDF.json",label+":handoff")
    pin(directory/"MF.json",label+":manifest",hdf["manifest_ref"])
    for relative, item in sorted(hdf["source_refs"].items()):
        pin(item["path"],label+":"+relative,item)
assert len(jsonload(NATIVE/"HDF.json")["source_refs"]) == 20
assert len(jsonload(MIGRATION/"HDF.json")["source_refs"]) == 10

relevant = [
 "internal/domain/backup_prepared_abandonment_upgrade_windows_test.go",
 "internal/domain/backup_prepared_abandonment_upgrade.go",
 "internal/domain/backup_prepared_abandonment_upgrade_windows.go",
 "internal/domain/backup_configuration_upgrade_test.go",
 "internal/domain/domain_test.go", "internal/domain/orchestration_test.go", "internal/domain/auth.go",
 "internal/recoveryauthority/types.go","internal/recoveryauthority/migration.go",
 "internal/recoveryauthority/migration_windows.go","internal/recoveryauthority/native_windows.go",
 "apps/control/prepared_recovery_windows.go","adapters/runtime/data_root_windows.go",
 "adapters/runtime/bridge_windows.go","adapters/runtime/process_windows.go",
]
for relative in relevant:
    pin(OLD/relative,"actual-read-api:"+relative)
for name in ["HDF.json","MF.json","CONTRACT.md","windows_owned_private_stdin.py"]:
    pin(HELPER/name,"private-stdin-helper:"+name)
assert ref(HELPER/"windows_owned_private_stdin.py")["sha256"] == "4654730495d3777c8bf63540a0f5795b17ff14a45e93d6cd915e2e2846213a3c"
assert ref(HELPER/"windows_owned_private_stdin.py")["bytes"] == 24629
pin(Path(sys.executable),"source-author-python")
for name in ["HDF.json","MF.json","failure-origin.798.json","original-tool-io.json"]:
    pin(FAILURE/name,"failure798:"+name)

program_pairs = []
for name in ["control-build","maintenance-root-build","enrollment-build","backup-build"]:
    pair = {}
    for label, directory in [("current",CURRENT),("previous",PREVIOUS)]:
        invocation_path = directory/(name+".invocation.json")
        invocation = jsonload(invocation_path)
        invref = pin(invocation_path,label+":"+name+":invocation")
        argv = invocation["argv"]
        assert "-o" in argv
        binary_path = Path(argv[argv.index("-o")+1])
        binary_ref = pin(binary_path,label+":"+name+":program")
        for stream in ["stdout","stderr"]:
            pin(invocation[stream+"_ref"]["path"],label+":"+name+":"+stream,invocation[stream+"_ref"])
        pair[label] = {"invocation":invref,"program":binary_ref,"argv":argv,
                       "cwd":invocation["cwd"],"actual_native_exit":invocation.get("actual_native_exit"),
                       "actual_result":invocation.get("result")}
    pair["same_current_previous_binary_bytes"] = (
        pair["current"]["program"]["sha256"] == pair["previous"]["program"]["sha256"] and
        pair["current"]["program"]["bytes"] == pair["previous"]["program"]["bytes"])
    pair["distinct_provenance_preserved"] = True
    pair["name"] = name
    program_pairs.append(pair)
for name in ["actual-full-test-compiler-input-inventory.json","validation.closed.json",
             "full-domain-and-native-authority-offline.invocation.json"]:
    pin(CURRENT/name,"current-root-composition:"+name)

go_path = ROOT/"candidate-root/internal/domain/native_migration_authority_harness_windows_test.go"
broker_path = ROOT/"root_only_native_broker.py"
go = load(go_path)
broker = load(broker_path)
ast.parse(broker,filename=str(broker_path))
compile(broker,str(broker_path),"exec",dont_inherit=True)
checks = {
 "windows_and_explicit_test_build_tag":go.startswith("//go:build windows && researchos_native_recovery_harness"),
 "one_harness_test":len(re.findall(r"func TestNativeMigrationAuthorityHarness\(",go)) == 1,
 "all_nine_cases":all('"'+v+'"' in go for v in [
  "positive-replay","missing-native-channel","wrong-purpose","mismatched-database",
  "release-pin-mismatch","expired-grant","missing-dynamic-pin","wrong-owner","lease-occupied"]),
 "no_opaque_token_or_authority_construction":all(v not in go for v in
  ["MigrationToken{","Token{","nativeSession{","InstallPrepared","SetAuthority"]),
 "public_versioned_fixture": "preparedUpgradePublicFixture(t)" in go,
 "credentials_before_snapshot":go.index("IssueCredential(ctx, f.owner") < go.index("before, err := preparedUpgradeSnapshot"),
 "public_configuration_roles":all('"'+v+'"' in go for v in ["root-program","control-program","backup-program",
  "enrollment-program","python-program","broker-source","private-stdin-helper"]),
 "native_backup_then_exact_original_invariant":"backupResult" in go and "rehearsal changed original fixture" in go,
 "root_exact_public_payload_review":"PayloadSHA256" in go and "SignedSHA256" in go and "bytes.Equal(wrapper.Payload, expected)" in go,
 "lease_actual_acquire_and_win32_probe":"errors.Is(probeErr,windows.ERROR_SHARING_VIOLATION)" in go,
 "lease_held_through_native_exit":"live lease ended before actual native process closure" in go,
 "missing_pin_exact_gate":"AUTHORITY_MIGRATION_REQUIRED_RAW_PIN_ABSENT" in go,
 "exact_schema_versions":"preparedUpgradeVersions(db,expectedVersion)" in go,
 "positive_complete_row_invariant":"preparedUpgradeRowInvariant(before,after)" in go,
 "negative_complete_rows_and_schema":"Hash(after)!=Hash(before) || afterSchema!=beforeSchema" in go,
 "explicit_replay_and_whole_post_state":"AUTHORITY_MIGRATION_GRANT_ALREADY_USED" in go and "Hash(replayRows)!=Hash(after)" in go,
 "graceful_fixture_retention":"t.Cleanup(cancel)" in go and "06-fixture-retained.ready.json" in go,
 "broker_anonymous_stdin_reader":"command.Stdin = strings.NewReader(input)" in go,
 "python_isolated_utf8":"\"-I\", \"-S\", \"-B\", \"-X\", \"utf8\"" in go,
 "private_pipe_input_bounded_mutable":"bytearray(4097)" in broker and "readinto(view)" in broker,
 "native_suspended_owned_helper":"helper.run_owned_private_stdin(" in broker,
 "broker_never_claims_authority_acceptance":'"NativeAuthorityAcceptance": False' in broker,
 "broker_ast_compile_without_execution":True,
}
assert all(checks.values()), {key:value for key,value in checks.items() if not value}
new("base-pins.json",{"schema":"researchos.public-source-input-pins.v1","pins":pins,
                      "original_base_source_files_verified":30,"drift_count":0})
new("program-provenance.json",{"schema":"researchos.current-and-prior-program-provenance.v1",
                              "program_pairs":program_pairs,"production_programs_executed_by_source_author":False})
new("static-evidence.json",{"schema":"researchos.native-migration-harness-static-evidence.v1",
                          "checks":checks,"all_static_checks":True,"go_compiled":False,"gofmt_run":False,
                          "go_tests_run":False,"native_cases_run":False,"sql_executed":False,
                          "private_reads":False,"signing_performed":False,"provider_requests":0,
                          "static_text_checks_are_not_runtime_proof":True,
                          "runtime_abandonment_gate_implemented":False})
new("failure-origin.798.json",jsonload(FAILURE/"failure-origin.798.json"))
members = {}
for path in sorted(ROOT.rglob("*")):
    if path.is_file():
        assert path.name not in ["HDF.json","MF.json"]
        members[path.relative_to(ROOT).as_posix()] = ref(path)
new("MF.json",{"schema":"researchos.native-migration-harness-source-manifest.v1","members":members})
source_refs = {p:ref(ROOT/p) for p in [
 "candidate-root/internal/domain/native_migration_authority_harness_windows_test.go",
 "root_only_native_broker.py"]}
new("HDF.json",{"schema":"researchos.native-migration-harness-source-handoff.v1",
 "status":"SOURCE_IMPLEMENTED_PENDING_ROOT_BUILD_NATIVE_EXECUTION_AND_INDEPENDENT_REVIEW",
 "sourceStatus":"EXECUTION_REPORTED","formal":False,"execution_authority":False,"production_ready":False,
 "actor_id":"codex:/root/command_queue_impl","source_root":str(ROOT),"source_file_count":2,
 "source_refs":source_refs,"manifest_member_count":len(members),"manifest_ref":ref(ROOT/"MF.json"),
 "contract_ref":ref(ROOT/"CONTRACT.md"),"base_pins_ref":ref(ROOT/"base-pins.json"),
 "program_provenance_ref":ref(ROOT/"program-provenance.json"),"static_evidence_ref":ref(ROOT/"static-evidence.json"),
 "original_tool_io_ref":ref(ROOT/"original-tool-io.json"),"failure_origin_ref":ref(ROOT/"failure-origin.798.json"),
 "failure798_separate_handoff_ref":ref(FAILURE/"HDF.json"),
 "case_count":9,"phase_protocol":"public-payload -> Root-private-signing-outside-harness -> public-approval -> native-actual -> Root-inspection -> fixture-release",
 "current_program_configuration":"Root frozen role pins, no hardcoded old program path",
 "private_credentials":"Go memory -> actual anonymous pipe -> bounded mutable Python buffer -> reviewed private stdin helper",
 "current_owner_not_persisted":True,"go_secret_memory_erasure_claimed":False,
 "private_helper_root_native_matrix_acceptance_required":True,
 "outer_job_inner_control_job_equivalence_claimed":False,
 "source_author_actions":{"go_or_gofmt":False,"native_programs":False,"sql":False,"private_resource_reads":False,
                          "signing":False,"provider_requests":0,"main_or_canonical_writes":False},
 "required_root_checks":["compile and selected fixture dependencies","actual helper independent acceptance",
  "frozen source/runtime/program guards","review and sign exact release/grant payloads","nine actual native cases",
  "retained complete database row/schema verification","actual Job and guard closure",
  "independent final verdict with wider full-suite failures kept separate"],
 "remaining_scope":["native prepared abandonment positive and hostile matrix with actual matching historical sixteen-role evidence",
  "all nine native migration cases unexecuted by Source author","no broader full-domain PASS claim"]})
for name,item in members.items():
    assert ref(ROOT/name) == item
for item in pins:
    current = ref(item["path"])
    assert current["sha256"] == item["sha256"] and current["bytes"] == item["bytes"], item["role"]
print(json.dumps({"HDF":ref(ROOT/"HDF.json"),"MF":ref(ROOT/"MF.json"),
                  "source_refs":source_refs,"members":len(members),"base_pin_count":len(pins),
                  "all_static_checks":True,"go_native_sql_run":False},ensure_ascii=True))

