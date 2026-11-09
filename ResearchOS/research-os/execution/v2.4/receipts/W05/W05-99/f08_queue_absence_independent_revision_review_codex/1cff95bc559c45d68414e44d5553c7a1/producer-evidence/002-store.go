package domain

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	"strconv"
	"strings"
	"time"
	_ "time/tzdata"
)

type Service struct {
	DB        *sql.DB
	Contracts *Contracts
	Protected protectedstore.Provider
	// Fixed by a trusted constructor, never by a request or environment selector.
	projectBindingRoute string
}
type Fault struct {
	Status        int
	Code, Message string
	Current       any
}

func (f *Fault) Error() string { return f.Code + ": " + f.Message }
func Fail(status int, code, msg string) error {
	return &Fault{Status: status, Code: code, Message: msg}
}

// NewCurrentMu is the installed current host's fixed construction policy. New
// remains the legacy constructor so existing stored projects and fixtures keep
// their historical binding semantics. Children inherit their stored parent.
func NewCurrentMu(db *sql.DB, contractsDir, migrationFile string) (*Service, error) {
	if err := validateProjectRules(projectRulesBytes, projectRulesMetadata); err != nil {
		return nil, err
	}
	s, err := New(db, contractsDir, migrationFile)
	if err != nil {
		return nil, err
	}
	s.projectBindingRoute = "MU_FORK"
	return s, nil
}

func New(db *sql.DB, contractsDir, migrationFile string) (*Service, error) {
	c, e := LoadContracts(contractsDir)
	if e != nil {
		return nil, e
	}
	files, e := filepath.Glob(filepath.Join(filepath.Dir(migrationFile), "[0-9][0-9][0-9][0-9]_*.sql"))
	if e != nil {
		return nil, e
	}
	if _, e = os.Stat(migrationFile); e != nil {
		return nil, e
	}
	// Refuse future/gapped inventories before domain, additive or fence DDL.
	// The lower storage layer has already opened the file and selected WAL.
	if _, e = checkMigrationInventory(db, files); e != nil {
		return nil, e
	}
	if e = CheckMigrationSafety(db, files); e != nil {
		return nil, e
	}
	tx, e := db.Begin()
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	for _, file := range files {
		version, err := strconv.Atoi(filepath.Base(file)[:4])
		if err != nil {
			return nil, err
		}
		if version < 2 {
			continue
		}
		var applied int
		if err := tx.QueryRow("SELECT count(*) FROM schema_migrations WHERE version=?", version).Scan(&applied); err != nil {
			return nil, err
		}
		if applied != 0 {
			continue
		}
		b, err := os.ReadFile(file)
		if err != nil {
			return nil, err
		}
		if _, err = tx.Exec(string(b)); err != nil {
			return nil, err
		}
		if _, err = tx.Exec("INSERT OR IGNORE INTO schema_migrations(version) VALUES(?)", version); err != nil {
			return nil, err
		}
	}
	// W03's additive session schema has its own unnumbered, idempotent path.
	// The production host must install it as well as the tests and import tools.
	// Keep it in the same transaction so a missing or invalid schema cannot
	// leave the business migrations committed with the typed client unusable.
	sessionSchema, err := os.ReadFile(filepath.Join(filepath.Dir(migrationFile), "next_v24_sessions.sql"))
	if err != nil {
		return nil, err
	}
	if _, err = tx.Exec(string(sessionSchema)); err != nil {
		return nil, err
	}
	if err = installClientSessionFence(context.Background(), tx, false); err != nil {
		return nil, err
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	return &Service{DB: db, Contracts: c, projectBindingRoute: "THIN_CORE"}, nil
}
func ID() string {
	var b [16]byte
	if _, e := rand.Read(b[:]); e != nil {
		panic(e)
	}
	return hex.EncodeToString(b[:])
}
func Now() string { return time.Now().UTC().Format(time.RFC3339Nano) }
func Base(project string) Object {
	now := Now()
	return Object{"id": ID(), "project_id": project, "revision": 1, "created_at": now, "updated_at": now}
}
func Merge(o Object, fields Object) Object {
	for k, v := range fields {
		o[k] = v
	}
	return o
}
func Empty() []any { return []any{} }
func load(tx *sql.Tx, project, kind, id string) (Object, error) {
	var raw string
	e := tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind=? AND id=?", project, kind, id).Scan(&raw)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, Fail(404, "NOT_FOUND", "object unavailable")
	}
	if e != nil {
		return nil, e
	}
	return Decode([]byte(raw))
}
func singleton(tx *sql.Tx, project, kind string) (Object, error) {
	var raw string
	e := tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind=?", project, kind).Scan(&raw)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, Fail(404, "NOT_FOUND", "object unavailable")
	}
	if e != nil {
		return nil, e
	}
	return Decode([]byte(raw))
}
func bump(o Object) error {
	n, e := Num(o, "revision")
	if e != nil {
		return e
	}
	if n == 1<<63-1 {
		return Fail(409, "STATE_CONFLICT", "revision exhausted")
	}
	o["revision"] = n + 1
	o["updated_at"] = Now()
	return nil
}

