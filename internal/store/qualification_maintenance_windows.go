//go:build windows

package store

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"errors"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// OpenQualificationMaintenance opens an existing schema-24 database. It never
// creates a file, runs migrations, or changes persistent journal settings.
// The caller must already hold the root's native lease and identity guards.
func OpenQualificationMaintenance(ctx context.Context, path string) (_ *sql.DB, err error) {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || filepath.Base(path) != "researchos.sqlite" ||
		strings.Contains(path[len(filepath.VolumeName(path)):], ":") {
		return nil, errors.New("qualification maintenance database path invalid")
	}
	info, err := os.Lstat(path)
	if err != nil || !info.Mode().IsRegular() {
		return nil, errors.New("qualification maintenance database absent or nonregular")
	}
	real, err := filepath.EvalSymlinks(path)
	if err != nil || !strings.EqualFold(filepath.Clean(real), path) {
		return nil, errors.New("qualification maintenance database alias")
	}
	u := url.URL{Scheme: "file", Opaque: filepath.ToSlash(path)}
	q := u.Query()
	q.Set("mode", "rw")
	q.Set("_foreign_keys", "1")
	q.Set("_synchronous", "FULL")
	q.Set("_busy_timeout", "5000")
	u.RawQuery = q.Encode()
	db, err := sql.Open("sqlite", u.String())
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	defer func() {
		if err != nil {
			_ = db.Close()
		}
	}()
	if err = db.PingContext(ctx); err != nil {
		return nil, err
	}
	for pragma, want := range map[string]string{"foreign_keys": "1", "journal_mode": "wal", "synchronous": "2", "busy_timeout": "5000"} {
		var got string
		if err = db.QueryRowContext(ctx, "PRAGMA "+pragma).Scan(&got); err != nil || got != want {
			return nil, fmt.Errorf("qualification maintenance %s=%s, want %s: %w", pragma, got, want, err)
		}
	}
	var maximum, minimum, count, applicationTables int
	if err = db.QueryRowContext(ctx, `SELECT max(version),min(version),count(DISTINCT version) FROM schema_migrations`).Scan(&maximum, &minimum, &count); err != nil {
		return nil, err
	}
	if maximum != 24 || minimum != 1 || count != 24 {
		return nil, errors.New("qualification maintenance requires exact schema 24 history")
	}
	if err = db.QueryRowContext(ctx, `SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'`).Scan(&applicationTables); err != nil {
		return nil, err
	}
	if applicationTables != 87 {
		return nil, fmt.Errorf("qualification maintenance requires 87 application tables, got %d", applicationTables)
	}
	verifyCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()
	var integrity string
	if err = db.QueryRowContext(verifyCtx, "PRAGMA quick_check").Scan(&integrity); err != nil || integrity != "ok" {
		return nil, fmt.Errorf("qualification maintenance quick_check=%s: %w", integrity, err)
	}
	return db, nil
}

// QualificationMaintenanceCensus uses the transaction's own connection so
// the frozen before image and write reservation refer to the same snapshot.
func QualificationMaintenanceCensus(ctx context.Context, tx *sql.Tx) (OwnedStopCensus, error) {
	if tx == nil {
		return OwnedStopCensus{}, errors.New("qualification maintenance transaction required")
	}
	return ownedStopCensus(ctx, tx)
}

