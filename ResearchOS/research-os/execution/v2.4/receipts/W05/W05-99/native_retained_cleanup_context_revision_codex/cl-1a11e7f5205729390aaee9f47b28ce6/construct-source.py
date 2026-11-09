import re,json,hashlib,difflib
from pathlib import Path
N=Path(__file__).resolve().parent
R=N.parents[6];B=R/"execution/v2.4/receipts/W05/W05-99"
T=R/".local/worktrees/codex-w0599-native-temp-1791506570123"
base=T/"internal/domain/native_migration_authority_harness_windows_test.go"
inventory=B/"integration_codex/native-temp-compile-unit-root-1791508539969/revision-list-manifest/formatted.source-members.json"
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 p=N/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def write(n,raw):
 p=N/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(raw)
 return pin(p)
ref=next(x for x in json.loads(inventory.read_bytes()) if Path(x["path"]).resolve()==base)
assert pin(base)==ref and (ref["sha256"],ref["bytes"])==("972166b2744d1048dc747e8a5b4991cd0b06cbbdc8a523c90fef12e27e02e0e9",35845)
refs=[pin(base),pin(inventory)]
original=base.read_bytes();text=original.decode()
newline="\r\n" if "\r\n" in text else "\n"
old='\tt.Cleanup(func() {\n\t\tnativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "06-fixture-retained.ready.json"), Object{\n\t\t\t"test_failed": t.Failed(), "database": opt.Source, "release_required": true})\n\t\tnativeHarnessWait(t, ctx, filepath.Join(cfg.OutputDirectory, "06-release-fixture.approval.json"), "release-fixture")\n\t})'.replace("\n",newline)
new='\tt.Cleanup(func() {\n\t\t// Start the bounded review window only when cleanup begins. Main execution\n\t\t// may already have exhausted its deadline; it must not cancel this hold.\n\t\tcleanupCtx, cleanupCancel := nativeHarnessCleanupReviewContext(ctx)\n\t\tdefer cleanupCancel()\n\t\tnativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "06-fixture-retained.ready.json"), Object{\n\t\t\t"test_failed": t.Failed(), "database": opt.Source, "release_required": true})\n\t\tnativeHarnessWait(t, cleanupCtx, filepath.Join(cfg.OutputDirectory, "06-release-fixture.approval.json"), "release-fixture")\n\t})'.replace("\n",newline)
assert text.count(old)==1
candidate=text.replace(old,new,1)
added=r'''
// The cleanup hold has its own four-minute budget. The twenty-minute main
// deadline and four-minute grant lifetime remain separate and unchanged.
// Root must still publish the exact fixture-release approval. Expiry is a test
// failure, not evidence of inspection or release. An earlier outer Go/Job
// timeout can still end this hold; no in-process context can prevent that.
func nativeHarnessCleanupReviewContext(_ context.Context) (context.Context, context.CancelFunc) {
	return context.WithTimeout(context.Background(), 4*time.Minute)
}

func TestNativeHarnessCleanupReviewContext(t *testing.T) {
	t.Run("expired-main-deadline", func(t *testing.T) {
		mainCtx, mainCancel := context.WithDeadline(context.Background(), time.Now().Add(-time.Second))
		defer mainCancel()
		if !errors.Is(mainCtx.Err(), context.DeadlineExceeded) {
			t.Fatal("main context must already have expired")
		}
		cleanupCtx, cleanupCancel := nativeHarnessCleanupReviewContext(mainCtx)
		defer cleanupCancel()
		if err := cleanupCtx.Err(); err != nil {
			t.Fatal("expired main deadline ended the independent cleanup hold", err)
		}
		select {
		case <-cleanupCtx.Done():
			t.Fatal("cleanup Done inherited the expired main context")
		default:
		}
	})
	t.Run("main-cancel-does-not-end-cleanup", func(t *testing.T) {
		mainCtx, mainCancel := context.WithCancel(context.Background())
		defer mainCancel()
		cleanupCtx, cleanupCancel := nativeHarnessCleanupReviewContext(mainCtx)
		defer cleanupCancel()
		mainCancel()
		if !errors.Is(mainCtx.Err(), context.Canceled) || cleanupCtx.Err() != nil {
			t.Fatal("main cancellation crossed the cleanup context boundary")
		}
	})
	t.Run("cleanup-cancel-does-not-cancel-main", func(t *testing.T) {
		mainCtx, mainCancel := context.WithCancel(context.Background())
		defer mainCancel()
		cleanupCtx, cleanupCancel := nativeHarnessCleanupReviewContext(mainCtx)
		defer cleanupCancel()
		cleanupCancel()
		if !errors.Is(cleanupCtx.Err(), context.Canceled) || mainCtx.Err() != nil {
			t.Fatal("cleanup cancellation did not remain independent")
		}
		select {
		case <-cleanupCtx.Done():
		default:
			t.Fatal("cleanup cancellation did not close Done")
		}
	})
	t.Run("fresh-four-minute-deadline", func(t *testing.T) {
		mainCtx, mainCancel := context.WithTimeout(context.Background(), time.Hour)
		defer mainCancel()
		before := time.Now()
		cleanupCtx, cleanupCancel := nativeHarnessCleanupReviewContext(mainCtx)
		defer cleanupCancel()
		after := time.Now()
		deadline, ok := cleanupCtx.Deadline()
		if !ok || deadline.Before(before.Add(4*time.Minute)) || deadline.After(after.Add(4*time.Minute)) {
			t.Fatal("cleanup review must have a fresh bounded four-minute deadline")
		}
		mainDeadline, ok := mainCtx.Deadline()
		if !ok || !deadline.Before(mainDeadline) {
			t.Fatal("cleanup inherited the main deadline instead of its own bound")
		}
	})
}
'''.replace("\n",newline)
candidate+=added
# Exact inverse proves all original cases, assertions, other tests, imports and
# production interactions remain byte-identical.
inverse=candidate[:-len(added)].replace(new,old,1)
assert inverse.encode()==original
assert candidate.count("context.WithTimeout(context.Background(), 20*time.Minute)")==text.count("context.WithTimeout(context.Background(), 20*time.Minute)")==1
assert candidate.count("now.Add(4 * time.Minute)")==text.count("now.Add(4 * time.Minute)")==1
caseblock=text.split("cases := map[string]string{",1)[1].split("\n\t}",1)[0]
case_names=re.findall(r'"([a-z]+(?:-[a-z]+)+)"\s*:',caseblock)
assert len(case_names)==9
original_assertions=re.findall(r'\bt\.(?:Fatalf?|Errorf?|FailNow|Fail)\(',text)
assert len(original_assertions)==90
core=text[:text.index("func nativeHarnessBrokerPublicEnvironment")]
core_assertions=len(re.findall(r'\bt\.(?:Fatalf?|Errorf?|FailNow|Fail)\(',core))
assert core_assertions==85
oldtests=re.findall(r'^func (Test\w+)\(',text,re.M)
newtests=re.findall(r'^func (Test\w+)\(',candidate,re.M)
assert newtests==oldtests+["TestNativeHarnessCleanupReviewContext"]
assert "time.Sleep(" not in added and "sql." not in added and "exec." not in added
# Source-only textual formatting preflight, NOT gofmt or Go AST.
assert not re.search(r'[ \t]+\r?$',candidate,re.M)
write("base-root/internal/domain/native_migration_authority_harness_windows_test.go",original)
candidate_ref=write("candidate-root/internal/domain/native_migration_authority_harness_windows_test.go",candidate.encode())
save("source-replacements.json",dict(original_block=old,replacement_block=new,appended_helper_and_tests=added,exact_inverse_bytes=True))
write("cleanup-context.patch","".join(difflib.unified_diff(text.splitlines(True),candidate.splitlines(True),fromfile="base/native_migration_authority_harness_windows_test.go",tofile="candidate/native_migration_authority_harness_windows_test.go")).encode())
save("static-preservation.json",dict(source_only=True,exact_inverse_original_bytes=True,base_ref=ref,candidate_ref=candidate_ref,nine_cases=case_names,original_core_assertion_calls=core_assertions,original_whole_file_assertion_calls=90,original_tests=oldtests,new_test="TestNativeHarnessCleanupReviewContext",new_pure_subtests=["expired-main-deadline","main-cancel-does-not-end-cleanup","cleanup-cancel-does-not-cancel-main","fresh-four-minute-deadline"],main20min_unchanged=True,grant4min_unchanged=True,cleanup_max_minutes=4,cleanup_started_inside_callback=True,cleanup_defer_cancel=True,explicit_fixture_release_gate_unchanged=True,Go_AST_gofmt_compile_test_ran=False,lexical_format_preflight=True))
assert all(pin(r["path"])==r for r in refs)
save("sourceguard.final.json",dict(refs=refs,all_unchanged=True,method="Source-only read and exact before-after pin",Main_canonical_unchanged_by_author=True))
print(json.dumps(dict(status="SOURCE_ONLY_PREPARED",candidate=candidate_ref,original_core_assertions=85,original_whole_file_assertions=90,nine_cases=case_names,new_native_SQL_model_Git_Go=False)))

