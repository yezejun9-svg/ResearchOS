package store

import (
	"context"
	"path/filepath"
	"testing"
)

func TestOpenSettings(t *testing.T) {
	db, err := Open(filepath.Join(t.TempDir(), "研究.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if err := Ready(context.Background(), db); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`CREATE TABLE parent(id INTEGER PRIMARY KEY); CREATE TABLE child(parent_id INTEGER REFERENCES parent(id))`); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`INSERT INTO child(parent_id) VALUES (999)`); err == nil {
		t.Fatal("foreign key constraint did not reject orphan")
	}
}
