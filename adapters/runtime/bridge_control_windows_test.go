//go:build windows

package runtime

import (
	"encoding/json"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
	"testing"
)

func TestBridgeQueueEmptyNeedsSDKProof(t *testing.T) {
	j := BridgeJournal{Manifest: json.RawMessage(`{"task_id":"task","run_id":"run","epoch":1,"admission":{"profile":{}}}`), QueueRequired: true, Frames: 4, Acknowledged: 4, State: "SETTLED", ProtocolComplete: true, Receipt: sandbox.Receipt{Stopped: true, StreamsDrained: true}}
	observation, err := j.Observation()
	if err != nil {
		t.Fatal(err)
	}
	if observation["queue_empty"] != false {
		t.Fatal("frame ACK count falsely proved SDK queue empty")
	}
	j.QueueSealed = true
	observation, err = j.Observation()
	if err != nil || observation["queue_empty"] != true {
		t.Fatal("sealed queue proof missing", err)
	}
	j.QueueSealed = false
	j.Cancelled = true
	observation, _ = j.Observation()
	if observation["queue_empty"] != false {
		t.Fatal("physical process death falsely proved queue empty")
	}
	j.QueueIdle = true
	j.QueueCancelIdle = true
	observation, _ = j.Observation()
	if observation["queue_empty"] != true {
		t.Fatal("cancel idle witness missing")
	}
}

func TestBridgeControlIdentityRejectsForeignProcessAndEpoch(t *testing.T) {
	identity := sandbox.Identity{PID: 12, Created: 123, Job: "job", SID: "sid", Profile: "profile", StagingDirectory: "stage"}
	bridge := &Bridge{journal: BridgeJournal{Manifest: json.RawMessage(`{"task_id":"task","run_id":"run","epoch":7}`), ManifestHash: "sha256:manifest", DispatchKey: "dispatch", Identity: identity}}
	raw := []byte(`{"task_id":"task","run_id":"run","runtime_epoch":7,"dispatch_key":"dispatch","manifest_hash":"sha256:manifest","queue_generation":"generation","process_identity":{"pid":12,"process_created_ns":"123","job":"job","appcontainer_sid":"sid","profile":"profile","staging_directory":"stage"}}`)
	good, err := bridgeMap(raw)
	if err != nil || bridge.validateControlBinding(good) != nil {
		t.Fatal("valid exact binding refused", err)
	}
	for _, field := range []string{"run_id", "task_id", "runtime_epoch", "dispatch_key", "manifest_hash", "process_identity"} {
		t.Run(field, func(t *testing.T) {
			bad, _ := bridgeMap(raw)
			bad[field] = "foreign"
			if bridge.validateControlBinding(bad) == nil {
				t.Fatal("foreign binding accepted")
			}
		})
	}
}
