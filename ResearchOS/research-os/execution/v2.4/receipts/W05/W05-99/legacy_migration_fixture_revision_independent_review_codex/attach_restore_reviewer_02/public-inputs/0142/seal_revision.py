import sys
sys.dont_write_bytecode = True
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

Q = Path(__file__).resolve().parent
T5 = Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2")
PACKAGE = Path("D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4")
def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
def assert_ref(item):
    assert ref(item["path"]) == item, "resource fingerprint mismatch: " + item["path"]
def load(name):
    return json.loads((Q / name).read_text(encoding="utf-8"))
def write(name, value):
    with (Q / name).open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

construction = load("construction.json")
verification = load("verification.json")
inspection = load("inspection.json")
resources = load("migration-resources.json")
resource_entry = load("historical20-resource-entry.json")
assert construction["authority"] == "NONE"
assert verification["mechanical_failures_this_branch"] == 0
for item in construction["member_refs"]:
    assert_ref(item)
for item in construction["diff_refs"].values():
    assert_ref(item)
for item in construction["static_checks"]:
    if "base_ref" in item:
        assert_ref(item["base_ref"])
        assert item["missing_original_assertion_call_nodes"] == []
        assert item["original_Test_names_preserved"] is True
    assert item["balanced"] is True
assert_ref(construction["lexical_utility_ref"])
for item in verification["source_contract_refs"]:
    assert_ref(item)
for item in inspection["test_sources"]:
    assert_ref(item["ref"])
for key in ["cause_manifest_ref", "cause_report_ref", "cause_source_pins_ref", "T5_actual_inventory_ref"]:
    assert_ref(inspection[key])
for item in inspection["T5_actual_test_refs"]:
    assert_ref(item)
candidate_root = Q / "candidate-root"
allowed = {
    "internal/domain/client_session_bootstrap_test.go",
    "internal/domain/retrieval_test.go",
    "internal/domain/legacy_migration_fixture_test.go",
    "internal/domain/testdata/pretranscript-3225a31f.sql",
}
actual_members = {p.relative_to(candidate_root).as_posix() for p in candidate_root.rglob("*") if p.is_file()}
assert actual_members == allowed
old_sql = Q / "resources/pretranscript-3225a31f.sql"
embedded_sql = candidate_root / "internal/domain/testdata/pretranscript-3225a31f.sql"
raw = old_sql.read_bytes()
assert raw == embedded_sql.read_bytes()
assert len(raw) == 2014
assert hashlib.sha256(raw).hexdigest() == "3b00677902c3be1dbffb8f7505293bae7242dc976e8017562ab86254ac212f2a"
assert hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest() == "9efc768f8f4cfb6ac31e1f88a78ad095877328af"
assert b"transcript_artifact_id" not in raw
assert_ref(verification["original_FULL_raw_ref"])
assert sum(x["original_assertion_call_count"] for x in verification["static_checks"]) == 126
assert sum(x["original_Test_count"] for x in verification["static_checks"]) == 12

excerpts = []
def excerpt(path, start, end, reason):
    source = Path(path).read_text(encoding="utf-8").splitlines()
    assert 1 <= start <= end <= len(source)
    excerpts.append({"source_ref": ref(path), "start_line": start, "end_line": end,
                     "reason": reason,
                     "lines": [{"line": n, "text": source[n - 1]} for n in range(start, end + 1)]})
contract = PACKAGE / "03_DATA_CONTRACTS.md"
for a, b, reason in [(7, 11, "old-field migration validation on backup copies"),
                     (148, 150, "fixture evidence is distinct from product PASS"),
                     (165, 168, "upgrade backup/restore exercise and old program/data supervision")]:
    excerpt(contract, a, b, reason)
for relative, a, b, reason in [
    ("internal/domain/store.go", 65, 74, "current New inventory and prebackup gates before DDL"),
    ("internal/domain/backup_migration.go", 15, 51, "populated authority requires matching-program backup and isolated migration"),
    ("internal/domain/backup_migration.go", 60, 105, "exact supported inventory and contiguous ledger"),
    ("internal/domain/client_session_fence.go", 24, 67, "real additive fence installation primitive and transaction"),
    ("internal/domain/v24_sessions.go", 78, 110, "session project validation and original legacy field insertion"),
    ("internal/store/sqlite.go", 74, 91, "truthful bootstrap SQL and version in one transaction"),
    ("migrations/sqlite/0009_retrieval_root_identity.sql", 1, 8, "fixed SQL9 root revocation semantics"),
]:
    excerpt(T5 / relative, a, b, reason)
write("contract-excerpts.json", {"authority": "NONE", "formal_acceptance": False,
                               "excerpts": excerpts, "production_changes": 0})

