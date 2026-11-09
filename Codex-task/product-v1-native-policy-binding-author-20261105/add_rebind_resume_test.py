from pathlib import Path
import hashlib

p = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-policy-binding-20261105\internal\domain\runtime_harness_windows_test.go')
raw = p.read_bytes()
anchor = b'// The terminal persistence fault is installed only after the real owned fake\n'
addition = b'''// The binding changes after runHarness captures the old source path and before
// its suspended child resumes. No output from that child may enter the Task.
type harnessRebindAtStartDriver struct {
    rt.CodexDriver
    db *sql.DB
    service *Service
    binding *WorkspaceBinding
    original, replacement string
    starts atomic.Int64
}
func (d *harnessRebindAtStartDriver) Start(ctx context.Context, in rt.CodexLaunch, cb rt.CodexCallbacks) (rt.CodexHandle, error) {
    d.starts.Add(1)
    if in.Workspace != d.original { return nil, fmt.Errorf("driver source was not the admitted source") }
    tx, err := d.db.BeginTx(ctx, nil)
    if err != nil { return nil, err }
    defer tx.Rollback()
    d.binding.RealPath = d.replacement
    d.binding.Revision++
    if err = d.service.putOpaque(ctx, tx, "", KindWorkspaceBinding, d.binding.AuthorizedRef, d.binding.record()); err != nil { return nil, err }
    if err = tx.Commit(); err != nil { return nil, err }
    return d.CodexDriver.Start(ctx, in, cb)
}
func TestHarnessSourceRebindBeforeResume(t *testing.T) {
    exe := harnessExecutable(t)
    f, c, b := harnessFixture(t, exe)
    id, _ := harnessSubmitFixture(t, f, c, b, "COMPLETE")
    driver := &harnessRebindAtStartDriver{CodexDriver: c.config.HarnessDriver, db: f.db, service: f.s,
        binding: b, original: b.RealPath, replacement: t.TempDir()}
    c.config.HarnessDriver = driver
    if err := c.Scan(context.Background()); err != nil { t.Fatal(err) }
    c.workers.Wait()
    view := harnessViewFixture(t, f, c, id)
    if driver.starts.Load() != 1 || view["status"] == "COMPLETED" || view["result"] != nil {
        t.Fatalf("rebound source resumed or fabricated result: starts=%d view=%s", driver.starts.Load(), Bytes(view))
    }
    events, err := c.HarnessV1().Events(context.Background(), f.token, HarnessEvents{ProjectID: f.project, TaskID: id, Cursor: "0", Limit: 500})
    if err != nil { t.Fatal(err) }
    for _, item := range Arr(events["data"].(map[string]any), "items") {
        row := item.(map[string]any)
        if row["kind"] == "ASSISTANT_DELTA" { t.Fatal("suspended rebound child emitted assistant content") }
    }
    if err = c.Scan(context.Background()); err != nil { t.Fatal(err) }
    c.workers.Wait()
    if driver.starts.Load() != 1 { t.Fatal("rebound dispatch relaunched") }
}

'''
assert raw.count(anchor) == 1
p.write_bytes(raw.replace(anchor, addition + anchor, 1))
print(hashlib.sha256(p.read_bytes()).hexdigest())
