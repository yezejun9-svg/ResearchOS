package domain

// Local administrative backup APIs are deliberately not registered as HTTP
// operations. Possession of the separately stored recovery key is required.
import (
	"context"
	"crypto/aes"
	"crypto/cipher"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"runtime/debug"
	"sort"
	"strings"
	"time"

	"researchos.local/research-os/internal/store"
)

type BackupFile struct {
	Name string `json:"name"`
	Hash string `json:"hash"`
	Size int    `json:"size"`
}
type BackupManifest struct {
	Format            string       `json:"format"`
	ID                string       `json:"id"`
	Started           string       `json:"started_at"`
	SnapshotCompleted string       `json:"snapshot_completed_at"`
	Migrations        []int        `json:"migrations"`
	SchemaHash        string       `json:"schema_hash"`
	Runtime           Object       `json:"runtime_versions"`
	Files             []BackupFile `json:"files"`
	Inventory         Object       `json:"inventory"`
	KeyPolicy         string       `json:"key_policy"`
	CachePolicy       string       `json:"cache_policy"`
	MAC               string       `json:"mac"`
	Purpose           Object       `json:"purpose,omitempty"`
}

// Internal policies are available only to the bounded local upgrade coordinator.
// Public backup/export/restore retain the ordinary format and protection guard.
type backupPolicy struct {
	format                                 string
	databaseName                           string
	purpose                                Object
	allowProtected                         func(*sql.DB, Object) error
	validate                               func(*sql.DB) error
	beforeRecovery                         func(*sql.DB) error
	afterRecovery                          func(*sql.DB) error
	preserveQueueUpgradeWorkspaces         func(*sql.DB) error
	preserveConfigurationUpgradeWorkspaces func(*sql.DB) error
	preservePreparedAbandonmentUpgradeWorkspaces func(*sql.DB) error
	publicPreparedAbandonmentHandoff bool
}

// Ordinary public validation remains mandatory for the fixed handoff policy.
func backupOrdinaryPublicPolicy(policy *backupPolicy) bool {
    return policy == nil || policy.publicPreparedAbandonmentHandoff
}

func backupFormat(policy *backupPolicy) string {
	if policy != nil {
		return policy.format
	}
	return "RESEARCHOS_BACKUP_V1"
}

func backupCipher(key []byte) (cipher.AEAD, error) {
	if len(key) != 32 {
		return nil, fmt.Errorf("BACKUP_KEY_UNAVAILABLE: separate 32-byte key required")
	}
	block, e := aes.NewCipher(key)
	if e != nil {
		return nil, e
	}
	return cipher.NewGCM(block)
}
func backupMAC(m BackupManifest, key []byte) string {
	m.MAC = ""
	raw, _ := json.Marshal(m)
	h := hmac.New(sha256.New, key)
	h.Write(raw)
	return hex.EncodeToString(h.Sum(nil))
}
func backupWrite(path string, raw []byte) error {
	f, e := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		return e
	}
	if _, e = f.Write(raw); e == nil {
		e = f.Sync()
	}
	closeErr := f.Close()
	if e != nil {
		return e
	}
	return closeErr
}
func backupEncrypt(a cipher.AEAD, id, name string, raw []byte) ([]byte, error) {
	nonce := make([]byte, a.NonceSize())
	if _, e := rand.Read(nonce); e != nil {
		return nil, e
	}
	return a.Seal(nonce, nonce, raw, []byte(id+"/"+name)), nil
}
func backupDecrypt(a cipher.AEAD, id, name string, raw []byte) ([]byte, error) {
	if len(raw) < a.NonceSize() {
		return nil, fmt.Errorf("BACKUP_CORRUPT")
	}
	b, e := a.Open(nil, raw[:a.NonceSize()], raw[a.NonceSize():], []byte(id+"/"+name))
	if e != nil {
		return nil, fmt.Errorf("BACKUP_KEY_OR_CONTENT_INVALID")
	}
	return b, nil
}
func backupNewStage(destination string) (string, error) {
	abs, e := filepath.Abs(destination)
	if e != nil {
		return "", e
	}
	if _, e = os.Lstat(abs); !os.IsNotExist(e) {
		return "", fmt.Errorf("DESTINATION_EXISTS: use a new empty destination")
	}
	parent := filepath.Dir(abs)
	if e = os.MkdirAll(parent, 0700); e != nil {
		return "", e
	}
	return os.MkdirTemp(parent, ".researchos-backup-stage-")
}

