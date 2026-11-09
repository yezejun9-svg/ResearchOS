package domain

import (
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"testing"
)

// This is a source wiring guard, not Native authority execution. The actual
// Native branch cannot be called with a fabricated nonzero migration token.
func TestPauseMigrationTemplateCallersBindTheirOwnDestination(t *testing.T) {
	for _, test := range []struct{ file, function, options, upgrade string }{
		{"backup_pause_handoff.go", "upgradePauseSchemaBackup", "opt", "u"},
		{"backup_pause_migration_windows.go", "ExecutePauseSchemaUpgrade", "pauseOpt", "opt"},
	} {
		t.Run(test.function, func(t *testing.T) {
			file, err := parser.ParseFile(token.NewFileSet(), test.file, nil, 0)
			if err != nil {
				t.Fatal(err)
			}
			calls := 0
			for _, decl := range file.Decls {
				function, ok := decl.(*ast.FuncDecl)
				if !ok || function.Name.Name != test.function {
					continue
				}
				ast.Inspect(function.Body, func(node ast.Node) bool {
					call, ok := node.(*ast.CallExpr)
					if !ok {
						return true
					}
					name, ok := call.Fun.(*ast.Ident)
					if !ok || name.Name != "pauseMigrationTemplate" {
						return true
					}
					calls++
					if len(call.Args) != 5 {
						t.Fatal("template lacks explicit bound options/parent")
					}
					options, ok := call.Args[1].(*ast.Ident)
					if !ok || options.Name != test.options {
						t.Fatal("template uses unrelated options")
					}
					parent, ok := call.Args[2].(*ast.CallExpr)
					if !ok || len(parent.Args) != 1 {
						t.Fatal("template parent not derived from destination")
					}
					selector, ok := parent.Fun.(*ast.SelectorExpr)
					if !ok || selector.Sel.Name != "Dir" {
						t.Fatal("template parent function changed")
					}
					pkg, ok := selector.X.(*ast.Ident)
					if !ok || pkg.Name != "filepath" {
						t.Fatal("template parent function is not filepath.Dir")
					}
					destination, ok := parent.Args[0].(*ast.SelectorExpr)
					if !ok || destination.Sel.Name != "Destination" {
						t.Fatal("template parent is not destination parent")
					}
					upgrade, ok := destination.X.(*ast.Ident)
					if !ok || upgrade.Name != test.upgrade {
						t.Fatal("template parent uses unrelated options")
					}
					return true
				})
			}
			if calls != 1 {
				t.Fatal("expected one bound template call", calls)
			}
		})
	}
}

func TestPauseHandoffMetadataSeparatesThreePrograms(t *testing.T) {
	programs := pauseMigrationPrograms{Digest([]byte("source24")), Digest([]byte("control25")), Digest([]byte("backup25"))}
	zero := 0
	manifest := BackupManifest{ID: "fixture-backup", Format: "RESEARCHOS_BACKUP_V1", Migrations: upgradeVersions(24)}
	valid := pauseBackupHandoffBinding{Schema: pauseMigrationHandoffSchema, SourceBackupOperation: "create", ObservedBackupExit: &zero,
		BackupID: manifest.ID, SourceProgramSHA256: programs.Source, TargetProgramSHA256: programs.Control, RehearsalProgramSHA256: programs.Rehearsal}
	if err := pauseHandoffMetadata(valid, programs, manifest, manifest); err != nil {
		t.Fatal(err)
	}
	for _, mutation := range []string{"old-schema", "old-version", "future-version", "missing-exit", "failed-exit", "wrong-operation", "same-targets", "swapped-targets", "wrong-stdout", "purpose"} {
		t.Run(mutation, func(t *testing.T) {
			b, p, m, stdout := valid, programs, manifest, manifest
			switch mutation {
			case "old-schema":
				b.Schema = preparedPublicHandoffSchema
			case "old-version":
				m.Migrations = upgradeVersions(23)
			case "future-version":
				m.Migrations = upgradeVersions(25)
			case "missing-exit":
				b.ObservedBackupExit = nil
			case "failed-exit":
				one := 1
				b.ObservedBackupExit = &one
			case "wrong-operation":
				b.SourceBackupOperation = "upgrade-local"
			case "same-targets":
				p.Rehearsal, b.RehearsalProgramSHA256 = p.Control, p.Control
			case "swapped-targets":
				p.Control, p.Rehearsal = p.Rehearsal, p.Control
			case "wrong-stdout":
				stdout.ID = "other"
			case "purpose":
				m.Purpose = Object{"kind": "local-upgrade"}
			}
			if err := pauseHandoffMetadata(b, p, m, stdout); err == nil {
				t.Fatal("invalid handoff accepted", mutation)
			}
		})
	}
}

func TestPauseHandoffCurrentExecutableHasOneRole(t *testing.T) {
	current, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	root := t.TempDir()
	source, control := filepath.Join(root, "source24.fixture"), filepath.Join(root, "control25.fixture")
	if err = os.WriteFile(source, []byte("distinct source metadata only"), 0600); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(control, []byte("distinct control metadata only"), 0600); err != nil {
		t.Fatal(err)
	}
	opt := PauseSchemaUpgradeOptions{Upgrade: LocalUpgradeOptions{SourceProgram: source, TargetProgram: control}, RehearsalProgram: current}
	if _, err = pauseMigrationProgramHashes(opt, false); err != nil {
		t.Fatal("current rehearsal identity rejected", err)
	}
	if _, err = pauseMigrationProgramHashes(opt, true); err == nil {
		t.Fatal("rehearsal program relabelled as control")
	}
}

func TestPauseHandoffRetainsOrdinaryPolicyAndStrictJSON(t *testing.T) {
	if !backupOrdinaryPublicPolicy(&backupPolicy{publicPauseUpgradeHandoff: true, format: "RESEARCHOS_BACKUP_V1"}) {
		t.Fatal("ordinary public backup validation lost")
	}
	for _, raw := range []string{`{"unexpected":true}`, `{} {}`} {
		var options PauseSchemaUpgradeOptions
		if err := pauseMigrationDecode([]byte(raw), &options); err == nil {
			t.Fatal("loose options accepted", raw)
		}
	}
}
