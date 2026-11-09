//go:build windows

package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"researchos.local/research-os/ops/supervisor"
)

func productFixture(t *testing.T) *productLayout {
	t.Helper()
	root := t.TempDir()
	data := filepath.Join(root, "data")
	if err := os.Mkdir(data, 0700); err != nil { t.Fatal(err) }
	return &productLayout{Root: root, Data: data,
		Discovery: filepath.Join(data, "discovery.json"),
		Binding: filepath.Join(data, "product-binding.json"),
		Witness: filepath.Join(data, "product-supervisor.json"),
		Marker: productMarker{InstallationID: strings.Repeat("a",64), Binaries: map[string]productBinary{
			"control": {SHA256: strings.Repeat("b",64)}, "electron": {SHA256: strings.Repeat("c",64)},
		}},
	}
}

func productWriteJSON(t *testing.T, name string, value any) {
	t.Helper()
	raw, err := json.Marshal(value)
	if err != nil { t.Fatal(err) }
	if err := os.WriteFile(name, raw, 0600); err != nil { t.Fatal(err) }
}

func TestProductHostRequiresTwoLiveExactProcessIdentities(t *testing.T) {
	p := productFixture(t)
	control := productProcessIdentity{PID: 4101, CreatedNS: "123", ImageSHA256: strings.Repeat("b",64)}
	parent := productProcessIdentity{PID: 4102, CreatedNS: "124", ImageSHA256: strings.Repeat("c",64)}
	productWriteJSON(t,p.Discovery,map[string]any{"url":"http://127.0.0.1:4321/","pid":4101,
		"data_dir":p.Data,"host_instance_id":"host-123456789abc"})
	productWriteJSON(t,p.Witness,productWitness{Schema:productWitnessSchema,
		InstallationID:p.Marker.InstallationID, DataRoot:p.Data, HostID:"host-123456789abc",
		Control:control, Parent:parent})
	previous := productObserve
	productObserve = func(pid uint32) (supervisor.ProcessIdentity,error) {
		switch pid {
		case control.PID: return supervisor.ProcessIdentity{PID:pid, CreatedNS:123, ImageSHA256:control.ImageSHA256},nil
		case parent.PID: return supervisor.ProcessIdentity{PID:pid, CreatedNS:124, ImageSHA256:parent.ImageSHA256},nil
		default: t.Fatalf("unexpected process %d",pid); return supervisor.ProcessIdentity{},nil
		}
	}
	t.Cleanup(func(){productObserve=previous})
	_, state, err := productSnapshot(p)
	if err != nil || state != "READY_CANDIDATE" { t.Fatalf("state=%s err=%v",state,err) }
	parent.CreatedNS = "125"
	productWriteJSON(t,p.Witness,productWitness{Schema:productWitnessSchema,
		InstallationID:p.Marker.InstallationID, DataRoot:p.Data, HostID:"host-123456789abc",
		Control:control, Parent:parent})
	_, state, err = productSnapshot(p)
	if err == nil || state != "FOREIGN" { t.Fatalf("stale parent state=%s err=%v",state,err) }
}

func TestProductDataBindingRefusesNonemptyAndConflictingRoot(t *testing.T) {
	p := productFixture(t)
	if err := os.WriteFile(filepath.Join(p.Data,"existing.db"),[]byte("old"),0600); err != nil {t.Fatal(err)}
	if err := prepareProductData(p); err == nil || err.Error() != "PRODUCT_DATA_UNBOUND" {t.Fatalf("unbound: %v",err)}
	if err := os.Remove(filepath.Join(p.Data,"existing.db")); err != nil {t.Fatal(err)}
	if err := prepareProductData(p); err != nil {t.Fatal(err)}
	productWriteJSON(t,p.Binding,map[string]any{"schema":productBindingSchema,"installation_id":strings.Repeat("d",64)})
	if err := prepareProductData(p); err == nil || err.Error() != "PRODUCT_DATA_INSTALLATION_CONFLICT" {t.Fatalf("conflict: %v",err)}
}
