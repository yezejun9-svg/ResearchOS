//go:build windows

package main

import "testing"

func TestQualificationMaintenanceEarlyArgumentIsolation(t *testing.T) {
	for _, args := range [][]string{
		{"--qualification-failure-maintenance", "preflight", "--data-root", "C:/fixture", "--proposal", "C:/proposal.json", "--out", "C:/plan.json"},
		{"--qualification-failure-maintenance", "commit", "--data-root", "C:/fixture", "--plan", "C:/plan.json", "--plan-sha256", "sha256:abc", "--operation-id", "id"},
		{"--qualification-failure-maintenance", "recover", "--data-root", "C:/fixture", "--plan", "C:/plan.json", "--plan-sha256", "sha256:abc", "--operation-id", "id"},
		{"--qualification-failure-maintenance", "abort", "--data-root", "C:/fixture", "--plan", "C:/plan.json", "--plan-sha256", "sha256:abc", "--operation-id", "id"},
	} {
		if err := classifyControlEarlyMode(args); err != nil {
			t.Fatal(err)
		}
		if _, err := parseQualificationMaintenance(args); err != nil {
			t.Fatalf("%v: %v", args, err)
		}
	}
	for _, args := range [][]string{
		{"--bootstrap-owner", "--qualification-failure-maintenance", "preflight"},
		{"--qualification-failure-maintenance=preflight"},
		{"--qualification-failure-maintenance", "preflight", "--data-root", "C:/fixture", "--proposal", "C:/proposal.json", "--out", "C:/plan.json", "--data-root", "C:/other"},
		{"--qualification-failure-maintenance", "commit", "--data-root", "C:/fixture", "--plan", "C:/plan.json", "--plan-sha256", "sha256:abc"},
		{"--qualification-failure-maintenance", "commit", "--data-root", "C:/fixture", "--plan", "C:/plan.json", "--plan-sha256", "sha256:abc", "--operation-id", "id", "--bootstrap-owner"},
	} {
		if classifyControlEarlyMode(args) == nil {
			if _, err := parseQualificationMaintenance(args); err == nil {
				t.Fatalf("mixed/partial mode accepted: %v", args)
			}
		}
	}
	if handled, err := runQualificationFailureMaintenance([]string{"--bootstrap-owner"}); handled || err != nil {
		t.Fatal("nonqualification early mode captured")
	}
	if handled, err := runQualificationFailureMaintenance([]string{"--qualification-failure-maintenance", "commit"}); !handled || err == nil {
		t.Fatal("malformed qualification mode reached host")
	}
}
