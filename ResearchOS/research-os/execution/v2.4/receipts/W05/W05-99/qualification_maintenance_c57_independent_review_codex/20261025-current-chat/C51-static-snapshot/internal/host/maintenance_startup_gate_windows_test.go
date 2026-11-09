//go:build windows

package host

import (
	"os"
	"path/filepath"
	"testing"

	"researchos.local/research-os/internal/qualificationmaintenancejournal"
)

func TestQualificationMaintenanceRootGateBothNamespaces(t *testing.T) {
	for _, namespace := range []string{qualificationmaintenancejournal.QualificationNamespace,
		qualificationmaintenancejournal.ReplacementNamespace} {
		t.Run(namespace, func(t *testing.T) {
			root := t.TempDir()
			if err := QualificationMaintenanceRootGate(root); err != nil {
				t.Fatalf("clean root refused: %v", err)
			}
			if err := os.MkdirAll(filepath.Join(root, "host", namespace, "unknown-operation"), 0700); err != nil {
				t.Fatal(err)
			}
			if err := QualificationMaintenanceRootGate(root); err == nil {
				t.Fatal("startup gate admitted an unclassified maintenance namespace")
			}
		})
	}
}
