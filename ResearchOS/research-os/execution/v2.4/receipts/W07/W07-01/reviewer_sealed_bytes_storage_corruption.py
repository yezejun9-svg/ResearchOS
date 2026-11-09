"""Reviewer mutant, take 2: does anything notice when the SEALED BYTES stop matching the reported digest?

Two stages, both on a COPY of a fresh run's database (the real run dir is never touched):

  stage A - plain UPDATE of uploaded_content.bytes. Expected: refused by the schema itself
            (migrations/sqlite/0002_domain.sql:41-42 triggers content_immutable / content_no_delete raise
            ABORT 'sealed bytes'). That is a product-level protection this card inherits, not one it built.
  stage B - drop those two triggers first, THEN flip one byte of the stored blob, leaving content_hash and
            sealed exactly as they were. This is the storage-corrupting mutant the builder disclosed as never
            having been run. The question is whether the check's own recompute row catches it.
"""
import io
import json
import os
import shutil
import sqlite3
import sys
import importlib.util

REPO = r"D:/作品集/ResearchOS/research-os"
RUN_DIR = sys.argv[1]
KIND = sys.argv[2] if len(sys.argv) > 2 else "PAPER"

spec = importlib.util.spec_from_file_location("w0701_check", os.path.join(REPO, "tests", "sources", "check", "main.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def main():
    out = {}
    root = os.path.join(REPO, RUN_DIR) if not os.path.isabs(RUN_DIR) else RUN_DIR
    rep_path = os.path.join(root, KIND.lower() + "-1", "report-" + KIND + ".json")
    rep = json.loads(io.open(rep_path, encoding="utf-8").read())
    db_abs = rep["db_path"] if os.path.isabs(rep["db_path"]) else os.path.join(REPO, rep["db_path"])
    items = rep["items"]

    # ---- what the check's recompute actually joins on, on the pristine database
    con = sqlite3.connect("file:" + db_abs.replace("\\", "/") + "?mode=ro", uri=True)
    join = []
    for it in items:
        ref = it.get("artifact_ref") or {}
        art_id = ref.get("id") if isinstance(ref, dict) else ref
        obj = con.execute("SELECT body FROM domain_objects WHERE id=?", (art_id,)).fetchone()
        storage_key = json.loads(obj[0]).get("storage_key") if obj else None
        by_id = con.execute("SELECT 1 FROM uploaded_content WHERE storage_key=?", (art_id,)).fetchone()
        by_sk = con.execute("SELECT sealed, content_hash, length(bytes) FROM uploaded_content WHERE storage_key=?",
                            (storage_key,)).fetchone()
        by_hash = con.execute("SELECT storage_key FROM uploaded_content WHERE content_hash=?",
                              (it["body_sha256"],)).fetchone()
        join.append({"artifact_ref_id": str(art_id), "artifact_storage_key": storage_key,
                     "check_primary_lookup_by_artifact_id_finds_row": bool(by_id),
                     "row_by_artifact_storage_key": list(by_sk) if by_sk else None,
                     "lookup_by_claimed_content_hash_finds_row": bool(by_hash),
                     "claimed": it["body_sha256"]})
    trig = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='trigger'")]
    n_uc = con.execute("SELECT COUNT(*), SUM(sealed) FROM uploaded_content").fetchone()
    con.close()
    out["join_resolution"] = {"per_item": join, "triggers_present": trig,
                             "uploaded_content_rows_and_sealed": list(n_uc)}
    out["pristine_recompute"] = mod.sealed_matches(db_abs, items)
    out["pristine_verdict"] = ("PASSES" if not out["pristine_recompute"]["mismatches"]
                              and not out["pristine_recompute"]["missing"] else "FAILS")

    copy = os.path.join(REPO, ".local", "reviewer_w0701_sealedcorrupt_%s.sqlite" % KIND)
    if os.path.exists(copy):
        os.remove(copy)
    shutil.copyfile(db_abs, copy)
    for suffix in ("-wal", "-shm"):
        if os.path.exists(db_abs + suffix):
            shutil.copyfile(db_abs + suffix, copy + suffix)

    # ---- stage A: the schema's own refusal
    con = sqlite3.connect(copy)
    stage_a = None
    try:
        con.execute("UPDATE uploaded_content SET bytes = bytes WHERE sealed = 1 AND rowid IN "
                    "(SELECT rowid FROM uploaded_content WHERE content_hash = ?)", (items[0]["body_sha256"],))
        con.commit()
        stage_a = {"refused": False, "note": "the UPDATE was accepted, so no schema guard fired"}
    except sqlite3.IntegrityError as exc:
        stage_a = {"refused": True, "error": str(exc)}
    con.close()
    out["stage_a_plain_update_of_sealed_bytes"] = stage_a

    # ---- stage B: remove the guard, then really flip a byte
    con = sqlite3.connect(copy)
    con.execute("DROP TRIGGER IF EXISTS content_immutable")
    con.execute("DROP TRIGGER IF EXISTS content_no_delete")
    row = con.execute("SELECT storage_key, content_hash, length(bytes), sealed FROM uploaded_content "
                      "WHERE content_hash = ?", (items[0]["body_sha256"],)).fetchone()
    sk, ch, ln, sealed = row
    blob = bytearray(con.execute("SELECT bytes FROM uploaded_content WHERE storage_key=?", (sk,)).fetchone()[0])
    blob[0] = (blob[0] + 1) % 256
    con.execute("UPDATE uploaded_content SET bytes=? WHERE storage_key=?", (bytes(blob), sk))
    con.commit()
    after = con.execute("SELECT content_hash, length(bytes), sealed FROM uploaded_content WHERE storage_key=?",
                        (sk,)).fetchone()
    con.close()
    out["stage_b_mutant"] = {"dropped_triggers": ["content_immutable", "content_no_delete"],
                            "storage_key_corrupted": sk, "byte_len_before": ln, "byte_len_after": after[1],
                            "content_hash_column_untouched": after[0] == ch,
                            "sealed_flag_untouched": after[2] == sealed,
                            "first_byte_before": blob[0] - 1 % 256 if False else None}
    res = mod.sealed_matches(copy, items)
    out["stage_b_recompute_after_corruption"] = res
    out["stage_b_detector_caught_it"] = bool(res["mismatches"])
    out["stage_b_which_rows_would_be_reported_failed"] = [
        "W0701-%s-SEALED-BYTES-MATCH-THE-REPORTED-HASH" % KIND]

    # ---- falsified-value control on the PRISTINE db: a claim the store does not hold
    fake = [dict(items[0], body_sha256="sha256:" + "0" * 64)]
    out["control_falsified_claim_on_pristine_db"] = mod.sealed_matches(db_abs, fake)

    os.remove(copy)
    for suffix in ("-wal", "-shm"):
        if os.path.exists(copy + suffix):
            os.remove(copy + suffix)
    out["copy_removed"] = True
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
