"""W05-01 evidence chain, serialized in one process so no two heavy Go suites ever overlap.

binding run x2 at HEAD -> freeze the invocations under the card receipt dir -> mutation matrix ->
captured command logs -> receipt.json. Every step prints a one-line verdict; the script stops at the
first step that does not report what it should, and never writes a receipt when the matrix is short.
"""
import glob, io, json, os, shutil, subprocess, sys

REPO = r"D:\作品集\ResearchOS\research-os"
RD = os.path.join(REPO, "execution", "v2.4", "receipts", "W05", "W05-01")
GO = os.path.join(REPO, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
PY = sys.executable
LOG = os.path.join(REPO, ".local", "w0501_chain.log")

env = dict(os.environ)
env.update({"GOTOOLCHAIN": "local", "GOENV": "off",
            "GOPATH": os.path.join(REPO, ".local", "gopath"),
            "GOCACHE": os.path.join(REPO, ".local", "gocache"),
            "RESEARCHOS_GO": GO, "RESEARCHOS_TASK_ID": "W05", "RESEARCHOS_CHECK_ID": "W05-01",
            "PYTHONIOENCODING": "utf-8"})

out = []


def say(line):
    out.append(line)
    io.open(LOG, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")


def step(name, argv, cwd=REPO, timeout=3600, expect_zero=True):
    p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    text = (p.stdout or "") + (p.stderr or "")
    say("%s exit=%s" % (name, p.returncode))
    for l in [x for x in text.splitlines() if x.strip()][-12:]:
        say("   | " + l[:400])
    if expect_zero and p.returncode != 0:
        say("STOP: %s failed" % name)
        sys.exit(1)
    return p, text


head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True,
                      text=True).stdout.strip()
say("chain starts at HEAD " + head[:8])

# 1. two binding runs through the registry, at this HEAD
ids = []
for n in (1, 2):
    p, text = step("binding_run_%d" % n, [PY, "execution/command_dispatcher/dispatch.py", "test.runtime",
                                          "--task-id", "W05", "--check-id", "W05-01"], timeout=1800)
    row = None
    for l in reversed(text.splitlines()):
        l = l.strip()
        if l.startswith("{"):
            row = json.loads(l)
            break
    if not row or row.get("status") != "PASS":
        say("STOP: binding run %d did not report PASS: %s" % (n, row))
        sys.exit(1)
    say("   run %d: %s assertions=%s" % (n, row["invocation_id"][:8], len(row.get("assertion_ids") or []) or row.get("assertions")))
    ids.append(row["invocation_id"])

# 2. freeze them inside the card receipt directory
for i in ids:
    src = os.path.join(REPO, "execution", "invocations", i)
    dst = os.path.join(RD, "invocations", i)
    if not os.path.isdir(src):
        say("STOP: no invocation directory for " + i)
        sys.exit(1)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    r = json.load(io.open(os.path.join(dst, "receipt.json"), encoding="utf-8-sig"))
    say("   frozen %s: %s code_revision=%s ids=%d" % (i[:8], r.get("status"),
        (r.get("code_revision") or "")[:8], len(r.get("assertion_ids") or [])))
    if (r.get("code_revision") or "") != head:
        say("STOP: the frozen run pins a different revision than HEAD")
        sys.exit(1)

# 3. the mutation matrix
step("mutation_matrix", [PY, os.path.join(RD, "mut_w0501.py")], timeout=5400, expect_zero=False)
m = json.load(io.open(os.path.join(RD, "mutation_selfcheck_w0501.json"), encoding="utf-8-sig"))
say("   matrix cases=%s buckets=%s tree_clean=%s equiv=%s"
    % (m.get("cases"), m.get("buckets"), m.get("tree_clean_after_restore"),
       [(e["id"], e["bucket"]) for e in (m.get("equivalence_probe") or {}).get("results") or []]))
for r in m.get("results") or []:
    if r["bucket"] != "caught":
        say("   NOT-CAUGHT " + r["id"] + " " + json.dumps(r.get("killed") or r.get("detail") or "")[:200])
ok = (m.get("buckets") or {}).get("caught") == m.get("cases") and m.get("tree_clean_after_restore")
if not ok:
    say("STOP: the matrix is not fully caught; the receipt generator must not run")
    sys.exit(1)

# 4. captured command logs at this HEAD, then the receipt
step("capture_logs", [PY, os.path.join(RD, "generate_receipt_w0501.py"), "--capture"], timeout=3600)
step("receipt", [PY, os.path.join(RD, "generate_receipt_w0501.py")], timeout=1800)
say("chain finished GREEN at HEAD " + head[:8])