// QualificationMaintenanceProtectedCensus binds every row of the 78 tables
// outside the one transaction's nine-table write allowlist. Row cells use the
// same typed, length-delimited framing as the full database census.
func QualificationMaintenanceProtectedCensus(ctx context.Context, tx *sql.Tx) (string, error) {
	if tx == nil {
		return "", errors.New("qualification protected census transaction required")
	}
	allowed := map[string]bool{
		"uploaded_content": true, "domain_versions": true, "domain_objects": true,
		"domain_refs": true, "runtime_observations": true, "runtime_dispatches": true,
		"outbox": true, "event_state_snapshots": true, "idempotency": true,
	}
	rows, e := tx.QueryContext(ctx, `SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name`)
	if e != nil {
		return "", e
	}
	var names []string
	seen := map[string]bool{}
	for rows.Next() {
		var name string
		if e = rows.Scan(&name); e != nil {
			break
		}
		if !ownedStopIdentifier.MatchString(name) {
			e = errors.New("qualification table identifier invalid")
			break
		}
		names = append(names, name)
		seen[name] = true
	}
	if e == nil {
		e = rows.Err()
	}
	rows.Close()
	if e != nil {
		return "", e
	}
	if len(names) != 87 {
		return "", fmt.Errorf("qualification application table count %d", len(names))
	}
	for name := range allowed {
		if !seen[name] {
			return "", fmt.Errorf("qualification allowed table %s absent", name)
		}
	}
	h := sha256.New()
	for _, table := range names {
		if allowed[table] {
			continue
		}
		ownedStopFrame(h, 'T', []byte(table))
		colRows, e := tx.QueryContext(ctx, `PRAGMA table_info("`+table+`")`)
		if e != nil {
			return "", e
		}
		type key struct {
			name  string
			order int
		}
		var keys []key
		for colRows.Next() {
			var cid, notnull, pk int
			var name, typ string
			var def sql.NullString
			if e = colRows.Scan(&cid, &name, &typ, &notnull, &def, &pk); e != nil {
				break
			}
			if !ownedStopIdentifier.MatchString(name) {
				e = errors.New("qualification column identifier invalid")
				break
			}
			if pk > 0 {
				keys = append(keys, key{name, pk})
			}
		}
		if e == nil {
			e = colRows.Err()
		}
		colRows.Close()
		if e != nil {
			return "", e
		}
		order := "rowid"
		if len(keys) > 0 {
			sort.Slice(keys, func(i, j int) bool { return keys[i].order < keys[j].order })
			parts := make([]string, len(keys))
			for i, k := range keys {
				parts[i] = `"` + k.name + `"`
			}
			order = strings.Join(parts, ",")
		}
		data, e := tx.QueryContext(ctx, `SELECT * FROM "`+table+`" ORDER BY `+order)
		if e != nil {
			return "", e
		}
		cols, e := data.Columns()
		if e != nil {
			data.Close()
			return "", e
		}
		for data.Next() {
			values := make([]any, len(cols))
			ptrs := make([]any, len(cols))
			for i := range values {
				ptrs[i] = &values[i]
			}
			if e = data.Scan(ptrs...); e != nil {
				break
			}
			ownedStopFrame(h, 'R', nil)
			for _, v := range values {
				if e = ownedStopCell(h, v); e != nil {
					break
				}
			}
			if e != nil {
				break
			}
		}
		if e == nil {
			e = data.Err()
		}
		data.Close()
		if e != nil {
			return "", e
		}
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

type QualificationResidualSelectors struct {
	Project, Run, Operation, Principal, UploadKey, EventID string
	Epoch, EventSequence                                   int64
	ArtifactID, ImpactLinkID, StateID                      string
	RunRevision, StateRevision                             int64
	ObservationHash                                        string
}

// QualificationMaintenanceResidualCensus hashes all rows in the nine allowed
// tables except precisely the rows this single operation may add or replace.
// Recovery compares this with its pre-BEGIN value and verifies the excluded
// rows separately. An unrelated change in an allowed table remains visible.
func QualificationMaintenanceResidualCensus(ctx context.Context, tx *sql.Tx, s QualificationResidualSelectors) (string, error) {
	if tx == nil || s.Project == "" || s.Run == "" || s.Operation == "" || s.UploadKey == "" || s.EventID == "" {
		return "", errors.New("qualification residual selectors invalid")
	}
	tables := []string{"uploaded_content", "domain_versions", "domain_objects", "domain_refs", "runtime_observations", "runtime_dispatches", "outbox", "event_state_snapshots", "idempotency"}
	h := sha256.New()
	value := func(v any) string {
		switch x := v.(type) {
		case []byte:
			return string(x)
		case string:
			return x
		case int64:
			return fmt.Sprint(x)
		default:
			return ""
		}
	}
	target := func(row map[string]any) bool {
		if value(row["project"]) != s.Project {
			return false
		}
		kind, id := value(row["kind"]), value(row["id"])
		switch kind {
		case "Artifact":
			return id == s.ArtifactID && value(row["revision"]) == "1"
		case "ImpactLink":
			return id == s.ImpactLinkID && value(row["revision"]) == "1"
		case "Run":
			return id == s.Run && value(row["revision"]) == fmt.Sprint(s.RunRevision)
		case "ProjectState":
			return id == s.StateID && value(row["revision"]) == fmt.Sprint(s.StateRevision)
		case "EventEnvelope":
			return id == s.EventID && value(row["revision"]) == "1"
		}
		return false
	}
	for _, table := range tables {
		ownedStopFrame(h, 'T', []byte(table))
		rows, e := tx.QueryContext(ctx, `SELECT * FROM "`+table+`" ORDER BY rowid`)
		if e != nil {
			return "", e
		}
		cols, e := rows.Columns()
		if e != nil {
			rows.Close()
			return "", e
		}
		for rows.Next() {
			vals := make([]any, len(cols))
			ptrs := make([]any, len(cols))
			for i := range vals {
				ptrs[i] = &vals[i]
			}
			if e = rows.Scan(ptrs...); e != nil {
				break
			}
			row := make(map[string]any, len(cols))
			for i, col := range cols {
				row[col] = vals[i]
			}
			skip := false
			switch table {
			case "uploaded_content":
				skip = value(row["storage_key"]) == s.UploadKey
			case "domain_versions", "domain_refs":
				skip = target(row)
			case "domain_objects":
				// Run and ProjectState existed before; their old rows are
				// excluded as the same exact keys whose new values are checked.
				kind, id := value(row["kind"]), value(row["id"])
				skip = value(row["project"]) == s.Project && (kind == "Artifact" && id == s.ArtifactID ||
					kind == "ImpactLink" && id == s.ImpactLinkID || kind == "Run" && id == s.Run ||
					kind == "ProjectState" && id == s.StateID || kind == "EventEnvelope" && id == s.EventID)
			case "runtime_observations":
				skip = value(row["project"]) == s.Project && value(row["run"]) == s.Run &&
					value(row["epoch"]) == fmt.Sprint(s.Epoch) && value(row["receipt_hash"]) == s.ObservationHash
			case "runtime_dispatches":
				skip = value(row["project"]) == s.Project && value(row["run"]) == s.Run && value(row["epoch"]) == fmt.Sprint(s.Epoch)
			case "outbox":
				skip = value(row["project"]) == s.Project && value(row["sequence"]) == fmt.Sprint(s.EventSequence) && value(row["id"]) == s.EventID
			case "event_state_snapshots":
				skip = value(row["project"]) == s.Project && value(row["event_id"]) == s.EventID
			case "idempotency":
				skip = value(row["principal"]) == s.Principal && value(row["project"]) == s.Project &&
					value(row["operation"]) == "host:qualification-failure-maintenance" && value(row["key"]) == s.Operation
			}
			if skip {
				continue
			}
			ownedStopFrame(h, 'R', nil)
			for _, v := range vals {
				if e = ownedStopCell(h, v); e != nil {
					break
				}
			}
			if e != nil {
				break
			}
		}
		if e == nil {
			e = rows.Err()
		}
		rows.Close()
		if e != nil {
			return "", e
		}
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}
