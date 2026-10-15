package store

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/binary"
	"encoding/hex"
	"errors"
	"fmt"
	"hash"
	"io"
	"math"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"modernc.org/sqlite"
)

// OwnedStopCensus is a hash of the exact sqlite_master rows and every user or
// SQLite-owned table row. Each cell has a type and length delimiter; BLOBs are
// hashed as bytes. A row count is included for review, not as a substitute.
type OwnedStopCensus struct {
	SHA256       string `json:"sha256"`
	SchemaSHA256 string `json:"schema_sha256"`
	Tables       int    `json:"tables"`
	Rows         int64  `json:"rows"`
	QuickCheck   string `json:"quick_check"`
}

type ownedStopQueryer interface {
	QueryContext(context.Context, string, ...any) (*sql.Rows, error)
	QueryRowContext(context.Context, string, ...any) *sql.Row
}

var ownedStopIdentifier = regexp.MustCompile(`^[A-Za-z_][A-Za-z0-9_]*$`)

func ownedStopURI(path, mode string) string {
	u := url.URL{Scheme: "file", Opaque: filepath.ToSlash(path)}
	q := u.Query()
	q.Set("mode", mode)
	q.Set("_busy_timeout", "1500")
	u.RawQuery = q.Encode()
	return u.String()
}

func ownedStopFrame(h hash.Hash, kind byte, raw []byte) {
	_, _ = h.Write([]byte{kind})
	var n [8]byte
	binary.BigEndian.PutUint64(n[:], uint64(len(raw)))
	_, _ = h.Write(n[:])
	_, _ = h.Write(raw)
}
func ownedStopCell(h hash.Hash, v any) error {
	switch x := v.(type) {
	case nil:
		ownedStopFrame(h, 'N', nil)
	case []byte:
		ownedStopFrame(h, 'B', x)
	case string:
		ownedStopFrame(h, 'S', []byte(x))
	case int64:
		ownedStopFrame(h, 'I', []byte(fmt.Sprintf("%d", x)))
	case float64:
		ownedStopFrame(h, 'F', []byte(fmt.Sprintf("%016x", math.Float64bits(x))))
	case bool:
		if x {
			ownedStopFrame(h, 'T', nil)
		} else {
			ownedStopFrame(h, 'f', nil)
		}
	case time.Time:
		ownedStopFrame(h, 'D', []byte(x.UTC().Format(time.RFC3339Nano)))
	default:
		return fmt.Errorf("unsupported SQLite cell type %T", v)
	}
	return nil
}

