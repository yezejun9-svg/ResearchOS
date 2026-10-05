//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"sort"
	"strings"

	"modernc.org/sqlite"
	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/evaluation/evolution"
)

const currentSnapshotLimit = 128 << 20

// SQLite's online backup is copied straight into an in-memory connection and
// serialized there. No original authority page is written to a temporary path.
func controlCurrentSnapshot(ctx context.Context, db *sql.DB) ([]byte, error) {
	conn, err := db.Conn(ctx)
	if err != nil {
		return nil, err
	}
	defer conn.Close()
	var snapshot []byte
	err = conn.Raw(func(raw any) error {
		source, ok := raw.(interface {
			NewBackup(string) (*sqlite.Backup, error)
		})
		if !ok {
			return fmt.Errorf("CONTROL_MEMORY_BACKUP_UNAVAILABLE")
		}
		backup, err := source.NewBackup(":memory:")
		if err != nil {
			return err
		}
		more, err := backup.Step(-1)
		if err != nil || more {
			_ = backup.Finish()
			return fmt.Errorf("CONTROL_MEMORY_BACKUP_INCOMPLETE")
		}
		dest, err := backup.Commit()
		if err != nil {
			return err
		}
		defer dest.Close()
		serializer, ok := dest.(interface{ Serialize() ([]byte, error) })
		if !ok {
			return fmt.Errorf("CONTROL_MEMORY_SERIALIZE_UNAVAILABLE")
		}
		snapshot, err = serializer.Serialize()
		return err
	})
	if err != nil {
		return nil, err
	}
	if len(snapshot) < 100 || len(snapshot) > currentSnapshotLimit || string(snapshot[:16]) != "SQLite format 3\x00" {
		return nil, fmt.Errorf("CONTROL_MEMORY_SNAPSHOT_BOUND")
	}
	return snapshot, nil
}

func controlSnapshotMemoryDB(ctx context.Context, snapshot []byte) (*sql.DB, error) {
	if len(snapshot) < 100 || len(snapshot) > currentSnapshotLimit || string(snapshot[:16]) != "SQLite format 3\x00" {
		return nil, fmt.Errorf("CONTROL_MEMORY_SNAPSHOT_BOUND")
	}
	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	conn, err := db.Conn(ctx)
	if err != nil {
		db.Close()
		return nil, err
	}
	err = conn.Raw(func(raw any) error {
		loader, ok := raw.(interface{ Deserialize([]byte) error })
		if !ok {
			return fmt.Errorf("CONTROL_MEMORY_DESERIALIZE_UNAVAILABLE")
		}
		// SQLite explicitly requires rollback header bytes for Deserialize.
		// Preserve the original snapshot/hash and normalize only this private
		// in-memory read copy: https://sqlite.org/c3ref/deserialize.html
		readCopy := append([]byte(nil), snapshot...)
		readCopy[18], readCopy[19] = 1, 1
		return loader.Deserialize(readCopy)
	})
	conn.Close()
	if err == nil {
		_, err = db.ExecContext(ctx, "PRAGMA query_only=ON")
	}
	if err == nil {
		var integrity string
		err = db.QueryRowContext(ctx, "PRAGMA quick_check").Scan(&integrity)
		if err == nil && integrity != "ok" {
			err = fmt.Errorf("CONTROL_MEMORY_SNAPSHOT_INTEGRITY")
		}
	}
	if err != nil {
		db.Close()
		return nil, err
	}
	return db, nil
}

func controlSavePrivateSnapshot(ctx context.Context, store *protectedstore.CanaryStore, project, session, stage string, raw []byte) (evolution.ControlPrivateSnapshot, error) {
	p := evolution.ControlPrivateSnapshot{Purpose: evolution.ControlCurrentPurpose, Stage: stage, SessionID: session, Hash: Digest(raw), Size: int64(len(raw)), Parts: []evolution.ControlPrivatePart{}}
	if stage != "B0" && stage != "G0" && stage != "G1" || session == "" {
		return p, fmt.Errorf("CONTROL_PRIVATE_SNAPSHOT_PURPOSE")
	}
	db, err := controlSnapshotMemoryDB(ctx, raw)
	if err != nil {
		return p, err
	}
	p.Generation, err = evolution.ControlDatabaseHash(db)
	db.Close()
	if err != nil {
		return p, err
	}
	for start := 0; start < len(raw); start += protectedstore.MaxBlobBytes {
		end := min(start+protectedstore.MaxBlobBytes, len(raw))
		blob, err := store.CreateCanary(ctx, project, controlSnapshotMedia(p), raw[start:end])
		if err != nil {
			return p, err
		}
		p.Parts = append(p.Parts, evolution.ControlPrivatePart{Ticket: blob.Ticket, Hash: blob.Hash, Size: blob.Size})
	}
	// Retain the exact ordered descriptor even if this process exits before
	// the final private proof. It is never published as a PROJECT artifact.
	if _, err := store.CreateCanary(ctx, project, "application/vnd.researchos.control-current-snapshot-descriptor; stage="+stage+"; session="+session, evolution.Bytes(p)); err != nil {
		return p, err
	}
	return p, nil
}

