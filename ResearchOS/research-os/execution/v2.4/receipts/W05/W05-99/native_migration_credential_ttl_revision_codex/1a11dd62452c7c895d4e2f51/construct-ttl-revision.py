"""Source-only two-credential TTL revision; no Go, native, SQL or private execution."""
import difflib, hashlib, json
from pathlib import Path
P=Path(__file__).resolve().parent
B=P.parent.parent
T5=Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2")
REL="internal/domain/native_migration_authority_harness_windows_test.go"
ACCEPTED=B/"native_migration_harness_error_revision_codex/e57c696eaf418862f0eb721ec8c8"
COMPILE=B/"integration_codex/native-harness43-compile-unit-root-c16a0730cf914bc5"
RUNTIME=B/"integration_codex/native-positive-controller-config-v2-root-0da7b5a0b3f84a13/controller-runtime"
FAILURE=B/"integration_codex/native-positive-failed-root-release-00ebc1bba04e4d4f/failure-origin.820.closed-qualified.json"
def ref(p):
    b=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def new_bytes(name,b):
    path=P/name
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("xb") as f:f.write(b)
def new_json(name,value):
    new_bytes(name,(json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))

baseline=T5/REL
before=baseline.read_bytes()
auth=(T5/"internal/domain/auth.go").read_bytes()
assert b"if ttl <= 0 || ttl > 15*time.Minute {" in auth
assert b"credential TTL must be at most 15 minutes" in auth
assert b"!time.Now().Before(t)" in auth
inventory=json.loads((COMPILE/"actual-tagged-compiler-input-inventory.json").read_bytes())
matches=[x for x in inventory["build_inputs"] if Path(x["path"]).resolve()==baseline.resolve()]
assert len(matches)==1
pin=matches[0]
assert ref(baseline)["sha256"]==pin["sha256"].removeprefix("sha256:")
assert ref(baseline)["bytes"]==pin["bytes"]
compile_invocation=json.loads((COMPILE/"tagged-test-binary-compile.invocation.json").read_bytes())
assert Path(compile_invocation["cwd"]).resolve()==T5.resolve()
assert compile_invocation["actual_native_exit"]==0
assert ref(ACCEPTED/"candidate-root"/REL)["sha256"]=="2a9640ccfec7b050898d87cfa794e372690d5452474f498c90263db20585f0d9"
assert ref(ACCEPTED/"HDF.json")["sha256"]=="e8886cf85b95a84bade493e12691f995a631c179460726d29beba8e5c2a9b92e"
needles=[
 b"f.s.IssueCredential(ctx, f.owner, time.Hour)",
 b'f.s.IssueCredential(ctx, Str(run, "executor_principal_id"), time.Hour)',
]
assert before.count(b"time.Hour")==2
after=before
changes=[]
for needle in needles:
    assert after.count(needle)==1
    replacement=needle.replace(b"time.Hour",b"15*time.Minute")
    after=after.replace(needle,replacement)
    changes.append({"before":needle.decode(),"after":replacement.decode(),
                    "baseline_line":before[:before.index(needle)].count(b"\n")+1})
inverse=after
for change in reversed(changes):
    old,new=change["before"].encode(),change["after"].encode()
    assert inverse.count(new)==1
    inverse=inverse.replace(new,old)
assert inverse==before
assert after.count(b"IssueCredential(")==before.count(b"IssueCredential(")==2
assert after.count(b"15*time.Minute")==2
assert b"time.Hour" not in after
assert before.count(b't.Fatal(')==after.count(b't.Fatal(')
assert before.count(b"ExpiresUTC: now.Add(4 * time.Minute)")==after.count(b"ExpiresUTC: now.Add(4 * time.Minute)")==1
assert before.splitlines()[0]==after.splitlines()[0]
new_bytes("candidate-root/"+REL,after)
diff="".join(difflib.unified_diff(before.decode().splitlines(keepends=True),
    after.decode().splitlines(keepends=True),fromfile="T5/"+REL,tofile="candidate-root/"+REL))
new_bytes("credential-ttl.patch",diff.encode("utf-8"))
new_json("ttl-replacements.json",changes)

invocation=json.loads((RUNTIME/"test.invocation.json").read_bytes())
result=invocation["result"]
assert (result["actual_exit"],result["owned_child_pid"],result["creation_time_100ns"])==(1,53352,134359747687806045)
assert result["job_cleanup"]["handles_closed"] and result["job_cleanup"]["job_idle_confirmed"]
assert result["job_cleanup"]["active_processes_last_observed"]==0
assert not result["job_cleanup"]["errors"]
stdout=(RUNTIME/"test.stdout.raw").read_bytes()
assert b"native_migration_authority_harness_windows_test.go:468: INVALID_REQUEST: credential TTL must be at most 15 minutes" in stdout
assert hashlib.sha256(stdout).hexdigest()==invocation["stdout_ref"]["sha256"].removeprefix("sha256:")
failure=json.loads(FAILURE.read_bytes())
assert failure["observed_ordinal"]==820
assert failure["signatures_created"]==0 and failure["migration_grants_published"]==0
paths=[baseline,T5/"internal/domain/auth.go",ACCEPTED/"candidate-root"/REL,
    ACCEPTED/"HDF.json",ACCEPTED/"MF.json",ACCEPTED/"CONTRACT.md",
    COMPILE/"tagged-test-binary-compile.invocation.json",COMPILE/"actual-tagged-compiler-input-inventory.json",
    RUNTIME/"test.invocation.json",RUNTIME/"test.stdout.raw",RUNTIME/"test.stderr.raw",FAILURE]
