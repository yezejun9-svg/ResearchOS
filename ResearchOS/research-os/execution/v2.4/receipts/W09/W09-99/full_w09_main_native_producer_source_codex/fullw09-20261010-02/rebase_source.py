"""Rebase only the copied Source package; no prepare, producer or native run."""
import hashlib
import json
from pathlib import Path
import uuid

N = Path(__file__).resolve().parent
R = Path("D:/作品集/ResearchOS/research-os")
OLD = "fullw09-20261009-01"
NEW = N.name
OLD_RUNTIME_SHA = "49b6aedb3028225445991acc76b0229278bb0257ac2fee75baa2fa538b8d1849"
AUTHOR = "codex:/root/w09_formal_profile_source_impl"
SESSION = "01a12011-7d41-7991-a01c-de2d71701ff7"

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

runtime = N / "full_w09_runtime.source.py"
runtime_sha = pin(runtime)["sha256"]
for name in ("full_w09_launcher.source.py", "prepare_full_w09.source.py", "run_full_w09.source.py"):
    path = N / name
    value = path.read_text(encoding="utf-8")
    assert value.count(OLD_RUNTIME_SHA) == 1
    path.write_text(value.replace(OLD_RUNTIME_SHA, runtime_sha), encoding="utf-8", newline="")

choice_path = N / "source.choice.json"
choice = json.loads(choice_path.read_bytes())
assert choice["actor_id"] == "codex:/root/native_temp_independent_review"
choice["actor_id"] = AUTHOR
choice["common"]["compiler_blueprint_ref"] = pin(N / "compiler-source-blueprint.json")
old_ids = {}
new_ids = {}
for key, row in choice["selectors"].items():
    old_ids[key] = row["run_id"]
    run_id = uuid.uuid4().hex
    assert run_id != old_ids[key]
    new_ids[key] = run_id
    row["run_id"] = run_id
    row["receipt_root"] = str(N / ("actual-" + key + "-" + run_id))
    row["scratch_root"] = str(R / ".local" / ("w09-full-" + key + "-" + run_id))
    row["output_root"] = str(R / "execution/receipts/W09/retrieval" / ("run-" + run_id))
dump(choice_path, choice)

contract_path = N / "root-calling-contract.json"
contract = json.loads(contract_path.read_bytes())
assert contract["author"] == contract["source_actor"] == "codex:/root/native_temp_independent_review"
contract["author"] = contract["source_actor"] = AUTHOR
contract["source_thread_id"] = SESSION
contract["bound_source_refs"] = {key: pin(N / name) for key, name in contract["source_file_bindings"].items()}
contract["future_argv"]["prepare"][6] = str(N / "prepare_full_w09.source.py")
contract["future_argv"]["run"][6] = str(N / "run_full_w09.source.py")
assert set(contract["source_file_bindings"]) == set(contract["bound_source_refs"])
dump(contract_path, contract)

result = {"schema": "researchos.fullw09-v2-source-rebase.v1", "source_author": AUTHOR,
          "prior_source_author": "codex:/root/native_temp_independent_review",
          "prior_v1_namespace": str(N.parent / OLD), "new_namespace": str(N),
          "prior_run_ids": old_ids, "new_run_ids": new_ids,
          "runtime_ref": pin(runtime), "choice_ref": pin(choice_path), "contract_ref": pin(contract_path),
          "prepare_ref": pin(N / "prepare_full_w09.source.py"), "run_ref": pin(N / "run_full_w09.source.py"),
          "launcher_ref": pin(N / "full_w09_launcher.source.py"), "blueprint_ref": pin(N / "compiler-source-blueprint.json"),
          "actual_prepare_run": False, "native_calls": 0, "Canon_modified": False}
with (N / "source-rebase.json").open("x", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2, ensure_ascii=False)
    stream.write("\n")
print(json.dumps({"rebase_ref": pin(N / "source-rebase.json"), "new_run_ids": new_ids}, ensure_ascii=False))
