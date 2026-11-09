import ast,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent
old=(O/"checkpoint_w09_v7.atomic.py").read_bytes()
assert hashlib.sha256(old).hexdigest()=="c2ea2582b501b6f82e3a0cd7a3842e31b39152cb75455ec6a98d328d9d66750d"
text=old.decode("utf-8")
text=text.replace('IDENTITY = R / "execution/project_identity.json"','''IDENTITY = R / "execution/project_identity.json"
OLD_SCOPE = R / "execution/v2.4/receipts/W09/W09-99/integration_codex/w09c19-root-scope-1791524400000/scope-registration.root.json"
OLD_SCOPE_REF = {"path": str(OLD_SCOPE.resolve()),
    "sha256": "17b5ebc80477f6ed9012eb751758a8ef9724956cd5f999ee3dd65f37cfa100f7", "bytes": 4891}''')
start=text.index("def verify(ref):")
end=text.index("\ndef save(",start)
text=text[:start]+'''def read_ref(ref):
    assert isinstance(ref, dict) and set(ref) == {"path", "sha256", "bytes"}, "REF_FIELDS"
    assert Path(ref["path"]).is_absolute() and type(ref["bytes"]) is int, "REF_TYPES"
    assert 0 <= ref["bytes"] <= 256 * 1024 * 1024, "REF_SIZE"
    assert isinstance(ref["sha256"], str) and len(ref["sha256"]) == 64
    assert all(c in "0123456789abcdef" for c in ref["sha256"]), "REF_HASH"
    p = Path(ref["path"]).resolve(strict=True)
    assert str(p) == ref["path"], "REF_CANONICAL_PATH"
    with p.open("rb") as f:
        raw = f.read(ref["bytes"] + 1)
    assert len(raw) == ref["bytes"] and hashlib.sha256(raw).hexdigest() == ref["sha256"], "REF_PIN"
    return raw

def verify(ref):
    read_ref(ref)
    return ref
''' + text[end:]
text=text.replace("def transform(c, o, facts, fr, old_c, old_o):",
                  "def transform(c, o, facts, fr, old_c, old_o, scope_object, old_scope_object):")
