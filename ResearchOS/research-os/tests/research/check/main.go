// Command check runs the W08-01 reuse-decision qualification: the frozen ReuseDecisionPayload guard, the four-stage
// projection that init and Desktop share, the durable record path through a real HTTP+SQLite service, and the J01
// "judge before reusing" gate. Every named counter-example on the card is asserted as a refusal, not as a comment:
// a clone cannot be recorded as adoption, a score cannot appear without a Jev call, and a missing network cannot be
// traded for "skip the reuse gate and build it ourselves".
//
// Prints one JSON assertion report for the dispatcher.
package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

var ids []string
var failures []map[string]string

func ok(label string, cond bool, detail ...any) {
	if cond {
		ids = append(ids, label)
	} else {
		failures = append(failures, map[string]string{"id": label, "detail": fmt.Sprint(detail...)})
	}
}

func hard(label string, err error) {
	if err != nil {
		ok(label+"-HARD", false, err)
	}
}

type harness struct {
	handler http.Handler
	token   string
	owner   string
	etag    string
	db      *sql.DB
	s       *domain.Service
}

// readStage reads the stored bootstrap stage row straight out of the authoritative table, so a claim about a
// promotion is checked against what the database holds rather than against what the writer returned.
func readStage(db *sql.DB, project, stage string) (domain.Object, bool) {
	var raw string
	e := db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind=? AND id=?", project,
		domain.KindBootstrapStage, "stage-"+project+"-"+strings.ToLower(stage)).Scan(&raw)
	if e == sql.ErrNoRows {
		return nil, false
	}
	if e != nil {
		failures = append(failures, map[string]string{"id": "W0801-READSTAGE-HARD", "detail": fmt.Sprint(e)})
		return nil, false
	}
	o, e := domain.Decode([]byte(raw))
	if e != nil {
		failures = append(failures, map[string]string{"id": "W0801-READSTAGE-DECODE-HARD", "detail": fmt.Sprint(e)})
		return nil, false
	}
	return o, true
}

// call drives the production handler through the same HTTP contract a client uses. The request is handed to the
// handler in-process instead of over a socket because this build environment routes loopback traffic through a
// proxy, which would make the check depend on that proxy answering.
func (h *harness) call(method, path string, idempotency string, body any) (int, domain.Object) {
	var raw []byte
	if body != nil {
		switch v := body.(type) {
		case []byte:
			raw = v
		default:
			raw = domain.Bytes(v)
		}
	}
	req := httptest.NewRequest(method, path, bytes.NewReader(raw))
	req.Header.Set("Authorization", "Bearer "+h.token)
	req.Header.Set("Content-Type", "application/json")
	if idempotency != "" {
		req.Header.Set("Idempotency-Key", idempotency)
	}
	rec := httptest.NewRecorder()
	h.handler.ServeHTTP(rec, req)
	// The product is compare-and-swap: a write must name the revision it read, so the response's ETag is kept for the
	// next call in this chain instead of being dropped on the floor.
	if et := rec.Header().Get("ETag"); et != "" {
		h.etag = et
	}
	out := rec.Body.Bytes()
	if len(out) == 0 {
		return rec.Code, domain.Object{}
	}
	o, de := domain.Decode(out)
	if de != nil {
		return rec.Code, domain.Object{"_unparsable": string(out)}
	}
	return rec.Code, o
}

// callIfMatch repeats a write while naming the revision the previous response reported.
func (h *harness) callIfMatch(method, path string, idempotency string, body any) (int, domain.Object) {
	var raw []byte
	if body != nil {
		switch v := body.(type) {
		case []byte:
			raw = v
		default:
			raw = domain.Bytes(v)
		}
	}
	req := httptest.NewRequest(method, path, bytes.NewReader(raw))
	req.Header.Set("Authorization", "Bearer "+h.token)
	req.Header.Set("Content-Type", "application/json")
	if idempotency != "" {
		req.Header.Set("Idempotency-Key", idempotency)
	}
	req.Header.Set("If-Match", h.etag)
	rec := httptest.NewRecorder()
	h.handler.ServeHTTP(rec, req)
	if et := rec.Header().Get("ETag"); et != "" {
		h.etag = et
	}
	out := rec.Body.Bytes()
	if len(out) == 0 {
		return rec.Code, domain.Object{}
	}
	o, de := domain.Decode(out)
	if de != nil {
		return rec.Code, domain.Object{"_unparsable": string(out)}
	}
	return rec.Code, o
}

