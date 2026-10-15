//go:build windows

package store

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// OwnedStopBarrier owns one SQLite connection and one zero-row writer reservation.
// It deliberately exposes no SQL executor or connection to its caller.
type OwnedStopBarrier struct {
	db       *sql.DB
	conn     *sql.Conn
	reserved bool
}

type OwnedStopSubject struct {
	Project     string `json:"project"`
	Run         string `json:"run"`
	Epoch       int    `json:"epoch"`
	DispatchKey string `json:"dispatch_key"`
	RequestKey  string `json:"request_key"`
}

type OwnedStopSafetySnapshot struct {
	RunStatus                 string `json:"run_status"`
	DispatchState             string `json:"dispatch_state"`
	DispatchKey               string `json:"dispatch_key"`
	UnresolvedOtherRuns       int    `json:"unresolved_other_runs"`
	UnresolvedOtherDispatches int    `json:"unresolved_other_dispatches"`
	UnresolvedExternalEffects int    `json:"unresolved_external_effects"`
	NonModelEffects           int    `json:"non_model_effects"`
	ConfirmedModelEffects     int    `json:"confirmed_model_effects"`
	PendingClientCommands     int    `json:"pending_client_commands"`
	PendingControlRequests    int    `json:"pending_control_requests"`
	SchemaVersion             int    `json:"schema_version"`
}

func (s OwnedStopSafetySnapshot) ExactOldSubjectSafe() bool {
	return s.SchemaVersion == 24 && s.RunStatus == "RUNNING" && s.DispatchState == "UNKNOWN" &&
		s.UnresolvedOtherRuns == 0 && s.UnresolvedOtherDispatches == 0 &&
		s.UnresolvedExternalEffects == 0 && s.NonModelEffects == 0 && s.ConfirmedModelEffects == 1 &&
		s.PendingClientCommands == 0 && s.PendingControlRequests == 0
}

func ownedStopExistingDB(path string) (string, error) {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || !strings.EqualFold(filepath.Ext(path), ".sqlite") {
		return "", errors.New("canonical existing SQLite path required")
	}
	actual, err := filepath.EvalSymlinks(path)
	if err != nil || !strings.EqualFold(filepath.Clean(actual), path) {
		return "", errors.New("SQLite path reparse or absence")
	}
	info, err := os.Stat(path)
	if err != nil || !info.Mode().IsRegular() {
		return "", errors.New("regular existing SQLite file required")
	}
	return path, nil
}

// AcquireOwnedStopBarrier does not call store.Open, create, bootstrap, migrate,
// checkpoint or change a persistent PRAGMA. The only SQLite writes it requests
// are BEGIN IMMEDIATE and ROLLBACK, with no product row write.
func AcquireOwnedStopBarrier(ctx context.Context, path string) (_ *OwnedStopBarrier, err error) {
	path, err = ownedStopExistingDB(path)
	if err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", ownedStopURI(path, "rw"))
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	b := &OwnedStopBarrier{db: db}
	defer func() {
		if err != nil {
			_ = b.Close()
		}
	}()
	b.conn, err = db.Conn(ctx)
	if err != nil {
		return nil, err
	}
	if _, err = b.conn.ExecContext(ctx, "BEGIN IMMEDIATE"); err != nil {
		return nil, fmt.Errorf("reserve writer: %w", err)
	}
	b.reserved = true
	if _, err = b.conn.ExecContext(ctx, "PRAGMA query_only=ON"); err != nil {
		return nil, fmt.Errorf("enable query_only: %w", err)
	}
	var readback int
	if err = b.conn.QueryRowContext(ctx, "PRAGMA query_only").Scan(&readback); err != nil || readback != 1 {
		return nil, errors.New("query_only readback failed")
	}
	return b, nil
}

// Census reads on the reserved connection, so a Core transaction committed
// while BEGIN IMMEDIATE waited is included in this exact snapshot.
func (b *OwnedStopBarrier) Census(ctx context.Context) (OwnedStopCensus, error) {
	if b == nil || b.conn == nil || !b.reserved {
		return OwnedStopCensus{}, errors.New("writer reservation unavailable")
	}
	return ownedStopCensus(ctx, b.conn)
}

// SafetySnapshot executes a closed catalog of parameterized SELECTs on the
// reserved connection. The one historical RUNNING/UNKNOWN subject is allowed;
// every other unresolved subject or external effect is rejected.
func (b *OwnedStopBarrier) SafetySnapshot(ctx context.Context, subject OwnedStopSubject) (OwnedStopSafetySnapshot, error) {
	if b == nil || b.conn == nil || !b.reserved {
		return OwnedStopSafetySnapshot{}, errors.New("reserved connection required")
	}
	return ownedStopSafetySnapshot(ctx, b.conn, subject)
}