anchor='    c["workers"][i] = copy.deepcopy(scope["worker"])\n'
insert='''    owner_mutable = {"scope_ref", "source_handoff_ref", "source_manifest_ref",
                     "independent_source_review_ref", "independent_source_manifest_ref",
                     "source_paths", "worktree_root", "fixed_write_roots"}
    worker_mutable = {"worktree", "scope_ref", "independent_source_review_ref"}
    new_owner, new_worker = scope["owner_subtask"], scope["worker"]
    assert set(new_owner) == set(old_owner) and set(new_worker) == set(old_worker), "OWNER_WORKER_FIELDS"
    assert all(new_owner[k] == old_owner[k] for k in old_owner if k not in owner_mutable), "OWNER_PROTECTED_FIELDS"
    assert all(new_worker[k] == old_worker[k] for k in old_worker if k not in worker_mutable), "WORKER_PROTECTED_FIELDS"
    assert new_worker["worktree"] == new_owner["worktree_root"], "WORKER_OWNER_ROOT"
    assert new_worker["independent_source_review_ref"] == new_owner["independent_source_review_ref"]
    candidate = Path(new_owner["worktree_root"]).resolve()
    expected_candidate = (R / ".local/worktrees/w09c19v7-1a11f30").resolve()
    assert candidate == expected_candidate, "FIXED_V7_CANDIDATE"
    fresh = {
        "candidate": str(R / ".local/worktrees/w09c19v7-1a11f30"),
        "isolation_receipt": str(R / "execution/v2.4/receipts/W09/W09-99/integration_codex/w09c19v7-isolation-1a11f30"),
        "producer_receipt": str(R / "execution/v2.4/receipts/W09/W09-99/integration_codex/w09c19v7-producer-1a11f30"),
        "prepare_environment": str(R / ".local/w09c19v7-isolation-env-1a11f30"),
        "producer_environment": str(R / ".local/w09c19v7-producer-env-1a11f30"),
    }
    assert all(Path(new_owner["fixed_write_roots"][k]).resolve() == Path(v).resolve()
               for k, v in fresh.items()), "FIXED_V7_WRITE_ROOTS"
    relative = ["internal/domain/domain_test.go", "internal/domain/retrieval_test.go",
                "ops/ci/retrieval.py", "internal/domain/w09_evidence_export_test.go",
                "ops/ci/w09_formal_router.py", "ops/ci/w09_evidence_closure.py"]
    assert len(new_owner["source_paths"]) == len(relative) and [
        Path(p).resolve() for p in new_owner["source_paths"]] == [
        candidate / p for p in relative], "SIX_FIXED_SOURCE_PATHS"
    for key in ("source_handoff_ref", "source_manifest_ref",
                "independent_source_review_ref", "independent_source_manifest_ref"):
        assert new_owner[key] == scope_object[key], "SCOPE_SOURCE_REVIEW_REF"
    assert scope_object["candidate_root"] == new_owner["worktree_root"], "SCOPE_CANDIDATE"
    assert scope_object["permitted_candidate_source_paths"] == new_owner["source_paths"], "SCOPE_SIX_SOURCE_PATHS"
    assert scope_object["fixed_write_roots"] == new_owner["fixed_write_roots"], "SCOPE_FIVE_WRITE_ROOTS"
    allowed_scope_changes = {"candidate_root", "source_handoff_ref", "source_manifest_ref",
        "independent_source_review_ref", "independent_source_manifest_ref",
        "permitted_candidate_source_paths", "fixed_write_roots"}
    assert set(scope_object) == set(old_scope_object), "SCOPE_FIELDS"
    assert all(scope_object[k] == old_scope_object[k] for k in old_scope_object
               if k not in allowed_scope_changes), "SCOPE_PROTECTED_FIELDS"
    assert scope_object["schema"] == "researchos.root-w09-c19-isolated-producer-scope.v1"
    assert scope_object["executor"] == scope_object["issued_by"] == "codex:/root"
    assert scope_object["main_adoption_authorized_by_this_scope"] is False
    assert scope_object["formal_consumer_execution_authorized_by_this_scope"] is False
    assert scope_object["formal_acceptance"] is False and scope_object["parent_acceptance"] is False
    assert scope_object["new_external_model_call"] is False and scope_object["original_trial_unchanged"] is True
    source_pairs = {(v["handoff_ref"]["path"], v["manifest_ref"]["path"]) for v in facts["reviews"]}
    assert (new_owner["source_handoff_ref"]["path"], new_owner["source_manifest_ref"]["path"]) in source_pairs
    assert (new_owner["independent_source_review_ref"]["path"],
            new_owner["independent_source_manifest_ref"]["path"]) in source_pairs
'''
assert text.count(anchor)==1
text=text.replace(anchor,insert+anchor)
text=text.replace('facts = json.loads(Path(fr["path"]).read_bytes())','facts_raw = read_ref(fr)\n    facts = json.loads(facts_raw)')
text=text.replace('    refs_c = [pin(p) for p in CANON]\n    assert [(v["sha256"], v["bytes"]) for v in refs_c] == BEFORE\n    assert refs_c == facts["canonical_refs"]\n    old = [p.read_bytes() for p in CANON]',
'''    refs_c = [{"path": str(p.resolve()), "sha256": sha, "bytes": size}
              for p, (sha, size) in zip(CANON, BEFORE)]
    assert refs_c == facts["canonical_refs"]
    old = [read_ref(ref) for ref in refs_c]''')
text=text.replace('    gm = module(GP, GP.read_bytes())\n    tm = module(TP, TP.read_bytes())',
'''    gp_ref = {"path": str(GP.resolve()), "sha256": "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85", "bytes": 11404}
    tp_ref = {"path": str(TP.resolve()), "sha256": "094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9", "bytes": 6877}
    gm = module(GP, read_ref(gp_ref))
    tm = module(TP, read_ref(tp_ref))''')
text=text.replace('members = json.loads(Path(item["manifest_ref"]["path"]).read_bytes())["members"]',
                  'members = json.loads(read_ref(item["manifest_ref"]))["members"]')
text=text.replace('    refs.append(verify(facts["w09_scope_registration"]["scope_ref"]))',
                  '    scope_ref = verify(facts["w09_scope_registration"]["scope_ref"])\n    refs.extend([scope_ref, verify(OLD_SCOPE_REF)])')
text=text.replace('    try:\n        transaction = tm.update_pair(refs_c[:2], lambda c, o:\n            transform(c, o, facts, fr, old_c, old_o), O, "activate")',
'''    try:
        assert guard.get_buffer(fr["path"]) == facts_raw, "HELD_FACTS_BYTES"
        facts = json.loads(guard.get_buffer(fr["path"]))
        scope_object = json.loads(guard.get_buffer(scope_ref["path"]))
        old_scope_object = json.loads(guard.get_buffer(OLD_SCOPE_REF["path"]))
        transaction = tm.update_pair(refs_c[:2], lambda c, o:
            transform(c, o, facts, fr, old_c, old_o, scope_object, old_scope_object), O, "activate")''')
ast.parse(text)
p=O/"checkpoint_w09_v7.v2.atomic.py"
with p.open("xb") as f:f.write(text.encode("utf-8"))
raw=p.read_bytes()
print({"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"AST_VALID":True,"actual_executed":False})
