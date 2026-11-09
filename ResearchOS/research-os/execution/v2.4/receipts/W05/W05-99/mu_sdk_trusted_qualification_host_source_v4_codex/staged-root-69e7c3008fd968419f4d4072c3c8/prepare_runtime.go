//go:build windows

package main

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"strings"

	"researchos.local/research-os/internal/domain"
)

// prepareRuntime uses production Domain APIs to create an independent,
// unadmitted DRAFT qualification Task before the ordinary CLI goal.start.
func prepareRuntime(ctx context.Context, s seed, digest string) (domain.Object, error) {
	if s.DraftGoalID != "" {
		return nil, errors.New("prepare-runtime seed must precede CLI draft goal")
	}
	if err := verifyEvidenceWorkspace(s); err != nil {
		return nil, err
	}
	e, err := openEnvironment(ctx, s)
	if err != nil {
		return nil, err
	}
	defer e.close()
	if _, err = os.Stat(statePath(s)); err == nil {
		return nil, errors.New("runtime preparation already claimed; inspect private state, no retry")
	} else if !errors.Is(err, os.ErrNotExist) {
		return nil, err
	}
	if err = e.startHTTP(e.handler(nil)); err != nil {
		return nil, err
	}
	if err = verifyCLIProjectBase(ctx, e, s); err != nil {
		return nil, err
	}
	if err = expectBusinessCounts(ctx, e, s, 0, 0, 0, 0, 0); err != nil {
		return nil, err
	}
	var heads int
	if err = e.db.QueryRowContext(ctx, "SELECT count(*) FROM host_model_config_heads WHERE principal=?", e.ownerID).Scan(&heads); err != nil {
		return nil, err
	}
	if heads != 0 {
		return nil, errors.New("existing Owner model head would override isolated runtime route")
	}
	v := state{Schema: schema, SeedSHA256: digest, HostInstanceID: e.host.InstanceID(), OwnerID: e.ownerID, ProjectID: s.ProjectID, Phase: "RUNTIME_PREPARE_CLAIMED"}
	if err = saveState(s, v); err != nil {
		return nil, err
	}
	// Production API writes Requirement/Goal/Runtime/Artifact/Task and the
	// formal qualification plan. It does not admit this DRAFT Task.
	if err = prepareObjects(ctx, e, s, &v); err != nil {
		return nil, err
	}
	if err = expectBusinessCounts(ctx, e, s, 1, 1, 0, 0, 1); err != nil {
		return nil, err
	}
	task, err := e.get(ctx, e.ownerToken, "/tasks/"+v.TaskID)
	if err != nil {
		return nil, err
	}
	if task["status"] != "DRAFT" || task["task_type"] != "runtime_qualification" || task["active_run_id"] != nil {
		return nil, errors.New("qualification Task is not an unadmitted DRAFT")
	}
	profile, err := sealedProfile(ctx, e, v)
	if err != nil {
		return nil, err
	}
	if err = verifyFormalBinding(ctx, e, v, profile); err != nil {
		return nil, err
	}
	model, ok := profile["model_config"].(map[string]any)
	if !ok {
		return nil, errors.New("sealed Mu profile model configuration absent")
	}
	v.ModelRef = domain.Str(model, "ref")
	if v.ModelRef == "" || strings.ContainsAny(v.ModelRef, "<>\r\n") || domain.Str(model, "route") == "" {
		return nil, errors.New("sealed Mu model ref/route is not concrete")
	}
	coordinator, err := makeCoordinator(ctx, e, v, profile)
	if err != nil {
		return nil, err
	}
	coordinator.APIURL = "" // Normal Host inserts its actual loopback listener URL.
	v.PreCoordinator, err = writePrivateCoordinator(e, coordinator)
	if err != nil {
		return nil, err
	}
	v.Phase = "RUNTIME_READY"
	if err = saveState(s, v); err != nil {
		return nil, err
	}
	return domain.Object{"status": "RUNTIME_READY", "project_id": v.ProjectID, "qualification_goal_id": v.QualificationGoalID, "qualification_task_id": v.TaskID, "qualification_task_status": "DRAFT", "runtime_id": v.RuntimeID, "profile_artifact_id": v.ProfileID, "profile_hash": v.ProfileHash, "model_ref": v.ModelRef, "host_instance_id": v.HostInstanceID, "private_coordinator_path": v.PreCoordinator.Path, "private_coordinator_sha256": v.PreCoordinator.SHA256, "private_coordinator_bytes": v.PreCoordinator.Bytes, "qualification_goals": 1, "qualification_tasks": 1, "ordinary_goals": 0, "ordinary_tasks": 0, "runs": 0, "provider_requests": 0}, nil
}

