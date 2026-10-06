"""Mutations for the W04-02 acceptance, resolution and governing-decision legs.

Each case is applied alone to internal/domain (all inside this card's write scope), the construction
check runs, the failing assertion ids are recorded, and the file is restored and hash-verified
before the next case. Anchors carry explicit escapes because a console heredoc mangles them.
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
CTX = "internal/domain/context.go"
OUT = os.path.join(".local", "mutation_selfcheck_w0402c.json")

MERGE_TAIL = ("\t\t\tunresolved = append(unresolved, \"governing decision no longer resolvable: \"+Str(r, \"id\"))\n"
              "\t\t\tcontinue\n"
              "\t\t}\n"
              "\t\tdecisions = append(decisions, r)")
MERGE_DROPPED = MERGE_TAIL.replace("decisions = append(decisions, r)", "_ = r")


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
    ("AA1-author-can-accept-own-change", CHG,
     "\t\tif id == p.ID {", "\t\tif false && id == p.ID {"),
    ("AA2-resolution-does-not-require-an-applied-change", CHG,
     "\tif proposal[\"status\"] != \"APPLIED\" {", "\tif proposal[\"status\"] == \"APPLIED\" {"),
    ("AC3-applied-change-stops-invalidating-its-dependents", CHG,
     "\t\t\to[\"status\"] = \"NEEDS_REVALIDATION\"", "\t\t\to[\"status\"] = \"DRAFT\""),
    ("AD1-freeze-ignores-the-governing-decisions", CTX, MERGE_TAIL, MERGE_DROPPED),
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