// Only removes files underneath a directory freshly created by this invocation.
func backupDiscard(stage string) {
	if strings.HasPrefix(filepath.Base(stage), ".researchos-backup-stage-") {
		_ = os.RemoveAll(stage)
	}
}
func backupMigrations(db *sql.DB) ([]int, error) {
	rows, e := db.Query("SELECT version FROM schema_migrations ORDER BY version")
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	v := []int{}
	for rows.Next() {
		var n int
		if e = rows.Scan(&n); e != nil {
			return nil, e
		}
		v = append(v, n)
	}
	return v, rows.Err()
}

func backupSchema(db *sql.DB) (string, error) {
	rows, e := db.Query("SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_master ORDER BY type,name")
	if e != nil {
		return "", e
	}
	defer rows.Close()
	all := []any{}
	for rows.Next() {
		var kind, name, table, sqlText string
		if e = rows.Scan(&kind, &name, &table, &sqlText); e != nil {
			return "", e
		}
		all = append(all, []any{kind, name, table, sqlText})
	}
	return Hash(all), rows.Err()
}
func backupRuntime(db *sql.DB) (Object, error) {
	var sqlite string
	if e := db.QueryRow("SELECT sqlite_version()").Scan(&sqlite); e != nil {
		return nil, e
	}
	out := Object{"go": runtime.Version(), "sqlite": sqlite, "platform": runtime.GOOS + "/" + runtime.GOARCH, "vcs_revision": nil, "module_versions": Object{}}
	if info, ok := debug.ReadBuildInfo(); ok {
		for _, dep := range info.Deps {
			out["module_versions"].(Object)[dep.Path] = dep.Version
		}
		for _, setting := range info.Settings {
			if setting.Key == "vcs.revision" {
				out["vcs_revision"] = setting.Value
			}
		}
	}
	return out, nil
}
func backupObjects(db *sql.DB, query string) ([]Object, error) {
	rows, e := db.Query(query)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	out := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			return nil, e
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			return nil, e
		}
		out = append(out, o)
	}
	return out, rows.Err()
}

