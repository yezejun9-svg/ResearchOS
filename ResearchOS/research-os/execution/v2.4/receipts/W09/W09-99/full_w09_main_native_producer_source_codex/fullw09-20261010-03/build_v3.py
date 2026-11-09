"""Rebase only the copied Source records into a fresh immutable candidate."""
import hashlib
import json
from pathlib import Path
import uuid

N = Path(__file__).resolve().parent
OLD = N.parent / "fullw09-20261010-02"
REVIEW = N.parent.parent / "full_w09_main_native_producer_independent_source_review_codex" / "review-fullw09-20261010-02"
AUTHOR = "codex:/root/w09_formal_profile_source_impl"
FILES = (
    "full_w09_runtime.source.py", "runtime-overrides.source.py",
    "full_w09_launcher.source.py", "prepare_full_w09.source.py",
    "run_full_w09.source.py", "compiler-source-blueprint.json",
)

def ref(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def replace_strings(value, mapping):
    if isinstance(value, str):
        for before, after in mapping.items():
            value = value.replace(before, after)
        return value
    if isinstance(value, list):
        return [replace_strings(item, mapping) for item in value]
    if isinstance(value, dict):
        return {key: replace_strings(item, mapping) for key, item in value.items()}
    return value

review = ref(REVIEW / "source-review-decision.json")
assert review["sha256"] == "ae1597399ee43d91eaeb96a70ecb5aeeeb0bbb1a758cfc2db17d65fc3a0e26dc"
for name in FILES:
    assert (N / name).read_bytes() == (OLD / name).read_bytes(), name

old_choice = json.loads((OLD / "source.choice.json").read_bytes())
old_contract = json.loads((OLD / "root-calling-contract.json").read_bytes())
assert old_choice["actor_id"] == old_contract["author"] == AUTHOR
old_ids = {key: item["run_id"] for key, item in old_choice["selectors"].items()}
new_ids = {key: uuid.uuid4().hex for key in old_ids}
assert len(set(new_ids.values())) == 3 and not set(old_ids.values()) & set(new_ids.values())
mapping = {str(OLD): str(N), **{old_ids[key]: new_ids[key] for key in old_ids}}

choice = replace_strings(old_choice, mapping)
assert choice["actor_id"] == AUTHOR
for key, item in choice["selectors"].items():
    assert item["run_id"] == new_ids[key]
    for root in ("receipt_root", "scratch_root", "output_root"):
        assert not Path(item[root]).exists(), (key, root)
write(N / "source.choice.json", choice)

contract = replace_strings(old_contract, mapping)
assert contract["status"] == "SOURCE_ONLY_NO_EXECUTION_GRANT"
for key, name in contract["source_file_bindings"].items():
    contract["bound_source_refs"][key] = ref(N / name)
write(N / "root-calling-contract.json", contract)

active = b"".join((N / name).read_bytes() for name in FILES + ("source.choice.json", "root-calling-contract.json"))
assert str(OLD).encode("utf-8") not in active
for old_id in old_ids.values():
    assert old_id.encode("ascii") not in active
for key, name in contract["source_file_bindings"].items():
    assert contract["bound_source_refs"][key] == ref(N / name)
assert choice["common"]["compiler_blueprint_ref"] == ref(N / "compiler-source-blueprint.json")

report = {
    "schema": "researchos.w09-fullw09-source-v3-rebase.v1",
    "source_author": AUTHOR,
    "prior_hdf_ref": ref(OLD / "HDF.json"),
    "prior_mf_ref": ref(OLD / "MF.json"),
    "prior_independent_review_ref": review,
    "prior_run_ids": old_ids,
    "new_run_ids": new_ids,
    "new_namespace": str(N),
    "unchanged_source_files": [ref(N / name) for name in FILES],
    "choice_ref": ref(N / "source.choice.json"),
    "contract_ref": ref(N / "root-calling-contract.json"),
    "no_prior_namespace_or_run_ids_in_active_source": True,
    "future_roots_absent": True,
    "actual_prepare_run": False,
    "go_native_sql_dispatcher_model_calls": 0,
    "Canon_modified": False,
}
write(N / "source-v3-rebase.json", report)
print(json.dumps({"choice": report["choice_ref"], "contract": report["contract_ref"], "new_run_ids": new_ids}, ensure_ascii=False))