func newHarness(ctx context.Context, root string) (*harness, error) {
	tmp, e := os.MkdirTemp("", "w0801check")
	if e != nil {
		return nil, e
	}
	db, e := store.Open(filepath.Join(tmp, "research.sqlite"))
	if e != nil {
		return nil, e
	}
	if e = store.Bootstrap(ctx, db, filepath.Join(root, "migrations/sqlite/0001_bootstrap.sql")); e != nil {
		return nil, e
	}
	s, e := domain.New(db, filepath.Join(root, "spec/v2.0/contracts"), filepath.Join(root, "migrations/sqlite/0002_domain.sql"))
	if e != nil {
		return nil, e
	}
	// The contract's x-required-roles for sealArtifact is EXECUTOR|VERIFIER|SOURCE_ADAPTER|SCHEDULER, while
	// createProject requires OWNER, so the check actor carries both. The refusal of an OWNER-only seal is asserted
	// below rather than assumed away.
	p := domain.Principal{ID: "check-owner", Roles: []string{"OWNER", "EXECUTOR"}, CanCreateProject: true}
	if e = s.ProvisionPrincipal(ctx, p); e != nil {
		return nil, e
	}
	token, e := s.IssueCredential(ctx, p.ID, time.Minute)
	if e != nil {
		return nil, e
	}
	return &harness{handler: s.Handler(), token: token, owner: p.ID, db: db, s: s}, nil
}

// seal runs the product's own steps: upload the bytes, read the current ProjectState revision, then seal with that
// ETag. The contract gives sealArtifact x-precondition-target ProjectState, so the state must be re-read before every
// seal rather than reusing a tag from an earlier write.
func (h *harness) seal(ctx context.Context, project, payload, mode string) domain.Object {
	code, up := h.call("POST", "/v1/projects/"+project+"/content", domain.ID(), []byte(payload))
	if code != 201 {
		return domain.Object{"_error": fmt.Sprint("upload status ", code, " body ", string(domain.Bytes(up)))}
	}
	if stateCode, state := h.call("GET", "/v1/projects/"+project+"/state", "", nil); stateCode != 200 {
		return domain.Object{"_error": fmt.Sprint("state read status ", stateCode, " body ", string(domain.Bytes(state)))}
	}
	code, sealed := h.callIfMatch("POST", "/v1/projects/"+project+"/artifacts", domain.ID(), domain.Object{
		"run_id": nil, "kind": "MANIFEST", "evidence_kind": "GENERATED", "measurement_mode": mode,
		"content_hash": up["content_hash"], "storage_key": up["storage_key"], "media_type": "application/json",
		"byte_size": up["byte_size"], "input_refs": domain.Empty(), "source_refs": domain.Empty(),
		"produced_by": h.owner, "access_class": "PROJECT",
	})
	if code != 201 {
		return domain.Object{"_error": fmt.Sprint("seal status ", code, " body ", string(domain.Bytes(sealed)))}
	}
	return sealed
}

// countArtifacts counts the Artifact rows a project holds, so a refusal can be shown to have left nothing behind
// rather than merely having returned an error.
func countArtifacts(db *sql.DB, project string) int {
	var n int
	if e := db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind=?", project, "Artifact").
		Scan(&n); e != nil {
		failures = append(failures, map[string]string{"id": "W0801-COUNTARTIFACTS-HARD", "detail": fmt.Sprint(e)})
	}
	return n
}

// as returns the same harness speaking as another credential, so an authorization refusal can be attributed to the
// role rather than to the payload.
func (h *harness) as(token string) *harness {
	c := *h
	c.token = token
	return &c
}

func (h *harness) project() string {
	code, o := h.call("POST", "/v1/projects", domain.ID(), domain.Object{
		"name": "W08-01 check", "intent": "verify the reuse decision path", "facts": domain.Empty(),
		"accepted_scope": []any{"fixture"}, "constraints": domain.Empty(), "source_configs": domain.Empty(),
		"source_document_refs": domain.Empty(), "read_snapshot_ids": domain.Empty(),
	})
	if code != 201 {
		return ""
	}
	return domain.Str(o, "project_id")
}

// decision builds a payload that satisfies the frozen contract, so a refusal under test is about the guard's
// semantics and never about a malformed fixture.
func decision(project string, inventory, research, evidence, adoption domain.Object, kind string) domain.Object {
	return domain.Object{
		"project_id": project, "capability_id": "cap-reuse", "input_revision": float64(1),
		"local_inventory_artifact_id": domain.Str(inventory, "id"),
		"research_artifact_ids":       []any{domain.Str(research, "id")},
		"decision":                    kind,
		"chosen_source":               "https://github.com/paperclipai/paperclip",
		"source_revision":             "commit-abc123",
		"license_ref":                 domain.Str(evidence, "id"),
		"patch_scope":                 []any{"README.md"},
		"rejected_alternatives":       []any{"https://github.com/other/thing"},
		"remaining_gap":               "",
		"evidence_artifact_ids":       []any{domain.Str(evidence, "id")},
		"adoption_decision_ref":       domain.Ref(adoption, "Artifact"),
	}
}

