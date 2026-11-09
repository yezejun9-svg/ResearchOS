import sys
sys.dont_write_bytecode = True
import ast, hashlib, json, types
from pathlib import Path

R = Path("D:/作品集/ResearchOS/research-os")
B = R/"execution/v2.4/receipts/W05/W05-99"
N = Path(__file__).resolve().parent
OLD = B/"integration_codex/history20-five-parent-sparse-root-source-h20v-1a11ebe661670a1a49d0ea22092604a"
CAND = B/"historical20_upgrade_test_revision_codex/h20r2-1a11ee4f162766098eda3028b0679f2"
ISO = B/"integration_codex/history20-r2-five-parent-isolation-root-1791521480000"
OUT = B/"integration_codex/history20-r2-five-parent-target-root-1791521480000"
WORK = R/".local/worktrees/h20r2s-1791521480000"
ENV = R/".local/history20-r2-five-parent-env-1791521480000"
GP = B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"

def pin(p):
    p = Path(p).resolve()
    raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
def verify(p, sha, size):
    result = pin(p)
    assert result["sha256"] == sha.removeprefix("sha256:") and result["bytes"] == size, str(p)
    return result
def refcheck(ref):
    return verify(ref["path"], ref["sha256"], ref["bytes"])
def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode("utf-8")
    with (N/name).open("xb") as stream:
        stream.write(raw)
    return pin(N/name)
def entries(m):
    v = m["members"]
    return list(v.values()) if isinstance(v, dict) else v
def module(p, raw):
    m = types.ModuleType("root_h20r2_source_guard")
    m.__file__ = str(p)
    sys.modules[m.__name__] = m
    exec(compile(raw, str(p), "exec"), m.__dict__)
    return m
def rewrite(name, raw, changes):
    text = raw.decode("utf-8")
    records = []
    for old, new, expected in changes:
        assert text.count(old) == expected, (name, old, text.count(old), expected)
        text = text.replace(old, new)
        records.append(dict(old=old, new=new, count=expected))
    reverse = text
    for item in reversed(records):
        assert reverse.count(item["new"]) == item["count"], (name, "inverse collision", item)
        reverse = reverse.replace(item["new"], item["old"])
    assert reverse.encode("utf-8") == raw
    ast.parse(text)
    with (N/name).open("xb") as stream:
        stream.write(text.encode("utf-8"))
    return dict(name=name, base_ref=pin(OLD/name), new_ref=pin(N/name), replacements=records, exact_inverse=True)

assert len(sys.argv) == 7, "REVIEW_HDF_PATH SHA BYTES REVIEW_MF_PATH SHA BYTES"
rh = verify(sys.argv[1], sys.argv[2], int(sys.argv[3]))
rm = verify(sys.argv[4], sys.argv[5], int(sys.argv[6]))
assert Path(rh["path"]).parent == Path(rm["path"]).parent
assert Path(rh["path"]).resolve().is_relative_to(B)
for p in (ISO, OUT, WORK, ENV):
    assert not p.exists(), "fresh path already exists: "+str(p)
assert verify(GP, "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85", 11404)
assert verify(CAND/"HDF.json", "7e6b01bb9bf1adaa6d92cfb3e0b9e558da4d300abe76be4258c1d6984abafb19", 6217)
assert verify(CAND/"MF.json", "c80d8a5c51bdc4a32eae36510f95af0ee0d9ed09705abb56988713002e55b396", 7132)
assert verify(OLD/"HDF.json", "fcc6de7fc2696474764cf8c2b27f9cfcd7942179bf5cdf6a589cf13ac45f4c76", 3189)
assert verify(OLD/"MF.json", "39e8c747edc6f4f323f1842190edfe32b04ea45cacc3ebd73b7d1443882a0b1b", 4962)
refs = [pin(__file__), pin(GP), rh, rm, pin(CAND/"HDF.json"), pin(CAND/"MF.json"), pin(OLD/"HDF.json"), pin(OLD/"MF.json")]
for manifest in (CAND/"MF.json", OLD/"MF.json", Path(rm["path"])):
    refs += [refcheck(ref) for ref in entries(json.loads(manifest.read_bytes()))]
