"""Two mutations for the acceptance and resolution legs W04-02 just added.

AA1 removes the rule that an author cannot independently accept its own change; AA2 inverts the rule
that only an accepted-and-applied change settles a conflict. Both live in internal/domain, which this
card's write scope covers, and each file is restored and hash-verified before the next case.
"""
import hashlib
import io
import json
import os
import subprocess

REPO = os.getcwd()
GO = os.path.join(REPO, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
ENV = dict(os.environ)
ENV.update({"GOTOOLCHAIN": "local", "GOFLAGS": "", "GOENV": "off",
            "GOPATH": os.path.join(REPO, ".local", "gopath"),
            "GOCACHE": os.path.join(REPO, ".local", "gocache"), "RESEARCHOS_GO": GO})
CHG = "internal/domain/changes.go"
OUT = os.path.join(".local", "mutation_selfcheck_w0402c.json")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def read(p):
    return io.open(p, encoding="utf-8", newline="").read()


def write(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def run_check():
    r = subprocess.run([GO, "run", "./tests/context/check"], cwd=REPO, env=ENV,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = [l for l in (r.stdout or "").strip().splitlines() if l.startswith("{")]
    if not lines:
        return {"status": "NOJSON", "assertions": 0,
                "failures": [{"id": "RAW", "detail": ((r.stdout or "") + (r.stderr or ""))[:200]}]}
    return json.loads(lines[-1])


MUTS = [
    ("AA1-author-can-accept-own-change", CHG, "\t\tif id == p.ID {", "\t\tif false && id == p.ID {"),
    ("AA2-resolution-does-not-require-an-applied-change", CHG,
     '\tif proposal["status"] != "APPLIED" {', '\tif proposal["status"] == "APPLIED" {'),
]

report = []
for name, path, old, new in MUTS:
    original = read(path)
    if original.count(old) != 1:
        report.append({"mutation": name, "file": path, "status": "ANCHOR_MISSING",
                       "anchor_count": original.count(old)})
        print("%-52s ANCHOR %d" % (name, original.count(old)), flush=True)
        continue
    h0 = sha(path)
    write(path, original.replace(old, new))
    d = run_check()
    failed = [f["id"] for f in (d.get("failures") or [])]
    write(path, original)
    report.append({"mutation": name, "file": path, "status": d["status"],
                   "assertions": d.get("assertions", 0), "failed_ids": failed,
                   "restored": h0 == sha(path)})
    print("%-52s %-7s failed=%d %s" % (name, d["status"], len(failed), ",".join(failed[:4])), flush=True)

d = run_check()
report.append({"baseline": d["status"], "assertions": d.get("assertions"), "failures": d.get("failures") or []})
print("BASELINE", d["status"], d.get("assertions"))
write(OUT, json.dumps(report, indent=1, ensure_ascii=False))
