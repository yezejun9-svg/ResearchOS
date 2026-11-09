import sys
sys.dont_write_bytecode=True
import json,hashlib,re
from pathlib import Path
O=Path(__file__).resolve().parent; B=O.parents[1]
N=B/"native_retained_cleanup_context_revision_codex/cl-1a11e7f5205729390aaee9f47b28ce6"
refs={}; checks=[]
def pin(p):
    p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p):
    p=Path(p).resolve();raw=p.read_bytes();refs[str(p)]=dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));return raw
def check(name,ok):
    checks.append(dict(name=name,passed=bool(ok)));assert ok,name
def write(name,value):
    with (O/name).open("x",encoding="utf-8",newline="\n") as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write("\n")
for name,h,size in [("HDF.json","def8d9e965e4a3c38fb6082c965ac59bfb199b8c4c986cde3063ac98f11bd269",4115),("MF.json","675fd9ab068cf2403df5986ad75215ab2b73a210bf748953ee58fbcaabfe4e53",4836)]:
    raw=read(N/name);check("fixed-"+name,(hashlib.sha256(raw).hexdigest(),len(raw))==(h,size))
hdf=json.loads(read(N/"HDF.json"));mf=json.loads(read(N/"MF.json"))
check("13-candidate-members",len(mf["members"])==13)
for name,ref in mf["members"].items():
    raw=read(ref["path"]);check("member:"+name,(hashlib.sha256(raw).hexdigest(),len(raw))==(ref["sha256"],ref["bytes"]))
base=read(hdf["base_ref"]["path"]);candidate=read(hdf["candidate_ref"]["path"])
check("original-live-base-pin",pin(hdf["base_ref"]["path"])==hdf["base_ref"])
check("candidate-pin",pin(hdf["candidate_ref"]["path"])==hdf["candidate_ref"])
basecopy=read(N/"base-root/internal/domain/native_migration_authority_harness_windows_test.go")
check("base-copy-exact",basecopy==base)
b=base.decode("utf-8");c=candidate.decode("utf-8")
replacements=json.loads(read(N/"source-replacements.json"))
old=replacements["original_block"];new=replacements["replacement_block"];added=replacements["appended_helper_and_tests"]
check("original-single-block",b.count(old)==1)
check("replacement-single-block",c.count(new)==1)
check("only-one-block-plus-append",b.replace(old,new,1)+added==c)
check("independent-exact-inverse",c[:-len(added)].replace(new,old,1).encode("utf-8")==base)

# Small read-only lexical scanner. This is not Go AST, compilation or testing.
token_pattern=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\x60[^\x60]*\x60|\x27(?:\\.|[^\x27\\])*\x27|[A-Za-z_][A-Za-z_0-9]*|[0-9]+|[^\s]',re.M)
def toks(source):
    return [(m.group(),m.start(),m.end()) for m in token_pattern.finditer(source) if not m.group().startswith(("//","/*"))]
def assertions(source):
    ts=toks(source);out=[]
    for i in range(len(ts)-3):
        if ts[i][0]=="t" and ts[i+1][0]=="." and ts[i+2][0] in {"Fatal","Fatalf","Error","Errorf","Fail","FailNow"} and ts[i+3][0]=="(":
            depth=0
            for j in range(i+3,len(ts)):
                if ts[j][0]=="(":depth+=1
                if ts[j][0]==")":depth-=1
                if depth==0:
                    out.append(source[ts[i][1]:ts[j][2]]);break
    return out
def funcs(source):
    ts=toks(source);out={}
    for i in range(len(ts)-2):
        if ts[i][0]!="func" or ts[i+2][0]!="(":continue
        start=next((j for j in range(i+2,len(ts)) if ts[j][0]=="{"),None)
        assert start is not None
        depth=0
        for j in range(start,len(ts)):
            if ts[j][0]=="{":depth+=1
            if ts[j][0]=="}":depth-=1
            if depth==0:
                out[ts[i+1][0]]=source[ts[i][1]:ts[j][2]];break
    return out
bf=funcs(b);cf=funcs(c)
check("two-added-declarations",set(cf)-set(bf)=={"nativeHarnessCleanupReviewContext","TestNativeHarnessCleanupReviewContext"})
check("no-declarations-removed",set(bf)<=set(cf))
for name in bf:
    expect=bf[name].replace(old,new,1) if name=="TestNativeMigrationAuthorityHarness" else bf[name]
    check("preserved-function:"+name,cf[name]==expect)