canon = [R/"execution/v2.4"/(v+".json") for v in ("checkpoint","path_ownership","step_state","commands")]
refs += [pin(p) for p in canon] + [pin(R/"execution/project_identity.json")]
refs += [pin(Path(sys.executable))]
for m in list(sys.modules.values()):
    for attr in ("__file__", "__cached__"):
        p = getattr(m, attr, None)
        if p and Path(p).is_file():
            refs.append(pin(p))
refs = list({str(Path(v["path"]).resolve()).casefold():v for v in refs}.values())
gm = module(GP, GP.read_bytes())
guard = gm.SourceReadGuard(per_file_cap=128*1024*1024, total_cap=512*1024*1024)
guard.acquire(refs)
candidate = {}
checks = []
try:
    source_handoff = json.loads(guard.get_buffer(str(CAND/"HDF.json")))
    candidate_root = CAND/"candidate-root"
    for value in source_handoff["candidate_files"]:
        p = Path(value["path"]).resolve()
        relative = p.relative_to(candidate_root.resolve()).as_posix()
        candidate[relative] = refcheck(value)
    assert len(candidate) == 5
    assert candidate["internal/domain/backup_history20_upgrade_test.go"]["sha256"] == "914792b2e903f15026ea0a6d0652e1db5401076dc24fc9132bebaad3fa930f2f"
    old_choice_ref = verify(OLD/"source.integration.choice.json", "a0674a8e54bb169ec190aec9cc0ddac80f088a43bd763c40f7a21fed4f062cd3", 27254)
    old_choice = json.loads(guard.get_buffer(old_choice_ref["path"]))
    choice = json.loads(json.dumps(old_choice))
    items = [v for v in choice["source_components"] if v["component"] == "H20R1"]
    assert len(items) == 1
    item = items[0]
    prior_item = json.loads(json.dumps(item))
    item.update(component="H20R2", candidate_namespace=CAND.relative_to(B).as_posix(),
                source_handoff=pin(CAND/"HDF.json"), source_manifest=pin(CAND/"MF.json"),
                independent_handoff=rh, independent_manifest=rm)
    for key, value in (("fresh_worktree",WORK), ("fresh_isolation_output",ISO),
                       ("fresh_validation_output",OUT), ("fresh_environment",ENV)):
        choice[key] = str(value)
    assert choice["expected_source_count"] == 61 and choice["expected_terminal_count"] == 9
    assert choice["exact_parent_names"] == old_choice["exact_parent_names"]
    assert choice["expected_terminal_names"] == old_choice["expected_terminal_names"]
    assert choice["source_preserved_parent_names"] == old_choice["source_preserved_parent_names"]
    restored_choice = json.loads(json.dumps(choice))
    restored_choice["source_components"][choice["source_components"].index(item)] = prior_item
    for key in ("fresh_worktree","fresh_isolation_output","fresh_validation_output","fresh_environment"):
        restored_choice[key] = old_choice[key]
    assert restored_choice == old_choice
    choice_ref = save("source.integration.choice.json", choice)
    paths = [
        ("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/history20-five-parent-sparse-isolation-root-h20v-1a11ebe6616", ISO.as_posix()),
        ("D:/作品集/ResearchOS/research-os/.local/worktrees/h20s-1a11ebe6616", WORK.as_posix())
    ]
    prep_changes = [(a,b,1) for a,b in paths]
    val_changes = [(paths[0][0],paths[0][1],1), (paths[1][0],paths[1][1],1),
        ("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/history20-five-parent-sparse-target-root-h20v-1a11ebe6616", OUT.as_posix(),1),
        ("D:/作品集/ResearchOS/research-os/.local/history20-five-parent-env-1a11ebe6616", ENV.as_posix(),1),
        ('"H20R1"', '"H20R2"', 2)]
    patches = [
        rewrite("prepare_history20_five_parent.actual_owned.py",
                guard.get_buffer(str(OLD/"prepare_history20_five_parent.actual_owned.py")), prep_changes),
        rewrite("validate_history20_five_parent.actual_owned.py",
                guard.get_buffer(str(OLD/"validate_history20_five_parent.actual_owned.py")), val_changes)
    ]
    save("exact-replacements.json", dict(callers=patches, choice_semantic_inverse=True,
        prior_h20_component=prior_item, new_h20_component=item,
        exact_prior_choice_ref=old_choice_ref, allowed_changed_choice_fields=[
        "source_components[H20R1]","fresh_worktree","fresh_isolation_output","fresh_validation_output","fresh_environment"]))
    save("input-pins.json", refs)
    checks = ["exact source and manifest pins", "full caller inverse", "choice full semantic inverse",
        "four fresh paths absent", "61 raw Source composition preserved", "5 parent names unchanged",
        "9 terminal names unchanged", "all prior other components unchanged",
        "R2 candidate test exact pin", "canonical sources guard held", "AST parses",
        "dynamic checkpoint and isolation ready pin arguments retained",
        "all owned process and finally logic byte equal after inverse",
        "ops CLI overlay is source-only, not a CLI execution claim"]
    save("static-controls.json",dict(status="PASS_SOURCE_ONLY", checks=checks, check_count=len(checks),
        construction_Git_Go_SQL_native_API_private_model=False, formal_acceptance=False,
        failure_counter_next_observed=917, ordinal_reservation=False))