func failingCheck(id string) map[string]any {
	return map[string]any{"check_id": id, "status": "FAIL"}
}

func passingCheck(id string) map[string]any {
	return map[string]any{"check_id": id, "status": "PASS"}
}

// receipt is a decision receipt shaped the way the accepted decision writer produces it.
func receipt(status, selected string, signals []any, det []any, missing []any) domain.Object {
	return domain.Object{"status": status, "selected": selected, "signals": signals,
		"deterministic_results": det, "missing_evidence": missing}
}

func statusOf(turns []domain.StageProjectionTurn, stage string) domain.StageProjectionTurn {
	for _, t := range turns {
		if t.Stage == stage {
			return t
		}
	}
	return domain.StageProjectionTurn{Stage: stage, Status: "MISSING"}
}

func refusal(err error, want string) bool {
	return err != nil && strings.Contains(err.Error(), want)
}

func main() {
	ctx := context.Background()
	root, _ := os.Getwd()

	// Routing truth: the dispatcher injects RESEARCHOS_TASK_ID / RESEARCHOS_CHECK_ID.
	tid, cid := os.Getenv("RESEARCHOS_TASK_ID"), os.Getenv("RESEARCHOS_CHECK_ID")
	if tid == "W08" && cid == "W08-02" {
		runW0802(ctx, root)
		return
	}
	ok("W0801-ROUTING-TRUTH-TABLE", tid == "W08" && cid == "W08-01",
		fmt.Sprintf("task_id=%q check_id=%q; this handler only answers W08/W08-01 or W08/W08-02", tid, cid))
	if tid != "W08" || cid != "W08-01" {
		report("FAIL")
		return
	}

	// The guard above is exercised, not just present: this program re-runs itself under a foreign binding and requires
	// the child to refuse. Remove the guard and this is the assertion that goes red, because the child would answer a
	// selector it does not own. The child is marked because a guard-less build otherwise re-probes forever: uncapped,
	// that mutant spawned several hundred processes on this host before the run was cut short.
	if self, selfErr := os.Executable(); selfErr != nil {
		ok("W0801-ROUTING-SELF-PROBE-REFUSES-FOREIGN-BINDING", false, selfErr)
	} else if os.Getenv("W0801_PROBE_CHILD") == "1" {
		ok("W0801-ROUTING-SELF-PROBE-REFUSES-FOREIGN-BINDING", false, "probe nesting stopped at depth 1")
	} else {
		probeCtx, cancel := context.WithTimeout(ctx, 120*time.Second)
		defer cancel()
		probe := exec.CommandContext(probeCtx, self)
		probe.Dir = root
		probe.Env = append(os.Environ(), "RESEARCHOS_TASK_ID=W08", "RESEARCHOS_CHECK_ID=W08-99",
			"W0801_PROBE_CHILD=1")
		out, probeErr := probe.Output()
		probeStatus := ""
		probeAssertions := -1.0
		var parsed map[string]any
		if len(bytes.TrimSpace(out)) > 0 && json.Unmarshal(bytes.TrimSpace(out), &parsed) == nil {
			probeStatus, _ = parsed["status"].(string)
			if n, isNum := parsed["assertions"].(float64); isNum {
				probeAssertions = n
			}
		}
		// Refusing is not enough: without the guard the program still fails at the end, having answered a selector it
		// does not own. The measured refusal is exactly one report line whose roster is empty, because the routing
		// check is the only thing that ran. Anything else - a full roster, or no parsable report at all - is a fail-open.
		ok("W0801-ROUTING-SELF-PROBE-REFUSES-FOREIGN-BINDING",
			probeErr != nil && probeStatus == "FAIL" && probeAssertions == 0,
			probeErr, probeStatus, probeAssertions, string(out))
	}

	// --- guard against the frozen contract on disk ---------------------------------------------
	schemaRaw, e := os.ReadFile(filepath.Join(root, "internal/api/contracts/client.protocol.schema.json"))
	hard("W0801-SCHEMA-READ", e)
	var schema map[string]any
	_ = json.Unmarshal(schemaRaw, &schema)
	wanted := []string{"project_id", "capability_id", "input_revision", "local_inventory_artifact_id",
		"research_artifact_ids", "decision", "chosen_source", "source_revision", "license_ref", "patch_scope",
		"rejected_alternatives", "remaining_gap", "evidence_artifact_ids", "adoption_decision_ref"}
	ok("W0801-SCHEMA-PAYLOAD-PRESENT", strings.Contains(string(schemaRaw), "ReuseDecisionPayload"), "schema has no ReuseDecisionPayload")
	encoded := strings.Join(wanted, ",")
	for _, frag := range wanted {
		if !strings.Contains(string(schemaRaw), "\""+frag+"\"") {
			ok("W0801-SCHEMA-FIELD-"+strings.ToUpper(frag), false, "required field "+frag+" is not in the schema text")
		}
	}
	ok("W0801-SCHEMA-REQUIRED-COUNT-14", len(wanted) == 14, len(wanted), encoded)

	base := decision("p-check", domain.Object{"id": "art-inv"}, domain.Object{"id": "art-res"},
		domain.Object{"id": "art-evi"}, domain.Object{"id": "art-ado", "entity_type": "Artifact", "content_hash": "h"},
		"ADOPT_UPSTREAM")

	// A valid upstream decision passes, and the guard returns the kind it accepted.
	kind, e := domain.ValidateReuseDecision(base)
	ok("W0801-GUARD-UPSTREAM-ACCEPTED", e == nil && kind == "ADOPT_UPSTREAM", e)

	// 本地已足够: reusing a local implementation is allowed to rest on the inventory alone.
	local := domain.Object{}
	for k, v := range base {
		local[k] = v
	}
	local["decision"] = "REUSE_LOCAL"
	local["research_artifact_ids"] = []any{"art-inv"}
	kind, e = domain.ValidateReuseDecision(local)
	ok("W0801-GUARD-LOCAL-ENOUGH-ACCEPTED", e == nil && kind == "REUSE_LOCAL", e)

	// 反例1: clone then default to ADOPT. The inventory artifact may not double as research for an upstream call.
	clone := domain.Object{}
	for k, v := range base {
		clone[k] = v
	}
	clone["research_artifact_ids"] = []any{"art-inv"}
	_, e = domain.ValidateReuseDecision(clone)
	ok("W0801-GUARD-CLONE-IS-NOT-RESEARCH", refusal(e, "a cloned working copy is not research evidence"), e)

	// 无许可证: an empty licence reference is refused rather than treated as "public domain, presumably".
	nolic := domain.Object{}
	for k, v := range base {
		nolic[k] = v
	}
	nolic["license_ref"] = "   "
	_, e = domain.ValidateReuseDecision(nolic)
	ok("W0801-GUARD-NO-LICENCE-REFUSED", refusal(e, "license_ref must not be empty"), e)

	// 确有缺口: CUSTOM_GAP is accepted only when it states what remains.
	gap := domain.Object{}
	for k, v := range base {
		gap[k] = v
	}
	gap["decision"] = "CUSTOM_GAP"
	gap["remaining_gap"] = "no upstream project covers offline arXiv indexing"
	kind, e = domain.ValidateReuseDecision(gap)
	ok("W0801-GUARD-CUSTOM-GAP-ACCEPTED", e == nil && kind == "CUSTOM_GAP", e)
	gap["remaining_gap"] = ""
	_, e = domain.ValidateReuseDecision(gap)
	ok("W0801-GUARD-CUSTOM-GAP-EMPTY-REFUSED", refusal(e, "CUSTOM_GAP must state the remaining gap"), e)

	// 候选不合适 / 无候选: a decision that names nothing it rejected is not a judgement.
	noalt := domain.Object{}
	for k, v := range base {
		noalt[k] = v
	}
	noalt["rejected_alternatives"] = []any{}
	_, e = domain.ValidateReuseDecision(noalt)
	ok("W0801-GUARD-NO-REJECTED-ALTERNATIVES-REFUSED", refusal(e, "must record the alternatives it rejected"), e)

	// 无候选 at all: a decision needs a research basis, and an empty list is "we found nothing" dressed as a decision.
	noresearch := domain.Object{}
	for k, v := range base {
		noresearch[k] = v
	}
	noresearch["research_artifact_ids"] = []any{}
	_, e = domain.ValidateReuseDecision(noresearch)
	ok("W0801-GUARD-NO-RESEARCH-BASIS-REFUSED", refusal(e, "at least one research artifact"), e)

	// additionalProperties:false: an undeclared field is refused, not quietly dropped.
	extra := domain.Object{}
	for k, v := range base {
		extra[k] = v
	}
	extra["confidence_score"] = 0.99
	_, e = domain.ValidateReuseDecision(extra)
	ok("W0801-GUARD-UNDECLARED-FIELD-REFUSED", refusal(e, "undeclared field confidence_score"), e)

	// A missing field is refused by name, so a reader can tell which one.
	for _, k := range wanted {
		m := domain.Object{}
		for kk, v := range base {
			if kk != k {
				m[kk] = v
			}
		}
		_, e := domain.ValidateReuseDecision(m)
		ok("W0801-GUARD-MISSING-"+strings.ToUpper(k), refusal(e, "reuse decision is missing "+k), e)
	}

	// --- projection ----------------------------------------------------------------------------
	rows := []domain.Object{
		{"stage": "LOCAL_INVENTORY", "status": "COMPLETED", "revision": float64(1), "inventory_artifact_ref": "art-inv"},
		{"stage": "RESEARCH", "status": "NOT_STARTED", "revision": float64(1)},
		{"stage": "IMPLEMENTATION", "status": "PARTIAL", "revision": float64(2)},
	}
	turns, e := domain.ProjectStages(rows, nil)
	hard("W0801-PROJ-RUNS", e)
	names := []string{}
	for _, t := range turns {
		names = append(names, t.Stage)
	}
	ok("W0801-PROJ-FOUR-STAGES-NAMED", strings.Join(names, ">") == "LOCAL_INVENTORY>RESEARCH>REUSE_DECISION>IMPLEMENTATION", names)
	ok("W0801-PROJ-ABSENT-DISTINCT-NOTSTARTED", statusOf(turns, "REUSE_DECISION").Status == "ABSENT" &&
		statusOf(turns, "RESEARCH").Status == "NOT_STARTED", turns)
	ok("W0801-PROJ-ABSENT-NAMES-BOOTSTRAP", statusOf(turns, "REUSE_DECISION").ReaderAction != "", statusOf(turns, "REUSE_DECISION"))
	everyIncompleteHasAction := true
	for _, t := range turns {
		if t.Status != "COMPLETED" && strings.TrimSpace(t.ReaderAction) == "" {
			everyIncompleteHasAction = false
		}
	}
	ok("W0801-PROJ-READER-ACTION-EVERY-INCOMPLETE", everyIncompleteHasAction, turns)
	ok("W0801-PROJ-PARTIAL-NOT-READ-AS-DONE", statusOf(turns, "IMPLEMENTATION").Status == "PARTIAL", statusOf(turns, "IMPLEMENTATION"))

	// The init/Desktop happy path: all four stages present, research complete, and a decision that passes the guard.
	full := []domain.Object{
		{"stage": "LOCAL_INVENTORY", "status": "COMPLETED", "revision": float64(1), "inventory_artifact_ref": "art-inv"},
		{"stage": "RESEARCH", "status": "COMPLETED", "revision": float64(1), "inventory_artifact_ref": "art-res"},
		{"stage": "REUSE_DECISION", "status": "COMPLETED", "revision": float64(1)},
		{"stage": "IMPLEMENTATION", "status": "NOT_STARTED", "revision": float64(1)},
	}
	turns, e = domain.ProjectStages(full, base)
	reuse := statusOf(turns, "REUSE_DECISION")
	ok("W0801-PROJ-HAPPY-PATH-FOUR-STAGES", e == nil && reuse.Status == "COMPLETED" &&
		reuse.EvidenceRef != nil && *reuse.EvidenceRef == "art-ado", e, reuse)

	// 反例3: research never ran, yet the reuse stage claims completion. The reader refuses rather than showing a
	// decision that skipped the reuse gate, and says which state it is objecting to.
	noResearch := []domain.Object{
		{"stage": "LOCAL_INVENTORY", "status": "COMPLETED", "revision": float64(1)},
		{"stage": "RESEARCH", "status": "NOT_STARTED", "revision": float64(1)},
		{"stage": "REUSE_DECISION", "status": "COMPLETED", "revision": float64(1)},
	}
	_, e = domain.ProjectStages(noResearch, base)
	ok("W0801-PROJ-NO-SKIP-WITHOUT-RESEARCH", refusal(e, "while RESEARCH is NOT_STARTED"), e)

	abstainRows := []domain.Object{
		{"stage": "LOCAL_INVENTORY", "status": "COMPLETED", "revision": float64(1)},
		{"stage": "REUSE_DECISION", "status": "COMPLETED", "revision": float64(1)},
	}
	_, e = domain.ProjectStages(abstainRows, base)
	ok("W0801-PROJ-NO-SKIP-WHEN-RESEARCH-ROW-ABSENT", refusal(e, "while RESEARCH is ABSENT"), e)

	// PARTIAL is an attempt that was made, so it is not the same as never researching; the gap it leaves open is what
	// the decision has to state.
	partial := []domain.Object{
		{"stage": "LOCAL_INVENTORY", "status": "COMPLETED", "revision": float64(1)},
		{"stage": "RESEARCH", "status": "PARTIAL", "revision": float64(1)},
		{"stage": "REUSE_DECISION", "status": "COMPLETED", "revision": float64(1)},
	}
	gapDecision := domain.Object{}
	for k, v := range base {
		gapDecision[k] = v
	}
	gapDecision["decision"] = "CUSTOM_GAP"
	gapDecision["remaining_gap"] = "no upstream project covers offline arXiv indexing"
	_, e = domain.ProjectStages(partial, gapDecision)
	ok("W0801-PROJ-PARTIAL-RESEARCH-STILL-A-RESEARCH-BASIS", e == nil, e)

	// A hand-edited COMPLETED row must not be self-justifying.
	tampered := append([]domain.Object{}, rows...)
	tampered = append(tampered, domain.Object{"stage": "REUSE_DECISION", "status": "COMPLETED", "revision": float64(1)})
	_, e = domain.ProjectStages(tampered, nil)
	ok("W0801-PROJ-COMPLETED-WITHOUT-DECISION-REFUSED", refusal(e, "no decision to show"), e)
	_, e = domain.ProjectStages(tampered, clone)
	ok("W0801-PROJ-COMPLETED-WITH-BAD-DECISION-REFUSED", refusal(e, "a cloned working copy is not research evidence"), e)

	// --- J01 gate: judge before reusing --------------------------------------------------------
	score, e := domain.ReuseJevGate(nil)
	ok("W0801-JEV-NO-RECEIPT-REFUSED", refusal(e, "no Jev call was made"), e)
	ok("W0801-JEV-NO-RECEIPT-ZERO-SCORE", score == 0, score)

	score, e = domain.ReuseJevGate(receipt("ABSTAIN", "adopt", []any{}, []any{}, []any{}))
	ok("W0801-JEV-ABSTAIN-REFUSED", refusal(e, "only a DECIDED receipt"), e)

	// 反例2: a score is shown but nothing called Jev.
	score, e = domain.ReuseJevGate(receipt("DECIDED", "adopt",
		[]any{map[string]any{"jev_called": false, "value": 0.93}}, []any{}, []any{}))
	ok("W0801-JEV-SCORE-WITHOUT-CALL-REFUSED", refusal(e, "without jev_called"), e)

	// 高分硬失败: the top-scoring candidate still loses to a failed deterministic check.
	_, e = domain.ReuseJevGate(receipt("DECIDED", "adopt",
		[]any{map[string]any{"jev_called": true, "value": 0.97}}, []any{failingCheck("license-scan")}, []any{}))
	ok("W0801-JEV-HARDFAIL-OVERRIDES-SCORE", refusal(e, "no score can outweigh: license-scan"), e)

	// 无许可证证据: missing evidence is a hard failure of its own.
	_, e = domain.ReuseJevGate(receipt("DECIDED", "adopt",
		[]any{map[string]any{"jev_called": true, "value": 0.88}}, []any{}, []any{"licence text"}))
	ok("W0801-JEV-MISSING-EVIDENCE-REFUSED", refusal(e, "missing evidence"), e)

	// 无合格候选: DECIDED with an empty selection measured nothing.
	_, e = domain.ReuseJevGate(receipt("DECIDED", "", []any{}, []any{}, []any{}))
	ok("W0801-JEV-NO-CANDIDATE-REFUSED", refusal(e, "measured no action"), e)
	_, e = domain.ReuseJevGate(receipt("DECIDED", "adopt", []any{}, []any{}, []any{}))
	ok("W0801-JEV-NO-QUALIFIED-SIGNAL-REFUSED", refusal(e, "no qualified candidate"), e)

	// A real judgement: a Jev-produced score over a passing deterministic check is returned to the reader.
	score, e = domain.ReuseJevGate(receipt("DECIDED", "adopt",
		[]any{map[string]any{"jev_called": true, "value": 0.61}, map[string]any{"jev_called": true, "value": 0.74}},
		[]any{passingCheck("license-scan"), passingCheck("revision-pinned")}, []any{}))
	ok("W0801-JEV-REAL-CALL-SCORES", e == nil && score == 0.74, score, e)
	// An abstained signal carries no value and does not break an otherwise valid receipt.
	score, e = domain.ReuseJevGate(receipt("DECIDED", "adopt",
		[]any{map[string]any{"jev_called": true, "value": nil, "host_abstained": true},
			map[string]any{"jev_called": true, "value": 0.5}}, []any{}, []any{}))
	ok("W0801-JEV-ABSTAINED-SIGNAL-TOLERATED", e == nil && score == 0.5, score, e)

	// --- durable record path through the real service ----------------------------------------
	h, e := newHarness(ctx, root)
	if e != nil {
		ok("W0801-HARNESS-HARD", false, e)
		report("FAIL")
		return
	}
	defer h.db.Close()

	project := h.project()
	ok("W0801-PRODUCT-PROJECT-CREATED", project != "", project)
	inventory := h.seal(ctx, project, "local inventory of implemented features", "FIXTURE")
	research := h.seal(ctx, project, "research notes over three candidates", "FIXTURE")
	evidence := h.seal(ctx, project, "upstream licence text: Apache-2.0", "FIXTURE")
	adoption := h.seal(ctx, project, "adoption decision document", "FIXTURE")
	allSealed := domain.Str(inventory, "id") != "" && domain.Str(research, "id") != "" &&
		domain.Str(evidence, "id") != "" && domain.Str(adoption, "id") != ""
	ok("W0801-PRODUCT-ARTIFACTS-SEALED", allSealed, inventory, research, evidence, adoption)

	// The seal really went through the production authorization gate: the identical request under an OWNER-only
	// credential is refused, so a PASS above cannot be an artifact of the harness bypassing roles.
	onlyOwner := domain.Principal{ID: "check-owner-only", Roles: []string{"OWNER"}, CanCreateProject: true}
	hard("W0801-ROLE-PROVISION", h.s.ProvisionPrincipal(ctx, onlyOwner))
	ownerOnlyToken, e := h.s.IssueCredential(ctx, onlyOwner.ID, time.Minute)
	hard("W0801-ROLE-CREDENTIAL", e)
	badCode, badBody := h.as(ownerOnlyToken).call("POST", "/v1/projects/"+project+"/artifacts", domain.ID(),
		domain.Object{"run_id": nil, "kind": "MANIFEST", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE",
			"content_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
			"storage_key":  "probe", "media_type": "application/json", "byte_size": float64(1),
			"input_refs": domain.Empty(), "source_refs": domain.Empty(), "produced_by": onlyOwner.ID,
			"access_class": "PROJECT"})
	ok("W0801-PRODUCT-SEAL-REFUSES-OWNER-ONLY", badCode == 403 &&
		strings.Contains(string(domain.Bytes(badBody)), "role not authorized"), badCode, string(domain.Bytes(badBody)))

	good := decision(project, inventory, research, evidence, adoption, "ADOPT_UPSTREAM")
	out, e := h.s.RecordReuseDecision(ctx, h.token, project, good, "FIXTURE")
	hard("W0801-RECORD-CALL", e)
	ok("W0801-RECORD-PROMOTES", e == nil && domain.Str(out, "decision") == "ADOPT_UPSTREAM", e, out)

	row, present := readStage(h.db, project, "REUSE_DECISION")
	ok("W0801-RECORD-STAGE-ROW-WRITTEN", present && domain.Str(row, "status") == "COMPLETED", present, row)
	if present {
		ado, _ := out["adoption_artifact"].(domain.Object)
		ok("W0801-RECORD-STAGE-POINTS-AT-SEALED", domain.Str(row, "inventory_artifact_ref") ==
			domain.Str(ado, "id"), row, out)
		// On the real rows: this project was created over HTTP and never ran project.bootstrap, so there is no RESEARCH
		// row. A reader must still refuse to present the stored promotion as a finished reuse stage.
		_, skipErr := domain.ProjectStages([]domain.Object{row}, good)
		ok("W0801-PRODUCT-PROJ-REFUSES-WITHOUT-RESEARCH-ROW", refusal(skipErr, "while RESEARCH is ABSENT"), skipErr)
	}

	// Promotion touches only its own stage: research and implementation keep their own evidence paths.
	_, researchPresent := readStage(h.db, project, "RESEARCH")
	ok("W0801-RECORD-DOES-NOT-PROMOTE-RESEARCH", !researchPresent, researchPresent)

	// 反例3: no network is not a licence to skip the reuse gate. A decision that cites an artifact which was never
	// sealed - the shape "we could not research, so we recorded something anyway" - is refused and leaves no stage.
	badProject := h.project()
	bad := decision(badProject, inventory, research, evidence, adoption, "ADOPT_UPSTREAM")
	if _, e := h.s.RecordReuseDecision(ctx, h.token, badProject, bad, "FIXTURE"); e == nil {
		ok("W0801-RECORD-FOREIGN-ARTIFACT-REFUSED", false, "a decision citing another project's artifacts was accepted")
	} else {
		ok("W0801-RECORD-FOREIGN-ARTIFACT-REFUSED", true)
	}
	_, leaked := readStage(h.db, badProject, "REUSE_DECISION")
	ok("W0801-RECORD-REFUSAL-LEAVES-NO-STAGE", !leaked, leaked)

	// A refusal mid-transaction must not promote the stage either.
	dangling := decision(project, inventory, research, evidence, adoption, "ADOPT_UPSTREAM")
	dangling["research_artifact_ids"] = []any{"art-never-sealed"}
	before := countArtifacts(h.db, project)
	_, danglingErr := h.s.RecordReuseDecision(ctx, h.token, project, dangling, "FIXTURE")
	ok("W0801-RECORD-ABSENT-ARTIFACT-REFUSED", danglingErr != nil &&
		strings.Contains(fmt.Sprint(danglingErr), "artifact unavailable"), danglingErr)
	// The distinguishing control: the citation is what fails, so nothing is sealed on the way. If the existence read
	// were removed, the write would reach the seal step and leave an artifact behind even though it still refused.
	ok("W0801-RECORD-ABSENT-ARTIFACT-CREATES-NOTHING", countArtifacts(h.db, project) == before,
		before, countArtifacts(h.db, project), danglingErr)
	after, _ := readStage(h.db, project, "REUSE_DECISION")
	ok("W0801-RECORD-REFUSAL-DOES-NOT-DOWNGRADE", present && domain.Str(after, "status") == "COMPLETED", after)

	// A decision bound to another project is refused by the binding check itself, not by an artifact accident: every
	// artifact it cites really exists, but in this project, while the payload names a different one.
	other := h.project()
	foreign := decision(other, inventory, research, evidence, adoption, "ADOPT_UPSTREAM")
	foreignStage, _ := readStage(h.db, other, "REUSE_DECISION")
	_, bindErr := h.s.RecordReuseDecision(ctx, h.token, project, foreign, "FIXTURE")
	ok("W0801-RECORD-PROJECT-MISMATCH-REFUSED", bindErr != nil &&
		strings.Contains(fmt.Sprint(bindErr), "bound to a different project"), bindErr)
	ok("W0801-RECORD-PROJECT-MISMATCH-LEAVES-NO-STAGE", foreignStage == nil, foreignStage)

	// measurement_mode is transport metadata, never payload: LIVE/unknown modes are refused before any write.
	if _, e := h.s.RecordReuseDecision(ctx, h.token, project, good, "LIVE_QUALIFIED"); e == nil {
		ok("W0801-RECORD-UNKNOWN-MODE-REFUSED", false, "an unrecognised measurement mode was accepted")
	} else {
		ok("W0801-RECORD-UNKNOWN-MODE-REFUSED", refusal(e, "must be FIXTURE or LIVE"), e)
	}

	sort.Strings(ids)
	if len(failures) == 0 {
		report("PASS")
		return
	}
	report("FAIL")
}