check("ninety-original-assertions",len(assertions(b))==90)
check("original-assertions-exact-order",assertions(c[:-len(added)])==assertions(b))
mainb=bf["TestNativeMigrationAuthorityHarness"];mainc=cf["TestNativeMigrationAuthorityHarness"]
caseblock=lambda s:s[s.index("cases := map[string]string{"):s.index("expectedError, ok := cases[cfg.Case]")]
check("original-nine-case-map-byte-exact",caseblock(mainb)==caseblock(mainc) and len(re.findall(r'"(?:positive-replay|missing-native-channel|wrong-purpose|mismatched-database|release-pin-mismatch|expired-grant|missing-dynamic-pin|wrong-owner|lease-occupied)"',caseblock(mainc)))==9)
helper=cf["nativeHarnessCleanupReviewContext"]
check("explicit-ignored-parent",helper.startswith("func nativeHarnessCleanupReviewContext(_ context.Context)"))
check("fresh-background-four-minute",helper.split("{",1)[1].strip()=="return context.WithTimeout(context.Background(), 4*time.Minute)\n}")
check("cleanup-created-in-callback",new.index("t.Cleanup(func() {")<new.index("cleanupCtx, cleanupCancel :=")<new.index('nativeHarnessWrite(t,'))
check("cleanup-cancel-deferred",new.count("defer cleanupCancel()")==1)
check("explicit-Root-release-gate", 'nativeHarnessWait(t, cleanupCtx, filepath.Join(cfg.OutputDirectory, "06-release-fixture.approval.json"), "release-fixture")' in new)
check("wait-errors-and-timeout-preserved",cf["nativeHarnessWait"]==bf["nativeHarnessWait"] and 't.Fatal("Root review window ended", ctx.Err())' in cf["nativeHarnessWait"])
check("20-minute-main-preserved",'ctx, cancel := context.WithTimeout(context.Background(), 20*time.Minute)' in mainc)
check("4-minute-grant-preserved",'ExpiresUTC: now.Add(4 * time.Minute).Format(time.RFC3339Nano)' in mainc)
tests=cf["TestNativeHarnessCleanupReviewContext"]
children=re.findall(r't.Run\("([^"]+)"',tests)
check("four-new-unit-children",children==["expired-main-deadline","main-cancel-does-not-end-cleanup","cleanup-cancel-does-not-cancel-main","fresh-four-minute-deadline"])
check("no-blocking-sleep-native-SQL-calls",not any(s in tests for s in ("time.Sleep","nativeHarnessBroker","sql.","exec.","os.","t.Parallel","t.TempDir")))
check("unit-cancel-all-created-contexts",tests.count("defer mainCancel()")==4 and tests.count("defer cleanupCancel()")==4)
check("expired-main-error-observed",'!errors.Is(mainCtx.Err(), context.DeadlineExceeded)' in tests)
check("main-cancel-independent",'!errors.Is(mainCtx.Err(), context.Canceled) || cleanupCtx.Err() != nil' in tests)
check("cleanup-cancel-independent",'!errors.Is(cleanupCtx.Err(), context.Canceled) || mainCtx.Err() != nil' in tests)
check("deadline-bounded-on-both-sides",'deadline.Before(before.Add(4*time.Minute)) || deadline.After(after.Add(4*time.Minute))' in tests)
check("Done-closes-on-cancel",'case <-cleanupCtx.Done():\n\t\tdefault:\n\t\t\tt.Fatal("cleanup cancellation did not close Done")' in tests)
check("imports-byte-exact",b[:b.index("type nativeMigrationHarnessConfig")]==c[:c.index("type nativeMigrationHarnessConfig")])
controller=read(B/"native_migration_controller_temp_env_revision_codex/e6a4d23ff0a84a6d9c2905181d97c2e4/root_native_migration_controller.py").decode("utf-8")
check("current-inner-owned-is-1260-not-1800", 'env, stdout, stderr, 1260,' in controller and 'deadline = time.monotonic() + 1270' in controller)
check("current-Go25min", '"-test.timeout=25m"' in controller)
write("sourceguard.initial.json",dict(method="read-only byte SHA256 before-after",refs=list(refs.values())))
for ref in list(refs.values()):check("unchanged:"+Path(ref["path"]).name,pin(ref["path"])==ref)
write("sourceguard.final.json",dict(refs=list(refs.values()),unchanged=True))
write("review-result.json",dict(status="SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL",checks=checks,checks_count=len(checks),source_inputs=len(refs),source_assertions_original=90,original_functions=len(bf),new_test_children=children,exact_inverse_original_bytes=True,Go_AST_gofmt_compile_test_executed=False,new_actual_Git_Go_SQL_native_model=False,private_read=False,Main_canonical_write=False,formal_acceptance=False))
print(json.dumps(dict(status="SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL",checks=len(checks),inputs=len(refs),original_functions=len(bf))))

