import hashlib
import json
import pathlib
from datetime import datetime, timezone

here = pathlib.Path(__file__).resolve().parent


def identity(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def main():
    supplement = here / "FINAL-supplement.json"
    data = json.loads(supplement.read_text(encoding="utf-8"))
    assert data["source_clean"] is True
    result = json.loads((here / "053-write-supplement/exit.json").read_text(encoding="utf-8"))
    assert result["exit"] == 0
    seal = {"schema": "researchos.source43-post-final-supplement-seal.v1", "created_utc": datetime.now(timezone.utc).isoformat(),
            "supplement": identity(supplement), "supplement_writer_053": {
                name: identity(here / "053-write-supplement" / name)
                for name in ("recipe.json", "invocation.json", "stdout.raw", "stderr.raw", "exit.json")},
            "supplement_writer_exit": result,
            "seal_writer_054_prepared": {name: identity(here / "054-seal-supplement" / name) for name in ("recipe.json", "invocation.json")},
            "self_result_boundary": "054 exit/stdout/stderr are deliberately outside this seal to avoid recursive hashing; inspect 054 receipt directly."}
    path = here / "FINAL-supplement-seal.json"
    path.write_text(json.dumps(seal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"supplement_sha256": identity(supplement)["sha256"], "supplement_bytes": identity(supplement)["bytes"],
                      "seal_sha256": identity(path)["sha256"], "seal_bytes": identity(path)["bytes"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