line_refs = []
for relative, anchors in [
    ("internal/domain/client_session_bootstrap_test.go",
     ["func TestClientTranscriptIndexUpgradesExistingSessionTable",
      "if err := useLegacyTranscriptFixture", "func TestClientTranscriptIndexUpgradeRollsBackWithCallerTransaction",
      "func TestClientTranscriptInstalledColumnRemovalRequiresPrebackup"]),
    ("internal/domain/retrieval_test.go",
     ["func TestW09LegacyRootMigrationRevokesUnidentifiedRoot", "func TestW09LegacyRootMigrationRejectsGappedInventory"]),
    ("internal/domain/legacy_migration_fixture_test.go",
     ["func", "//go:embed"]),
]:
    path = candidate_root / relative
    lines = path.read_text(encoding="utf-8").splitlines()
    hits = []
    for n, line in enumerate(lines, 1):
        if any(anchor in line for anchor in anchors):
            hits.append({"line": n, "text": line})
    assert hits, "no candidate source anchors: " + relative
    line_refs.append({"source_ref": ref(path), "anchors": hits})
write("candidate-line-refs.json", {"authority": "NONE", "source_only": True, "members": line_refs})

mapping = {
    "authority": "NONE", "formal_acceptance": False, "candidate_execution": "NOT_RUN",
    "original_failure_ref": verification["original_FULL_raw_ref"],
    "original_failed_nodes_preserved": verification["original_failed_nodes_preserved"],
    "cases": [
        {"name": "TestClientTranscriptIndexUpgradesExistingSessionTable/ordinary",
         "status": "BLOCKED_HISTORICAL20_MATCHING_PROGRAM_BACKUP_RESTORE_UPGRADE",
         "preserved": "original New positive call and all original row/field/count assertions",
         "source_change": "genuine historical 1..20 plus pinned pre-transcript DDL",
         "missing_resources": ["complete frozen historical20 compiler Source closure",
                              "matching historical20 installed program with actual toolchain/dependency pins",
                              "matching-program backup and isolated restore evidence",
                              "supported explicitly authorized historical20-to-current upgrade path"],
         "no_partial_parent_acceptance": True},
        {"name": "TestClientTranscriptIndexUpgradesExistingSessionTable/restore",
         "status": "SOURCE_PREPARED_NOT_EXECUTED",
         "scope": "fence primitive on genuine DDL with synthetic Project metadata",
         "preserved": "revision7/epoch3/watermark19/project/writer/upstream/null transcript/single row/repeated installation",
         "product_upgrade_acceptance": False},
        {"name": "TestClientTranscriptIndexUpgradeRollsBackWithCallerTransaction",
         "status": "SOURCE_PREPARED_NOT_EXECUTED",
         "scope": "real caller-transaction additive install and rollback",
         "preserved": "column installed inside transaction and absent after rollback",
         "product_upgrade_acceptance": False},
        {"name": "TestW09LegacyRootMigrationRevokesUnidentifiedRoot",
         "status": "SOURCE_PREPARED_NOT_PRODUCT_UPGRADE",
         "scope": "real contiguous SQL1..8 then frozen SQL9 semantics",
         "preserved": "original root insert, empty identity/revoked1/revision2 and W09 assertion emission",
         "current_New_positive_execution_removed_from_unit": True,
         "product_upgrade_acceptance": False},
        {"name": "TestClientTranscriptInstalledColumnRemovalRequiresPrebackup",
         "status": "SOURCE_PREPARED_NOT_EXECUTED",
         "scope": "explicit current-schema corruption refusal; no historical positive claim",
         "expected": "MIGRATION_PREBACKUP_REQUIRED with schema/data fingerprint unchanged"},
        {"name": "TestW09LegacyRootMigrationRejectsGappedInventory",
         "status": "SOURCE_PREPARED_NOT_EXECUTED",
         "scope": "explicit invalid ledger1,7 refusal",
         "expected": "MIGRATION_UNSUPPORTED_OR_GAPPED_VERSION with schema/data fingerprint unchanged"},
    ],
}
write("case-mapping.json", mapping)
write("source-pins.json", {
    "authority": "NONE",
    "base_refs": [x["ref"] for x in inspection["test_sources"]],
    "T5_actual_inventory_ref": inspection["T5_actual_inventory_ref"],
    "candidate_refs": construction["member_refs"],
    "diff_refs": construction["diff_refs"],
    "production_and_contract_refs": verification["source_contract_refs"] + [ref(contract)],
    "historical_DDL_ref": ref(old_sql),
    "historical_commit": "3225a31fd25969c6a5e071a2fc686cb4a835e162",
    "historical_DDL_git_blob": "9efc768f8f4cfb6ac31e1f88a78ad095877328af",
    "migration_inventory_ref": ref(Q / "migration-resources.json"),
    "historical20_resource_entry_ref": ref(Q / "historical20-resource-entry.json"),
    "lexical_utility_ref": construction["lexical_utility_ref"],
})
handoff = {
    "schema": "researchos.source-preparation-handoff.v1",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "namespace": str(Q),
    "authority": "NONE", "formal_acceptance": False,
    "status": "SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_WITH_BLOCKED_ORDINARY_UPGRADE",
    "scope": "only two original legacy fixture test files, one new test helper and exact historical SQL testdata",
    "execution": {"Python_static": "actual 0 for construct and verify; seal current invocation pending exit report",
                  "read_only_Git": "actual 0; original IO preserved",
                  "Go_AST": None, "Go": None, "gofmt": None, "compiler": None,
                  "product_native": None, "SQL": None, "model": None,
                  "private_credentials": None},
    "candidate_members": construction["member_refs"],
    "base_refs": [x["ref"] for x in inspection["test_sources"]],
    "T5_actual_inventory_ref": inspection["T5_actual_inventory_ref"],
    "minimal_diff_refs": construction["diff_refs"],
    "report_ref": ref(Q / "report.md"),
    "case_mapping_ref": ref(Q / "case-mapping.json"),
    "source_pins_ref": ref(Q / "source-pins.json"),
    "candidate_line_refs_ref": ref(Q / "candidate-line-refs.json"),
    "contract_excerpts_ref": ref(Q / "contract-excerpts.json"),
    "verification_ref": ref(Q / "verification.json"),
    "construction_ref": ref(Q / "construction.json"),
    "migration_resources_ref": ref(Q / "migration-resources.json"),
    "historical20_resource_entry_ref": ref(Q / "historical20-resource-entry.json"),
    "git_source_observation_ref": ref(Q / "git-source-observation.json"),
    "tool_io_ref": ref(Q / "tool-io.json"),
    "seal_revision_input_io_ref": ref(Q / "seal-revision-input-io.json"),
    "failure_origin_833_ref": ref(Q / "failure-origin.833.json"),
    "original_FULL_raw_ref": verification["original_FULL_raw_ref"],
    "original_failed_nodes": verification["original_failed_nodes_preserved"],
    "static": {"original_assertion_calls_preserved": 126,
               "original_Test_names_preserved": 12, "explicit_negative_tests_added": 2,
               "unrelated_original_Test_bodies_byte_equal": 9,
               "checks": verification["static_checks"],
               "limits": "Python lexical/source checks; no Go AST, syntax, compilation or runtime pass claimed"},
    "boundary": {"ordinary_upgrade": mapping["cases"][0],
                "primitive_and_SQL9": "synthetic test fixture/component only, NOT_FORMAL",
                "historical_DDL": "real Git blob bytes; no historical installed program authority",
                "Root_next": "independent Source review, then new guarded isolated integration and actual compile/component scopes",
                "do_not_accept_entire_parent_from_restore_only": True},
    "write_scope": {"new_namespace_only": True, "production_Source": 0, "Main": 0,
                    "T5": 0, "T6": 0, "canonical": 0, "release_authority_created": False},
    "failures": {"mechanical_this_branch": 1, "assigned_ordinal": 833,
                 "initial_static_verification_preceded_seal_failure": True,
                 "failed_seal_source_preserved_not_retried": True, "prior_826_preserved_not_reset": True,
                 "prior_FULL_1261_pass_25_fail_4_skip_unchanged": True},
    "manifest_exclusions": {
        "MANIFEST.json": "self fingerprint cannot be embedded",
        "postseal-tool-io.json": "later seal/write invocation IO; separately pinned in Root delivery",
    },
}
write("HANDOFF.json", handoff)
members = []
for p in sorted(Q.rglob("*")):
    if p.is_file() and p.name not in {"MANIFEST.json", "postseal-tool-io.json"}:
        members.append({"relative_path": p.relative_to(Q).as_posix(), **ref(p)})
