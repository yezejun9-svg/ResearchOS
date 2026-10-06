package store

import (
	"context"
	"database/sql"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"time"

	_ "modernc.org/sqlite"
)

// Open initializes the single local authoritative database connection.
func Open(path string) (*sql.DB, error) {
	abs, err := filepath.Abs(path)
	if err != nil {
		return nil, err
	}
	if err := os.MkdirAll(filepath.Dir(abs), 0700); err != nil {
		return nil, err
	}
	u := url.URL{Scheme: "file", Opaque: filepath.ToSlash(abs)}
	q := u.Query()
	q.Set("_foreign_keys", "1")
	q.Set("_journal_mode", "WAL")
	q.Set("_synchronous", "FULL")
	q.Set("_busy_timeout", "5000")
	u.RawQuery = q.Encode()
	db, err := sql.Open("sqlite", u.String())
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return nil, err
	}
	if err := Ready(ctx, db); err != nil {
		db.Close()
		return nil, err
	}
	return db, nil
}

// Ready checks the live connection settings, rather than treating a file as readiness.
func Ready(ctx context.Context, db *sql.DB) (diagErr error) {
fmt.Printf("SLOW_READY start %s stats=%+v\n",time.Now().UTC().Format(time.RFC3339Nano),db.Stats());defer func(){fmt.Printf("SLOW_READY end %s error=%v stats=%+v\n",time.Now().UTC().Format(time.RFC3339Nano),diagErr,db.Stats())}()
	for pragma, want := range map[string]string{
		"foreign_keys": "1", "journal_mode": "wal", "synchronous": "2", "busy_timeout": "5000",
	} {
		fmt.Printf("SLOW_READY pragma-start %s %s\n",time.Now().UTC().Format(time.RFC3339Nano),pragma)
var got string
		if err := db.QueryRowContext(ctx, "PRAGMA "+pragma).Scan(&got); err != nil {
			return fmt.Errorf("%s: %w", pragma, err)
		}
		fmt.Printf("SLOW_READY pragma-end %s %s\n",time.Now().UTC().Format(time.RFC3339Nano),pragma)
if got != want {
			return fmt.Errorf("%s=%s, want %s", pragma, got, want)
		}
	}
	fmt.Printf("SLOW_READY quick-check-start %s\n",time.Now().UTC().Format(time.RFC3339Nano))
var integrity string
	if err := db.QueryRowContext(ctx, "PRAGMA quick_check").Scan(&integrity); err != nil {
		return err
	}
	fmt.Printf("SLOW_READY quick-check-end %s\n",time.Now().UTC().Format(time.RFC3339Nano))
if integrity != "ok" {
		return fmt.Errorf("sqlite quick_check: %s", integrity)
	}
	return nil
}

// Bootstrap records only the empty storage baseline; W03 owns business tables.
func Bootstrap(ctx context.Context, db *sql.DB, migrationFile string) error {
	sqlText, err := os.ReadFile(migrationFile)
	if err != nil {
		return err
	}
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if _, err := tx.ExecContext(ctx, string(sqlText)); err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `INSERT OR IGNORE INTO schema_migrations(version) VALUES (1)`); err != nil {
		return err
	}
	return tx.Commit()
}