func backupPortable(db *sql.DB) ([]Object, error) {
	rows, e := db.Query("SELECT kind,body FROM domain_versions ORDER BY project,kind,id,revision")
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	out := []Object{}
	for rows.Next() {
		var kind, raw string
		if e = rows.Scan(&kind, &raw); e != nil {
			return nil, e
		}
		obj, e := Decode([]byte(raw))
		if e != nil {
			return nil, e
		}
		out = append(out, Object{"entity_type": kind, "object": obj})
	}
	return out, rows.Err()
}
func backupInventory(db *sql.DB) (Object, error) {
	inventory := Object{}
	for _, table := range []string{"domain_objects", "domain_versions", "domain_refs", "uploaded_content", "outbox", "source_pages", "consumer_positions", "consumer_inbox", "resource_effects"} {
		var n int
		if e := db.QueryRow("SELECT count(*) FROM " + table).Scan(&n); e != nil {
			return nil, e
		}
		inventory[table] = n
	}
	rows, e := db.Query("SELECT project,kind,id,revision,body FROM domain_objects ORDER BY project,kind,id")
	if e != nil {
		return nil, e
	}
	entries := []any{}
	for rows.Next() {
		var p, k, id, b string
		var rev int
		if e = rows.Scan(&p, &k, &id, &rev, &b); e != nil {
			rows.Close()
			return nil, e
		}
		entries = append(entries, []any{p, k, id, rev, Digest([]byte(b))})
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, e
	}
	inventory["entity_revision_digest"] = Hash(entries)
	var seq int64
	if e = db.QueryRow("SELECT coalesce(max(sequence),0) FROM outbox").Scan(&seq); e != nil {
		return nil, e
	}
	inventory["max_event_sequence"] = seq
	queue, err := backupQueueState(db)
	if err != nil {
		return nil, err
	}
	if queue != nil {
		inventory["command_queue_digest"] = Hash(queue)
	}
	configuration, err := backupHostConfigurationState(db)
	if err != nil {
		return nil, err
	}
	if configuration != nil {
		inventory["host_configuration_digest"] = Hash(configuration)
	}
	pause, err := backupPauseState(db)
	if err != nil {
		return nil, err
	}
	if pause != nil {
		inventory["runtime_pause_digest"] = Hash(pause)
	}
	return inventory, nil
}
func backupIntegrity(db *sql.DB) error {
	return backupIntegrityPolicy(db, nil)
}
func backupIntegrityPolicy(db *sql.DB, policy *backupPolicy) error {
	if err := validateBackupPause(db); err != nil {
		return err
	}
	if err := validateBackupHostConfiguration(db); err != nil {
		return err
	}
	if err := validateBackupQueue(db); err != nil {
		return err
	}
	if policy != nil && policy.validate != nil {
		if e := policy.validate(db); e != nil {
			return e
		}
	}
	var result string
	if e := db.QueryRow("PRAGMA integrity_check").Scan(&result); e != nil {
		return e
	}
	if result != "ok" {
		return fmt.Errorf("BACKUP_DB_INTEGRITY")
	}
	rows, e := db.Query("PRAGMA foreign_key_check")
	if e != nil {
		return e
	}
	bad := rows.Next()
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	if bad {
		return fmt.Errorf("BACKUP_DANGLING_REFERENCE")
	}
	// Every version, including historical accepted evidence, must retain its bytes.
	arts, e := backupObjects(db, "SELECT body FROM domain_versions WHERE kind='Artifact'")
	if e != nil {
		return e
	}
	for _, o := range arts {
		if o["access_class"] != "PROJECT" {
			if policy == nil || policy.allowProtected == nil {
				return fmt.Errorf("PROTECTED_BACKUP_REQUIRES_W17")
			}
			if e = policy.allowProtected(db, o); e != nil {
				return e
			}
			continue
		}
		var raw []byte
		var hash string
		var sealed int
		if e = db.QueryRow("SELECT bytes,content_hash,sealed FROM uploaded_content WHERE storage_key=? AND project=?", o["storage_key"], o["project_id"]).Scan(&raw, &hash, &sealed); e != nil {
			return fmt.Errorf("BACKUP_ARTIFACT_MISSING")
		}
		if sealed != 1 || Digest(raw) != hash || hash != o["content_hash"] {
			return fmt.Errorf("BACKUP_ARTIFACT_HASH")
		}
	}
	receipts, e := backupObjects(db, "SELECT body FROM domain_versions WHERE json_type(body,'$.receipt_hash')='text'")
	if e != nil {
		return e
	}
	for _, o := range receipts {
		if o["receipt_hash"] != Receipt(o) {
			return fmt.Errorf("BACKUP_RECEIPT_HASH")
		}
	}
	return nil
}

