//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"testing"
)

func projectionBinding(ref, principal string, project *string, revision int64) *WorkspaceBinding {
	return &WorkspaceBinding{AuthorizedRef: ref, DisplayName: ref, DisplayPath: "visible/" + ref,
		RealPath: "private/" + ref, Access: "READ_ONLY", ProjectID: project, Revision: revision,
		Status: WorkspaceActive, PrincipalID: principal, HostPrincipalRef: "private-host",
		ClientID: "private-client", SelectionRef: "private-selection", CommandID: "private-command", CreatedAt: Now()}
}

func TestWorkspaceProjectionCurrentTransactionAndPrincipal(t *testing.T) {
	ctx := context.Background()
	f := contextFixture(t)
	doc := clientHistoryDoc(t)
	svc := &ClientService{Doc: doc, Host: ClientHostInfo{WorkspaceBind: []any{Object{"real_path": "hostile-static"}}}}
	foreign := "projection-foreign"
	if err := f.s.ProvisionPrincipal(ctx, Principal{ID: foreign, Roles: []string{"OWNER"}, Grants: []Grant{{ProjectID: f.project}}}); err != nil {
		t.Fatal(err)
	}
	reader := "projection-reader"
	if err := f.s.ProvisionPrincipal(ctx, Principal{ID: reader, Roles: []string{"PLANNER"}}); err != nil {
		t.Fatal(err)
	}
	device := "projection-device"
	if err := f.s.ProvisionPrincipal(ctx, Principal{ID: device, Roles: []string{"OWNER"}, Grants: []Grant{{ProjectID: f.project}}}); err != nil {
		t.Fatal(err)
	}
	tx, err := f.db.BeginTx(ctx, nil)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	own := projectionBinding("own", f.owner, nil, 1)
	other := projectionBinding("foreign", foreign, &f.project, 1)
	readonly := projectionBinding("readonly", reader, nil, 1)
	remote := projectionBinding("remote", device, &f.project, 1)
	for _, b := range []*WorkspaceBinding{own, other, readonly, remote} {
		if err := f.s.putOpaque(ctx, tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record()); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := tx.ExecContext(ctx, "INSERT INTO remote_devices(id,owner,body) VALUES(?,?,?)", device, f.owner, string(Bytes(Object{"status": "ACTIVE", "role": "OWNER"}))); err != nil {
		t.Fatal(err)
	}
	env := &Envelope{ProjectID: nil}
	readOnlyItems, err := svc.clientWorkspaceProjection(ctx, tx, env, reader)
	if err != nil || len(readOnlyItems) != 1 || readOnlyItems[0].(Object)["access"] != "READ_ONLY" {
		t.Fatalf("local metadata required project creation/write authority: %v %v", readOnlyItems, err)
	}
	if _, err := svc.clientWorkspaceProjection(ctx, tx, env, device); err == nil {
		t.Fatal("remote principal obtained local paths")
	}
	items, err := svc.clientWorkspaceProjection(ctx, tx, env, f.owner)
	if err != nil || len(items) != 1 || items[0].(Object)["revision"] != int64(1) {
		t.Fatalf("uncommitted own registration invisible: %v %v", items, err)
	}
	bound := own.bindProject(f.project)
	if err := f.s.putOpaque(ctx, tx, "", KindWorkspaceBinding, own.AuthorizedRef, bound); err != nil {
		t.Fatal(err)
	}
	items, err = svc.clientWorkspaceProjection(ctx, tx, env, f.owner)
	if err != nil || len(items) != 1 {
		t.Fatalf("same-tx bootstrap invisible: %v %v", items, err)
	}
	reply := items[0].(Object)
	if len(reply) != 7 || reply["revision"] != int64(2) || reply["project_id"] != f.project || reply["real_path"] != nil {
		t.Fatalf("projection shape/revision: %v", reply)
	}
	if err := doc.ValidateDef("WorkspaceBinding", reply); err != nil {
		t.Fatal(err)
	}
	projectEnv := &Envelope{ProjectID: &f.project}
	method := "workspace.list"
	for _, claim := range []*Envelope{
		{Method: &method, Payload: Bytes(Object{}), SessionID: strptr("foreign-session")},
		{Method: &method, Payload: Bytes(Object{}), ExpectedRevision: revPtr(1)},
		{Method: &method, Payload: Bytes(Object{}), WriterEpoch: revPtr(1)},
	} {
		response, err := svc.dispatch(ctx, tx, claim, f.owner)
		if err != nil || deref(response.ErrorCode) != "INVALID_REQUEST" {
			t.Fatalf("direct command accepted host-level claim: %v %v", response, err)
		}
	}
	items, err = svc.clientWorkspaceProjection(ctx, tx, projectEnv, f.owner)
	if err != nil || len(items) != 1 {
		t.Fatalf("legal project filter: %v %v", items, err)
	}
	if _, err := tx.ExecContext(ctx, "DELETE FROM auth_grants WHERE principal=?", f.owner); err != nil {
		t.Fatal(err)
	}
	if _, err := tx.ExecContext(ctx, "INSERT INTO auth_grants(principal,project,task,run,restricted) VALUES(?,?,?,?,0)", f.owner, f.project, "task-only", ""); err != nil {
		t.Fatal(err)
	}
	unbound := projectionBinding("unbound", f.owner, nil, 1)
	if err := f.s.putOpaque(ctx, tx, "", KindWorkspaceBinding, unbound.AuthorizedRef, unbound.record()); err != nil {
		t.Fatal(err)
	}
	items, err = svc.clientWorkspaceProjection(ctx, tx, env, f.owner)
	if err != nil || len(items) != 1 || items[0].(Object)["authorized_workspace_ref"] != "unbound" {
		t.Fatalf("removed project grant still exposed path: %v %v", items, err)
	}
	if _, err := svc.clientWorkspaceProjection(ctx, tx, projectEnv, f.owner); err == nil {
		t.Fatal("foreign project context accepted")
	}
	if err := tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	var count int
	if err := f.db.QueryRowContext(ctx, "SELECT count(*) FROM domain_objects WHERE kind=?", KindWorkspaceBinding).Scan(&count); err != nil || count != 0 {
		t.Fatalf("projection mutated durable bindings: count=%d err=%v", count, err)
	}
}

func TestWorkspaceProjectionRevocationMalformedAndLimit(t *testing.T) {
	ctx := context.Background()
	f := contextFixture(t)
	svc := &ClientService{Doc: clientHistoryDoc(t)}
	bind := projectionBinding("revoked", f.owner, nil, 1)
	bind.Status = WorkspaceRevoked
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		return f.s.putOpaque(ctx, tx, "", KindWorkspaceBinding, bind.AuthorizedRef, bind.record())
	})
	tx, err := f.db.BeginTx(ctx, nil)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	items, err := svc.clientWorkspaceProjection(ctx, tx, &Envelope{}, f.owner)
	if err != nil || len(items) != 1 || items[0].(Object)["status"] != WorkspaceRevoked {
		t.Fatalf("revoked history hidden: %v %v", items, err)
	}
	// A foreign malformed body cannot make this principal's projection fail.
	if _, err := tx.ExecContext(ctx, `INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, "foreign-invalid", `{"principal_id":"projection-foreign","revision":"bad"}`); err != nil {
		t.Fatal(err)
	}
	items, err = svc.clientWorkspaceProjection(ctx, tx, &Envelope{}, f.owner)
	if err != nil || len(items) != 1 {
		t.Fatalf("foreign corruption leaked: %v %v", items, err)
	}
	if _, err := tx.ExecContext(ctx, `UPDATE domain_objects SET body=json_set(body,'$.project_id',99) WHERE id='revoked'`); err != nil {
		t.Fatal(err)
	}
	if _, err := svc.clientWorkspaceProjection(ctx, tx, &Envelope{}, f.owner); err == nil {
		t.Fatal("malformed own project silently skipped")
	}
	if err := tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	// The 1001st eligible row is an explicit typed boundary, while foreign
	// rows do not consume the limit.
	tx, err = f.db.BeginTx(ctx, nil)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	if _, err := tx.ExecContext(ctx, "DELETE FROM domain_objects WHERE kind=? AND id='revoked'", KindWorkspaceBinding); err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 1000; i++ {
		b := projectionBinding(fmt.Sprintf("limit-%04d", i), f.owner, nil, 1)
		if err := f.s.putOpaque(ctx, tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record()); err != nil {
			t.Fatal(err)
		}
	}
	items, err = svc.clientWorkspaceProjection(ctx, tx, &Envelope{}, f.owner)
	if err != nil || len(items) != 1000 {
		t.Fatalf("exact published limit: %d %v", len(items), err)
	}
	extra := projectionBinding("limit-1000", f.owner, nil, 1)
	if err := f.s.putOpaque(ctx, tx, "", KindWorkspaceBinding, extra.AuthorizedRef, extra.record()); err != nil {
		t.Fatal(err)
	}
	items, err = svc.clientWorkspaceProjection(ctx, tx, &Envelope{}, f.owner)
	if items != nil || err == nil {
		t.Fatalf("1001 returned partial success: %d %v", len(items), err)
	}
	if fault, ok := err.(*Fault); !ok || fault.Code != "RESOURCE_BLOCKED" {
		t.Fatalf("overflow is not typed: %v", err)
	}
}
