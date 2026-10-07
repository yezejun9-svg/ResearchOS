"""Capture the non-dispatch command results this card quotes, at the current HEAD.

The round-1 review found six command entries in receipt.json were typed literals. This script is the
only sanctioned way for those rows to exist: it runs each command, records argv, exit code, a derived
result string and the HEAD it ran at, and the receipt generator refuses to quote a command whose log
is missing or was captured on a different tree. Nothing here decides what the receipt claims; it only
makes the claim come from a file.
"""
import datetime, hashlib, io, json, os, subprocess, sys

def find_repo(start):
    d = start
    for _ in range(8):
        if os.path.isdir(os.path.join(d, "execution", "v2.4")) and os.path.isdir(os.path.join(d, "internal")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("repository root not found from %s" % start)

REPO = find_repo(os.path.dirname(os.path.abspath(__file__)))
RD = os.path.join(REPO, "execution", "v2.4", "receipts", "W12", "W12-01")
LOGS = os.path.join(RD, "invocations", "logs")
GO = os.path.join(REPO, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
if not os.path.exists(GO):
    raise SystemExit("locked toolchain missing at %s" % GO)

env = dict(os.environ)
env.update({"GOTOOLCHAIN": "local", "GOENV": "off",
            "GOPATH": os.path.join(REPO, ".local", "gopath"),
            "GOCACHE": os.path.join(REPO, ".local", "gocache"),
            "RESEARCHOS_GO": GO, "PYTHONIOENCODING": "utf-8"})

head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

COMMANDS = [
 ("go_build", ["build", "./..."], "clean"),
 ("go_vet_domain", ["vet", "./internal/domain"], "clean"),
 ("go_test_takeover", ["test", "./internal/domain", "-count=1", "-run", "TestW12BudgetLeaseTakeover$"], "ok"),
 ("go_test_w12", ["test", "./internal/domain", "-count=1", "-run", "TestW12"], "ok"),
 ("go_test_runtime_coordinator", ["test", "./internal/domain", "-count=1", "-run", "TestRuntimeCoordinator"], "ok"),
]

os.makedirs(LOGS, exist_ok=True)
written = []
for key, argv, expect in COMMANDS:
    p = subprocess.run([GO] + argv, cwd=REPO, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=1800)
    text = ((p.stdout or "") + (p.stderr or ""))
    fails = [l for l in text.splitlines() if l.startswith("--- FAIL") or l.startswith("FAIL")]
    if p.returncode != 0:
        result = "exit %d: %s" % (p.returncode, text.strip()[-400:])
    elif fails:
        result = "exit 0 but the output names failures: %s" % " | ".join(fails)[:400]
    else:
        tail = [l for l in text.splitlines() if l.strip()]
        result = "%s; last line of output: %s" % (expect, tail[-1] if tail else "(no output)")
    body = {"key": key, "cwd": "REPOSITORY", "argv": [os.path.relpath(GO, REPO).replace("\\", "/")] + argv,
            "exit_code": p.returncode, "result": result, "code_revision": head,
            "output_sha256": hashlib.sha256(text.encode("utf-8", "replace")).hexdigest(),
            "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    out = os.path.join(LOGS, key + ".json")
    io.open(out, "w", encoding="utf-8", newline="\n").write(json.dumps(body, ensure_ascii=False, indent=1))
    written.append((key, p.returncode, result[:90]))
    print(key, "exit", p.returncode, "|", result[:90])

print("HEAD", head[:8], "| logs", len(written))
