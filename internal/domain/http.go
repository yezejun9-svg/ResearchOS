package domain

import (
	"database/sql"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"
)

func (s *Service) Handler() http.Handler {
	mux := http.NewServeMux()
	remote := s.newRemoteHandler()
	for _, op := range s.Contracts.Operations {
		mux.HandleFunc(op.Method+" "+op.Path, func(w http.ResponseWriter, r *http.Request) {
			if !s.remoteOperationBoundary(w, r, op) {
				return
			}
			if remoteOperations[op.ID] {
				remote.handle(w, r, op)
				return
			}
			if op.ID == "streamEvents" {
				s.streamWorkbenchEvents(w, r, op)
				return
			}
			if op.ID == "recordAcceptance" || op.ID == "claimTask" {
				s.handleAuditedOrchestration(w, r, op)
				return
			}
			s.handle(w, r, op)
		})
	}
	mux.HandleFunc("/v1/", func(w http.ResponseWriter, r *http.Request) {
		s.writeError(w, ID(), Fail(404, "NOT_FOUND", "operation unavailable"))
	})
	return mux
}
func (s *Service) writeError(w http.ResponseWriter, cid string, e error) {
	f, ok := e.(*Fault)
	if !ok {
		f = &Fault{500, "INTERNAL_ERROR", "operation failed", nil}
		if strings.Contains(e.Error(), "constraint failed") {
			f = &Fault{409, "STATE_CONFLICT", "persistent invariant rejected operation", nil}
		}
	}
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Correlation-ID", cid)
	if f.Current != nil {
		w.Header().Set("ETag", fmt.Sprintf("\"r%v\"", f.Current))
	}
	w.WriteHeader(f.Status)
	w.Write(Bytes(Object{"code": f.Code, "message": f.Message, "correlation_id": cid, "retryable": f.Status == 503, "current_revision": f.Current, "details": Empty()}))
}

var etagPattern = regexp.MustCompile(`^"r[1-9][0-9]*"$`)

const BodyReadTimeout = 5 * time.Second

