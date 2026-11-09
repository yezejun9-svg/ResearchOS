from review_tools import E, W, write, pin

source = W/'internal/host/runtime_pause_windows_test.go'
raw = source.read_text(encoding='utf-8')
raw = raw.replace('func productMuPauseNative(t *testing.T, cancelPaused bool, preparedRecovery ...bool) {', '''func TestReviewMuSecondPauseNative(t *testing.T) {
	productMuPauseNative(t, false)
}

func productMuPauseNative(t *testing.T, cancelPaused bool, preparedRecovery ...bool) {
	secondPause := t.Name() == "TestReviewMuSecondPauseNative"
	resumeArrived, resumeRelease := make(chan struct{}), make(chan struct{})
	var resumeOnce sync.Once
	defer resumeOnce.Do(func() { close(resumeRelease) })''')
raw = raw.replace('\t\tif n == 2 {', '''		if n == 4 && secondPause {
			close(resumeArrived)
			select {
			case <-resumeRelease:
			case <-ctx.Done():
				return
			}
		}
		if n == 2 {''')
needle = '\twait("same Run settles after native resume", func() bool {'
assert raw.count(needle) == 1
raw = raw.replace(needle, '''	if secondPause {
		wait("resumed model in flight", func() bool {
			select { case <-resumeArrived: return true; default: return false }
		})
		status, _, headers = httpCall(resumeToken, "GET", path, "", "", nil)
		if status != 200 { t.Fatal(status) }
		status, secondResult, _ := httpCall(resumeToken, "POST", path+"/actions", domain.ID(), headers.Get("ETag"), domain.Object{"action":"PAUSE", "reason":"independent second pause during resumed model"})
		resumeOnce.Do(func() { close(resumeRelease) })
		var secondState string
		deadline := time.Now().Add(15*time.Second)
		for time.Now().Before(deadline) {
			_ = c.Scan(ctx)
			_ = db.QueryRow(`SELECT state FROM runtime_pause_intents WHERE run=? AND epoch=2`, runID).Scan(&secondState)
			if secondState == "PAUSED_CONFIRMED" { break }
			time.Sleep(50*time.Millisecond)
		}
		evidence := domain.Object{"classification":"NATIVE_SYNTHETIC_INDEPENDENT_SECOND_PAUSE", "http_status":status, "http_result":secondResult, "second_pause_state":secondState, "synthetic_model_calls":calls.Load(), "actual_host_tool_calls":tools.Load(), "live_model_calls":0, "formal_increment":0}
		for name, query := range map[string]string{"pause_intents":"SELECT * FROM runtime_pause_intents", "pause_receipts":"SELECT * FROM runtime_pause_receipts", "activations":"SELECT * FROM runtime_checkpoint_activations", "dispatches":"SELECT * FROM runtime_dispatches", "queue":"SELECT * FROM client_command_queue", "objects":"SELECT * FROM domain_objects WHERE kind IN ('Run','Task')"} {
			evidence[name] = pauseNativeRows(t, db, query)
		}
		evidenceDir := filepath.Join(*pauseNativeEvidence, t.Name())
		if err = os.MkdirAll(evidenceDir, 0700); err != nil { t.Fatal(err) }
		if err = os.WriteFile(filepath.Join(evidenceDir,"canonical-evidence.json"), domain.Bytes(evidence), 0600); err != nil { t.Fatal(err) }
		if status != 200 || secondResult["status"] != "BLOCKED" || secondState != "PAUSED_CONFIRMED" {
			t.Fatalf("second PAUSE HTTP=%d task=%v intent=%s; canonical evidence retained", status, secondResult["status"], secondState)
		}
		return
	}
''' + needle)
overlayfile=E/'review-runtime_pause_windows_test.go'
overlayfile.write_text(raw,encoding='utf-8')
write(E/'review-overlay.json',{'Replace':{str(source):str(overlayfile)}})
write(E/'review-overlay-inputs.json',{'source':pin(source),'overlay':pin(overlayfile),'purpose':'Exercise ordinary HTTP PAUSE again while the actual resumed AppContainer has a synthetic model request in flight; production source unchanged.'})
