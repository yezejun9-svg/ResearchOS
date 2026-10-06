package domain

import "database/sql"

const ResourceRecoverySchema = "researchos.resource-recovery.v1"
const ResourceRecoveryMediaType = "application/vnd.researchos.resource-recovery+json"

// Recovery is an explicit, sealed instruction carried by the existing
// ResolveResourceRequest evidence. It neither grants a runtime permission nor
// certifies a qualification. The same current-purpose and side-effect gates
// used by the coordinator are applied again in the resolution transaction.
func (s *Service) applyResourceRecovery(tx *sql.Tx, p Principal, project string, request Object, refs []any) error {
	var action Object
	for _, raw := range refs {
		ref, ok := raw.(map[string]any)
		if !ok || ref["entity_type"] != "Artifact" {
			continue
		}
		artifact, e := version(tx, project, ref)
		if e != nil {
			return e
		}
		if artifact["media_type"] != ResourceRecoveryMediaType {
			continue
		}
		value, e := s.artifactJSON(tx, project, ref)
		if e != nil {
			return e
		}
		body, ok := value.(map[string]any)
		if !ok || body["schema"] != ResourceRecoverySchema {
			return Fail(400, "INVALID_REQUEST", "invalid resource recovery instruction")
		}
		if action != nil {
			return Fail(422, "GATE_FAILED", "exactly one resource recovery instruction is allowed")
		}
		if artifact["produced_by"] != p.ID || !p.HasRole("OWNER") {
			return Fail(403, "FORBIDDEN", "resource recovery requires the owner's own sealed instruction")
		}
		action = body
	}
	if action == nil {
		return nil // Existing evidence-only resolutions preserve their contract.
	}
	if len(action) != 4 || action["action"] != "SWITCH_RUNTIME" || Hash(action["resource_request_ref"]) != Hash(Ref(request, "ResourceRequest")) {
		return Fail(412, "STALE_INPUT", "resource recovery must bind the current request")
	}
	if e := resourceWriteLock(tx); e != nil {
		return e
	}
	items := Arr(action, "replacements")
	if len(items) == 0 || len(items) != len(Arr(request, "blocked_task_ids")) {
		return Fail(422, "GATE_FAILED", "recovery must cover every blocked task exactly once")
	}
	blocked := map[string]bool{}
	for _, taskID := range Arr(request, "blocked_task_ids") {
		blocked[taskID.(string)] = true
	}
	for _, raw := range items {
		item, ok := raw.(map[string]any)
		if !ok || len(item) != 3 {
			return Fail(400, "INVALID_REQUEST", "recovery requires task, run and runtime references")
		}
		objects := map[string]Object{}
		for field, kind := range map[string]string{"task_ref": "Task", "run_ref": "Run", "runtime_ref": "RuntimeRegistration"} {
			ref, ok := item[field].(map[string]any)
			if !ok || ref["entity_type"] != kind {
				return Fail(400, "INVALID_REQUEST", "invalid recovery reference")
			}
			if e := s.Contracts.Validate("VersionRef", ref); e != nil {
				return Fail(400, "INVALID_REQUEST", "invalid recovery reference shape")
			}
			if e := s.effective(tx, project, ref); e != nil {
				return e
			}
			o, e := s.readObject(tx, p, project, kind, Str(ref, "id"))
			if e != nil {
				return e
			}
			if Hash(Ref(o, kind)) != Hash(ref) {
				return Fail(412, "STALE_INPUT", "recovery input changed")
			}
			objects[field] = o
		}
		task, run, replacement := objects["task_ref"], objects["run_ref"], objects["runtime_ref"]
		if !blocked[Str(task, "id")] || task["active_run_id"] != run["id"] || run["task_id"] != task["id"] {
			return Fail(422, "GATE_FAILED", "recovery task/run does not match the blocked request")
		}
		delete(blocked, Str(task, "id"))
		current, e := load(tx, project, "RuntimeRegistration", Str(run, "runtime_id"))
		if e != nil {
			return e
		}
		if _, e = s.qualifiedReplacement(tx, project, task, current, replacement); e != nil {
			return e
		}
		// All writes remain in this transaction. A failure on a later task rolls
		// back the earlier switches and leaves the original request open.
		result, e := s.switchResource(tx, p, project, Str(run, "id"), Str(replacement, "id"), nil)
		if e != nil {
			return e
		}
		if result["status"] != "SWITCHED" {
			return Fail(422, "GATE_FAILED", "resource recovery could not be scheduled")
		}
	}
	return nil
}