func (s *Service) handle(w http.ResponseWriter, r *http.Request, op Operation) {
	cid := ID()
	auth := r.Header.Get("Authorization")
	if !strings.HasPrefix(auth, "Bearer ") {
		s.writeError(w, cid, Fail(401, "UNAUTHENTICATED", "Bearer credential required"))
		return
	}
	// Read bounded input before acquiring SQLite's single authoritative connection.
	controller := http.NewResponseController(w)
	if e := controller.SetReadDeadline(time.Now().Add(BodyReadTimeout)); e != nil && !errors.Is(e, http.ErrNotSupported) {
		s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "body read unavailable"))
		return
	}
	raw, e := io.ReadAll(io.LimitReader(r.Body, 64*1024*1024+1))
	if e != nil || len(raw) > 64*1024*1024 {
		s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "invalid, timed out or oversized body"))
		return
	}
	var prepared *preparedAcceptance
	var qualificationProof *preparedQualification
	var preparationError error
	if op.ID == "recordAcceptance" {
		if input, err := Decode(raw); err == nil && s.Contracts.Validate(op.Request, input) == nil {
			if ref, ok := input["subject_ref"].(map[string]any); ok && (ref["entity_type"] == "Task" || ref["entity_type"] == "Goal") {
				prepared, preparationError = s.prepareTaskAcceptance(r.Context(), strings.TrimPrefix(auth, "Bearer "), r.PathValue("project_id"), input)
			} else if ok && ref["entity_type"] == "Qualification" {
				qualificationProof, preparationError = s.prepareQualification(r.Context(), strings.TrimPrefix(auth, "Bearer "), r.PathValue("project_id"), Str(ref, "id"))
			}
		}
	}
	if op.ID == "recordQualificationResult" {
		if input, err := Decode(raw); err == nil && s.Contracts.Validate(op.Request, input) == nil {
			qualificationProof, preparationError = s.prepareQualification(r.Context(), strings.TrimPrefix(auth, "Bearer "), r.PathValue("project_id"), r.PathValue("object_id"))
		}
	}
	tx, e := s.DB.BeginTx(r.Context(), nil)
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	defer tx.Rollback()
	if resourceOperations[op.ID] && op.Method != "GET" {
		if e = resourceWriteLock(tx); e != nil {
			s.writeError(w, cid, e)
			return
		}
	}
	p, e := authenticate(tx, strings.TrimPrefix(auth, "Bearer "))
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	w.Header().Set("X-ResearchOS-Principal-ID", p.ID)
	roleOK := false
	for _, role := range op.Roles {
		if p.HasRole(role) {
			roleOK = true
		}
	}
	if !roleOK {
		s.writeError(w, cid, Fail(403, "FORBIDDEN", "role not authorized for operation"))
		return
	}
	project, id := r.PathValue("project_id"), r.PathValue("object_id")
	if !op.Implemented {
		s.writeError(w, cid, Fail(503, "RESOURCE_UNAVAILABLE", "operation requires "+op.Owner))
		return
	}
	if op.ID == "createProject" && !p.CanCreateProject {
		s.writeError(w, cid, Fail(403, "FORBIDDEN", "project creation is not granted"))
		return
	}
	b := Object{}
	if op.Request != "" {
		b, e = Decode(raw)
		if e == nil {
			e = s.Contracts.Validate(op.Request, b)
		}
		if e != nil {
			s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "request violates "+op.Request+" schema"))
			return
		}
	} else if op.Method == "GET" && len(raw) != 0 {
		s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "GET body unsupported"))
		return
	}
	if project != "" && !p.Allowed(project, "", "", false) && !s.runtimeScope(tx, p, project, id, op.ID, b) {
		s.writeError(w, cid, Fail(404, "NOT_FOUND", "project or object unavailable"))
		return
	}
	requestKind := ""
	if op.ID == "qualifyRuntime" {
		requestKind = "RuntimeRegistration"
	}
	if !s.visibleAs(tx, p, project, requestKind, b) {
		s.writeError(w, cid, Fail(403, "FORBIDDEN", "restricted reference unavailable"))
		return
	}
	if op.ID == "markNotificationRead" {
		if _, e = s.readObject(tx, p, project, "Notification", id); e != nil {
			s.writeError(w, cid, e)
			return
		}
	}
	search := op.ID == "searchEvidence"
	write := op.Method != "GET" && !search
	key := r.Header.Get("Idempotency-Key")
	var requestHash string
	searchSeen := false
	if search {
		values, present := r.Header[http.CanonicalHeaderKey("Idempotency-Key")]
		if !present {
			s.writeError(w, cid, Fail(428, "PRECONDITION_REQUIRED", "Idempotency-Key required"))
			return
		}
		if len(values) != 1 || s.Contracts.Validate("Idempotency-Key", key) != nil {
			s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "Idempotency-Key violates header schema"))
			return
		}
		requestHash = Hash([]any{op.ID, r.URL.EscapedPath(), r.URL.Query().Encode(), b})
		var oldHash string
		e = tx.QueryRow("SELECT request_hash FROM retrieval_dedupe WHERE principal=? AND project=? AND key=?", p.ID, project, key).Scan(&oldHash)
		if e == nil {
			searchSeen = true
			if oldHash != requestHash {
				s.writeError(w, cid, Fail(409, "IDEMPOTENCY_CONFLICT", "key already used with different request"))
				return
			}
		} else if !errors.Is(e, sql.ErrNoRows) {
			s.writeError(w, cid, e)
			return
		}
	}
	if write {
		values, present := r.Header[http.CanonicalHeaderKey("Idempotency-Key")]
		if !present {
			s.writeError(w, cid, Fail(428, "PRECONDITION_REQUIRED", "Idempotency-Key required"))
			return
		}
		if len(values) != 1 || s.Contracts.Validate("Idempotency-Key", key) != nil {
			s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "Idempotency-Key violates header schema"))
			return
		}
		var body any = b
		if op.ID == "uploadContent" {
			body = Digest(raw)
		}
		requestHash = Hash([]any{op.ID, r.URL.EscapedPath(), r.URL.Query().Encode(), r.Header.Get("If-Match"), body})
		var oldHash, headers string
		var status int
		var bodyBytes []byte
		e = tx.QueryRow("SELECT request_hash,status,body,headers FROM idempotency WHERE principal=? AND project=? AND operation=? AND key=?", p.ID, project, op.ID, key).Scan(&oldHash, &status, &bodyBytes, &headers)
		if e == nil {
			if oldHash != requestHash {
				s.writeError(w, cid, Fail(409, "IDEMPOTENCY_CONFLICT", "key already used with different request"))
				return
			}
			h, _ := Decode([]byte(headers))
			if !s.replayAllowed(tx, p, op, bodyBytes) {
				s.writeError(w, cid, Fail(403, "FORBIDDEN", "current permission denies replay"))
				return
			}
			for k, v := range h {
				w.Header().Set(k, v.(string))
			}
			w.Header().Set("Idempotency-Replayed", "true")
			w.WriteHeader(status)
			w.Write(bodyBytes)
			return
		}
		if !errors.Is(e, sql.ErrNoRows) {
			s.writeError(w, cid, e)
			return
		}
		if op.Target != "" {
			match := r.Header.Get("If-Match")
			if match == "" {
				s.writeError(w, cid, Fail(428, "PRECONDITION_REQUIRED", "If-Match required"))
				return
			}
			if !etagPattern.MatchString(match) {
				s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "strong revision ETag required"))
				return
			}
			target, e := s.precondition(tx, project, id, op, b)
			if e != nil {
				s.writeError(w, cid, e)
				return
			}
			tag, e := ETag(target)
			if e != nil {
				s.writeError(w, cid, e)
				return
			}
			if match != tag {
				current, e := Num(target, "revision")
				if e != nil {
					s.writeError(w, cid, e)
					return
				}
				s.writeError(w, cid, &Fault{412, "STALE_REVISION", "aggregate changed", current})
				return
			}
		}
	}
	var result Object
	status := 200
	kind := ""
	headers := Object{"Content-Type": "application/json", "Cache-Control": "no-store", "X-Correlation-ID": cid}
	switch op.ID {
	case "createProject":
		result, e = s.createProject(tx, p, b)
		kind = "ProjectProfile"
		status = 201
	case "createRequirement":
		result, e = s.createRequirement(tx, project, b)
		if e == nil {
			e = s.registerIntentSubmission(tx, p, project, result)
		}
		kind = "Requirement"
		status = 201
	case "createEvidence":
		result, e = s.createEvidence(tx, project, b)
		kind = "Evidence"
		status = 201
	case "verifyEvidence":
		result, e = s.verifyEvidence(tx, p, project, id, b)
		kind = "Evidence"
	case "searchEvidence":
		result, e = s.searchEvidence(tx, p, project, b)
	case "advanceSourceCursor":
		result, e = s.advanceSourceCursor(tx, project, id, b)
		kind = "SourceCursor"
	case "actOnRequirement":
		result, e = s.acceptIntentRequirement(tx, p, project, id, b)
		kind = "Requirement"
	case "createSystemCandidate":
		result, e = s.createSystemCandidate(tx, p, project, b)
		kind = "SystemCandidate"
		status = 201
	case "actOnSystemCandidate":
		result, e = s.actSystemCandidate(tx, p, project, id, b)
		kind = "SystemCandidate"
	case "createExperiment":
		result, e = s.createExperiment(tx, project, b)
		kind = "Experiment"
		status = 201
	case "createSkillCandidate":
		result, e = s.createSkillCandidate(tx, p, project, b)
		kind = "SkillVersion"
		status = 201
	case "promoteSkill":
		result, e = s.promoteSkill(tx, project, id, b)
		kind = "SkillVersion"
	case "registerExperiment":
		result, e = s.registerExperiment(tx, project, id, b)
		kind = "Experiment"
	case "recordExperimentResult":
		result, e = s.recordExperimentResult(tx, project, id, b)
		kind = "Experiment"
	case "createGoal":
		result, e = s.createGoal(tx, project, b)
		kind = "Goal"
		status = 201
	case "createTask":
		result, e = s.createTask(tx, project, b)
		kind = "Task"
		status = 201
	case "recordAcceptance":
		if b["subject_ref"].(map[string]any)["entity_type"] == "Task" || b["subject_ref"].(map[string]any)["entity_type"] == "Goal" {
			if preparationError != nil {
				e = preparationError
			} else {
				result, e = s.acceptTask(tx, p, project, b, prepared, cid)
			}
		} else if b["subject_ref"].(map[string]any)["entity_type"] == "SkillVersion" {
			result, e = s.acceptSkill(tx, p, project, b)
		} else if b["subject_ref"].(map[string]any)["entity_type"] == "Qualification" {
			if preparationError != nil {
				e = preparationError
			} else {
				result, e = s.acceptQualification(tx, p, project, b, qualificationProof)
			}
		} else {
			result, e = s.acceptChange(tx, p, project, b)
		}
		kind = "AcceptanceReceipt"
		status = 201
	case "recordQualificationResult":
		if preparationError != nil {
			e = preparationError
		} else {
			result, e = s.recordQualificationResult(tx, p, project, id, b, qualificationProof)
		}
		kind = "Qualification"
	case "actOnGoal":
		result, e = s.actGoal(tx, project, id, b)
		kind = "Goal"
	case "claimTask":
		result, e = s.claimTask(tx, p, project, id, b, cid)
		status = 201
	case "actOnTask":
		result, e = s.actTask(tx, p, project, id, b, cid)
		kind = "Task"
	case "uploadContent":
		if p.Allowed(project, "", "", false) {
			result, e = s.upload(tx, p, project, raw)
		} else {
			result, e = s.runtimeUpload(tx, p, project, raw)
		}
		status = 201
	case "sealArtifact":
		if p.Allowed(project, "", "", false) {
			result, e = s.seal(tx, p, project, b)
		} else {
			result, e = s.runtimeSeal(tx, p, project, b)
		}
		kind = "Artifact"
		status = 201
	case "getArtifactContent":
		s.content(w, r, tx, p, project, id, cid)
		return
	case "getProjectProfile":
		result, e = singleton(tx, project, "ProjectProfile")
	case "getProjectState":
		result, e = singleton(tx, project, "ProjectState")
	case "getProgressProjection":
		result, e = s.workbenchProgress(tx, p, project)
	case "createMilestoneRelease":
		result, e = s.createMilestone(tx, p, project, b, cid)
		status = 201
	case "markNotificationRead":
		result, e = s.readNotification(tx, p, project, id, cid)
	case "getGlobalBudgetPolicy", "getGlobalRunPolicy":
		k := strings.TrimPrefix(op.ID, "getGlobal")
		result, e = singleton(tx, "", k)
	case "getBudgetPolicy", "getRunPolicy":
		profile, err := singleton(tx, project, "ProjectProfile")
		e = err
		if e == nil {
			k := strings.TrimPrefix(op.ID, "get")
			field := "budget_policy_id"
			if k == "RunPolicy" {
				field = "run_policy_id"
			}
			result, e = load(tx, project, k, Str(profile, field))
		}
	case "getGoalBudgetPolicy", "getExperimentBudgetPolicy":
		result, e = s.resourcePolicyTarget(tx, project, id, op.ID, b)
	default:
		if strings.HasPrefix(op.ID, "get") {
			kind = strings.TrimPrefix(op.ID, "get")
			result, e = s.readObject(tx, p, project, kind, id)
		} else if strings.HasPrefix(op.ID, "list") {
			result, e = s.page(tx, p, project, op, r)
		} else if runtimeOperations[op.ID] {
			result, kind, status, e = s.runtimeOperation(tx, p, project, id, b, op.ID, cid)
		} else if resourceOperations[op.ID] {
			result, kind, status, e = s.resourceOperation(tx, p, project, id, b, op.ID)
		} else if researchOperations[op.ID] {
			result, kind, status, e = s.researchOperation(tx, p, project, id, b, op.ID)
		} else if decisionOperations[op.ID] {
			result, kind, status, e = s.decisionOperation(tx, p, project, id, b, op.ID)
		} else if contextOperations[op.ID] {
			result, kind, status, e = s.contextOperation(tx, p, project, id, b, op.ID)
		} else {
			e = Fail(503, "RESOURCE_UNAVAILABLE", "operation unavailable")
		}
	}
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	visibilityKind := kind
	if op.ID == "listRuntimeRegistration" {
		visibilityKind = "RuntimeRegistration"
	}
	if op.ID == "getRuntimeRegistration" {
		visibilityKind = "RuntimeRegistration"
	}
	if !s.visibleAs(tx, p, project, visibilityKind, result) {
		s.writeError(w, cid, Fail(403, "FORBIDDEN", "result references restricted content"))
		return
	}
	responseSchema := op.Response
	if op.ID == "createResearchCycle" && status == http.StatusConflict {
		// A competing trigger was durably coalesced, but no new cycle was
		// created. Commit its pending window and idempotency result together;
		// keep the active cycle's inputs and event history unchanged.
		active := result
		result = Object{"code": "STATE_CONFLICT", "message": "An active research cycle already exists; the pending window was coalesced.",
			"correlation_id": cid, "retryable": false, "current_revision": active["revision"],
			"details": []any{Object{"field": "active_cycle_id", "message": Str(active, "id")},
				Object{"field": "active_window", "message": Str(active, "window_from") + " / " + Str(active, "window_to")}}}
		kind, responseSchema = "", "Error"
	}
	if write && kind != "" && (project != "" || op.ID == "createProject") {
		ep := project
		if op.ID == "createProject" {
			ep = Str(result, "project_id")
		}
		eventType := "PROJECT_UPDATED"
		if op.ID == "applyChangeProposal" {
			eventType = "CHANGE_APPLIED"
		}
		if op.ID == "recordAcceptance" {
			eventType = "ACCEPTANCE_RECORDED"
		}
		if op.ID == "recordDecision" {
			eventType = "DECISION_RECORDED"
		}
		if kind == "ResourceRequest" {
			eventType = "RESOURCE_REQUESTED"
		}
		if kind == "BudgetPolicy" || kind == "RunPolicy" {
			eventType = "POLICY_CHANGED"
		}
		if kind == "Run" {
			eventType = "RUN_CHANGED"
		}
		if kind == "Task" {
			eventType = "TASK_CHANGED"
		}
		if e = s.event(tx, ep, kind, result, p.ID, cid, eventType); e != nil {
			s.writeError(w, cid, e)
			return
		}
	}
	if responseSchema != "" {
		if e = s.Contracts.Validate(responseSchema, result); e != nil {
			s.writeError(w, cid, Fail(500, "INTERNAL_ERROR", "response contract mismatch"))
			return
		}
	}
	if _, ok := result["revision"]; ok {
		tag, e := ETag(result)
		if e != nil {
			s.writeError(w, cid, e)
			return
		}
		headers["ETag"] = tag
	}
	response := Bytes(result)
	if search && !searchSeen {
		if _, e = tx.Exec("INSERT INTO retrieval_dedupe(principal,project,key,request_hash) VALUES(?,?,?,?)", p.ID, project, key, requestHash); e != nil {
			s.writeError(w, cid, e)
			return
		}
	}
	if write {
		if _, e = tx.Exec("INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,?,?,?,?,?,?,?)", p.ID, project, op.ID, key, requestHash, status, response, string(Bytes(headers)), Now()); e != nil {
			s.writeError(w, cid, e)
			return
		}
	}
	if e = tx.Commit(); e != nil {
		s.writeError(w, cid, e)
		return
	}
	for k, v := range headers {
		w.Header().Set(k, v.(string))
	}
	w.WriteHeader(status)
	w.Write(response)
}
func (s *Service) precondition(tx *sql.Tx, project, id string, op Operation, b Object) (Object, error) {
	if op.Target == "BudgetPolicy" || op.Target == "RunPolicy" {
		return s.resourcePolicyTarget(tx, project, id, op.ID, b)
	}
	switch op.Target {
	case "subject_ref":
		r := b["subject_ref"].(map[string]any)
		return load(tx, project, Str(r, "entity_type"), Str(r, "id"))
	case "ProjectState":
		return singleton(tx, project, "ProjectState")
	case "Goal":
		if id == "" {
			id = Str(b, "goal_id")
		}
		return load(tx, project, "Goal", id)
	default:
		return load(tx, project, op.Target, id)
	}
}
func (s *Service) replayAllowed(tx *sql.Tx, p Principal, op Operation, raw []byte) bool {
	o, e := Decode(raw)
	if e != nil {
		return false
	}
	if project := Str(o, "project_id"); project != "" && !p.Allowed(project, "", "", false) && !s.runtimeScope(tx, p, project, Str(o, "id"), op.ID, o) && !(op.ID == "sealArtifact" && s.artifactUseScope(tx, p, project, Str(o, "id"))) {
		return false
	}
	kind := ""
	if op.ID == "qualifyRuntime" {
		kind = "RuntimeRegistration"
	}
	return s.visibleAs(tx, p, Str(o, "project_id"), kind, o)
}

