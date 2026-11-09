import sys
sys.dont_write_bytecode = True
import difflib
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409")
PINS = {
    "internal/domain/backup_command_queue_test.go": ("8aaacf735f566374bd7ae9280812c8f00b68040c02bad7ed8d8f9f693499bfdb", 14626),
    "internal/domain/backup_host_configuration_test.go": ("c58af6fe34678c44c911906adb00a3a59445a1c7753b904f7efc1efb618e2518", 25386),
    "internal/domain/client_configuration_test.go": ("bbf66dd56a5deed70aeb11a639ff0824c95b7e7a3283e63313bda3bd8ff01298", 23696),
}

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def write_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)

def write_json(name, obj):
    write_new(OUT / name, (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

def block(text, name, following):
    start = text.index("func " + name + "(")
    stop = text.index("func " + following + "(", start)
    return start, stop, text[start:stop]

def once(text, old, new):
    if text.count(old) != 1:
        raise AssertionError("replacement cardinality: " + repr(old))
    return text.replace(old, new, 1)

base_refs = {}
source_refs = {}
patches = []
checks = []
texts = {}
for rel, (want_hash, want_bytes) in PINS.items():
    current = pin(BASE / rel)
    if current["sha256"] != want_hash or current["bytes"] != want_bytes:
        raise AssertionError("base drift: " + rel)
    base_refs[rel] = current
    texts[rel] = (BASE / rel).read_bytes().decode("utf-8")

rel = "internal/domain/backup_command_queue_test.go"
old = texts[rel]
start, stop, selected = block(old, "TestClientQueueFreshNumberedSchema", "TestClientQueueHistorical22NumberedSchema")
new_selected = once(selected, 'upgradeConfigurationRelease("../..", 23)', 'preparedUpgradeRelease("../..", 24)')
new_selected = once(new_selected, "len(sqls) != 24", "len(sqls) != 25")
new_selected = once(new_selected, "exact installed schema23 release:", "exact installed schema24 release:")
new_selected = once(new_selected, '"fresh-current23"', '"fresh-current24"')
new = old[:start] + new_selected + old[stop:]
assert new[:start] == old[:start] and new[start + len(new_selected):] == old[stop:]
assert "applied != count" in new_selected and "count != want" in new_selected and "version != want" in new_selected
assert 'for _, table := range clientQueueTables' in new_selected
assert 'os.ReadFile("../../migrations/sqlite/0022_client_command_queue.sql")' in new_selected
texts[rel] = (old, new)
checks.append({"check": "current_queue_exact_release24_and_numbered1_through24", "result": True, "release_function": "preparedUpgradeRelease", "release_version": 24, "pinned_sql_count_including_additive": 25})
checks.append({"check": "queue_contiguous_count_max_empty_queue_and_SQL22_assertions_preserved", "result": True})
checks.append({"check": "entire_historical22_queue_test_and_other_queue_source_byte_identical", "result": True, "unchanged_suffix_sha256": hashlib.sha256(old[stop:].encode("utf-8")).hexdigest()})

rel = "internal/domain/client_configuration_test.go"
old = texts[rel]
parent_start = old.index("func TestClientConfigurationFreshAndNumberedMigration(")
start = old.index('\tt.Run("actual_Service_New",', parent_start)
stop = old.index("\nfunc ", start)
selected = old[start:stop]
new_selected = once(selected, "e != nil || version != 23", "e != nil || version != 24")
new = old[:start] + new_selected + old[stop:]
assert new[:start] == old[:start] and new[start + len(new_selected):] == old[stop:]
texts[rel] = (old, new)
checks.append({"check": "actual_Service_New_only_changes_current_expected_version23_to24", "result": True})
checks.append({"check": "both_numbered22_to23_additive_branches_and_all_other_configuration_source_byte_identical", "result": True, "unchanged_prefix_sha256": hashlib.sha256(old[:start].encode("utf-8")).hexdigest(), "unchanged_suffix_sha256": hashlib.sha256(old[stop:].encode("utf-8")).hexdigest()})

rel = "internal/domain/backup_host_configuration_test.go"
old = texts[rel]
start, stop, selected = block(old, "TestHandlerRejectedSessionPublicBackupReplay", "TestHandlerRejectedOriginalProofBackupTampering")
nl = "\r\n" if "\r\n" in selected else "\n"
original_prefix = "func TestHandlerRejectedSessionPublicBackupReplay(t *testing.T) {" + nl + "\tf := setup(t)" + nl
assert selected.startswith(original_prefix)
original_body = selected[len(original_prefix):]
body = once(original_body, "SupportedMigrations: upgradeVersions(23)", "SupportedMigrations: upgradeVersions(version)")
assert "handlerRejectedSessionPublicBackupReplay" not in old
wrapper = """func TestHandlerRejectedSessionPublicBackupReplay(t *testing.T) {
	t.Run("current24", func(t *testing.T) {
		handlerRejectedSessionPublicBackupReplay(t, setup(t), 24)
	})
	t.Run("historical23", func(t *testing.T) {
		root := configurationUpgradeReleaseFixture(t, 23)
		f := setupWithConstructor(t, func(db *sql.DB, _, _ string) (*Service, error) {
			return New(db, filepath.Join(root, "spec/v2.0/contracts"), filepath.Join(root, "migrations/sqlite/0002_domain.sql"))
		})
		handlerRejectedSessionPublicBackupReplay(t, f, 23)
	})
}

func handlerRejectedSessionPublicBackupReplay(t *testing.T, f *fixture, version int) {
	t.Helper()
""".replace("\n", nl)
new_selected = wrapper + body
new = old[:start] + new_selected + old[stop:]
assert new[:start] == old[:start] and new[start + len(new_selected):] == old[stop:]
assert body.replace("SupportedMigrations: upgradeVersions(version)", "SupportedMigrations: upgradeVersions(23)", 1) == original_body
assert '\t"database/sql"' in old and '\t"path/filepath"' in old
for retained in [
    "revision <= 201", 'len(Arr(status.Result, "model_configurations")) != 100',
    "historicalConfigs != 201", 'deref(r.Status) != "REJECTED"',
    'deref(r.ErrorCode) != "NOT_FOUND"', 'foreign.CommandID, foreign.SessionID, foreign.ProjectID',
    'string(Bytes(response)) != original', "!replay", "rebound == root",
    'filepath.Join(t.TempDir(), "rebackup")', "validateBackupHostConfiguration(f.db)",
]:
    assert retained in body, retained
texts[rel] = (old, new)
checks.append({"check": "PublicReplay_current24_and_real_New_over_frozen_numbered23_subcases", "result": True, "parent_test": "TestHandlerRejectedSessionPublicBackupReplay", "subcases": ["current24", "historical23"]})
checks.append({"check": "PublicReplay_complete_original_body_byte_identical_except_explicit_supported_version_parameter", "result": True, "original_body_sha256": hashlib.sha256(original_body.encode("utf-8")).hexdigest(), "roundtrip_restored_body_sha256": hashlib.sha256(body.replace("SupportedMigrations: upgradeVersions(version)", "SupportedMigrations: upgradeVersions(23)", 1).encode("utf-8")).hexdigest()})
checks.append({"check": "PublicReplay_201_config_100_status_unknown_foreign_rejected_raw_session_workspace_and_rebackup_assertions_preserved", "result": True})
checks.append({"check": "all_other_host_configuration_source_byte_identical", "result": True, "unchanged_prefix_sha256": hashlib.sha256(old[:start].encode("utf-8")).hexdigest(), "unchanged_suffix_sha256": hashlib.sha256(old[stop:].encode("utf-8")).hexdigest()})

for rel, (old, new) in texts.items():
    raw = new.encode("utf-8")
    assert old.count("\r\n") == old.count("\n") if "\r\n" in old else "\r\n" not in new
    path = OUT / "candidate-root" / rel
    write_new(path, raw)
    source_refs[rel] = pin(path)
    source_refs[rel]["base_ref"] = base_refs[rel]
    patches.extend(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True), fromfile="base/" + rel, tofile="candidate-root/" + rel))
    if pin(BASE / rel) != base_refs[rel]:
        raise AssertionError("base changed during construction: " + rel)

