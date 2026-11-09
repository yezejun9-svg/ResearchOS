//go:build windows

package main

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/ops/supervisor"
)

func productFixture(t *testing.T) *productLayout {
	t.Helper()
	root := t.TempDir()
	data := filepath.Join(root, "data")
	if err := os.Mkdir(data, 0700); err != nil {
		t.Fatal(err)
	}
	return &productLayout{Root: root, Base: root, Data: data, Electron: filepath.Join(root, "electron.exe"),
		Discovery: filepath.Join(data, "discovery.json"),
		Config:    filepath.Join(root, "cli-config.json"),
		Binding:   filepath.Join(data, "product-binding.json"),
		Witness:   filepath.Join(data, "product-supervisor.json"),
		Marker: productMarker{InstallationID: strings.Repeat("a", 64), InventoryDigest: strings.Repeat("d", 64), Binaries: map[string]productBinary{
			"control": {Path: "control.exe", SHA256: strings.Repeat("b", 64)}, "electron": {Path: "electron.exe", SHA256: strings.Repeat("c", 64)},
		}},
	}
}

func productWriteJSON(t *testing.T, name string, value any) {
	t.Helper()
	raw, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(name, raw, 0600); err != nil {
		t.Fatal(err)
	}
}

func TestProductHostRequiresTwoLiveExactProcessIdentities(t *testing.T) {
	p := productFixture(t)
	control := productProcessIdentity{PID: 4101, CreatedNS: "123", ImageSHA256: strings.Repeat("b", 64)}
	parent := productProcessIdentity{PID: 4102, CreatedNS: "124", ImageSHA256: strings.Repeat("c", 64)}
	productWriteJSON(t, p.Discovery, map[string]any{"url": "http://127.0.0.1:4321/", "pid": 4101,
		"data_dir": p.Data, "host_instance_id": "host-123456789abc"})
	productWriteJSON(t, p.Witness, productWitness{Schema: productWitnessSchema, State: "READY", InstallRoot: p.Root,
		InventoryDigest: p.Marker.InventoryDigest, Nonce: "fixture-1", InstallationID: p.Marker.InstallationID, DataRoot: p.Data, HostID: "host-123456789abc",
		Control: control, Parent: parent})
	previous := productObserve
	previousExtra := productProcessExtra
	productProcessExtra = func(pid uint32, image string, parentPID uint32) error {
		if pid == control.PID && (parentPID != parent.PID || image != filepath.Join(p.Root, "control.exe")) {
			return errors.New("wrong core origin")
		}
		if pid == parent.PID && (parentPID != 0 || image != p.Electron) {
			return errors.New("wrong parent image")
		}
		return nil
	}
	productObserve = func(pid uint32) (supervisor.ProcessIdentity, error) {
		switch pid {
		case control.PID:
			return supervisor.ProcessIdentity{PID: pid, CreatedNS: 123, ImageSHA256: control.ImageSHA256}, nil
		case parent.PID:
			return supervisor.ProcessIdentity{PID: pid, CreatedNS: 124, ImageSHA256: parent.ImageSHA256}, nil
		default:
			t.Fatalf("unexpected process %d", pid)
			return supervisor.ProcessIdentity{}, nil
		}
	}
	t.Cleanup(func() { productObserve = previous; productProcessExtra = previousExtra })
	observed, err := productReadSnapshot(p)
	if err != nil || observed.State != "READY_CANDIDATE" {
		t.Fatalf("state=%s err=%v", observed.State, err)
	}
	parent.CreatedNS = "125"
	productWriteJSON(t, p.Witness, productWitness{Schema: productWitnessSchema, State: "READY", InstallRoot: p.Root,
		InventoryDigest: p.Marker.InventoryDigest, Nonce: "fixture-1", InstallationID: p.Marker.InstallationID, DataRoot: p.Data, HostID: "host-123456789abc",
		Control: control, Parent: parent})
	observed, err = productReadSnapshot(p)
	if err == nil || observed.State != "FOREIGN" {
		t.Fatalf("stale parent state=%s err=%v", observed.State, err)
	}
}