// CreateBackup uses a transactional SQLite snapshot, including WAL commits and
// sealed BLOBs in the same consistency window. Files are derived ONLY from that
// closed snapshot. Publication happens after all hashes and the manifest pass.
func (s *Service) CreateBackup(ctx context.Context, destination string, key []byte) (BackupManifest, error) {
	return s.createBackupPolicy(ctx, destination, key, nil)
}
func (s *Service) createBackupPolicy(ctx context.Context, destination string, key []byte, policy *backupPolicy, sources ...WorkspaceBackupSource) (BackupManifest, error) {
	m := BackupManifest{Format: backupFormat(policy), ID: ID(), Started: Now(), KeyPolicy: "AES-256-GCM; key stored separately; credentials require fresh provisioning after restore", CachePolicy: "SQLite FTS cache included; external worker/context workspaces excluded and rebuilt from sealed content"}
	if policy != nil {
		m.Purpose = policy.purpose
	}
	a, e := backupCipher(key)
	if e != nil {
		return m, e
	}
	stage, e := backupNewStage(destination)
	if e != nil {
		return m, e
	}
	defer backupDiscard(stage)
	plain := filepath.Join(stage, "snapshot.sqlite")
	if _, e = s.DB.ExecContext(ctx, "VACUUM INTO ?", plain); e != nil {
		return m, e
	}
	m.SnapshotCompleted = Now()
	db, e := store.Open(plain)
	if e != nil {
		return m, e
	}
	defer db.Close()
	if e = backupIntegrityPolicy(db, policy); e != nil {
		return m, e
	}
	if m.Migrations, e = backupMigrations(db); e != nil {
		return m, e
	}
	if m.SchemaHash, e = backupSchema(db); e != nil {
		return m, e
	}
	if m.Runtime, e = backupRuntime(db); e != nil {
		return m, e
	}
	if m.Inventory, e = backupInventory(db); e != nil {
		return m, e
	}
	files := map[string][]byte{}
	rows, e := db.Query("SELECT storage_key,bytes,content_hash FROM uploaded_content WHERE sealed=1 ORDER BY storage_key")
	if e != nil {
		return m, e
	}
	for rows.Next() {
		var k, h string
		var b []byte
		if e = rows.Scan(&k, &b, &h); e != nil {
			rows.Close()
			return m, e
		}
		if Digest(b) != h {
			rows.Close()
			return m, fmt.Errorf("BACKUP_CONTENT_HASH")
		}
		files["content-"+strings.TrimPrefix(Digest([]byte(k)), "sha256:")+".bin"] = b
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return m, e
	}
	if policy == nil {
		objects, e := backupPortable(db)
		if e != nil {
			return m, e
		}
		queue, err := backupQueueState(db)
		if err != nil {
			return m, err
		}
		if queue != nil {
			files["command-queue.json"] = Bytes(queue)
		}
		files["portable.json"] = Bytes(Object{"format": "RESEARCHOS_PORTABLE_V1", "objects": objects, "authority": "state.sqlite; portable objects preserve IDs, revisions, source relationships and receipt hashes"})
		var source WorkspaceBackupSource
		if len(sources) != 0 {
			source = sources[0]
		}
		workspaceFiles, count, err := backupWorkspaceFiles(ctx, db, source, destination)
		if err != nil {
			return m, err
		}
		for name, raw := range workspaceFiles {
			files[name] = raw
		}
		if count != 0 {
			m.CachePolicy = "SQLite FTS cache included; authorized workspaces encrypted and bounded; external worker/context caches rebuilt from sealed content"
		}
	}
	if _, e = db.Exec("PRAGMA wal_checkpoint(TRUNCATE)"); e != nil {
		return m, e
	}
	if e = db.Close(); e != nil {
		return m, e
	}
	files["state.sqlite"], e = os.ReadFile(plain)
	if e != nil {
		return m, e
	}
	for name, raw := range files {
		encrypted, e := backupEncrypt(a, m.ID, name, raw)
		if e != nil {
			return m, e
		}
		if e = backupWrite(filepath.Join(stage, name+".enc"), encrypted); e != nil {
			return m, e
		}
		m.Files = append(m.Files, BackupFile{Name: name, Hash: Digest(raw), Size: len(raw)})
	}
	sort.Slice(m.Files, func(i, j int) bool { return m.Files[i].Name < m.Files[j].Name })
	m.MAC = backupMAC(m, key)
	if e = backupWrite(filepath.Join(stage, "manifest.json"), Bytes(m)); e != nil {
		return m, e
	}
	for _, suffix := range []string{"", "-wal", "-shm"} {
		if e = os.Remove(plain + suffix); e != nil && !os.IsNotExist(e) {
			return m, e
		}
	}
	if e = ctx.Err(); e != nil {
		return m, e
	}
	if e = os.Rename(stage, destination); e != nil {
		return m, e
	}
	return m, nil
}

