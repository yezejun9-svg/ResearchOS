package recoveryauthority

import (
	"encoding/json"
	"strconv"
	"testing"
	"time"
)

// Synthetic parser fixtures prove reject/retain behavior only. They cannot mint
// a native Token or satisfy issuer/image/OS acceptance in production.
func historicalParserFixture(t *testing.T) (map[string][]byte, Tuple, []RawPin) {
	t.Helper()
	a, _, _, _, _ := testAdoption(t)
	tuple := a.Tuple
	raw := map[string][]byte{}
	for _, role := range requiredHistoryRoles {
		raw[role] = []byte("{}")
	}
	raw["stdout-admit"] = nil
	raw["stderr-admit"] = nil
	raw["stdout-execute"] = nil
	raw["stderr-execute"] = []byte("original diagnostic")
	raw["coordinator-source"] = []byte("original source")
	ref := func(role string) map[string]any {
		return map[string]any{"path": role, "sha256": digest(raw[role])[7:], "bytes": len(raw[role])}
	}
	raw["clock"] = encoded(map[string]any{"started_utc": a.RootStartedUTC, "deadline_utc": a.RootClockExpiredUTC, "clock_reset_permitted": false})
	raw["once"] = encoded(map[string]any{"state": "CONSUMED_FOR_HOST_GO", "qualification_run_id": tuple.RunID, "owner_pid": 1})
	raw["go"] = encoded(map[string]any{"qualification_run_id": tuple.RunID, "started_utc": a.RootStartedUTC, "execution_authority_ref": ref("original-authority"), "coordinator_source_ref": ref("coordinator-source")})
	held := map[string]any{"run_uuid": "old:host-execute-admitted", "owner_pid": 1, "runner_pid": 2, "creation_time_100ns": json.Number("134359521876434319"), "job_binding_id": "old-job", "captured_before_resume": true, "held_job_handle": true, "held_primary_handle": true}
	raw["contract"] = encoded(map[string]any{"held_identity": held, "root_pid": 1, "host_pid": 2, "root_job_id": "old-job", "deadline_utc": a.RootClockExpiredUTC})
	raw["probe"] = encoded(map[string]any{"held_identity": held, "root_pid": 1, "host_pid": 2, "root_job_id": "old-job", "captured_before_resume": true, "in_job": true, "descendant_of_root": true, "direct_CreateProcess_from_root": true, "actual_IsProcessInJob_return": true})
	jobs := []any{}
	for _, mode := range []string{"admit", "execute"} {
		label := "host-admit-only"
		exit := 0
		pid := 3
		birth := "134359521871765470"
		job := "old-admit-job"
		if mode == "execute" {
			label = "host-execute-admitted"
			exit = 1
			pid = 2
			birth = "134359521876434319"
			job = "old-job"
		}
		proof := map[string]any{"run_uuid": "old:" + label, "owner_pid": 1, "runner_pid": pid, "creation_time_100ns": json.Number(birth), "job_binding_id": job, "captured_before_resume": true, "held_job_handle": true, "held_primary_handle": true, "active_processes": 0, "primary_exit_confirmed": true, "primary_exit_code": exit, "pid_match": true, "creation_match": true, "errors": []any{}, "observed_monotonic": json.Number("338455.6112153")}
		producer := map[string]any{"run_uuid": "old:" + label, "owner_pid": 1, "closed": true, "job_handle_closed": true, "primary_handle_closed": true, "errors": []any{}}
		jobs = append(jobs, map[string]any{"label": label, "cleanup": map[string]any{"proof": proof, "producer": producer, "watchdog": map[string]any{"duplicate_handle_closed": true, "errors": []any{}}, "closed": true}})
		raw["invoke-"+mode] = encoded(map[string]any{"native_exit": exit, "error": "original failure retained", "stdout_ref": ref("stdout-" + mode), "stderr_ref": ref("stderr-" + mode), "result": map[string]any{"owned_child_pid": pid, "creation_time_100ns": json.Number(birth), "actual_exit": exit, "resumed": true, "job_cleanup": map[string]any{"assigned_before_resume": true, "unnamed_exclusive_job": true, "kill_on_job_close_configured": true, "active_processes_last_observed": 0, "job_idle_confirmed": true, "primary_exit_confirmed": true, "handles_closed": true, "errors": []any{}}}})
	}
	guardRef := ref("clock")
	guardRef["verified"] = true
	guardRef["final_path_match"] = true
	guardRef["closed"] = true
	raw["lifecycle"] = encoded(map[string]any{"state": "FAILED_EXECUTION_CLOSED", "error": "original failure", "go_sent": true, "actual_parent_pid": 1, "provider_requests": nil, "automatic_retry": false, "jobs": jobs, "source_guard_cleanup": []any{map[string]any{"closed": true, "verification": "PASSED", "share_mode": "FILE_SHARE_READ_ONLY", "retained_handles_count": 0, "errors": []any{}, "entries": []any{guardRef}}}})
	pins := []RawPin{}
	for role, data := range raw {
		pins = append(pins, RawPin{Role: role, Path: role, SHA256: digest(data), Bytes: int64(len(data))})
	}
	return raw, tuple, pins
}
func TestAuthorityHistoricalParserPreservesLosslessFactsAndRejectsFootprint(t *testing.T) {
	raw, tuple, pins := historicalParserFixture(t)
	observed, _, _, err := readHistorical(raw, tuple, pins)
	if err != nil {
		t.Fatal(err)
	}
	if observed.HostBirth100ns != "134359521876434319" || observed.ClosedObservedMonotonic != "338455.6112153" || observed.ExactJobClosedUTC != nil || observed.OriginalRootSignature != nil {
		t.Fatal("historical facts rewritten")
	}
	for _, mutation := range []string{"reopen-job", "erase-error", "provider-zero", "reuse-once", "reset-clock", "omit-transitive-source"} {
		t.Run(mutation, func(t *testing.T) {
			raw, tuple, pins := historicalParserFixture(t)
			life, err := historyObject(raw["lifecycle"])
			if err != nil {
				t.Fatal(err)
			}
			switch mutation {
			case "reopen-job":
				jobs := life["jobs"].([]any)
				obj(obj(jobs[1].(map[string]any), "cleanup"), "proof")["active_processes"] = json.Number("1")
				raw["lifecycle"] = encoded(life)
			case "erase-error":
				life["error"] = ""
				raw["lifecycle"] = encoded(life)
			case "provider-zero":
				life["provider_requests"] = json.Number("0")
				raw["lifecycle"] = encoded(life)
			case "reuse-once":
				once, _ := historyObject(raw["once"])
				once["qualification_run_id"] = "different"
				raw["once"] = encoded(once)
			case "reset-clock":
				clock, _ := historyObject(raw["clock"])
				clock["clock_reset_permitted"] = true
				clock["deadline_utc"] = time.Now().Add(time.Hour).UTC().Format(time.RFC3339Nano)
				raw["clock"] = encoded(clock)
			case "omit-transitive-source":
				kept := []RawPin{}
				for _, p := range pins {
					if p.Role != "coordinator-source" {
						kept = append(kept, p)
					}
				}
				pins = kept
			}
			// Rehashing a changed statement cannot manufacture its semantics.
			for i := range pins {
				if data, ok := raw[pins[i].Role]; ok {
					pins[i].SHA256 = digest(data)
					pins[i].Bytes = int64(len(data))
				}
			}
			if _, _, _, err = readHistorical(raw, tuple, pins); err == nil {
				t.Fatal("unsafe historical mutation accepted: " + mutation + strconv.Itoa(len(raw)))
			}
		})
	}
}
