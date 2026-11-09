# r2mutants3.py - re-run of R2-M13 as a well-formed mutant (the first attempt left the
# `strings` import unused, so the CLI package stopped compiling and the gate caught a
# build break rather than the EmptyPayload mirror). Self-contained; writes its own file.
import json, os, subprocess, time

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GO = r"D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin\go.exe"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "GOTOOLCHAIN": "local", "GOENV": "off",
       "GOPATH": os.path.join(REPO, ".local", "gopath"),
       "GOCACHE": os.path.join(REPO, ".local", "gocache"), "RESEARCHOS_GO": GO}
FLAKE = ("HOST_UNREACHABLE", "UNKNOWN_STATUS:<absent>", "connection attempt failed",
         "context deadline exceeded")

MUT = {"id": "R2-M13b-empty-payload-mirror-removed-well-formed", "file": "apps/cli/cli_v2.go",
       "old": ("\tif c.payload == \"EmptyPayload\" && len(keys) > 0 {\n"
               "\t\treturn nil, \"UNEXPECTED_PAYLOAD_KEYS:\" + strings.Join(sortedKeys(keys), \",\")\n"
               "\t}"),
       "new": ("\tif false && c.payload == \"EmptyPayload\" && len(keys) > 0 {\n"
               "\t\treturn nil, \"UNEXPECTED_PAYLOAD_KEYS:\" + strings.Join(sortedKeys(keys), \",\")\n"
               "\t}"),
       "expected": ["W0503-STATUS-SENDS-HOST-STATUS", "W0503-MALFORMED-HOST-REPLY-FAILS"],
       "claim": ("the client mirrors the published schema's EmptyPayload rule for host.status "
                 "and session.get, so a stray payload key is refused locally")}


def read(p):
    return open(os.path.join(REPO, p), encoding="utf-8", errors="replace").read()


def run_check():
    r = subprocess.run([GO, "run", "./tests/runtime/cli_contract"], cwd=REPO, env=ENV,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    payload = None
    for l in reversed((r.stdout or "").strip().splitlines()):
        if l.startswith("{"):
            payload = json.loads(l)
            break
    if payload is None:
        return {"compile_error": True, "stderr": (r.stderr or "")[-1200:]}
    payload["compile_error"] = False
    payload["exit"] = r.returncode
    return payload


path = MUT["file"]
src = read(path)
rec = {"mutant": MUT["id"], "file": path, "attack_claim": MUT["claim"], "expected_rows": MUT["expected"],
       "anchor_occurrences": src.count(MUT["old"])}
if rec["anchor_occurrences"] != 1:
    rec["classification"] = "anchor-missing"
else:
    open(os.path.join(REPO, path), "w", encoding="utf-8", newline="").write(
        src.replace(MUT["old"], MUT["new"], 1))
    p = run_check()
    if p.get("compile_error"):
        rec.update({"classification": "crashed-mutant-ill-formed", "stderr": p["stderr"]})
    else:
        red = sorted(f["id"] for f in p["failures"])
        allflake = p["status"] != "PASS" and all(
            any(k in f["detail"] for k in FLAKE) for f in p["failures"])
        rec["flake_suspected"] = allflake
        if allflake:
            p = run_check()
            red = sorted(f["id"] for f in p["failures"])
            rec["after_retry"] = {"status": p["status"], "red_rows": red}
        hit = [x for x in MUT["expected"] if x in red]
        rec.update({"status": p["status"], "assertions": p["assertions"], "red_rows": red})
        rec["classification"] = ("survived" if not red else
                                 ("caught-by-card-id" if hit else "caught-by-gate-id-only"))
    subprocess.run(["git", "checkout", "--", path], cwd=REPO, env=ENV)
    rec["restored_clean"] = subprocess.run(["git", "status", "--porcelain", "--", path], cwd=REPO,
                                           env=ENV, capture_output=True, text=True).stdout.strip() == ""
    rec["restored_sha_matches_baseline"] = read(path) == src
print(rec["mutant"], rec.get("classification"), rec.get("red_rows"))
with open(os.path.join(REPO, ".local", "r2", "reviewer_mutants_r2b.json"), "w", encoding="utf-8") as f:
    json.dump({"program": "reviewer round-2 mutation matrix, R2-M13 well-formed re-run", "matrix": [rec]},
              f, ensure_ascii=False, indent=1)
