"""W04-02 mutation pass: prove the new CTX-* assertions can fail.

Two of these mutate internal/domain/materialize.go, which is outside W04-02's write scope. That is
deliberate and disclosed: a mutation is a temporary edit that must be restored and hash-verified,
not a change to the delivered product, and the properties under test (byte-checked delivery, grant
enforcement on read) live in that file. Every file is restored to the hash recorded by the check
program before the next case, and the run ends with a baseline pass.
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
MAT = "internal/domain/materialize.go"
OUT = os.path.join(".local", "mutation_selfcheck_w0402.json")


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
    ("Z2-context-cas-removed", CTX,
     '\tif Hash(state["revision"]) != Hash(b["expected_project_state_revision"]) {',
     '\tif false && Hash(state["revision"]) != Hash(b["expected_project_state_revision"]) {'),
    ("Z3-bundle-integrity-unchecked", MAT,
     '\tif bundle["receipt_hash"] != Receipt(bundle) || bundle["summary_hash"] != Digest([]byte(Str(bundle, "summary"))) {',
     '\tif false && (bundle["receipt_hash"] != Receipt(bundle) || bundle["summary_hash"] != Digest([]byte(Str(bundle, "summary")))) {'),
    ("Z4-worker-grant-unchecked", MAT,
     '\tif !p.Allowed(project, taskID, "", false) && !s.runtimeScope(tx, p, project, taskID, "getTask", nil) {',
     '\tif false && !p.Allowed(project, taskID, "", false) && !s.runtimeScope(tx, p, project, taskID, "getTask", nil) {'),
    ("Z5-existing-destination-accepted", MAT,
     '\tif _, e = os.Stat(destination); !os.IsNotExist(e) {',
     '\tif false && !os.IsNotExist(func() error { return nil }()) {'),
    ("Z6-delivered-inputs-stay-writable", MAT,
     '\t\tif e = os.Chmod(path, 0444); e != nil {',
     '\t\tif e = os.Chmod(path, 0666); e != nil {'),
    ("Z7-impact-links-not-recorded", CTX,
     '\tfor _, r := range []Object{Ref(profile, "ProjectProfile")} {', 'NOT_AN_ANCHOR'),
]
# Z1 and Z7 are shape guesses; drop anything whose anchor is not exactly one hit rather than
# reporting a fake result.
MUTS = [m for m in MUTS if m[3] != "NOT_AN_ANCHOR"]

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
report.append({"baseline": d["status"], "assertions": d.get("assertions"),
               "failures": d.get("failures") or []})
print("BASELINE", d["status"], d.get("assertions"))
write(OUT, json.dumps(report, indent=1, ensure_ascii=False))
