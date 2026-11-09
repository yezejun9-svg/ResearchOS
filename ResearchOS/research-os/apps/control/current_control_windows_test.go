//go:build windows

package main

import (
	"context"
	"strings"
	"testing"

	"researchos.local/research-os/ops/supervisor"
)

func TestCurrentControlPrivateGate(t *testing.T) {
	d := &controlDrain{}
	frame := supervisor.DrainFrame{Release: &supervisor.ReleasePrivateMessage{Snapshot: &supervisor.ReleaseState{}}}
	if _, err := d.currentControl(context.Background(), frame); err == nil || !strings.Contains(err.Error(), "INHERITED_CAPABILITY_REQUIRED") {
		t.Fatalf("current proof without inherited capability: %v", err)
	}
	d.startup = &supervisor.DrainBootstrap{FixtureStore: "inherited-fixture-locator"}
	if _, err := d.currentControl(context.Background(), frame); err == nil || !strings.Contains(err.Error(), "OWNER_NOT_READY") {
		t.Fatalf("current proof without held native owner lease: %v", err)
	}
	t.Log("current proof requires inherited capability and actual ready owner before domain access")
}