func readBackup(directory string, key []byte) (BackupManifest, map[string][]byte, error) {
	return readBackupPolicy(directory, key, nil)
}
func readBackupPolicy(directory string, key []byte, policy *backupPolicy) (BackupManifest, map[string][]byte, error) {
	var m BackupManifest
	a, e := backupCipher(key)
	if e != nil {
		return m, nil, e
	}
	raw, e := os.ReadFile(filepath.Join(directory, "manifest.json"))
	if e != nil {
		return m, nil, e
	}
	if e = json.Unmarshal(raw, &m); e != nil {
		return m, nil, e
	}
	if m.Format != backupFormat(policy) || !hmac.Equal([]byte(m.MAC), []byte(backupMAC(m, key))) {
		return m, nil, fmt.Errorf("BACKUP_MANIFEST_INVALID")
	}
	if policy != nil && Hash(m.Purpose) != Hash(policy.purpose) {
		return m, nil, fmt.Errorf("BACKUP_PURPOSE_MISMATCH")
	}
	files := map[string][]byte{}
	for _, f := range m.Files {
		if filepath.Base(f.Name) != f.Name || strings.ContainsAny(f.Name, "/\\:") || files[f.Name] != nil {
			return m, nil, fmt.Errorf("BACKUP_MANIFEST_PATH")
		}
		raw, e = os.ReadFile(filepath.Join(directory, f.Name+".enc"))
		if e != nil {
			return m, nil, fmt.Errorf("BACKUP_FILE_MISSING: %s", f.Name)
		}
		raw, e = backupDecrypt(a, m.ID, f.Name, raw)
		if e != nil {
			return m, nil, e
		}
		if len(raw) != f.Size || Digest(raw) != f.Hash {
			return m, nil, fmt.Errorf("BACKUP_FILE_HASH: %s", f.Name)
		}
		files[f.Name] = raw
	}
	if files["state.sqlite"] == nil || (backupOrdinaryPublicPolicy(policy) && files["portable.json"] == nil) {
		return m, nil, fmt.Errorf("BACKUP_REQUIRED_FILE_MISSING")
	}
	if !backupOrdinaryPublicPolicy(policy) && files["portable.json"] != nil {
		return m, nil, fmt.Errorf("UPGRADE_PORTABLE_EXPORT_PROHIBITED")
	}
	return m, files, nil
}

type RestoreOptions struct {
	Key                 []byte
	SupportedMigrations []int
	Contracts           *Contracts
	WorkspaceTarget     WorkspaceRestoreTarget
	// DatabaseName is the production data-root filename. The library default
	// remains state.sqlite for callers that manage a standalone restore bundle.
	DatabaseName string
	// Migration executes only against the unpublished isolated copy. Irreversible
	// migration is never promoted automatically; restore the old backup instead.
	Migration    func(context.Context, *sql.DB) error
	Irreversible bool
}
type RestoreReport struct {
	BackupID   string `json:"backup_id"`
	Started    string `json:"started_at"`
	Finished   string `json:"finished_at"`
	DurationMS int64  `json:"duration_ms"`
	Before     Object `json:"before"`
	After      Object `json:"after"`
	Recovery   Object `json:"recovery"`
	Status     string `json:"status"`
}

