//go:build windows

package main

import (
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
