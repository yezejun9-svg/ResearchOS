//go:build windows

package main

import (
	"context"
	"errors"
	"os"

	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/ops/supervisor"
)

// The same inherited peer/MAC boundary carries thin current-proof requests.
// It grants no release action and never returns the request or its credentials.
func (d *controlDrain) currentControl(ctx context.Context, frame supervisor.DrainFrame) (supervisor.ReleasePrivateMessage, error) {
	var out supervisor.ReleasePrivateMessage
	if d.startup == nil || d.startup.FixtureStore == "" || frame.Release == nil || frame.Release.Snapshot == nil {
		return out, errors.New("CURRENT_CONTROL_INHERITED_CAPABILITY_REQUIRED")
	}
	if d.service == nil || d.lease == nil || !d.lease.Held() || d.lease.Root() != d.root || d.listener == nil || d.listener.Addr().String() != d.startup.Listener || d.gate == nil || d.operation != "" {
		return out, errors.New("CURRENT_CONTROL_OWNER_NOT_READY")
	}
	if d.coordinator != nil && !d.coordinator.StartupReady() {
		return out, errors.New("CURRENT_CONTROL_STARTUP_INCOMPLETE")
	}
	identity, err := supervisor.ObserveProcess(uint32(os.Getpid()))
	snapshot := frame.Release.Snapshot
	if err != nil || snapshot.Phase != "STABLE" || snapshot.Operation != frame.Operation || snapshot.Epoch != frame.Epoch || snapshot.Data != d.root || snapshot.PID != identity.PID || snapshot.CreatedNS != identity.CreatedNS || snapshot.ImageSHA256 != identity.ImageSHA256 || snapshot.Active != identity.ImageSHA256 {
		return out, errors.New("CURRENT_CONTROL_HOST_SNAPSHOT_CHANGED")
	}
	var request evolution.ControlCurrentRequest
	if err = evolution.StrictControlJSON(frame.Release.Request, &request); err != nil {
		return out, errors.New("CURRENT_CONTROL_REQUEST_INVALID")
	}
	switch request.Phase {
	case "SAMPLE", "REGISTER", "FREEZE", "EVALUATE", "SEAL":
	default:
		return out, errors.New("CURRENT_CONTROL_PHASE_INVALID")
	}
	d.gate.mu.Lock()
	if d.gate.closing || d.gate.quiesced {
		d.gate.mu.Unlock()
		return out, errors.New("CURRENT_CONTROL_INGRESS_CLOSED")
	}
	d.gate.inflight++
	d.gate.requests.Add(1)
	d.gate.mu.Unlock()
	defer func() {
		d.gate.mu.Lock()
		d.gate.inflight--
		d.gate.mu.Unlock()
		d.gate.requests.Done()
	}()
	if !d.currentConfigured {
		root, err := os.Getwd()
		if err != nil {
			return out, errors.New("CURRENT_CONTROL_SOURCE_ROOT_UNAVAILABLE")
		}
		if err = d.service.ConfigureCurrentControlHost([]string{root}); err != nil {
			return out, err
		}
		d.currentConfigured = true
	}
	result, err := d.service.HandleCurrentControlFixture(ctx, d.lease, request)
	if err != nil {
		return out, err
	}
	out.Result = evolution.Bytes(result)
	return out, nil
}
