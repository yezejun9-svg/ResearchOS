from pathlib import Path

path = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-normal-home-binding-20261105\adapters\runtime\codex_qualification_windows_test.go")
with path.open("r", encoding="utf-8", newline="") as stream:
    text = stream.read()
marker = "func TestQualificationNormalHomeEarlyGateRejectsChangedOrEmptyProfile(t *testing.T) {"
if text.count(marker) != 1:
    raise RuntimeError("early gate marker is not unique")
addition = '''func TestQualificationNormalHomeEarlyGateAcceptsSlashEquivalentProfile(t *testing.T) {
\tq, _ := qualifiedFixture(t)
\tq.rpc.options.NormalHome = filepath.Clean(q.rpc.options.NormalHome)
\tt.Setenv("USERPROFILE", filepath.ToSlash(q.rpc.options.NormalHome))
\t// A deliberately mismatched synthetic helper digest stops before collector
\t// launch, after the home gate and its existing private-root checks.
\tq.options.ShippedHelperSHA256 = Hash([]byte("different synthetic helper"))
\tin := CodexLaunch{TaskID: "task", RunID: "run", Epoch: "1", Workspace: q.options.SyntheticSource, Directory: filepath.Join(q.options.ApprovedRoot, "run"), SourceBindingHash: "sha256:source"}
\tobs, err := q.ensureLaunch(context.Background(), in)
\tif err == nil || err.Error() != "QUALIFICATION_BOOTSTRAP_BLOCKED" || obs.ReceiptPath == "" || !obs.PreflightNoChild || obs.Capture.PID != 0 || q.state != "FAILED" {
\t\tt.Fatal("separator-equivalent home failed the early gate or reached a child", obs.ReceiptPath, obs.Capture.PID, q.state, err)
\t}
}

'''
text = text.replace(marker, addition + marker)
with path.open("w", encoding="utf-8", newline="") as stream:
    stream.write(text)