new_json("public-input-pins.json",{"schema":"researchos.native-harness-ttl-inputs.v1",
    "inputs":[ref(p) for p in paths],"actual_formatted_T5_source_matches_selected_compiler_input":True})
new_json("static-evidence.json",{
    "schema":"researchos.native-harness-ttl-static.v1",
    "baseline_ref":ref(baseline),"candidate_ref":ref(P/"candidate-root"/REL),
    "exactly_two_ttl_expressions_changed":True,"replacements":changes,
    "inverse_restores_all_baseline_raw_bytes":True,
    "all_other_assertions_scenarios_authority_Owner_nonce_payload_Job_cleanup_bytes_unchanged":True,
    "IssueCredential_call_count_before":2,"IssueCredential_call_count_after":2,
    "t_Fatal_call_count_preserved":before.count(b"t.Fatal("),
    "four_minute_grant_expression_unchanged":True,
    "production_auth_source_changed":False,
    "production_cap":"0 < ttl <= 15*time.Minute",
    "production_expiry_check":"time.Now().Before(expires_at)",
    "Go_gofmt_or_native_execution":False,"SQL_or_private_access":False,
    "test_status":"SOURCE_STATIC_ONLY_PENDING_ROOT_INDEPENDENT_REVIEW_AND_FRESH_ISOLATED_BUILD"
})
contract="""# Native migration harness credential TTL revision

Status: SOURCE_ONLY_PENDING_ROOT_INDEPENDENT_REVIEW_AND_FRESH_ISOLATED_BUILD.

This package replaces only candidate-root/internal/domain/native_migration_authority_harness_windows_test.go.
Its base is the actual formatted T5 source, verified against T5's selected tagged
compiler input inventory. The accepted e57c Source, contract and handoff remain
inputs. No Main, T5, previous package, production auth, native binary, broker or
controller is modified.

Exactly two arguments change: owner and executor IssueCredential calls use
15*time.Minute instead of time.Hour. The actual production auth.go accepts
strictly positive TTL up to and including 15*time.Minute and authenticates only
while time.Now().Before(stored expires_at). There is no smaller cap in this API.
Production rules are unchanged. Credentials still come from the existing real
public issuance APIs, are issued before backup and retained only in process.

The inverse two replacements recover every byte of the formatted T5 baseline.
All assertions, nine cases, schema/whole-row invariants, exact error matching,
true Owner source, native authority/channel inputs, four-minute grant interval,
nonce, replay, Job ownership and cleanup remain unchanged.

Root must complete all operations requiring these credentials, including the
actual native invocation and planned positive replay, within 15 minutes of
the initial issuance of each credential. The 20-minute review hold/controller
lifetime does not guarantee that Owner stays valid. Root must inspect the
existing absolute expiries and budget both review/sign/publish pauses within
the original credential TTL and the unchanged grant validity. This package
adds no Owner refresh, reissuance, retry, deadline extension or automatic
approval. If time expires, preserve the actual failure and obtain the required
Root decision for any fresh isolated attempt; do not mutate the old case.

Failure 820 remains the original real single-positive Go exit 1:
PID 53352, creation FILETIME 134359747687806045, exact error
INVALID_REQUEST: credential TTL must be at most 15 minutes at original line 468.
Its actual closed invocation, stdout and Root's closed-qualified failure record
are pinned. Source author did not repeat the run, read the retained DB, or
perform native signing. Root reported prior fixture inspection/release; the
author only verifies the public invocation's actual Job closure and the
failure record's zero signatures/grants.

Diagnostic 822 is a separate functions.exec orchestration failure before any
exec_command or process launch; outer/Python/native exits are null, not 1.
Its complete original input and returned error are retained.

Root next independently reviews this minimal delta, composes a fresh isolated
T7, builds/freezes its actual compiler inputs and creates a fresh case/config.
No Go/native/SQL/private/model execution, production acceptance or retry is
claimed by this Source-only package. The prior e57c execution contract otherwise
remains applicable without relaxation.
"""
new_bytes("CONTRACT.md",contract.encode("utf-8"))
print(json.dumps({"source_root":str(P),"candidate":ref(P/"candidate-root"/REL),
    "baseline":ref(baseline),"changes":changes,"public_inputs":len(paths),
    "diagnostic822":ref(P/"diagnostic-822.json"),"inverse_raw_equal":True},ensure_ascii=True))

