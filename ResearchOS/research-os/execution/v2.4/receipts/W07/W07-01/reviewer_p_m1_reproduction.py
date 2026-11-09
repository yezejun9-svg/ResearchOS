"""Reviewer reproduction of P-M1: delete the product guard 'incomplete page may only advance its page cursor'.

The builder's headline negative result claims this passes the entire accepted W07 suite. This script reproduces it
independently:
  1. record the pristine bytes and sha256 of internal/domain/sources.go;
  2. wrap the guard's condition in `false && (...)` so it can never fire, keeping every variable referenced so the
     file still compiles (a whole-statement deletion would not build, which is a different experiment);
  3. prove the guard is really inert by asserting the mutant text on disk;
  4. run the suite with the locked go, by absolute path, exactly as the card does;
  5. restore the pristine bytes, re-hash, and refuse to continue unless the sha matches;
  6. re-run clean.

Only internal/domain/sources.go is written, and only for the duration of one command. Nothing else is touched.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

REPO = r"D:/作品集/ResearchOS/research-os"
TARGET = os.path.join(REPO, "internal", "domain", "sources.go")
SUITE = ["test", "-count=1", "-run", "^TestW07", "./adapters/sources", "./internal/domain", "./tests/sources/live"]
ANCHOR = '} else if newCovered != oldCovered || Str(b, "opaque_cursor") == "" || b["pending_window_from"] != from || b["pending_window_to"] != to {'
REFUSAL = "incomplete page may only advance its page cursor"


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def go_bin():
    t = json.loads(open(os.path.join(REPO, "execution", "toolchains", "locked.json"), encoding="utf-8-sig").read())
    return t["tools"]["go"]["path"]


def run(go, label):
    p = subprocess.run([go] + SUITE, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=REPO, env=dict(os.environ, GOFLAGS="-mod=mod"), timeout=900)
    out = (p.stdout or "") + (p.stderr or "")
    failing = [l for l in out.splitlines()
               if re.search(r"^(--- FAIL|FAIL|panic:|# )", l) or "FAIL\t" in l]
    return {"label": label, "rc": p.returncode,
            "failing_lines": failing[:30],
            "failing_line_count": len(failing),
            "packages": [l for l in out.splitlines() if l.startswith("ok ") or l.startswith("FAIL")][:10],
            "refusal_message_still_in_source_test_output": REFUSAL in out,
            "tail": out[-400:]}


def main():
    go = go_bin()
    pristine = open(TARGET, "rb").read()
    pristine_sha = hashlib.sha256(pristine).hexdigest()
    result = {"pristine_sha256": pristine_sha, "pristine_bytes_len": len(pristine)}
    text = pristine.decode("utf-8")
    if text.count(ANCHOR) != 1:
        print(json.dumps({"ABORT": "anchor not found exactly once", "count": text.count(ANCHOR)}))
        return 1
    guard_line_no = text[:text.index(ANCHOR)].count("\n") + 1
    result["guard_condition_line"] = guard_line_no
    result["refusal_message_line"] = text[:text.index(REFUSAL)].count("\n") + 1

    mutant_text = text.replace(ANCHOR, '} else if false && (newCovered != oldCovered || Str(b, "opaque_cursor") == "" || b["pending_window_from"] != from || b["pending_window_to"] != to) {', 1)
    assert len(mutant_text) == len(text) + len("false && (") + 1  # '(' + ')' added
    assert mutant_text.count("false && (newCovered") == 1

    try:
        with open(TARGET, "wb") as f:
            f.write(mutant_text.encode("utf-8"))
        result["mutant_written_sha256"] = sha(TARGET)
        result["mutant_actually_on_disk"] = ANCHOR not in open(TARGET, encoding="utf-8").read()
        result["mutant_guard_is_inert"] = "false && (newCovered != oldCovered" in open(TARGET, encoding="utf-8").read()
        result["git_status_of_target_during_mutation"] = subprocess.run(
            ["git", "-C", REPO, "status", "--porcelain", "--untracked-files=no", "internal/domain/sources.go"],
            capture_output=True, text=True).stdout.strip()
        result["mutant_run"] = run(go, "P-M1 with the guard wrapped in false && (...)")
    finally:
        with open(TARGET, "wb") as f:
            f.write(pristine)
        restored_sha = sha(TARGET)
        result["restored_sha256"] = restored_sha
        result["restored_byte_exact"] = restored_sha == pristine_sha
        result["git_dirty_after_restore"] = subprocess.run(
            ["git", "-C", REPO, "status", "--porcelain", "--untracked-files=no"],
            capture_output=True, text=True).stdout.strip()

    if result["restored_byte_exact"]:
        result["clean_recheck"] = run(go, "clean re-run after byte-exact restore")
    else:
        result["ABORT"] = "restore did not match; the clean re-run was NOT executed"
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