finally:
    cleanup = guard.close()
    save("sourceguard.final.json", cleanup)
    assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"] == 0
save("README.json",dict(schema="researchos.history20-r2-root-caller-instructions.v1",
    status="SOURCE_PREPARED_PENDING_INDEPENDENT_CALLER_REVIEW",
    prepare_argv=["CHECKPOINT_SHA256","CHECKPOINT_BYTES","CHECKPOINT_REVISION"],
    validate_argv=["CHOICE_SHA256","CHOICE_BYTES","CHECKPOINT_SHA256","CHECKPOINT_BYTES","CHECKPOINT_REVISION","ISOLATION_READY_SHA256","ISOLATION_READY_BYTES"],
    worktree=str(WORK),isolation_output=str(ISO),validation_output=str(OUT),environment=str(ENV),
    expected_sources=61,expected_parents=5,expected_terminals=9,
    old914_immutable=True, Root_actual_only=True, Main_adopted=False,
    full20_to24="OPEN", formal_acceptance=False))
members = [pin(p) for p in sorted(N.iterdir()) if p.is_file()]
mf = save("MF.json",dict(schema="researchos.source-packet-manifest.v1",members=members,member_count=len(members),excludes=["HDF.json","MF.json","postseal-original-root-tool-io.json"]))
hdf = save("HDF.json",dict(schema="researchos.history20-r2-five-parent-root-caller-source-handoff.v1",
    status="SOURCE_PREPARED_PENDING_NONAUTHOR_CALLER_REVIEW_AND_ROOT_ACTUAL",
    manifest_ref=mf,manifest_member_count=len(members),
    prepare_ref=pin(N/"prepare_history20_five_parent.actual_owned.py"),
    validate_ref=pin(N/"validate_history20_five_parent.actual_owned.py"),choice_ref=choice_ref,
    h20r2_source_handoff_ref=pin(CAND/"HDF.json"),h20r2_independent_handoff_ref=rh,
    old_caller_handoff_ref=pin(OLD/"HDF.json"),source_count=61,expected_parent_count=5,
    expected_terminal_count=9,Main_canonical_unchanged=True,Main_adopted=False,
    actual_Git_Go_SQL_native_API_private_model=False,formal_acceptance=False,
    overall20_to24="OPEN",STOP=True))
print(json.dumps(dict(handoff_ref=hdf,manifest_ref=mf,choice_ref=choice_ref,static_check_count=len(checks),native_exit=None,Source_only=True),ensure_ascii=False))