write("MANIFEST.json", {
    "schema": "researchos.source-preparation-manifest.v1",
    "namespace": str(Q), "authority": "NONE", "formal_acceptance": False,
    "status": handoff["status"], "members": members,
    "exclusions": handoff["manifest_exclusions"],
    "candidate_members_count": 4,
    "production_Source_changes": 0,
    "Root_actual_and_independent_acceptance_pending": True,
})
for item in members:
    assert ref(item["path"])["sha256"] == item["sha256"]
    assert ref(item["path"])["bytes"] == item["bytes"]
print(json.dumps({
    "authority": "NONE", "formal_acceptance": False,
    "status": handoff["status"],
    "refs": {name: ref(Q / name) for name in [
        "HANDOFF.json", "MANIFEST.json", "report.md", "case-mapping.json",
        "source-pins.json", "contract-excerpts.json", "candidate-line-refs.json",
        "verification.json", "construction.json", "migration-resources.json",
        "historical20-resource-entry.json", "tool-io.json",
        "failure-origin.833.json", "seal-revision-input-io.json"]},
    "member_count": len(members),
    "candidate_refs": construction["member_refs"],
    "ordinary_upgrade": "BLOCKED", "all_candidate_execution": "NOT_RUN",
    "mechanical_this_branch": 1, "assigned_ordinal": 833, "prior_826_not_reset": True,
}, ensure_ascii=False))

