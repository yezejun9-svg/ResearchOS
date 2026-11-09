"""W04-02 mutation pass B: teeth for the change-impact and gating assertions.

context.go and changes.go are both inside this card's write scope; each mutation is applied alone,
the construction check runs, the failing ids are recorded, and the file is restored and
hash-verified before the next case.
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
CTX = "internal/domain/context.go"
CHG = "internal/domain/changes.go"
OUT = os.path.join(".local", "mutation_selfcheck_w0402b.json")


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
    ("Z7-impact-link-basis-not-deterministic", CTX,
     '"relation": "DEPENDS_ON", "basis": "DETERMINISTIC"', '"relation": "DEPENDS_ON", "basis": "USER_STATED"'),
    ("Z7b-freeze-records-no-dependency-links", CTX,
     "\tfor _, r := range refs {", "\tfor _, r := range []Object{} {"),
    ("Z8-supported-checks-freeze-unenforced", CHG,
     '\tif Hash(b["test_check_ids"]) != Hash(changeChecks) {', "\tif false && Hash(b[\"test_check_ids\"]) != Hash(changeChecks) {"),
    ("Z9-proposal-base-cas-removed", CHG,
     '\tif Hash(state["revision"]) != Hash(b["base_state_revision"]) {',
     '\tif false && Hash(state["revision"]) != Hash(b["base_state_revision"]) {'),
    ("Z10-missing-context-gate-removed", CTX,
     '\t\treturn Fail(422, "GATE_FAILED", "task context required")', "\t\treturn nil"),
    ("Z11-edit-target-staleness-unchecked", CHG,
     "\t\tif Hash(Ref(current, kind)) != Hash(r) {", "\t\tif false && Hash(Ref(current, kind)) != Hash(r) {"),
]

report = []
for name, path, old, new in MUTS:
    original = read(path)
    if original.count(old) != 1:
        report.append({"mutation": name, "file": path, "status": "ANCHOR_MISSING",
                       "anchor_count": original.count(old)})
        print("%-42s ANCHOR %d" % (name, original.count(old)), flush=True)
        continue
    h0 = sha(path)
    write(path, original.replace(old, new))
    d = run_check()
    failed = [f["id"] for f in (d.get("failures") or [])]
    write(path, original)
    report.append({"mutation": name, "file": path, "status": d["status"],
                   "assertions": d.get("assertions", 0), "failed_ids": failed,
                   "restored": h0 == sha(path)})
    print("%-42s %-7s failed=%d %s" % (name, d["status"], len(failed), ",".join(failed[:4])), flush=True)

d = run_check()
report.append({"baseline": d["status"], "assertions": d.get("assertions"), "failures": d.get("failures") or []})
print("BASELINE", d["status"], d.get("assertions"))
write(OUT, json.dumps(report, indent=1, ensure_ascii=False))
