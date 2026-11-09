import sys
sys.dont_write_bytecode = True
import hashlib
import json
import traceback
from pathlib import Path

Q = Path(__file__).resolve().parent
REVIEW = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/legacy_migration_fixture_independent_review_codex/4ec609adce7346a9b8fe61e898a8a15e")
def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
def main():
    expected = {
        "HDF.json": ("f6fe3a4a299797ee315274941a180f8e8f58389a2352cc89f36d373e2cdc1d2f", 3407),
        "MF.json": ("8d6e16c64fc68ce802c07d38dadc782f02d273082c8f427acfd805e6c4050c2e", 17122),
    }
    refs = {}
    decoded = {}
    dest = Q / "inputs/review"
    dest.mkdir(parents=True, exist_ok=False)
    for name, (digest, length) in expected.items():
        p = REVIEW / name
        item = ref(p)
        assert item["sha256"] == digest and item["bytes"] == length, name + " pinned input differs"
        refs[name] = item
        raw = p.read_bytes()
        decoded[name] = json.loads(raw.decode("utf-8"))
        (dest / name).write_bytes(raw)
    output = {"authority": "NONE", "review_metadata_verified": True, "refs": refs,
              "HDF": decoded["HDF.json"],
              "MF_top_keys": list(decoded["MF.json"]),
              "MF_nonmembers": {k: v for k, v in decoded["MF.json"].items() if k != "members"}}
    (Q / "review-metadata-verification.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))
exit_code = 0
try:
    main()
except Exception:
    traceback.print_exc()
    exit_code = 1
finally:
    print("ROOT_PYTHON_EXIT=" + str(exit_code))
sys.exit(exit_code)