func (s *Service) visible(tx *sql.Tx, p Principal, project string, value any) bool {
	return s.visibleAs(tx, p, project, "", value)
}
func (s *Service) visibleGraph(tx *sql.Tx, p Principal, project string, value any, seen map[string]bool) bool {
	return s.visibleGraphKind(tx, p, project, "", value, seen)
}
func (s *Service) visibleAs(tx *sql.Tx, p Principal, project, ownerKind string, value any) bool {
	return s.visibleGraphKind(tx, p, project, ownerKind, value, map[string]bool{})
}
func (s *Service) visibleGraphKind(tx *sql.Tx, p Principal, project, ownerKind string, value any, seen map[string]bool) bool {
	switch o := value.(type) {
	case map[string]any:
		if project == "" {
			project = Str(o, "project_id")
		}
		if !s.workbenchVisible(tx, p, project, ownerKind, o, seen) {
			return false
		}
		if o["access_class"] == "VERIFIER_ONLY" && (!p.Allowed(project, "", "", true) || !(p.HasRole("OWNER") || p.HasRole("VERIFIER"))) {
			return false
		}
		if o["entity_type"] == "Artifact" {
			var access string
			if e := tx.QueryRow("SELECT json_extract(body,'$.access_class') FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?", project, o["id"]).Scan(&access); e == nil && access == "VERIFIER_ONLY" && (!p.Allowed(project, "", "", true) || !(p.HasRole("OWNER") || p.HasRole("VERIFIER"))) {
				return false
			}
		}
		if kind := Str(o, "entity_type"); kind != "" {
			key := Hash([]any{project, o})
			if !seen[key] {
				seen[key] = true
				obj, e := version(tx, project, o)
				if e == nil && !s.visibleGraphKind(tx, p, project, kind, obj, seen) {
					return false
				}
			}
		}
		for _, v := range o {
			if !s.visibleGraphKind(tx, p, project, ownerKind, v, seen) {
				return false
			}
		}
	case []any:
		for _, v := range o {
			if !s.visibleGraphKind(tx, p, project, ownerKind, v, seen) {
				return false
			}
		}
	}
	return true
}
func (s *Service) readObject(tx *sql.Tx, p Principal, project, kind, id string) (Object, error) {
	if kind == "Artifact" {
		var access string
		e := tx.QueryRow("SELECT json_extract(body,'$.access_class') FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?", project, id).Scan(&access)
		if e != nil || access == "VERIFIER_ONLY" && (!p.Allowed(project, "", "", true) || !(p.HasRole("OWNER") || p.HasRole("VERIFIER"))) {
			return nil, Fail(404, "NOT_FOUND", "artifact unavailable")
		}
	}
	o, e := load(tx, project, kind, id)
	if e == nil && !s.visibleAs(tx, p, project, kind, o) {
		return nil, Fail(404, "NOT_FOUND", "object unavailable")
	}
	return o, e
}
func (s *Service) content(w http.ResponseWriter, r *http.Request, tx *sql.Tx, p Principal, project, id, cid string) {
	o, e := s.readObject(tx, p, project, "Artifact", id)
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	if e = s.requireCurrentArtifactBody(tx, project, o); e != nil {
		s.writeError(w, cid, e)
		return
	}
	if o["access_class"] == "VERIFIER_ONLY" {
		s.protectedContent(w, r, tx, project, id, cid)
		return
	}
	var b []byte
	e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, o["storage_key"]).Scan(&b)
	size, numberErr := Num(o, "byte_size")
	if e != nil || numberErr != nil || Digest(b) != o["content_hash"] || int64(len(b)) != size {
		s.writeError(w, cid, Fail(422, "CONTENT_HASH_MISMATCH", "sealed content verification failed"))
		return
	}
	hash, _ := hex.DecodeString(strings.TrimPrefix(Str(o, "content_hash"), "sha256:"))
	w.Header().Set("Content-Type", Str(o, "media_type"))
	w.Header().Set("Digest", "sha-256="+base64.StdEncoding.EncodeToString(hash))
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Content-Security-Policy", "sandbox; default-src 'none'")
	w.Header().Set("Content-Disposition", "attachment")
	w.Header().Set("Cache-Control", "no-store")
	tag, e := ETag(o)
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	w.Header().Set("ETag", tag)
	w.Write(b)
}
func (s *Service) page(tx *sql.Tx, p Principal, project string, op Operation, r *http.Request) (Object, error) {
	for key, values := range r.URL.Query() {
		if len(values) != 1 || (key != "limit" && key != "cursor" && !(op.ID == "listEvents" && key == "after_sequence")) {
			return nil, Fail(400, "INVALID_REQUEST", "unsupported or repeated query parameter")
		}
	}
	limit := 50
	if q := r.URL.Query().Get("limit"); q != "" {
		v, e := strconv.Atoi(q)
		if e != nil || v < 1 || v > 100 {
			return nil, Fail(400, "INVALID_REQUEST", "limit must be 1..100")
		}
		limit = v
	}
	grantHash := Hash([]any{p.Grants, p.Roles})
	after := int64(0)
	if q := r.URL.Query().Get("after_sequence"); q != "" {
		n, e := strconv.ParseInt(q, 10, 64)
		if e != nil || n < 0 {
			return nil, Fail(400, "INVALID_REQUEST", "invalid event sequence")
		}
		after = n
	}
	operationKey := op.ID + ":" + Hash(Object{"limit": limit, "after_sequence": after})
	var items []any
	var seq int64
	cursor := r.URL.Query().Get("cursor")
	if cursor != "" {
		var raw, expires string
		e := tx.QueryRow("SELECT body,expires_at FROM page_cursors WHERE id=? AND principal=? AND project=? AND operation=? AND grant_hash=?", cursor, p.ID, project, operationKey, grantHash).Scan(&raw, &expires)
		if e != nil {
			return nil, Fail(400, "INVALID_REQUEST", "cursor is not valid for this scope")
		}
		expiry, e := time.Parse(time.RFC3339Nano, expires)
		if e != nil || time.Now().After(expiry) {
			return nil, Fail(410, "CURSOR_EXPIRED", "cursor expired")
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			return nil, e
		}
		items = Arr(o, "items")
		seq, e = Num(o, "snapshot_event_sequence")
		if e != nil {
			return nil, e
		}
	} else {
		kind := strings.TrimPrefix(op.ID, "list")
		if op.ID == "listProjects" {
			kind = "ProjectProfile"
		}
		if op.ID == "listEvents" {
			kind = "EventEnvelope"
		}
		if project != "" {
			state, e := singleton(tx, project, "ProjectState")
			if e != nil {
				return nil, e
			}
			seq, e = Num(state, "event_sequence")
			if e != nil {
				return nil, e
			}
		}
		query := "SELECT body FROM domain_objects WHERE kind=?"
		args := []any{kind}
		if project != "" {
			query += " AND project=?"
			args = append(args, project)
		}
		if kind == "EventEnvelope" {
			query += " AND json_extract(body,'$.sequence')>? ORDER BY json_extract(body,'$.sequence')"
			args = append(args, after)
		} else {
			query += " ORDER BY json_extract(body,'$.created_at'),id"
		}
		rows, e := tx.Query(query, args...)
		if e != nil {
			return nil, e
		}
		items = Empty()
		for rows.Next() {
			var raw string
			if e = rows.Scan(&raw); e != nil {
				rows.Close()
				return nil, e
			}
			o, e := Decode([]byte(raw))
			if e != nil {
				rows.Close()
				return nil, e
			}
			if !p.Allowed(Str(o, "project_id"), "", "", false) {
				continue
			}
			if o["access_class"] == "VERIFIER_ONLY" && (!p.Allowed(Str(o, "project_id"), "", "", true) || !(p.HasRole("OWNER") || p.HasRole("VERIFIER"))) {
				continue
			}
			items = append(items, o)
		}
		e = rows.Err()
		rows.Close()
		if e != nil {
			return nil, e
		}
		// Resolve event/reference permissions after closing rows on the single connection.
		visible := Empty()
		for _, v := range items {
			if s.visibleAs(tx, p, Str(v.(map[string]any), "project_id"), kind, v) {
				visible = append(visible, v)
			}
		}
		items = visible
	}
	var next any
	if len(items) > limit {
		next = ID()
		tail := Object{"items": items[limit:], "snapshot_event_sequence": seq}
		_, e := tx.Exec("INSERT INTO page_cursors(id,principal,project,operation,grant_hash,body,expires_at) VALUES(?,?,?,?,?,?,?)", next, p.ID, project, operationKey, grantHash, string(Bytes(tail)), time.Now().UTC().Add(15*time.Minute).Format(time.RFC3339Nano))
		if e != nil {
			return nil, e
		}
		items = items[:limit]
	}
	// ponytail: snapshots materialize matching rows; indexed snapshot pagination replaces this when projects exceed local scale.
	return Object{"items": items, "next_cursor": next, "snapshot_event_sequence": seq}, nil
}