func RestoreBackup(ctx context.Context, directory, destination string, opt RestoreOptions) (RestoreReport, error) {
	return restoreBackupPolicy(ctx, directory, destination, opt, nil)
}
func restoreBackupPolicy(ctx context.Context, directory, destination string, opt RestoreOptions, policy *backupPolicy) (RestoreReport, error) {
	start := time.Now()
	r := RestoreReport{Started: Now(), Status: "FAILED"}
	absDestination, absErr := filepath.Abs(destination)
	if absErr != nil {
		return r, absErr
	}
	destination = absDestination
	if opt.Contracts == nil || len(opt.SupportedMigrations) == 0 {
		return r, fmt.Errorf("RESTORE_VERSION_POLICY_REQUIRED")
	}
	if opt.Irreversible {
		return r, fmt.Errorf("IRREVERSIBLE_MIGRATION_MAINTENANCE_REQUIRED")
	}
	m, files, e := readBackupPolicy(directory, opt.Key, policy)
	if e != nil {
		return r, e
	}
	if backupOrdinaryPublicPolicy(policy) {
		if e = backupWorkspaceRestorePaths(files, directory, destination); e != nil {
			return r, e
		}
	}
	r.BackupID = m.ID
	if Hash(m.Migrations) != Hash(opt.SupportedMigrations) {
		return r, fmt.Errorf("MIGRATION_INCOMPATIBLE: restore with matching application version")
	}
	stage, e := backupNewStage(destination)
	if e != nil {
		return r, e
	}
	defer backupDiscard(stage)
	databaseName := "state.sqlite"
	if opt.DatabaseName != "" {
		if filepath.Base(opt.DatabaseName) != opt.DatabaseName || strings.ContainsAny(opt.DatabaseName, "/\\:") {
			return r, fmt.Errorf("RESTORE_DATABASE_NAME_INVALID")
		}
		databaseName = opt.DatabaseName
	}
	if policy != nil && policy.databaseName != "" {
		if filepath.Base(policy.databaseName) != policy.databaseName || strings.ContainsAny(policy.databaseName, "/\\:") {
			return r, fmt.Errorf("RESTORE_DATABASE_NAME_INVALID")
		}
		databaseName = policy.databaseName
	}
	if e = backupWrite(filepath.Join(stage, databaseName), files["state.sqlite"]); e != nil {
		return r, e
	}
	db, e := store.Open(filepath.Join(stage, databaseName))
	if e != nil {
		return r, e
	}
	defer db.Close()
	if e = backupIntegrityPolicy(db, policy); e != nil {
		return r, e
	}
	actual, e := backupMigrations(db)
	if e != nil {
		return r, e
	}
	if Hash(actual) != Hash(m.Migrations) {
		return r, fmt.Errorf("MIGRATION_MANIFEST_MISMATCH")
	}
	schema, e := backupSchema(db)
	if e != nil {
		return r, e
	}
	if schema != m.SchemaHash {
		return r, fmt.Errorf("BACKUP_SCHEMA_HASH_MISMATCH")
	}
	if backupOrdinaryPublicPolicy(policy) {
		queue, err := backupQueueState(db)
		if err != nil {
			return r, err
		}
		if queue != nil {
			var saved Object
			if json.Unmarshal(files["command-queue.json"], &saved) != nil || Hash(saved) != Hash(queue) {
				return r, fmt.Errorf("RESTORE_QUEUE_SIDECAR_MISMATCH")
			}
		}
	}
	// Types are loaded separately so schema evolution cannot silently reinterpret
	// stored objects under a changed application contract.
	types, e := db.Query("SELECT kind,body FROM domain_versions")
	if e != nil {
		return r, e
	}
	for types.Next() {
		var kind, raw string
		if e = types.Scan(&kind, &raw); e != nil {
			types.Close()
			return r, e
		}
		obj, e := Decode([]byte(raw))
		if e != nil {
			types.Close()
			return r, e
		}
		if e = opt.Contracts.Validate(kind, obj); e != nil {
			types.Close()
			return r, fmt.Errorf("RESTORE_CONTRACT_INCOMPATIBLE: %s", kind)
		}
	}
	e = types.Err()
	types.Close()
	if e != nil {
		return r, e
	}
	r.Before, e = backupInventory(db)
	if e != nil {
		return r, e
	}
	if Hash(r.Before) != Hash(m.Inventory) {
		return r, fmt.Errorf("RESTORE_INVENTORY_MISMATCH")
	}
	var workspaceRequests []WorkspaceRestoreRequest
	if policy != nil && policy.preserveQueueUpgradeWorkspaces != nil {
		plan, ok := policy.purpose["plan"].(Object)
		if !ok || policy.format != localUpgradeFormat || plan["id"] != "schema21-to22-client-command-queue-v1" {
			return r, fmt.Errorf("RESTORE_QUEUE_WORKSPACE_POLICY_MISMATCH")
		}
		// Only the fixed same-host upgrade may retain source path identities. Its
		// callback rechecks the source protection and every original row/path.
		e = policy.preserveQueueUpgradeWorkspaces(db)
	} else if policy != nil && policy.preserveConfigurationUpgradeWorkspaces != nil {
		plan, ok := policy.purpose["plan"].(Object)
		if !ok || policy.format != localUpgradeFormat || plan["id"] != ConfigurationSchemaUpgradePlan {
			return r, fmt.Errorf("RESTORE_CONFIGURATION_WORKSPACE_POLICY_MISMATCH")
		}
		e = policy.preserveConfigurationUpgradeWorkspaces(db)
	} else if policy != nil && policy.preservePreparedAbandonmentUpgradeWorkspaces != nil {
		plan, ok := policy.purpose["plan"].(Object)
        fixedLocal := ok && policy.format == localUpgradeFormat && plan["id"] == PreparedAbandonmentSchemaUpgradePlan
        fixedPublic := policy.publicPreparedAbandonmentHandoff && policy.format == "RESEARCHOS_BACKUP_V1" &&
            len(policy.purpose) == 0 && policy.allowProtected == nil
        if !fixedLocal && !fixedPublic {
            return r, fmt.Errorf("RESTORE_PREPARED_ABANDONMENT_WORKSPACE_POLICY_MISMATCH")
        }
		e = policy.preservePreparedAbandonmentUpgradeWorkspaces(db)
	} else {
		workspaceRequests, e = backupPrepareWorkspaces(ctx, db, files, stage, destination)
	}
	if e != nil {
		return r, e
	}
	if len(workspaceRequests) != 0 && opt.WorkspaceTarget == nil {
		return r, fmt.Errorf("RESTORE_WORKSPACE_TARGET_REQUIRED")
	}
	rows, e := db.Query("SELECT storage_key,bytes FROM uploaded_content WHERE sealed=1")
	if e != nil {
		return r, e
	}
	for rows.Next() {
		var k string
		var b []byte
		if e = rows.Scan(&k, &b); e != nil {
			rows.Close()
			return r, e
		}
		name := "content-" + strings.TrimPrefix(Digest([]byte(k)), "sha256:") + ".bin"
		raw, ok := files[name]
		if !ok || Digest(raw) != Digest(b) {
			rows.Close()
			return r, fmt.Errorf("RESTORE_ARTIFACT_MANIFEST_MISMATCH")
		}
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return r, e
	}
	svc := &Service{DB: db, Contracts: opt.Contracts}
	if policy != nil && policy.beforeRecovery != nil {
		if e = policy.beforeRecovery(db); e != nil {
			return r, e
		}
	}
	if e = svc.backupRelocateSources(stage, destination); e != nil {
		return r, e
	}
	if r.Recovery, e = svc.backupFence(ctx); e != nil {
		return r, e
	}
	if opt.Migration != nil {
		if e = opt.Migration(ctx, db); e != nil {
			return r, fmt.Errorf("MIGRATION_FAILED: isolated copy discarded; stable backup retained: %w", e)
		}
	}
	acceptance, e := svc.backupRecomputeAcceptance()
	if e != nil {
		return r, e
	}
	r.Recovery["acceptance_revalidation"] = acceptance
	if e = svc.backupPublishSourcePaths(stage, destination); e != nil {
		return r, e
	}
	if e = backupIntegrityPolicy(db, policy); e != nil {
		return r, e
	}
	if policy != nil {
		if policy.afterRecovery != nil {
			if e = policy.afterRecovery(db); e != nil {
				return r, e
			}
		}
		r.Recovery["local_upgrade"] = policy.purpose
	}
	r.After, e = backupInventory(db)
	if e != nil {
		return r, e
	}
	if _, e = db.Exec("PRAGMA wal_checkpoint(TRUNCATE)"); e != nil {
		return r, e
	}
	if e = db.Close(); e != nil {
		return r, e
	}
	if e = ctx.Err(); e != nil {
		return r, e
	}
	r.Status = "RESTORED_RECONCILIATION_REQUIRED"
	if len(workspaceRequests) != 0 {
		r.Status = "RESTORE_WORKSPACE_PIN_PENDING"
		r.Recovery["workspace_roots_pending"] = len(workspaceRequests)
	}
	r.Finished = Now()
	r.DurationMS = time.Since(start).Milliseconds()
	if e = backupWrite(filepath.Join(stage, "restore-report.json"), Bytes(r)); e != nil {
		return r, e
	}
	if e = os.Rename(stage, destination); e != nil {
		return r, e
	}
	if len(workspaceRequests) != 0 {
		pins, pinErr := opt.WorkspaceTarget(ctx, destination, workspaceRequests)
		if pinErr != nil {
			return r, fmt.Errorf("RESTORE_WORKSPACE_PIN_FAILED: restored copy remains non-active: %w", pinErr)
		}
		finalDB, openErr := store.Open(filepath.Join(destination, databaseName))
		if openErr != nil {
			return r, openErr
		}
		if e = backupActivateWorkspaces(ctx, finalDB, workspaceRequests, pins); e == nil {
			r.After, e = backupInventory(finalDB)
		}
		closeErr := finalDB.Close()
		if e != nil {
			return r, e
		}
		if closeErr != nil {
			return r, closeErr
		}
		r.Status = "RESTORED_RECONCILIATION_REQUIRED"
		delete(r.Recovery, "workspace_roots_pending")
		r.Recovery["workspace_roots_rebound"] = len(workspaceRequests)
		r.Finished = Now()
		r.DurationMS = time.Since(start).Milliseconds()
		updatedReport := filepath.Join(destination, "restore-report-updated.json")
		if e = backupWrite(updatedReport, Bytes(r)); e != nil {
			return r, e
		}
		if e = os.Rename(updatedReport, filepath.Join(destination, "restore-report.json")); e != nil {
			return r, e
		}
	}
	return r, nil
}
