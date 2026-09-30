package domain

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"

	"researchos.local/research-os/adapters/retrieval"
	"researchos.local/research-os/internal/store"
)

func backupAliasRows(t *testing.T, db *sql.DB, root string) string {
	t.Helper()
	rows, err := db.Query("SELECT relative_path,artifact_id,content_hash,status FROM retrieval_snapshots WHERE root_id=? ORDER BY relative_path,artifact_id", root)
	if err != nil {
		t.Fatal(err)
	}
	defer rows.Close()
	state := Empty()
	for rows.Next() {
		var path, artifact, hash, status string
		if err = rows.Scan(&path, &artifact, &hash, &status); err != nil {
			t.Fatal(err)
		}
		state = append(state, Object{"path": path, "artifact": artifact, "hash": hash, "status": status})
	}
	if err = rows.Err(); err != nil {
		t.Fatal(err)
	}
	return Hash(state)
}

func backupAliasPackage(t *testing.T, dir string) string {
	t.Helper()
	files := Object{}
	err := filepath.WalkDir(dir, func(path string, entry os.DirEntry, err error) error {
		if err != nil || entry.IsDir() {
			return err
		}
		raw, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(dir, path)
		files[rel] = Digest(raw)
		return err
	})
	if err != nil {
		t.Fatal(err)
	}
	return Hash(files)
}

func TestW18SourceAliases(t *testing.T) {
	ctx := context.Background()
	for _, tc := range []struct{ name, first, alias string }{
		{"DOT", "input.txt", "./input.txt"},
		{"WINDOWS-CASE", "input.txt", "INPUT.TXT"},
		{"WINDOWS-SEPARATORS", "nested/input.txt", `nested\.\input.txt`},
	} {
		if strings.HasPrefix(tc.name, "WINDOWS") && runtime.GOOS != "windows" {
			t.Skip("Windows native path identity required")
		}
		for _, conflict := range []bool{false, true} {
			t.Run(fmt.Sprintf("%s/conflict=%t", tc.name, conflict), func(t *testing.T) {
				f := contextFixture(t)
				source := t.TempDir()
				file := filepath.Join(source, filepath.FromSlash(tc.first))
				if err := os.MkdirAll(filepath.Dir(file), 0700); err != nil {
					t.Fatal(err)
				}
				write := func(body string) {
					t.Helper()
					if err := os.WriteFile(file, []byte(body), 0600); err != nil {
						t.Fatal(err)
					}
				}
				write("sealed first source")
				root, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, source)
				if err != nil {
					t.Fatal(err)
				}
				first, err := f.s.CaptureLocalSnapshot(ctx, f.token, f.project, root, tc.first)
				if err != nil {
					t.Fatal(err)
				}
				if conflict {
					write("sealed conflicting source")
				}
				second, err := f.s.CaptureLocalSnapshot(ctx, f.token, f.project, root, tc.alias)
				if err != nil {
					t.Fatal(err)
				}
				if (Str(first, "id") != Str(second, "id")) != conflict {
					t.Fatal("fixture did not establish the intended canonical artifact relationship")
				}
				before := backupAliasRows(t, f.db, root)
				key := backupTestKey(t)
				pkg, _ := backupTestCreate(t, f.s, key)
				packageBefore := backupAliasPackage(t, pkg)
				write("live source after backup")
				destination := filepath.Join(t.TempDir(), "restored")
				_, restoreErr := RestoreBackup(ctx, pkg, destination, backupOpt(t, f.s, key))
				actual, err := os.ReadFile(file)
				if err != nil {
					t.Fatal(err)
				}
				unchanged := string(actual) == "live source after backup" && before == backupAliasRows(t, f.db, root) && packageBefore == backupAliasPackage(t, pkg)
				var originalRoot string
				if err = f.db.QueryRow("SELECT path FROM retrieval_roots WHERE id=?", root).Scan(&originalRoot); err != nil {
					t.Fatal(err)
				}
				unchanged = unchanged && originalRoot == source
				evidence := Object{"paths": []string{tc.first, tc.alias}, "source_and_package_unchanged": unchanged}
				if conflict {
					_, statErr := os.Lstat(destination)
					evidence["error"] = fmt.Sprint(restoreErr)
					evidence["destination_unpublished"] = os.IsNotExist(statErr)
					backupAssert(t, "W18-ALIAS-"+tc.name+"-CONFLICT", true, unchanged && restoreErr != nil && strings.Contains(restoreErr.Error(), "RESTORE_SOURCE_CONFLICT") && os.IsNotExist(statErr), evidence)
					return
				}
				if restoreErr != nil {
					t.Fatal(restoreErr)
				}
				db, err := store.Open(filepath.Join(destination, "state.sqlite"))
				if err != nil {
					t.Fatal(err)
				}
				defer db.Close()
				var restoredRoot, identity string
				if err = db.QueryRow("SELECT path,root_identity FROM retrieval_roots WHERE id=?", root).Scan(&restoredRoot, &identity); err != nil {
					t.Fatal(err)
				}
				preserved := before == backupAliasRows(t, db, root)
				for _, path := range []string{tc.first, tc.alias} {
					raw, err := retrieval.ReadFileBound(restoredRoot, identity, path)
					if err != nil || string(raw) != "sealed first source" {
						t.Fatalf("restored alias %q: %s %v", path, raw, err)
					}
				}
				evidence["snapshot_paths_and_artifacts_preserved"] = preserved
				evidence["both_aliases_read_sealed_bytes"] = true
				backupAssert(t, "W18-ALIAS-"+tc.name+"-IDENTICAL", true, unchanged && preserved, evidence)
			})
		}
	}
}