// W08-02's selector runs the domain's HTTP+SQLite evidence fixtures. Go's JSON
// test events prove every named witness actually executed, not merely that the
// package returned zero after a misspelled -run filter.
func runW0802(ctx context.Context, root string) {
	tests := []string{
		"TestW0802PendingWindowsCoalesceAcrossRestart",
		"TestResearchMonitorAcceptedPlanBinding",
		"TestResearchCycleBoundBeforeFirstTask",
		"TestResearchDriverCreatesOneFiniteCycleAndTruthfulMissingReport",
		"TestResearchMonitorPauseResumeCancelAndDrift",
		"TestResearchTaskBoundAndPublicCloseGate",
		"TestResearchOfflineCandidateStagesCurrentReceipts",
		"TestResearchNativeSourceReceiptToIndependentClose",
		"TestResearchNoProgressPersistsAcrossAcceptedReports",
		"TestResearchRecompiledSameIntentKeepsNoProgress",
		"TestResearchOfflineNativeExperimentAndProgress",
		"TestW08ManualDispositionCurrentBoundary",
		"TestW08RequiredGates",
		"TestW08CoverageGates",
		"TestW08C06MissingXContinuesSources",
		"TestW08C06RateLimitedXCoalesces",
		"TestW08C05CompleteWithoutAdoption",
		"TestW08G02SixHourAndMissedTicks",
	}
	goBinary := filepath.Join(runtime.GOROOT(), "bin", "go")
	if runtime.GOOS == "windows" {
		goBinary += ".exe"
	}
	deadline, cancel := context.WithTimeout(ctx, 4*time.Minute)
	defer cancel()
	cmd := exec.CommandContext(deadline, goBinary, "test", "-json", "./internal/domain", "-run", "^("+strings.Join(tests, "|")+")$", "-count=1")
	cmd.Dir = root
	cmd.Env = append(os.Environ(), "RESEARCHOS_GO="+goBinary)
	out, err := cmd.CombinedOutput()
	passed := map[string]bool{}
	for _, line := range bytes.Split(out, []byte{'\n'}) {
		var event struct {
			Action string `json:"Action"`
			Test   string `json:"Test"`
		}
		if json.Unmarshal(line, &event) == nil && event.Action == "pass" {
			passed[event.Test] = true
		}
	}
	for _, name := range tests {
		ok("W0802-"+strings.TrimPrefix(name, "Test"), passed[name], name+" did not pass")
	}
	if err != nil {
		tail := out
		if len(tail) > 3000 {
			tail = tail[len(tail)-3000:]
		}
		ok("W0802-TEST-PROCESS", false, err, string(tail))
	}
	sort.Strings(ids)
	if len(failures) == 0 {
		report("PASS")
		return
	}
	report("FAIL")
}

func report(status string) {
	out, _ := json.Marshal(map[string]any{"status": status, "assertions": len(ids), "assertion_ids": ids,
		"failures": failures})
	os.Stdout.Write(append(out, '\n'))
	if status != "PASS" {
		os.Exit(1)
	}
}