func TestProductDataBindingRefusesNonemptyAndConflictingRoot(t *testing.T) {
	p := productFixture(t)
	if err := os.WriteFile(filepath.Join(p.Data, "existing.db"), []byte("old"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := prepareProductData(p); err == nil || err.Error() != "PRODUCT_DATA_UNBOUND" {
		t.Fatalf("unbound: %v", err)
	}
	if err := os.Remove(filepath.Join(p.Data, "existing.db")); err != nil {
		t.Fatal(err)
	}
	if err := prepareProductData(p); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(p.Binding); !os.IsNotExist(err) {
		t.Fatalf("CLI wrote binding: %v", err)
	}
	productWriteJSON(t, p.Binding, map[string]any{"schema": productBindingSchema, "installation_id": strings.Repeat("d", 64)})
	if err := prepareProductData(p); err == nil || err.Error() != "PRODUCT_DATA_INSTALLATION_CONFLICT" {
		t.Fatalf("conflict: %v", err)
	}
}

func TestProductHostStartsOnlyForBoundCommands(t *testing.T) {
	for _, command := range []string{"", "--project", "init", "goal", "status", "task", "/model"} {
		if !requiresProductHost(command) {
			t.Fatalf("host-bound %q skipped", command)
		}
	}
	if !requiresProductHost("config", "set-model") {
		t.Fatal("config set-model skipped host")
	}
	for _, command := range []string{"doctor", "version", "--version", "help", "--help", "/help", "commands", "typo", "--unknown"} {
		if requiresProductHost(command) {
			t.Fatalf("read-only or invalid %q started host", command)
		}
	}
	for _, args := range [][]string{{}, {"show"}, {"settle-run"}} {
		if requiresProductHost("config", args...) {
			t.Fatalf("local config %q started host", args)
		}
	}
}

func TestProductInteractiveRequiresSelectedProject(t *testing.T) {
	if got := productInteractiveSelectionReason(cliConfig{}, ""); got != "PROJECT_SELECTION_REQUIRED" {
		t.Fatal(got)
	}
	cfg := cliConfig{ProjectID: "project-one", WorkspaceRef: "workspace-one"}
	if got := productInteractiveSelectionReason(cfg, "project-two"); got != "PROJECT_SELECTION_CONFLICT" {
		t.Fatal(got)
	}
	if got := productInteractiveSelectionReason(cfg, "project-one"); got != "" {
		t.Fatal(got)
	}
}

func TestProductStartingIgnoresOnlyDeadPreviousDiscovery(t *testing.T) {
	p := productFixture(t)
	parent := productProcessIdentity{PID: 4102, CreatedNS: "124", ImageSHA256: strings.Repeat("c", 64)}
	starting := productWitness{Schema: productWitnessSchema, State: "STARTING", InstallRoot: p.Root,
		InstallationID: p.Marker.InstallationID, InventoryDigest: p.Marker.InventoryDigest,
		DataRoot: p.Data, Nonce: "fresh", Parent: parent}
	productWriteJSON(t, p.Witness, starting)
	productWriteJSON(t, p.Discovery, map[string]any{"url": "http://127.0.0.1:4321/", "pid": 4101,
		"data_dir": p.Data, "host_instance_id": "host-123456789abc"})
	beforeObserve, beforeExtra, beforeGone := productObserve, productProcessExtra, productGone
	productObserve = func(pid uint32) (supervisor.ProcessIdentity, error) {
		if pid == parent.PID {
			return supervisor.ProcessIdentity{PID: pid, CreatedNS: 124, ImageSHA256: parent.ImageSHA256}, nil
		}
		return supervisor.ProcessIdentity{}, errors.New("previous core exited")
	}
	productProcessExtra = func(pid uint32, image string, parentPID uint32) error {
		if pid == parent.PID && image == p.Electron && parentPID == 0 {
			return nil
		}
		return errors.New("wrong origin")
	}
	productGone = func(pid uint32) (bool, error) { return pid == 4101, nil }
	t.Cleanup(func() { productObserve, productProcessExtra, productGone = beforeObserve, beforeExtra, beforeGone })
	got, err := productReadSnapshot(p)
	if err != nil || got.State != "STARTING" {
		t.Fatalf("dead previous discovery: %s %v", got.State, err)
	}
	starting.State = "READY"
	productWriteJSON(t, p.Witness, starting)
	got, err = productReadSnapshot(p)
	if err == nil || got.State != "FOREIGN" {
		t.Fatalf("ready record with dead core: %s %v", got.State, err)
	}
}

func TestEnsureProductHostWaitsForNativeReadyWithoutSecondLaunch(t *testing.T) {
	p := productFixture(t)
	previousProduct, previousSnapshot, previousStatus := currentProduct, productSnapshot, productStatus
	previousLaunch, previousNow, previousSleep := productLaunch, productNow, productSleep
	currentProduct = p
	now := time.Unix(100, 0)
	productNow = func() time.Time { return now }
	productSleep = func(d time.Duration) { now = now.Add(d) }
	launches, snapshots, checks := 0, 0, 0
	productLaunch = func(*productLayout) error { launches++; return nil }
	productSnapshot = func(*productLayout) (productObservation, error) {
		snapshots++
		if snapshots == 1 {
			return productObservation{State: "ABSENT"}, nil
		}
		if snapshots == 2 {
			return productObservation{State: "STARTING"}, nil
		}
		return productObservation{State: "READY_CANDIDATE"}, nil
	}
	productStatus = func(*productLayout, productObservation) error {
		checks++
		if checks == 1 {
			return errors.New("native still starting")
		}
		return nil
	}
	t.Cleanup(func() {
		currentProduct, productSnapshot, productStatus = previousProduct, previousSnapshot, previousStatus
		productLaunch, productNow, productSleep = previousLaunch, previousNow, previousSleep
	})
	if err := ensureProductHost(); err != nil || launches != 1 || checks != 2 {
		t.Fatalf("ready wait err=%v launches=%d checks=%d", err, launches, checks)
	}
}

func TestProductStartingRequiresMatchingLiveSingleton(t *testing.T) {
	p := productFixture(t)
	parent := productProcessIdentity{PID: 4102, CreatedNS: "124", ImageSHA256: strings.Repeat("c", 64)}
	control := supervisor.ProcessIdentity{PID: 4101, CreatedNS: 123, ImageSHA256: strings.Repeat("b", 64)}
	beforeObserve, beforeExtra := productObserve, productProcessExtra
	productObserve = func(pid uint32) (supervisor.ProcessIdentity, error) {
		if pid == parent.PID {
			return supervisor.ProcessIdentity{PID: pid, CreatedNS: 124, ImageSHA256: parent.ImageSHA256}, nil
		}
		if pid == control.PID {
			return control, nil
		}
		return supervisor.ProcessIdentity{}, errors.New("not found")
	}
	productProcessExtra = func(pid uint32, image string, parentPID uint32) error {
		if pid == parent.PID && image == p.Electron && parentPID == 0 {
			return nil
		}
		if pid == control.PID && image == filepath.Join(p.Root, "control.exe") && parentPID == parent.PID {
			return nil
		}
		return errors.New("wrong origin")
	}
	t.Cleanup(func() { productObserve = beforeObserve; productProcessExtra = beforeExtra })
	starting := productWitness{Schema: productWitnessSchema, State: "STARTING", InstallRoot: p.Root,
		InstallationID: p.Marker.InstallationID, InventoryDigest: p.Marker.InventoryDigest,
		DataRoot: p.Data, Nonce: "one", Parent: parent}
	productWriteJSON(t, p.Witness, starting)
	got, err := productReadSnapshot(p)
	if err != nil || got.State != "STARTING" {
		t.Fatalf("matching parent %s %v", got.State, err)
	}
	productWriteJSON(t, p.Discovery, map[string]any{"url": "http://127.0.0.1:4321/", "pid": 4101,
		"data_dir": p.Data, "host_instance_id": "host-123456789abc"})
	got, err = productReadSnapshot(p)
	if err != nil || got.State != "STARTING" {
		t.Fatalf("Core during startup %s %v", got.State, err)
	}
	if err := os.Remove(p.Witness); err != nil {
		t.Fatal(err)
	}
	got, err = productReadSnapshot(p)
	if err == nil || got.State != "FOREIGN" {
		t.Fatalf("live Core without record %s %v", got.State, err)
	}
	starting.InstallRoot = filepath.Join(p.Root, "other")
	productWriteJSON(t, p.Witness, starting)
	got, err = productReadSnapshot(p)
	if err == nil || got.State != "FOREIGN" {
		t.Fatalf("foreign install root %s %v", got.State, err)
	}
}