var idTargets = map[string]string{
	"budget_policy_id": "BudgetPolicy", "run_policy_id": "RunPolicy", "goal_id": "Goal", "task_id": "Task", "task_ids": "Task", "dependency_task_ids": "Task", "active_run_id": "Run", "run_id": "Run", "run_ids": "Run", "runtime_id": "RuntimeRegistration", "context_bundle_id": "ContextBundle", "no_progress_record_id": "NoProgressRecord", "acceptance_id": "AcceptanceReceipt", "acceptance_ids": "AcceptanceReceipt", "output_artifact_ids": "Artifact", "result_artifact_ids": "Artifact", "checkpoint_artifact_id": "Artifact", "blocking_conflict_ids": "Conflict", "conflict_ids": "Conflict", "active_goal_ids": "Goal", "active_cycle_id": "ResearchCycle", "latest_release_id": "MilestoneRelease", "pending_change_ids": "ChangeProposal", "origin_evidence_id": "Evidence", "verified_by_run_id": "Run", "candidate_evidence_ids": "Evidence", "required_experiment_ids": "Experiment", "decision_ids": "DecisionReceipt", "follow_up_task_ids": "Task", "cycle_id": "ResearchCycle", "qualification_id": "Qualification", "qualification_ids": "Qualification", "impact_link_ids": "ImpactLink", "semantic_review_run_id": "Run", "blocked_task_ids": "Task", "continuable_task_ids": "Task", "parent_release_id": "MilestoneRelease", "open_resource_request_ids": "ResourceRequest", "baseline_skill_id": "SkillVersion", "experiment_id": "Experiment", "rollback_skill_id": "SkillVersion", "regression_acceptance_id": "AcceptanceReceipt", "canary_acceptance_id": "AcceptanceReceipt", "rollback_verified_receipt_id": "AcceptanceReceipt", "last_cycle_id": "ResearchCycle", "policy_id": "BudgetPolicy", "reservation_id": "BudgetLedgerEntry", "release_id": "MilestoneRelease", "resource_request_id": "ResourceRequest", "resolution_proposal_id": "ChangeProposal",
}

func relationKind(owner, field string) string {
	if owner == "RuntimeRegistration" && field == "qualification_ids" {
		return "AcceptanceReceipt"
	}
	return idTargets[field]
}

