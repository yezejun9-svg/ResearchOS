package domain

import (
	"context"
	"database/sql"
	"encoding/json"
)

// The wire receipt and the original domain operation commit together. Public
// Go callers retain their original transaction-owning wrappers.
func (s *ClientService) clientFirstUse(ctx context.Context, tx *sql.Tx, env *Envelope, principal string) (*Response, error) {
	if s.Domain == nil || s.Doc == nil || s.WorkspaceAuthority == nil {
		return NewTypedRejection(env, "HOST_UNAVAILABLE", "trusted local workspace authority unavailable"), nil
	}
	if env.ProjectID != nil || env.SessionID != nil || env.WriterEpoch != nil || env.ExpectedRevision != nil {
		return NewTypedRejection(env, "INVALID_REQUEST", "first-use command must not claim a project, session or writer revision"), nil
	}
	p, err := clientAuthenticatedPrincipal(ctx, tx, principal)
	if err != nil {
		return clientFault(env, err)
	}
	if !p.HasRole("OWNER") || !p.CanCreateProject || p.DeviceID != "" {
		return NewTypedRejection(env, "FORBIDDEN", "local project creation authority required"), nil
	}
	var result Object
	if _, err = tx.ExecContext(ctx, "SAVEPOINT client_first_use"); err != nil {
		return nil, err
	}
	switch *env.Method {
	case "workspace.register":
		var input struct {
			Selection   string `json:"selection_ref"`
			DisplayName string `json:"display_name"`
			Access      string `json:"requested_access"`
		}
		if err = json.Unmarshal(env.Payload, &input); err != nil {
			return nil, err
		}
		result, err = s.Domain.registerWorkspaceTx(ctx, tx, p, s.WorkspaceAuthority, s.Doc, RegisterWorkspaceInput{SelectionRef: input.Selection, DisplayName: input.DisplayName, RequestedAccess: input.Access, ClientID: deref(env.ClientID), CommandID: deref(env.CommandID)})
	case "project.bootstrap":
		if s.InventoryScanner == nil {
			return NewTypedRejection(env, "HOST_UNAVAILABLE", "local inventory scanner unavailable"), nil
		}
		var input struct {
			Workspace   string `json:"authorized_workspace_ref"`
			DisplayName string `json:"display_name"`
		}
		if err = json.Unmarshal(env.Payload, &input); err != nil {
			return nil, err
		}
		result, err = s.Domain.bootstrapProjectTx(ctx, tx, p, s.WorkspaceAuthority, s.Doc, s.InventoryScanner, BootstrapProjectInput{AuthorizedWorkspaceRef: input.Workspace, DisplayName: input.DisplayName, ClientID: deref(env.ClientID), CommandID: deref(env.CommandID), MeasurementMode: "LIVE"})
	}
	if err != nil {
		if _, rollbackErr := tx.ExecContext(ctx, "ROLLBACK TO client_first_use"); rollbackErr != nil {
			return nil, rollbackErr
		}
		if _, releaseErr := tx.ExecContext(ctx, "RELEASE client_first_use"); releaseErr != nil {
			return nil, releaseErr
		}
		return clientFault(env, err)
	}
	if _, err = tx.ExecContext(ctx, "RELEASE client_first_use"); err != nil {
		return nil, err
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), Revision: revPtr(1), Result: result}, nil
}