func controlReadPrivateSnapshot(ctx context.Context, store *protectedstore.CanaryStore, project string, p evolution.ControlPrivateSnapshot) ([]byte, *sql.DB, error) {
	if p.Purpose != evolution.ControlCurrentPurpose || p.Stage != "B0" && p.Stage != "G0" && p.Stage != "G1" || p.SessionID == "" || p.Size < 100 || p.Size > currentSnapshotLimit || len(p.Parts) == 0 || len(p.Parts) > currentSnapshotLimit/protectedstore.MaxBlobBytes {
		return nil, nil, fmt.Errorf("CONTROL_PRIVATE_SNAPSHOT_BOUND")
	}
	raw := make([]byte, 0, p.Size)
	seen := map[string]bool{}
	for _, part := range p.Parts {
		if seen[part.Ticket] || part.Size <= 0 || part.Size > protectedstore.MaxBlobBytes {
			return nil, nil, fmt.Errorf("CONTROL_PRIVATE_SNAPSHOT_PART")
		}
		seen[part.Ticket] = true
		blob := protectedstore.Blob{Ticket: part.Ticket, Project: project, Hash: part.Hash, Size: part.Size, MediaType: controlSnapshotMedia(p), MeasurementMode: "FIXTURE"}
		b, err := store.Read(ctx, blob)
		if err != nil {
			return nil, nil, err
		}
		raw = append(raw, b...)
	}
	if int64(len(raw)) != p.Size || Digest(raw) != p.Hash {
		return nil, nil, fmt.Errorf("CONTROL_PRIVATE_SNAPSHOT_HASH")
	}
	db, err := controlSnapshotMemoryDB(ctx, raw)
	if err != nil {
		return nil, nil, err
	}
	generation, err := evolution.ControlDatabaseHash(db)
	if err != nil || generation != p.Generation {
		db.Close()
		return nil, nil, fmt.Errorf("CONTROL_PRIVATE_SNAPSHOT_GENERATION")
	}
	return raw, db, nil
}

func controlSnapshotMedia(p evolution.ControlPrivateSnapshot) string {
	return "application/vnd.researchos.control-current-snapshot; stage=" + p.Stage + "; session=" + p.SessionID
}

type controlQuery interface {
	Query(string, ...any) (*sql.Rows, error)
}

func controlCurrentRows(q controlQuery) (upgradeData, error) {
	list, err := q.Query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
	if err != nil {
		return nil, err
	}
	tables := []string{}
	for list.Next() {
		var table string
		if err = list.Scan(&table); err != nil {
			list.Close()
			return nil, err
		}
		tables = append(tables, table)
	}
	err = list.Err()
	list.Close()
	if err != nil {
		return nil, err
	}
	result := upgradeData{}
	for _, table := range tables {
		rows, err := q.Query(`SELECT * FROM "` + strings.ReplaceAll(table, `"`, `""`) + `"`)
		if err != nil {
			return nil, err
		}
		columns, err := rows.Columns()
		if err != nil {
			rows.Close()
			return nil, err
		}
		entries := []Object{}
		for rows.Next() {
			values, pointers := make([]any, len(columns)), make([]any, len(columns))
			for i := range pointers {
				pointers[i] = &values[i]
			}
			if err = rows.Scan(pointers...); err != nil {
				rows.Close()
				return nil, err
			}
			row := Object{}
			for i, column := range columns {
				row[column] = values[i]
			}
			entries = append(entries, row)
		}
		err = rows.Err()
		rows.Close()
		if err != nil {
			return nil, err
		}
		sort.Slice(entries, func(i, j int) bool { return Hash(entries[i]) < Hash(entries[j]) })
		result[table] = entries
	}
	return result, nil
}