candidate_files = sorted(str(p.relative_to(OUT / "candidate-root")).replace("\\", "/") for p in (OUT / "candidate-root").rglob("*") if p.is_file())
assert candidate_files == sorted(PINS)
write_new(OUT / "revision.patch", "".join(patches).encode("utf-8"))
write_json("base-refs.json", base_refs)
write_json("source-refs.json", source_refs)
write_json("static-evidence.json", {
    "schema": "researchos.schema24-current-fixture-source-static.v1",
    "kind": "SOURCE_TEXT_STATIC_ONLY",
    "checks": checks,
    "source_file_count": 3,
    "source_input_drift_count": 0,
    "candidate_files": candidate_files,
    "execution_authority": "NONE",
    "actual_author_execution": {"Go": False, "SQL": False, "native": False, "Git": False, "provider": False, "original_database": False, "Main_write": False, "T3_write": False, "canonical_write": False},
    "limits": [
        "No Go format/build/test has run in the Source author task.",
        "historical23 covers current public API initialized by real New over fixed numbered23 SQL and additive inventory; it is not a frozen historical program/native acceptance result.",
        "Root composition and actual validation plus independent review remain required."
    ],
})
print(json.dumps({"namespace": str(OUT), "source_count": len(source_refs), "source_refs": source_refs, "static_checks": len(checks), "base_drift": 0, "execution_authority": "NONE"}, ensure_ascii=False))

