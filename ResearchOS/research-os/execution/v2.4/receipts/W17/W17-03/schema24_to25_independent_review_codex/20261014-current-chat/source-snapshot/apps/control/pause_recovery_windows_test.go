//go:build windows

package main

import (
	"path/filepath"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/recoveryauthority"
	"testing"
)

func TestPausePrivateControlRejectsBeforeNormalStartup(t *testing.T) {
	t.Setenv("RESEARCHOS_PRIVATE_ADOPTION_BOOTSTRAP_HANDLE", "")
	for _, args := range [][]string{{recoveryauthority.PauseMigrationArgument}, {recoveryauthority.PauseMigrationArgument, "--db", "invented.sqlite"}, {recoveryauthority.MigrationArgument}, {recoveryauthority.MaintenanceArgument}} {
		handled, err := runPreparedRecoveryMaintenance(args)
		if !handled || err == nil {
			t.Fatal("private mode fell through or accepted public caller", args, handled, err)
		}
	}
	if handled, err := runPreparedRecoveryMaintenance([]string{"--help"}); handled || err != nil {
		t.Fatal("ordinary flags intercepted", handled, err)
	}
}

func TestPausePrivateControlRejectsAmbiguousPathsBeforeDBOpen(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, "source.sqlite")
	opt := domain.PauseSchemaUpgradeOptions{Upgrade: domain.LocalUpgradeOptions{Source: path, SourceRoot: root, TargetRoot: root, SourceProgram: path, TargetProgram: path, KeyFile: path, Snapshot: root, Destination: root}, RehearsalProgram: path, HandoffBindingFile: path}
	binding := recoveryauthority.MigrationBinding{Root: root, Database: path}
	if err := pauseSchemaMaintenancePaths(binding, opt); err != nil {
		t.Fatal(err)
	}
	for _, which := range []string{"database-fragment", "source-fragment", "source-query", "root-fragment", "rehearsal-fragment", "binding-fragment", "database-mismatch", "relative"} {
		t.Run(which, func(t *testing.T) {
			b, o := binding, opt
			switch which {
			case "database-fragment":
				b.Database += "#other"
			case "source-fragment":
				o.Upgrade.Source += "#other"
			case "source-query":
				o.Upgrade.Source += "?mode=rw"
			case "root-fragment":
				b.Root += "#other"
			case "rehearsal-fragment":
				o.RehearsalProgram += "#other"
			case "binding-fragment":
				o.HandoffBindingFile += "#other"
			case "database-mismatch":
				b.Database = filepath.Join(root, "different.sqlite")
			case "relative":
				o.Upgrade.Source = "source.sqlite"
			}
			if pauseSchemaMaintenancePaths(b, o) == nil {
				t.Fatal("ambiguous database open allowed")
			}
		})
	}
}
