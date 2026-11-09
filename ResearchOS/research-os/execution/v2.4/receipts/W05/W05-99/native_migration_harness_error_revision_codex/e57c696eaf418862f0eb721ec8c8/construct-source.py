"""Construct only the minimal exact-error Source revision. No Go/native/SQL."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent
B=ROOT.parent.parent
OLD=B/"native_migration_fixture_harness_source_codex/7050b5e73f7b3f54cb8fa9dc18"
GO="candidate-root/internal/domain/native_migration_authority_harness_windows_test.go"
UNIT="candidate-root/internal/domain/native_migration_error_match_windows_test.go"
BROKER="root_only_native_broker.py"
def ref(path):
    raw=path.read_bytes()
    return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def put(name,raw):
    path=ROOT/name
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("xb") as stream: stream.write(raw)
def js(name,value):
    put(name,(json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
hdf=json.loads((OLD/"HDF.json").read_text(encoding="utf-8"))
assert ref(OLD/"HDF.json")["sha256"]=="bea28f1679be60a36ff12170d919f8f441ec1deb748628125e21d40d75e4e9c5"
assert ref(OLD/"MF.json")["sha256"]=="8591362975b6b8f24d38f5794bdc39cc67e1eb86df8a1a6a09024693bc2430bf"
inputs=[]
for name in ["HDF.json","MF.json","CONTRACT.md","base-pins.json","program-provenance.json",
             "static-evidence.json","original-tool-io.json",GO,BROKER]:
    inputs.append(ref(OLD/name))
for name in [GO,BROKER]:
    oldref=ref(OLD/name)
    expected=hdf["source_refs"][name]
    assert oldref["sha256"]==expected["sha256"] and oldref["bytes"]==expected["bytes"]
for name,key in [("CONTRACT.md","contract_ref"),("base-pins.json","base_pins_ref"),
                 ("program-provenance.json","program_provenance_ref")]:
    actual=ref(OLD/name)
    assert actual["sha256"]==hdf[key]["sha256"] and actual["bytes"]==hdf[key]["bytes"]
native=B/"prepared_abandonment_native_authority_source_codex/b1599aaf259c435db5a0a5313ab0ea65/candidate-root"
for name in ["apps/control/main.go","ops/supervisor/recovery_root/main_windows.go"]:
    inputs.append(ref(native/name))
inputs.append(ref(B.parents[4]/".local/worktrees/codex-w0599-prepared-maintenance-native-52c5a209cfd34eca/internal/domain/store.go"))
old=(OLD/GO).read_bytes()
helper=r'''// nativeHarnessExpectedError compares the first nonempty native stderr line.
// Only the actual standard log.Fatal timestamp is stripped. A later expected
// message cannot hide an earlier different error, and a separate Root
// "exit status N" line after the Control error does not change that error.
func nativeHarnessExpectedError(stderr []byte, expected string) bool {
    for _, line := range strings.Split(string(stderr), "\n") {
        line = strings.TrimSuffix(line, "\r")
        if line == "" { continue }
        if len(line) >= 20 && line[19] == ' ' {
            if _, err := time.Parse("2006/01/02 15:04:05", line[:19]); err == nil {
                line = line[20:]
            }
        }
        return expected != "" && line == expected
    }
    return false
}

'''.encode("utf-8")
anchor=b"func nativeHarnessReadDB("
assert old.count(anchor)==1
changes=[
 (b'"wrong-owner":"current project Owner required"',b'"wrong-owner":"FORBIDDEN: current project Owner required"'),
 (b'!bytes.Contains(replayErr,[]byte("AUTHORITY_MIGRATION_GRANT_ALREADY_USED"))',
  b'!nativeHarnessExpectedError(replayErr,"AUTHORITY_MIGRATION_GRANT_ALREADY_USED")'),
 (b'!bytes.Contains(stderr,[]byte(expectedError))',b'!nativeHarnessExpectedError(stderr,expectedError)'),
]
new=old
for before,after in changes:
    assert new.count(before)==1
    new=new.replace(before,after,1)
new=new.replace(anchor,helper+anchor,1)
inverse=new.replace(helper,b"",1)
for before,after in reversed(changes):
    assert inverse.count(after)==1
    inverse=inverse.replace(after,before,1)
assert inverse==old
put(GO,new)
put(BROKER,(OLD/BROKER).read_bytes())
expected="AUTHORITY_MIGRATION_GRANT"
stamp="2026/10/09 05:01:02 "
owner="FORBIDDEN: current project Owner required"
lease="示例租约错误（仅匹配测试）"
cases=[
 ("bare-exact",expected,expected,True),
 ("standard-time-prefix",stamp+expected,expected,True),
 ("native-id-collision",stamp+expected+"_NATIVE_ID",expected,False),
 ("already-used-collision",stamp+expected+"_ALREADY_USED",expected,False),
 ("size-collision",stamp+expected+"_SIZE",expected,False),
 ("authority-no-expected",stamp+"AUTHORITY_PRIVATE_INHERITANCE_REQUIRED",expected,False),
 ("expected-prefix-text",stamp+"failure: "+expected,expected,False),
 ("expected-suffix-text",stamp+expected+" additional detail",expected,False),
 ("unknown-log-prefix","WARN "+stamp+expected,expected,False),
 ("invalid-date-prefix","2026/99/09 05:01:02 "+expected,expected,False),
 ("fractional-prefix-not-current-format","2026/10/09 05:01:02.123456 "+expected,expected,False),
 ("extra-space-after-time",stamp+" "+expected,expected,False),
 ("control-error-then-root-exit-status",stamp+expected+"\n"+stamp+"exit status 1\n",expected,True),
 ("first-other-error-not-hidden",stamp+"AUTHORITY_RAW_PIN_MISMATCH\n"+stamp+expected+"\n",expected,False),
 ("crlf",stamp+expected+"\r\n"+stamp+"exit status 1\r\n",expected,True),
 ("blank-before-exact","\n"+stamp+expected+"\n",expected,True),
 ("no-error","",expected,False),
 ("empty-expected","", "",False),
 ("replay-exact",stamp+expected+"_ALREADY_USED",expected+"_ALREADY_USED",True),
 ("replay-longer-collision",stamp+expected+"_ALREADY_USED_EXTRA",expected+"_ALREADY_USED",False),
 ("wrong-owner-complete",stamp+owner,owner,True),
 ("wrong-owner-missing-fault-code",stamp+"current project Owner required",owner,False),
 ("lease-full-localized-message",stamp+lease,lease,True),
 ("lease-extra-prefix",stamp+"detail: "+lease,lease,False),
]
unit='''//go:build windows && researchos_native_recovery_harness

package domain

import "testing"

// Pure matching checks only. Root executes this test independently; it does
// not create fixtures, sign grants, invoke native programs or touch a DB.
func TestNativeHarnessExpectedError(t *testing.T) {
    cases := []struct {
        name string
        stderr string
        expected string
        want bool
    }{
'''
for name,stderr,wanted,want in cases:
    unit+="        {"+", ".join(json.dumps(v,ensure_ascii=False) for v in [name,stderr,wanted])+(", true" if want else ", false")+"},\n"
unit+='''    }
    for _, tc := range cases {
        t.Run(tc.name,func(t *testing.T){
            if got:=nativeHarnessExpectedError([]byte(tc.stderr),tc.expected);got!=tc.want{
                t.Fatalf("match=%v want=%v stderr=%q expected=%q",got,tc.want,tc.stderr,tc.expected)
            }
        })
    }
}
'''
put(UNIT,unit.encode("utf-8"))
js("guard-cases.json",{"schema":"researchos.native-error-match-cases.v1",
                     "go_test_executed":False,"cases":[{"name":n,"stderr":s,"expected":e,"want":w} for n,s,e,w in cases]})
for name in ["base-pins.json","program-provenance.json"]:
    put(name,(OLD/name).read_bytes())
contract=(OLD/"CONTRACT.md").read_bytes()
oldword=b"current project Owner required; original state unchanged."
newword=b"FORBIDDEN: current project Owner required; original state unchanged."
assert contract.count(oldword)==1
contractnew=contract.replace(oldword,newword,1)
append=r'''

## Exact native error matching revision

The first nonempty stderr line is the actual error under the observed production log.Fatal path. Remove only a valid standard YYYY/MM/DD HH:MM:SS timestamp followed by exactly one space, then require complete equality with the expected message. CRLF line ending is normalized by dropping only its trailing CR. Arbitrary prefixes, suffixes, unknown timestamp formats and a later expected error after a different first error are rejected. A later separate Root exit status N line does not replace the Control error.

This applies uniformly to every Authority rejection, replay, the complete Fault.Error message FORBIDDEN: current project Owner required, and the actual measured localized lease error. It prevents AUTHORITY_MIGRATION_GRANT_NATIVE_ID, AUTHORITY_MIGRATION_GRANT_ALREADY_USED and AUTHORITY_MIGRATION_GRANT_SIZE from satisfying the expired-grant expectation AUTHORITY_MIGRATION_GRANT.

Root first runs the guarded pure unit test with -tags researchos_native_recovery_harness -run ^TestNativeHarnessExpectedError$ -count=1 ./internal/domain. Its 24 cases are Source only and unexecuted by the author. The nine-case signed/native workflow, complete state assertions and credential pipe remain unchanged. The copied 93-entry base-pins.json and program-provenance.json retain original verified provenance; this minimal revision did not re-run that full inventory.
'''.encode("utf-8")
put("CONTRACT.md",contractnew+append)
assert (contractnew+append).removesuffix(append).replace(newword,oldword,1)==contract
patch="".join(difflib.unified_diff(old.decode("utf-8").splitlines(keepends=True),new.decode("utf-8").splitlines(keepends=True),
                                  fromfile="7050/"+GO,tofile="revision/"+GO))
patch+="".join(difflib.unified_diff([],unit.splitlines(keepends=True),fromfile="/dev/null",tofile="revision/"+UNIT))
patch+="".join(difflib.unified_diff(contract.decode("utf-8").splitlines(keepends=True),(contractnew+append).decode("utf-8").splitlines(keepends=True),
                                   fromfile="7050/CONTRACT.md",tofile="revision/CONTRACT.md"))
put("revision.patch",patch.encode("utf-8"))
js("finding-origin.json",{
 "schema":"researchos.native-migration-error-match-finding.v1",
 "classification":"SOURCE_FALSE_POSITIVE_NOT_NEW_MECHANICAL_FAILURE",
 "original_source":ref(OLD/GO),"original_lines":{"expected_expired_code":263,"replay_contains":429,"negative_contains":432},
 "finding":"bytes.Contains accepts a longer error code sharing AUTHORITY_MIGRATION_GRANT prefix and can hide wrong rejection layers",
 "reviewer_sealed_handoff":"pending separately; anchored to exact original Source and Root review instruction",
 "fix":"first nonempty stderr line, strip only verified standard log timestamp, complete message equality",
 "wrong_owner_full_error":"FORBIDDEN: current project Owner required",
 "go_native_sql_signing_executed":False})
ast.parse((ROOT/BROKER).read_text(encoding="utf-8"),filename=str(ROOT/BROKER))
checks={
 "go_exact_inverse_to_original":inverse==old,
 "broker_raw_identical":(ROOT/BROKER).read_bytes()==(OLD/BROKER).read_bytes(),
 "contract_exact_inverse":(contractnew+append).removesuffix(append).replace(newword,oldword,1)==contract,
 "only_two_error_assertions_rewired":new.count(b"!nativeHarnessExpectedError(")==2,
 "wrong_owner_fault_code_complete":b'"wrong-owner":"FORBIDDEN: current project Owner required"' in new,
 "nineteen_character_standard_time_parse":b'time.Parse("2006/01/02 15:04:05", line[:19])' in new,
 "first_nonempty_line_complete_equality":b'return expected != "" && line == expected' in new,
 "rejection_contains_calls_removed":b"bytes.Contains(" not in new,
 "nine_cases_and_all_other_bytes_preserved":inverse==old,
 "unit_guarded_build_tag":unit.startswith("//go:build windows && researchos_native_recovery_harness"),
 "unit_case_count_24":len(cases)==24,
 "inherited_base_index_raw_identical":(ROOT/"base-pins.json").read_bytes()==(OLD/"base-pins.json").read_bytes(),
 "broker_ast_parse_only":True,
}
assert all(checks.values()),checks
js("revision-input-pins.json",{"schema":"researchos.source-revision-input-pins.v1","pins":inputs,
                            "inherited_93_base_index":ref(OLD/"base-pins.json"),
                            "inherited_93_full_inventory_reexecuted":False})
js("static-evidence.json",{"schema":"researchos.native-error-match-revision-static.v1","checks":checks,
                          "go_unit_cases":24,"go_or_gofmt_run":False,"native_or_sql_run":False,
                          "private_reads_or_signing":False,"unit_results":"SOURCE_ONLY_NOT_RUN"})
print(json.dumps({"source_root":str(ROOT),"source_refs":{name:ref(ROOT/name) for name in [GO,UNIT,BROKER]},
                  "static_checks":checks,"source_only":True},ensure_ascii=True))