// ReadOwnedStopSafetyPreflight is informational. Commit repeats this exact
// catalog after acquiring the writer reservation and uses that result.
func ReadOwnedStopSafetyPreflight(ctx context.Context, path string, subject OwnedStopSubject) (OwnedStopSafetySnapshot, error) {
	path, err := ownedStopExistingDB(path)
	if err != nil {
		return OwnedStopSafetySnapshot{}, err
	}
	db, err := sql.Open("sqlite", ownedStopURI(path, "ro"))
	if err != nil {
		return OwnedStopSafetySnapshot{}, err
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	return ownedStopSafetySnapshot(ctx, db, subject)
}

func ownedStopSafetySnapshot(ctx context.Context, source ownedStopQueryer, subject OwnedStopSubject) (OwnedStopSafetySnapshot, error) {
	var s OwnedStopSafetySnapshot
	if subject.Project == "" || subject.Run == "" || subject.Epoch < 1 || subject.DispatchKey == "" || subject.RequestKey == "" {
		return s, errors.New("exact subject required")
	}
	var n, minVersion int
	if err := source.QueryRowContext(ctx, `SELECT max(version),min(version),count(DISTINCT version) FROM schema_migrations`).Scan(&s.SchemaVersion, &minVersion, &n); err != nil || s.SchemaVersion != 24 || minVersion != 1 || n != 24 {
		return s, errors.New("schema 24 required")
	}
	if err := source.QueryRowContext(ctx, `SELECT json_extract(body,'$.status') FROM domain_objects WHERE project=? AND kind='Run' AND id=?`, subject.Project, subject.Run).Scan(&s.RunStatus); err != nil {
		return s, err
	}
	if err := source.QueryRowContext(ctx, `SELECT state,dispatch_key FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?`, subject.Project, subject.Run, subject.Epoch).Scan(&s.DispatchState, &s.DispatchKey); err != nil {
		return s, err
	}
	queries := []struct {
		sql  string
		args []any
		dst  *int
	}{
		{`SELECT count(*) FROM domain_objects WHERE kind='Run' AND NOT(project=? AND id=?) AND coalesce(json_extract(body,'$.status'),'UNKNOWN') NOT IN ('SETTLED','FAILED','CANCELLED')`, []any{subject.Project, subject.Run}, &s.UnresolvedOtherRuns},
		{`SELECT count(*) FROM runtime_dispatches WHERE NOT(project=? AND run=? AND epoch=?) AND state IN ('PREPARED','STARTED','UNKNOWN')`, []any{subject.Project, subject.Run, subject.Epoch}, &s.UnresolvedOtherDispatches},
		{`SELECT count(*) FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')`, nil, &s.UnresolvedExternalEffects},
		{`SELECT count(*) FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND (coalesce(json_extract(body,'$.payload.capability'),'')!='MODEL' OR json_extract(body,'$.state')!='CONFIRMED' OR NOT(x.project=? AND x.run=?))`, []any{subject.Project, subject.Run}, &s.NonModelEffects},
		{`SELECT count(*) FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.payload.capability')='MODEL' AND json_extract(body,'$.state')='CONFIRMED' AND x.project=? AND x.run=?`, []any{subject.Project, subject.Run}, &s.ConfirmedModelEffects},
		{`SELECT count(*) FROM client_command_queue WHERE state NOT IN ('CONSUMED','DROPPED')`, nil, &s.PendingClientCommands},
		{`SELECT count(*) FROM client_control_requests WHERE state!='CONFIRMED'`, nil, &s.PendingControlRequests},
	}
	for _, q := range queries {
		if err := source.QueryRowContext(ctx, q.sql, q.args...).Scan(q.dst); err != nil {
			return s, err
		}
	}
	if s.DispatchKey != subject.DispatchKey {
		return s, errors.New("dispatch identity mismatch")
	}
	var requestCount int
	if err := source.QueryRowContext(ctx, `SELECT count(*) FROM idempotency WHERE project=? AND operation='host:managed-runtime-qualification' AND key=?`, subject.Project, subject.RequestKey).Scan(&requestCount); err != nil {
		return s, err
	}
	if requestCount != 1 {
		return s, errors.New("exact original request not found")
	}
	return s, nil
}

// Close is idempotent and always rolls back; no COMMIT path exists.
func (b *OwnedStopBarrier) Close() error {
	if b == nil {
		return nil
	}
	var errs []error
	if b.conn != nil {
		if b.reserved {
			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			_, err := b.conn.ExecContext(ctx, "ROLLBACK")
			cancel()
			if err != nil {
				errs = append(errs, err)
			}
			b.reserved = false
		}
		if err := b.conn.Close(); err != nil {
			errs = append(errs, err)
		}
		b.conn = nil
	}
	if b.db != nil {
		if err := b.db.Close(); err != nil {
			errs = append(errs, err)
		}
		b.db = nil
	}
	return errors.Join(errs...)
}
