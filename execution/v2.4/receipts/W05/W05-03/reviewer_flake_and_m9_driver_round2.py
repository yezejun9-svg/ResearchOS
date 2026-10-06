# r2flakecheck.py - one clean baseline run plus repeated runs of R2-M9, whose first
# classification was contaminated by the check's own loopback flake. Reports each run's
# red set so the classification rests on a run where the fixture host was reachable.
import json, os, subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GO = r"D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin\go.exe"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "GOTOOLCHAIN": "local", "GOENV": "off",
       "GOPATH": os.path.join(REPO, ".local", "gopath"),
       "GOCACHE": os.path.join(REPO, ".local", "gocache"), "RESEARCHOS_GO": GO}
M9OLD = '\tcode, stdout, stderr, err := installed(exe, "version")'
M9NEW = '\texe = filepath.Join(*repo, ".local", "w0503_cli.exe")\n' + M9OLD
PATH = "ops/cli_distribution/main.go"


def read(p):
    return open(os.path.join(REPO, p), encoding="utf-8", errors="replace").read()


def run_check():
    r = subprocess.run([GO, "run", "./tests/runtime/cli_contract"], cwd=REPO, env=ENV,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    for l in reversed((r.stdout or "").strip().splitlines()):
        if l.startswith("{"):
            d = json.loads(l)
            d["exit"] = r.returncode
            return d
    return {"status": "NO_JSON", "failures": [{"id": "COMPILE", "detail": (r.stderr or "")[-800:]}],
            "assertions": 0, "exit": r.returncode}


res = {"clean_baseline": None, "m9_runs": []}
b = run_check()
res["clean_baseline"] = {"status": b["status"], "assertions": b.get("assertions"),
                         "red": sorted(f["id"] for f in b.get("failures", []))}
print("clean baseline:", res["clean_baseline"])

src = read(PATH)
open(os.path.join(REPO, PATH), "w", encoding="utf-8", newline="").write(src.replace(M9OLD, M9NEW, 1))
for i in range(3):
    p = run_check()
    red = sorted(f["id"] for f in p.get("failures", []))
    res["m9_runs"].append({"attempt": i + 1, "status": p["status"], "assertions": p.get("assertions"),
                           "red_rows": red})
    print("m9 attempt", i + 1, p["status"], "assertions", p.get("assertions"), "red", len(red))
    if not red:
        break
subprocess.run(["git", "checkout", "--", PATH], cwd=REPO, env=ENV)
res["restored_clean"] = subprocess.run(["git", "status", "--porcelain", "--", PATH], cwd=REPO, env=ENV,
                                       capture_output=True, text=True).stdout.strip() == ""
res["restored_sha_matches_baseline"] = read(PATH) == src
json.dump(res, open(os.path.join(REPO, ".local", "r2", "r2_flake_and_m9.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