func expectBusinessCounts(ctx context.Context, e *environment, s seed, goals, tasks, runs, sessions, plans int) error {
	for _, item := range []struct {
		kind string
		want int
	}{{"Goal", goals}, {"Task", tasks}, {"Run", runs}} {
		var got int
		if err := e.db.QueryRowContext(ctx, "SELECT count(*) FROM domain_objects WHERE project=? AND kind=?", s.ProjectID, item.kind).Scan(&got); err != nil {
			return err
		}
		if got != item.want {
			return errors.New("isolated project business count differs: " + item.kind)
		}
	}
	var got int
	if err := e.db.QueryRowContext(ctx, "SELECT count(*) FROM client_sessions WHERE project_id=?", s.ProjectID).Scan(&got); err != nil {
		return err
	}
	if got != sessions {
		return errors.New("isolated project session count differs")
	}
	if err := e.db.QueryRowContext(ctx, "SELECT count(*) FROM runtime_qualification_plans WHERE project=?", s.ProjectID).Scan(&got); err != nil {
		return err
	}
	if got != plans {
		return errors.New("isolated project qualification plan count differs")
	}
	return nil
}

func verifyFormalBinding(ctx context.Context, e *environment, v state, profile domain.Object) error {
	artifact, err := e.get(ctx, e.ownerToken, "/artifacts/"+v.ProfileID)
	if err != nil {
		return err
	}
	expected := domain.Ref(artifact, "Artifact")
	var raw, refHash, technicalHash, owner string
	if err = e.db.QueryRowContext(ctx, "SELECT profile_ref,profile_hash,technical_hash,owner FROM runtime_bindings WHERE project=? AND runtime=?", v.ProjectID, v.RuntimeID).Scan(&raw, &refHash, &technicalHash, &owner); err != nil {
		return err
	}
	ref, err := domain.Decode([]byte(raw))
	if err != nil {
		return err
	}
	if owner != e.ownerID || domain.Hash(ref) != domain.Hash(expected) || refHash != domain.Hash(expected) || technicalHash != domain.Str(profile, "technical_hash") {
		return errors.New("formal owner/profile/technical runtime binding differs")
	}
	return nil
}

// finalizePrepare observes an actual, completed CLI goal.start. It writes no
// replacement binding or plan; the independent qualification Task stays DRAFT.
func finalizePrepare(ctx context.Context, s seed, digest, draftGoalID string) (domain.Object, error) {
	if s.DraftGoalID != "" || draftGoalID == "" {
		return nil, errors.New("finalize-prepare needs an actual CLI draft goal ID and pre-draft seed")
	}
	v, err := loadState(s, digest)
	if err != nil {
		return nil, err
	}
	if v.Phase != "RUNTIME_READY" || v.DraftGoalID != "" || v.RunID != "" {
		return nil, errors.New("runtime preparation not ready for one CLI draft")
	}
	if err = verifyEvidenceWorkspace(s); err != nil {
		return nil, err
	}
	e, err := openEnvironment(ctx, s)
	if err != nil {
		return nil, err
	}
	defer e.close()
	if e.host.InstanceID() != v.HostInstanceID || e.ownerID != v.OwnerID {
		return nil, errors.New("trusted Host identity changed")
	}
	if err = e.startHTTP(e.handler(nil)); err != nil {
		return nil, err
	}
	if err = verifyCLIProjectBase(ctx, e, s); err != nil {
		return nil, err
	}
	if err = expectBusinessCounts(ctx, e, s, 2, 1, 0, 1, 1); err != nil {
		return nil, err
	}
	goal, err := e.get(ctx, e.ownerToken, "/goals/"+draftGoalID)
	if err != nil {
		return nil, err
	}
	if goal["project_id"] != s.ProjectID || goal["status"] != "DRAFT" || goal["id"] == v.QualificationGoalID {
		return nil, errors.New("ordinary CLI goal is not an independent DRAFT")
	}
	profile, err := sealedProfile(ctx, e, v)
	if err != nil {
		return nil, err
	}
	if err = verifyFormalBinding(ctx, e, v, profile); err != nil {
		return nil, err
	}
	model, ok := profile["model_config"].(map[string]any)
	if !ok || model["ref"] != v.ModelRef {
		return nil, errors.New("CLI model ref differs from sealed runtime profile")
	}
	if err = verifyPin(v.PreCoordinator); err != nil {
		return nil, err
	}
	if err = verifyCLIGoalCreation(ctx, e, s, v, draftGoalID); err != nil {
		return nil, err
	}
	v.DraftGoalID = draftGoalID
	v.Phase = "PREPARED"
	if err = saveState(s, v); err != nil {
		return nil, err
	}
	return domain.Object{"status": "PREPARED", "project_id": v.ProjectID, "draft_goal_id": v.DraftGoalID, "qualification_goal_id": v.QualificationGoalID, "qualification_task_id": v.TaskID, "runtime_id": v.RuntimeID, "profile_artifact_id": v.ProfileID, "profile_hash": v.ProfileHash, "model_ref": v.ModelRef, "host_instance_id": v.HostInstanceID, "qualification_tasks": 1, "ordinary_goal_tasks": 0, "runs": 0, "provider_requests": 0}, nil
}