// Fixed statement forms are constructed only from identifiers returned by
// sqlite_master and PRAGMA table_info. The connection is never returned.
func ownedStopCensus(ctx context.Context, q ownedStopQueryer) (OwnedStopCensus, error) {
	var out OwnedStopCensus
	if err := q.QueryRowContext(ctx, "PRAGMA quick_check").Scan(&out.QuickCheck); err != nil || out.QuickCheck != "ok" {
		return out, fmt.Errorf("quick_check: %s: %w", out.QuickCheck, err)
	}
	schema := sha256.New()
	all := sha256.New()
	rows, err := q.QueryContext(ctx, "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name,tbl_name,sql")
	if err != nil {
		return out, err
	}
	tables := []string{}
	for rows.Next() {
		var typ, name, tbl string
		var sqlText sql.NullString
		if err = rows.Scan(&typ, &name, &tbl, &sqlText); err != nil {
			break
		}
		for _, s := range []string{typ, name, tbl} {
			ownedStopFrame(schema, 'S', []byte(s))
		}
		if sqlText.Valid {
			ownedStopFrame(schema, 'S', []byte(sqlText.String))
		} else {
			ownedStopFrame(schema, 'N', nil)
		}
		if typ == "table" {
			tables = append(tables, name)
		}
	}
	if err == nil {
		err = rows.Err()
	}
	rows.Close()
	if err != nil {
		return out, err
	}
	out.SchemaSHA256 = hex.EncodeToString(schema.Sum(nil))
	ownedStopFrame(all, 'H', schema.Sum(nil))
	for _, table := range tables {
		if !ownedStopIdentifier.MatchString(table) {
			return out, errors.New("noncanonical SQLite table identifier")
		}
		colRows, e := q.QueryContext(ctx, "PRAGMA table_info(\""+table+"\")")
		if e != nil {
			return out, e
		}
		type key struct {
			name  string
			order int
		}
		var keys []key
		for colRows.Next() {
			var cid, notnull, pk int
			var name, typ string
			var defaultValue sql.NullString
			if e = colRows.Scan(&cid, &name, &typ, &notnull, &defaultValue, &pk); e != nil {
				break
			}
			if !ownedStopIdentifier.MatchString(name) {
				e = errors.New("noncanonical SQLite column identifier")
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
			return out, e
		}
		order := "rowid"
		if len(keys) > 0 {
			sort.Slice(keys, func(i, j int) bool { return keys[i].order < keys[j].order })
			parts := make([]string, len(keys))
			for i, k := range keys {
				parts[i] = "\"" + k.name + "\""
			}
			order = strings.Join(parts, ",")
		}
		ownedStopFrame(all, 'T', []byte(table))
		data, e := q.QueryContext(ctx, "SELECT * FROM \""+table+"\" ORDER BY "+order)
		if e != nil {
			return out, e
		}
		columns, e := data.Columns()
		if e != nil {
			data.Close()
			return out, e
		}
		for data.Next() {
			values := make([]any, len(columns))
			ptrs := make([]any, len(columns))
			for i := range values {
				ptrs[i] = &values[i]
			}
			if e = data.Scan(ptrs...); e != nil {
				break
			}
			ownedStopFrame(all, 'R', nil)
			for _, v := range values {
				if e = ownedStopCell(all, v); e != nil {
					break
				}
			}
			if e != nil {
				break
			}
			out.Rows++
		}
		if e == nil {
			e = data.Err()
		}
		data.Close()
		if e != nil {
			return out, e
		}
		out.Tables++
	}
	out.SHA256 = hex.EncodeToString(all.Sum(nil))
	return out, nil
}

// OnlineOwnedStopBackup creates a new destination outside the source root and
// uses the pinned native online-backup API. It returns only hashes and counts.
func OnlineOwnedStopBackup(ctx context.Context, source, destination string) (OwnedStopCensus, string, error) {
	if !filepath.IsAbs(source) || !filepath.IsAbs(destination) || filepath.Clean(destination) != destination {
		return OwnedStopCensus{}, "", errors.New("canonical backup paths required")
	}
	rel, e := filepath.Rel(filepath.Dir(source), destination)
	if e != nil || (!strings.HasPrefix(rel, ".."+string(filepath.Separator)) && rel != "..") {
		return OwnedStopCensus{}, "", errors.New("backup destination must be outside data root")
	}
	if _, err := os.Stat(source); err != nil {
		return OwnedStopCensus{}, "", err
	}
	f, err := os.OpenFile(destination, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return OwnedStopCensus{}, "", err
	}
	if err = f.Close(); err != nil {
		return OwnedStopCensus{}, "", err
	}
	src, err := sql.Open("sqlite", ownedStopURI(source, "rw"))
	if err != nil {
		return OwnedStopCensus{}, "", err
	}
	defer src.Close()
	src.SetMaxOpenConns(1)
	conn, err := src.Conn(ctx)
	if err != nil {
		return OwnedStopCensus{}, "", err
	}
	defer conn.Close()
	destURI := ownedStopURI(destination, "rw")
	err = conn.Raw(func(driverConn any) error {
		maker, ok := driverConn.(interface {
			NewBackup(string) (*sqlite.Backup, error)
		})
		if !ok {
			return errors.New("pinned native backup unavailable")
		}
		backup, e := maker.NewBackup(destURI)
		if e != nil {
			return e
		}
		var stepErr error
		complete := false
		for steps := 0; steps < 100000; steps++ {
			if e = ctx.Err(); e != nil {
				stepErr = e
				break
			}
			var more bool
			more, e = backup.Step(128)
			if e != nil {
				stepErr = e
				break
			}
			if !more {
				complete = true
				break
			}
		}
		if !complete && stepErr == nil {
			stepErr = errors.New("online backup step limit")
		}
		return errors.Join(stepErr, backup.Finish())
	})
	if err != nil {
		return OwnedStopCensus{}, "", err
	}
	closed, err := os.OpenFile(destination, os.O_RDWR, 0)
	if err != nil {
		return OwnedStopCensus{}, "", err
	}
	if err = closed.Sync(); err != nil {
		closed.Close()
		return OwnedStopCensus{}, "", err
	}
	h := sha256.New()
	_, err = io.Copy(h, closed)
	closeErr := closed.Close()
	if err != nil {
		return OwnedStopCensus{}, "", err
	}
	if closeErr != nil {
		return OwnedStopCensus{}, "", closeErr
	}
	ro, err := sql.Open("sqlite", ownedStopURI(destination, "ro"))
	if err != nil {
		return OwnedStopCensus{}, "", err
	}
	defer ro.Close()
	ro.SetMaxOpenConns(1)
	census, err := ownedStopCensus(ctx, ro)
	return census, hex.EncodeToString(h.Sum(nil)), err
}

// ReadOwnedStopBackup rereads a closed backup as a read-only database. It is
// used when committing a reviewed plan; it never refreshes the backup.
func ReadOwnedStopBackup(ctx context.Context, path string) (OwnedStopCensus, string, error) {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path {
		return OwnedStopCensus{}, "", errors.New("canonical backup path required")
	}
	f, err := os.Open(path)
	if err != nil {
		return OwnedStopCensus{}, "", err
	}
	h := sha256.New()
	_, err = io.Copy(h, f)
	closeErr := f.Close()
	if err != nil {
		return OwnedStopCensus{}, "", err
	}
	if closeErr != nil {
		return OwnedStopCensus{}, "", closeErr
	}
	db, err := sql.Open("sqlite", ownedStopURI(path, "ro"))
	if err != nil {
		return OwnedStopCensus{}, "", err
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	census, err := ownedStopCensus(ctx, db)
	return census, hex.EncodeToString(h.Sum(nil)), err
}

func ReadOwnedStopCensus(ctx context.Context, path string) (OwnedStopCensus, error) {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path {
		return OwnedStopCensus{}, errors.New("canonical existing SQLite path required")
	}
	db, err := sql.Open("sqlite", ownedStopURI(path, "ro"))
	if err != nil {
		return OwnedStopCensus{}, err
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	return ownedStopCensus(ctx, db)
}
