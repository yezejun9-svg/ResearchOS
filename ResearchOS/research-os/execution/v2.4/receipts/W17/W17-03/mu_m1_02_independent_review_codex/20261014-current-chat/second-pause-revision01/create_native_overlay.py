from review_tools import E,W,write,pin
src=W/'internal/host/runtime_pause_windows_test.go'
raw=src.read_text(encoding='utf-8')
marker='func productMuPauseNative(t *testing.T, cancelPaused, recoverPrepared, secondPause, delayToolPublish bool) {'
assert raw.count(marker)==1
raw=raw.replace(marker,'''func TestReviewMuSecondPauseAcrossHeartbeatNative(t *testing.T) {
	productMuPauseNative(t, false, false, true, false)
}

func TestReviewMuBudgetFailureRollsBackNativeSuccessor(t *testing.T) {
	productMuPauseNative(t, false, false, false, false)
}

'''+marker)
marker='\t\tresumedOnce.Do(func() { close(resumedRelease) })'
assert raw.count(marker)==1
raw=raw.replace(marker,'''\t\tif t.Name() == "TestReviewMuSecondPauseAcrossHeartbeatNative" {
			// Keep the already admitted response in flight across the real 15s
			// periodic heartbeat; the synthetic model request has not failed.
			select {
			case <-time.After(17 * time.Second):
			case <-ctx.Done(): t.Fatal(ctx.Err())
			}
		}
'''+marker)
marker='\tif recoverPrepared {\n\t\t// Simulate loss of the volatile post-commit lease:'
assert raw.count(marker)==1
raw=raw.replace(marker,'''\tif t.Name() == "TestReviewMuBudgetFailureRollsBackNativeSuccessor" {
		request := "runtime-local-launch/" + runID + "/1"
		var held string
		if err = db.QueryRow(`SELECT body FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_event_id')=?`, projectID, request).Scan(&held); err != nil { t.Fatal(err) }
		hold, decodeErr := domain.Decode([]byte(held))
		if decodeErr != nil { t.Fatal(decodeErr) }
		forged := domain.Merge(domain.Base(projectID), domain.Object{"policy_id":hold["policy_id"], "run_id":runID, "operation":"RELEASE", "money":hold["money"], "provider_request_id":request, "provider_event_id":request+"/released", "reservation_id":domain.ID(), "cost_basis":"ACTUAL", "occurred_at":domain.Now()})
		delete(forged,"updated_at")
		forged["receipt_hash"] = domain.Receipt(forged)
		if _, err = db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,content_hash,immutable) VALUES(?,'BudgetLedgerEntry',?,1,?,?,1)`, projectID,forged["id"],string(domain.Bytes(forged)),domain.Hash(forged)); err != nil { t.Fatal(err) }
		capture := func() domain.Object {
			result := domain.Object{}
			for name,query := range map[string]string{"objects":"SELECT * FROM domain_objects WHERE kind IN ('Run','Task','BudgetLedgerEntry') ORDER BY kind,id", "intents":"SELECT * FROM runtime_pause_intents ORDER BY project,run,epoch", "receipts":"SELECT * FROM runtime_pause_receipts ORDER BY project,pause_id,sequence", "activations":"SELECT * FROM runtime_checkpoint_activations ORDER BY project,run,epoch", "carries":"SELECT * FROM resource_checkpoint_carries ORDER BY rowid", "dispatches":"SELECT * FROM runtime_dispatches ORDER BY project,run,epoch"} {
				result[name] = pauseNativeRows(t,db,query)
			}
			return result
		}
		before := capture()
		err = c.Scan(ctx)
		after := capture()
		evidenceDir := filepath.Join(*pauseNativeEvidence,t.Name())
		if makeErr := os.MkdirAll(evidenceDir,0700); makeErr != nil { t.Fatal(makeErr) }
		evidence := domain.Object{"classification":"NATIVE_SETUP_CANONICAL_FAULT_INJECTION", "production_source_modified":false, "fault":"valid receipt, wrong reservation_id on synthetic DB only", "scan_error":fmt.Sprint(err), "before":before, "after":after, "same_state":domain.Hash(before)==domain.Hash(after), "synthetic_model_calls":calls.Load(), "actual_host_tool_calls":tools.Load(), "formal_increment":0}
		if writeErr := os.WriteFile(filepath.Join(evidenceDir,"canonical-evidence.json"),domain.Bytes(evidence),0600); writeErr != nil { t.Fatal(writeErr) }
		if err == nil || !strings.Contains(err.Error(),"invalid prior runtime local launch release") { t.Fatalf("wrong native successor error: %v",err) }
		if domain.Hash(before) != domain.Hash(after) { t.Fatal("failed native successor changed Run/Task/pause/receipt/carry/activation/dispatch/ledger state") }
		t.Log("NATIVE_SETUP_CANONICAL_FAULT_INJECTION wrong release rejected, complete successor transaction unchanged; source unchanged")
		return
	}
'''+marker)
target=E/'overlay-runtime_pause_windows_test.go';target.write_text(raw,encoding='utf-8')
write(E/'native-overlay.json',{'Replace':{str(src):str(target)}})
write(E/'native-overlay-inputs.json',{'purpose':'Test-only native probes: second pause crosses real 15s heartbeat; malformed release in synthetic DB exercises complete successor rollback. Production source unchanged.','source':pin(src),'overlay':pin(target)})