func verifyCLIGoalCreation(ctx context.Context, e *environment, s seed, v state, goalID string) error {
	rows, err := e.db.QueryContext(ctx, "SELECT body FROM idempotency WHERE principal=? AND project=? AND operation='v2:goal.start'", e.ownerID, s.ProjectID)
	if err != nil {
		return err
	}
	var matchedSnapshot map[string]any
	matches := 0
	for rows.Next() {
		var body string
		if err = rows.Scan(&body); err != nil {
			rows.Close()
			return err
		}
		var response domain.Object
		if err = json.Unmarshal([]byte(body), &response); err != nil {
			rows.Close()
			return err
		}
		result, _ := response["result"].(map[string]any)
		if result["goal_id"] != goalID {
			continue
		}
		snapshot, _ := result["snapshot"].(map[string]any)
		if response["status"] != "COMPLETED" || response["method"] != "goal.start" || response["session_id"] != nil || snapshot["workspace_ref"] != s.WorkspaceRef || snapshot["model_config_ref"] != v.ModelRef {
			rows.Close()
			return errors.New("CLI goal.start identity or workspace/model snapshot differs")
		}
		matchedSnapshot = snapshot
		matches++
	}
	iterationErr := rows.Err()
	closeErr := rows.Close()
	if iterationErr != nil {
		return iterationErr
	}
	if closeErr != nil {
		return closeErr
	}
	if matches != 1 {
		return errors.New("expected one actual completed CLI goal.start")
	}
	sid := domain.Str(matchedSnapshot, "session_id")
	if sid == "" {
		return errors.New("CLI draft did not create a session")
	}
	// SQLite's production pool has one connection. No query runs until the
	// idempotency cursor releases that connection, including every error path.
	var workspace, model, storedGoal, task, run string
	if err = e.db.QueryRowContext(ctx, "SELECT workspace_ref,model_config_ref,coalesce(goal_id,''),coalesce(task_id,''),coalesce(run_id,'') FROM client_sessions WHERE project_id=? AND id=?", s.ProjectID, sid).Scan(&workspace, &model, &storedGoal, &task, &run); err != nil {
		return err
	}
	if workspace != s.WorkspaceRef || model != v.ModelRef || storedGoal != goalID || task != "" || run != "" {
		return errors.New("CLI draft session has wrong Goal/workspace/model or started Task/Run")
	}
	var ordinaryTasks int
	if err = e.db.QueryRowContext(ctx, "SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task' AND json_extract(body,'$.goal_id')=?", s.ProjectID, goalID).Scan(&ordinaryTasks); err != nil {
		return err
	}
	if ordinaryTasks != 0 {
		return errors.New("ordinary CLI draft unexpectedly has a Task")
	}
	return nil
}
