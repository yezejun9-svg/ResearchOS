//go:build windows

package main

import (
	"path/filepath"
	"strings"
	"testing"
)

func TestControlReplayRefusesOrdinaryToken(t *testing.T) {
	handled, err := runFixtureControlReplay([]string{"--fixture-control-replay", filepath.Join(t.TempDir(), "absent-request.json")})
	if !handled || err == nil || !strings.Contains(err.Error(), "requires AppContainer") {
		t.Fatalf("ordinary token must be refused before request read: handled=%v err=%v", handled, err)
	}
	t.Log("ordinary token refused before request read")
}

func TestControlReplaySecondWriterRefused(t *testing.T) {
	root := t.TempDir()
	first, err := replayOutputLease(root)
	if err != nil {
		t.Fatal(err)
	}
	defer first.Close()
	second, err := replayOutputLease(root)
	if err == nil {
		second.Close()
		t.Fatal("second writer acquired same replay data root")
	}
	t.Logf("second writer refused while first lock held: %v", err)
}
