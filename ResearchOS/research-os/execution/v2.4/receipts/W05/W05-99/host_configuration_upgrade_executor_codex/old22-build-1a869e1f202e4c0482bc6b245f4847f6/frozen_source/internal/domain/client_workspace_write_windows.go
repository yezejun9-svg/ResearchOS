//go:build windows

package domain

import (
	"context"
	"database/sql"
)

func (c *RuntimeCoordinator) AuthorizeWorkspaceWrite(ctx context.Context, tx *sql.Tx, principal, project, session string, task Object, relativePath string, byteSize int) error {
	var taskID, model string
	if err := tx.QueryRowContext(ctx, "SELECT COALESCE(task_id,''),COALESCE(model_config_ref,'') FROM client_sessions WHERE id=? AND project_id=?", session, project).Scan(&taskID, &model); err != nil {
		return err
	}
	if taskID != Str(task, "id") || task["task_type"] != "mu_turn" {
		return Fail(403, "POLICY_DENIED", "select the existing task authorized for this session")
	}
	runtime, profile, err := c.sessionModel(tx, project, model)
	if err != nil {
		return err
	}
	profileRef, _, err := c.service.currentRuntimeBinding(tx, project, runtime)
	if err != nil {
		return err
	}
	frozen := false
	for _, value := range Arr(task, "input_refs") {
		if Hash(value) == Hash(profileRef) {
			frozen = true
		}
	}
	if !frozen {
		return Fail(403, "POLICY_DENIED", "task has no current frozen write profile; a new task must authorize later changes")
	}
	if err = c.service.effective(tx, project, profileRef); err != nil {
		return err
	}
	policy, _ := profile["tool_policy"].(map[string]any)
	allowed := false
	for _, entry := range Arr(policy, "write_paths") {
		if entry == relativePath {
			allowed = true
		}
	}
	max, err := Num(policy, "max_write_bytes")
	if !allowed || err != nil || max < 1 || int64(byteSize) > max {
		return Fail(403, "POLICY_DENIED", "file is outside the task's current frozen write permission")
	}
	return nil
}

func (c *RuntimeCoordinator) FreezeClientTaskInputs(ctx context.Context, tx *sql.Tx, project, model string) ([]any, error) {
	runtime, _, err := c.sessionModel(tx, project, model)
	if err != nil {
		return nil, err
	}
	ref, _, err := c.service.currentRuntimeBinding(tx, project, runtime)
	if err != nil {
		return nil, err
	}
	if err = c.service.effective(tx, project, ref); err != nil {
		return nil, err
	}
	return []any{ref}, nil
}

var _ ClientWorkspaceWriteAuthority = (*RuntimeCoordinator)(nil)
