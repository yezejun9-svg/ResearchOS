"""Read-only hash checks over the preserved synthetic fixture; no evaluation."""
import hashlib
import json
import pathlib
import sqlite3
import sys

evidence = pathlib.Path(sys.argv[1]).resolve()
locators = json.loads((evidence / "private-locators.json").read_bytes())
database = pathlib.Path(locators["database"])
private = pathlib.Path(locators["canary_store"])
build = json.loads((evidence / "actual-build.json").read_bytes())
summary = json.loads((evidence / "current-control-native.json").read_bytes())

def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()

ref = summary["sealed"]["proof_ref"]
proof_bytes = (private / (ref["ticket"][4:] + ".bin")).read_bytes()
assert digest(proof_bytes) == ref["content_hash"]
proof = json.loads(proof_bytes)
snapshots = []
for name in ("b0", "g0", "g1"):
    descriptor = proof[name]
    parts = []
    for part in descriptor["parts"]:
        raw = (private / (part["ticket"][4:] + ".bin")).read_bytes()
        assert digest(raw) == part["hash"] and len(raw) == part["size"]
        parts.append(raw)
    joined = b"".join(parts)
    assert digest(joined) == descriptor["hash"] and len(joined) == descriptor["size"]
    snapshots.append({"stage": descriptor["stage"], "generation": descriptor["generation"], "hash": descriptor["hash"], "size": descriptor["size"], "parts": len(parts), "ordered_chunks_verified": True})

connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
code = json.loads(connection.execute("SELECT body FROM domain_objects WHERE kind='Artifact' AND json_extract(body,'$.kind')='CODE'").fetchone()[0])
code_bytes = connection.execute("SELECT bytes FROM uploaded_content WHERE storage_key=?", (code["storage_key"],)).fetchone()[0]
connection.close()
image_hash = digest(pathlib.Path(build["image_path"]).read_bytes())
# ReleaseJournal.ImageSHA256 uses bare hex; domain digests use a sha256 prefix.
journal_hash = "sha256:" + summary["native_owner"]["image_hash"].removeprefix("sha256:")
hashes = {"actual_image": image_hash, "code_artifact": code["content_hash"], "stored_code": digest(code_bytes), "build": build["binary_hash"], "journal_owner": journal_hash, "protected_owner": proof["owner"]["image_hash"]}
assert len(set(hashes.values())) == 1
result = {"image_bindings": hashes, "source_inventory_hash": build["source_provenance"]["inventory_hash"], "original_database_file_hash": digest(database.read_bytes()), "snapshots": snapshots, "proof_hash": digest(proof_bytes), "acceptance_verdict": summary["acceptance"]["verdict"], "normal_gate": summary["candidate"]["status"], "host_phase_at_seal": summary["host_phase"], "reservation_count": summary["reservation_count"], "completion_count": summary["completion_count"], "current_at_seal": summary["sealed"]["current"], "current_after_disposable_process_cleanup": False, "evaluation_reexecuted": False}
(evidence / "persisted-binding-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