func (s *Service) put(tx *sql.Tx, kind string, o Object) error {
	if !s.Contracts.Entities[kind] {
		return Fail(400, "INVALID_REQUEST", "unknown entity")
	}
	if e := s.Contracts.Validate(kind, o); e != nil {
		return Fail(400, "INVALID_REQUEST", "entity violates "+kind+" schema")
	}
	project := Str(o, "project_id")
	id := Str(o, "id")
	rev, e := Num(o, "revision")
	if e != nil {
		return e
	}
	old, e := load(tx, project, kind, id)
	if e == nil {
		if _, immutable := old["receipt_hash"]; immutable {
			return Fail(409, "STATE_CONFLICT", "receipt immutable")
		}
		oldRevision, e := Num(old, "revision")
		if e != nil {
			return e
		}
		if oldRevision == 1<<63-1 || rev != oldRevision+1 {
			return Fail(409, "STATE_CONFLICT", "revision must advance once")
		}
		if kind == "Task" && !taskTransition(old, o) {
			return Fail(409, "STATE_CONFLICT", "transition requires lifecycle owner")
		}
	} else if f, ok := e.(*Fault); !ok || f.Status != 404 {
		return e
	}
	if e = s.invariants(kind, o); e != nil {
		return e
	}
	var hash any
	immutable := 0
	if h, ok := o["receipt_hash"]; ok {
		if h != Receipt(o) {
			return Fail(422, "CONTENT_HASH_MISMATCH", "receipt hash mismatch")
		}
		hash = h
		immutable = 1
	} else if kind == "Artifact" {
		hash = o["content_hash"]
	}
	if _, e = tx.Exec("INSERT INTO domain_versions(project,kind,id,revision,body,content_hash) VALUES(?,?,?,?,?,?)", project, kind, id, rev, string(Bytes(o)), hash); e != nil {
		return e
	}
	if _, e = tx.Exec("INSERT INTO domain_objects(project,kind,id,revision,body,content_hash,immutable) VALUES(?,?,?,?,?,?,?) ON CONFLICT(project,kind,id) DO UPDATE SET revision=excluded.revision,body=excluded.body,content_hash=excluded.content_hash", project, kind, id, rev, string(Bytes(o)), hash, immutable); e != nil {
		return e
	}
	return s.refs(tx, project, kind, id, rev, "", o)
}
func (s *Service) refs(tx *sql.Tx, project, kind, id string, rev int64, path string, value any) error {
	switch v := value.(type) {
	case map[string]any:
		if _, ok := v["entity_type"]; ok {
			if e := s.Contracts.Validate("VersionRef", v); e != nil {
				return Fail(400, "INVALID_REQUEST", "invalid reference")
			}
			version, e := Num(v, "revision")
			if e != nil {
				return e
			}
			return s.ref(tx, project, kind, id, rev, path, project, Str(v, "entity_type"), Str(v, "id"), version, v["content_hash"], true)
		}
		for field, x := range v {
			if field == "id" || field == "project_id" {
				continue
			}
			target := relationKind(kind, field)
			if field == "supersedes_id" {
				target = kind
			}
			if field == "parent_policy_id" {
				target = kind
			}
			if target != "" && x != nil {
				values := []any{x}
				if a, ok := x.([]any); ok {
					values = a
				}
				for _, a := range values {
					tid, ok := a.(string)
					if !ok {
						return Fail(400, "INVALID_REQUEST", "invalid relation")
					}
					tp := project
					if field == "parent_policy_id" {
						var found int
						tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind=? AND id=?", project, target, tid).Scan(&found)
						if found == 0 {
							tp = ""
						}
					}
					obj, e := load(tx, tp, target, tid)
					if e != nil {
						return Fail(422, "GATE_FAILED", "related object unavailable")
					}
					version, e := Num(obj, "revision")
					if e != nil {
						return e
					}
					if e = s.ref(tx, project, kind, id, rev, path+"/"+field, tp, target, tid, version, nil, false); e != nil {
						return e
					}
				}
			} else if e := s.refs(tx, project, kind, id, rev, path+"/"+field, x); e != nil {
				return e
			}
		}
	case []any:
		for i, x := range v {
			if e := s.refs(tx, project, kind, id, rev, fmt.Sprintf("%s/%d", path, i), x); e != nil {
				return e
			}
		}
	}
	return nil
}
func (s *Service) ref(tx *sql.Tx, project, kind, id string, rev int64, path, tp, tk, tid string, tr int64, hash any, exact bool) error {
	var current int64
	var h sql.NullString
	e := tx.QueryRow("SELECT revision,content_hash FROM domain_objects WHERE project=? AND kind=? AND id=?", tp, tk, tid).Scan(&current, &h)
	if e != nil {
		return Fail(422, "GATE_FAILED", "reference unavailable")
	}
	history := kind == "Conflict" || kind == "Artifact" || kind == "ContextBundle" || kind == "DecisionReceipt" || kind == "AcceptanceReceipt" || kind == "AgentMessage" || kind == "ImpactLink" || kind == "ChangeProposal" || kind == "EventEnvelope" || kind == "SkillVersion" || ((kind == "Task" || kind == "Goal") && rev > 1)
	if exact && kind == "ResearchCycle" && path == "/profile_ref" && tk == "ProjectProfile" && tp == project && rev > 1 {
		var priorRaw, currentRaw string
		e = tx.QueryRow("SELECT prior.body,current.body FROM domain_versions prior JOIN domain_versions current ON current.project=prior.project AND current.kind=prior.kind AND current.id=prior.id AND current.revision=prior.revision+1 WHERE prior.project=? AND prior.kind='ResearchCycle' AND prior.id=? AND prior.revision=?", project, id, rev-1).Scan(&priorRaw, &currentRaw)
		if e != nil {
			return Fail(422, "GATE_FAILED", "cycle cancellation needs its previous version")
		}
		prior, err := Decode([]byte(priorRaw))
		if err != nil {
			return err
		}
		currentCycle, err := Decode([]byte(currentRaw))
		if err != nil {
			return err
		}
		history = currentCycle["status"] == "CANCELLED" && Hash(currentCycle["profile_ref"]) == Hash(prior["profile_ref"])
	}
	if exact && history {
		e = tx.QueryRow("SELECT revision,content_hash FROM domain_versions WHERE project=? AND kind=? AND id=? AND revision=?", tp, tk, tid, tr).Scan(&current, &h)
		if e != nil {
			return Fail(422, "GATE_FAILED", "historical reference unavailable")
		}
	}
	if exact && current != tr {
		return Fail(412, "STALE_INPUT", "reference revision changed")
	}
	if exact && ((h.Valid && hash != h.String) || (!h.Valid && hash != nil)) {
		return Fail(422, "CONTENT_HASH_MISMATCH", "reference hash mismatch")
	}
	_, e = tx.Exec("INSERT INTO domain_refs(project,kind,id,revision,field,target_project,target_kind,target_id,target_revision) VALUES(?,?,?,?,?,?,?,?,?)", project, kind, id, rev, path, tp, tk, tid, tr)
	return e
}
func (s *Service) invariants(kind string, o Object) error {
	if tz := Str(o, "timezone"); tz != "" {
		if _, e := time.LoadLocation(tz); e != nil {
			return Fail(400, "INVALID_REQUEST", "invalid IANA timezone")
		}
	}
	if kind == "RunPolicy" {
		lease, e := Num(o, "lease_seconds")
		if e != nil {
			return e
		}
		heartbeat, e := Num(o, "heartbeat_seconds")
		if e != nil {
			return e
		}
		if lease <= heartbeat {
			return Fail(422, "GATE_FAILED", "lease must exceed heartbeat")
		}
	}
	if kind == "BudgetPolicy" || kind == "RunPolicy" {
		scope := Str(o, "scope_type")
		if scope == "PROJECT" && o["scope_id"] != o["project_id"] {
			return Fail(422, "GATE_FAILED", "policy scope mismatch")
		}
	}
	return nil
}
func (s *Service) event(tx *sql.Tx, project, kind string, o Object, actor, correlation, eventType string) error {
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return e
	}
	seq, e := Num(state, "event_sequence")
	if e != nil {
		return e
	}
	// Typed session events share this outbox and allocate from its committed
	// watermark. Continue the same sequence inside the existing transaction;
	// ProjectState may predate intervening typed events.
	var outboxSequence int64
	if e = tx.QueryRow("SELECT COALESCE(MAX(sequence),0) FROM outbox WHERE project=?", project).Scan(&outboxSequence); e != nil {
		return e
	}
	if outboxSequence > seq {
		seq = outboxSequence
	}
	if seq == 1<<63-1 {
		return Fail(409, "STATE_CONFLICT", "event sequence exhausted")
	}
	seq++
	if e = bump(state); e != nil {
		return e
	}
	state["event_sequence"] = seq
	if e = s.put(tx, "ProjectState", state); e != nil {
		return e
	}
	ev := Object{"id": ID(), "project_id": project, "revision": 1, "created_at": Now(), "sequence": seq, "event_type": eventType, "aggregate_ref": Ref(o, kind), "actor_id": actor, "correlation_id": correlation, "causation_id": nil, "event_data_artifact_ref": nil}
	ev["receipt_hash"] = Receipt(ev)
	if e = s.put(tx, "EventEnvelope", ev); e != nil {
		return e
	}
	_, e = tx.Exec("INSERT INTO outbox(project,sequence,id,body) VALUES(?,?,?,?)", project, seq, ev["id"], string(Bytes(ev)))
	if e != nil {
		return e
	}
	_, e = tx.Exec("INSERT INTO event_state_snapshots(project,event_id,revision,body) VALUES(?,?,?,?)", project, ev["id"], state["revision"], string(Bytes(state)))
	return e
}

// AcknowledgeEvent is idempotent. Unacknowledged events remain durable for retry.
func (s *Service) AcknowledgeEvent(ctx context.Context, project, id string) error {
	res, e := s.DB.ExecContext(ctx, "UPDATE outbox SET acknowledged=1 WHERE project=? AND id=?", project, id)
	if e != nil {
		return e
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return Fail(404, "NOT_FOUND", "event unavailable")
	}
	return nil
}
func (s *Service) PendingEvents(ctx context.Context, project string) ([]Object, error) {
	rows, e := s.DB.QueryContext(ctx, "SELECT body FROM outbox WHERE project=? AND acknowledged=0 ORDER BY sequence", project)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	out := []Object{}
	for rows.Next() {
		var b string
		if e = rows.Scan(&b); e != nil {
			return nil, e
		}
		o, e := Decode([]byte(b))
		if e != nil {
			return nil, e
		}
		out = append(out, o)
	}
	return out, rows.Err()
}
func safeRole(role string) bool {
	return strings.Contains(" OWNER PLANNER EXECUTOR VERIFIER SCHEDULER RELEASE_SERVICE SOURCE_ADAPTER READER ", " "+role+" ")
}
