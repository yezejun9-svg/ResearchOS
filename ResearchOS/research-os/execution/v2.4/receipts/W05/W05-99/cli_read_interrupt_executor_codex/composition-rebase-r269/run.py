import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
WT = ROOT / ".local/worktrees/codex-w0599-cli-read-interrupt"
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
PATHS = ["apps/cli/cli_stream.go", "apps/cli/cli_continuation.go", "apps/cli/cli_read_interrupt_test.go", "apps/cli/cli_v2.go"]
COMMITS = ["6eb611b11364ba25a9560ba54c1b54f3a549eb32", "0bbcef5347ed9bd3a1174c7d3df9dfd8a270e837", "890d4c164bffad73e562ceacfdc216820d0313fd", "c571781e9703bc7a96fa63629e0cc3bee7f3deec"]


def save(name, value):
    with (OUT / name).open("xb") as stream:
        stream.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())


def run(name, argv):
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.run(argv,cwd=WT,capture_output=True)
    for suffix,raw in [("stdout.raw",proc.stdout),("stderr.raw",proc.stderr)]:
        with (OUT/(name+"."+suffix)).open("xb") as stream:
            stream.write(raw)
    save(name+".invocation.json",{"argv":argv,"cwd":str(WT),"started_at":start,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"actual_exit":proc.returncode,"stdout_sha256":hashlib.sha256(proc.stdout).hexdigest(),"stderr_sha256":hashlib.sha256(proc.stderr).hexdigest()})
    assert proc.returncode == 0,(name,proc.returncode)
    return proc.stdout


def snap():
    return {name:hashlib.sha256((WT/name).read_bytes()).hexdigest() for name in PATHS}


assert run("head-before",["git","rev-parse","HEAD"]).decode().strip() == "4ba293847072069cd99154e5054f6ef4ae2b92e1"
assert not run("index-before",["git","diff","--cached","--name-only","-z"])
scope = ROOT/(BASE+"integration_codex/cli-read-causal-scope-r267/scope_registration.json")
assert hashlib.sha256(scope.read_bytes()).hexdigest() == "b950974027f665aaf543029dd4dffbf5cbee23fb5b38a3e819a35dc508a333dc"
before = snap()
save("cli.before.json",before)
run("status-before",["git","status","--short","--untracked-files=no"])
actual = []
for index,commit in enumerate(COMMITS):
    run(f"cherry-{index}",["git","cherry-pick",commit])
    actual.append({"original":commit,"new_head":run(f"head-{index}",["git","rev-parse","HEAD"]).decode().strip()})
    assert snap() == before
after = snap()
save("cli.after.json",after)
main_sources = json.loads((ROOT/(BASE+"integration_codex/main-stream-source-integration-r268/main-source.after.json")).read_bytes())
checked = []
for name,expected in main_sources.items():
    if name in PATHS:
        continue
    if expected == "MISSING":
        assert not (WT/name).exists(),name
    else:
        assert hashlib.sha256((WT/name).read_bytes()).hexdigest() == expected["sha256"],name
    checked.append(name)
run("status-after",["git","status","--short","--untracked-files=no"])
result = {"schema":"researchos.root.cli-read-composition-rebase.v1","actor":"codex:/root","actual_exit":0,"actual_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"worktree":str(WT),"head":actual[-1]["new_head"],"integrated_reviewed_commits":actual,"cli_exact4_unchanged":before==after,"main_non_cli_source_entries_matching":len(checked),"main_integration_ref":{"path":BASE+"integration_codex/main-stream-source-integration-r268/result.json","sha256":"2a76e1bbd9e1264c0fe9a7f8269985be0586bf546839fe3cb7d35f6b9e3bb9ec"},"measurement_mode":"SOURCE_COMPOSITION_PREPARATION_NOT_TEST_NOT_FORMAL","formal_increment":0}
save("result.json",result)
print(json.dumps(result,ensure_ascii=False))
