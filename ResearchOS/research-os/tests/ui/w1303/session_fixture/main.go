// W13-03-only typed Session projection fixture. It writes only an isolated
// researchos-w13-ui-* SQLite and never mints a credential or claims LIVE work.
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

const sessionCount = 102

type output struct {
	MainSessionID string   `json:"main_session_id"`
	SessionIDs    []string `json:"session_ids"`
	WorkspaceRef  string   `json:"workspace_ref"`
	SessionCount  int      `json:"session_count"`
	EventCount    int      `json:"main_event_count"`
	Provenance    []string `json:"provenance"`
}

func main() {
	var dataDir, projectID, ownerID, artifactID string
	flag.StringVar(&dataDir, "data-dir", "", "temporary W13 data directory")
	flag.StringVar(&projectID, "project-id", "", "existing temporary project ID")
	flag.StringVar(&ownerID, "owner-id", "", "existing Owner principal ID")
	flag.StringVar(&artifactID, "artifact-id", "", "existing sealed Artifact ID")
	flag.Parse()
	if err := validateInputs(dataDir, projectID, ownerID, artifactID); err != nil {
		fail(err)
	}
	result, err := seed(dataDir, projectID, ownerID, artifactID)
	if err != nil {
		fail(err)
	}
	if err := json.NewEncoder(os.Stdout).Encode(result); err != nil {
		fail(err)
	}
}

func fail(err error) {
	// Database and schema errors must not emit credential-bearing object bodies.
	fmt.Fprintln(os.Stderr, "W13 session fixture failed:", err)
	os.Exit(1)
}

func validateInputs(dataDir, projectID, ownerID, artifactID string) error {
	if os.Getenv("RESEARCHOS_TASK_ID") != "W13" {
		return errors.New("RESEARCHOS_TASK_ID=W13 required")
	}
	if dataDir == "" || projectID == "" || ownerID == "" || artifactID == "" {
		return errors.New("--data-dir, --project-id, --owner-id and --artifact-id required")
	}
	abs, err := filepath.Abs(dataDir)
	if err != nil {
		return err
	}
	if filepath.Base(abs) != "data" || !strings.HasPrefix(filepath.Base(filepath.Dir(abs)), "researchos-w13-ui-") {
		return errors.New("only a researchos-w13-ui-*/data fixture is allowed")
	}
	if _, err := os.Stat(filepath.Join(abs, "researchos.sqlite")); err != nil {
		return errors.New("temporary fixture SQLite is absent")
	}
	return nil
}

func seed(dataDir, projectID, ownerID, artifactID string) (*output, error) {
	ctx := context.Background()
	absolute, _ := filepath.Abs(dataDir)
	db, err := store.Open(filepath.Join(absolute, "researchos.sqlite"))
	if err != nil {
		return nil, err
	}
	defer db.Close()
	doc, err := api.ClientProtocolDocument()
	if err != nil {
		return nil, err
	}
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	// Older temporary W13 databases may predate the additive typed index. The
	// committed migration is idempotent and stays inside this fixture transaction.
	sessionSchema, err := os.ReadFile(filepath.Join("migrations", "sqlite", "next_v24_sessions.sql"))
	if err != nil {
		return nil, err
	}
	if _, err = tx.ExecContext(ctx, string(sessionSchema)); err != nil {
		return nil, err
	}
	if err = domain.EnsureClientSessionFence(ctx, tx); err != nil {
		return nil, err
	}
	var principalRoles string
	if err = tx.QueryRowContext(ctx, "SELECT roles FROM auth_principals WHERE id=? AND revoked=0", ownerID).Scan(&principalRoles); err != nil {
		return nil, errors.New("existing active Owner was not found")
	}
	var roles []string
	if err = json.Unmarshal([]byte(principalRoles), &roles); err != nil {
		return nil, err
	}
	hasOwner := false
	for _, role := range roles {
		hasOwner = hasOwner || role == "OWNER"
	}
	if !hasOwner {
		return nil, errors.New("principal is not an Owner")
	}
	var projectCount int
	if err = tx.QueryRowContext(ctx, "SELECT count(*) FROM domain_objects WHERE kind='ProjectProfile' AND id=?", projectID).Scan(&projectCount); err != nil || projectCount != 1 {
		return nil, errors.New("existing project profile was not found")
	}
	var artifactBody string
	if err = tx.QueryRowContext(ctx, "SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?", projectID, artifactID).Scan(&artifactBody); err != nil {
		return nil, errors.New("existing sealed Artifact was not found")
	}
	var artifact domain.Object
	if err = json.Unmarshal([]byte(artifactBody), &artifact); err != nil {
		return nil, err
	}
	if artifact["validity"] != "CURRENT" || artifact["content_hash"] == nil {
		return nil, errors.New("Artifact is not current sealed content")
	}
	ref := domain.Ref(artifact, "Artifact")
	batch := domain.ID()
	workspaceRef := "w1303-fixture-workspace-" + batch
	clientID := "w1303-fixture-writer-" + batch
	binding := domain.WorkspaceBinding{AuthorizedRef: workspaceRef,
		DisplayName: "W13-03 FIXTURE workspace", DisplayPath: "W13-03 temporary fixture data",
		RealPath: absolute, Access: "READ_ONLY", ProjectID: &projectID, Revision: 1,
		Status: domain.WorkspaceActive, PrincipalID: ownerID, ClientID: clientID,
		HostPrincipalRef: "w13-local-fixture", CreatedAt: domain.Now()}
	if err = doc.ValidateDef("WorkspaceBinding", binding.Reply()); err != nil {
		return nil, err
	}
	if _, err = tx.ExecContext(ctx, `INSERT INTO domain_objects(project,kind,id,revision,body,immutable)
		VALUES('',?,?,1,?,0)`, domain.KindWorkspaceBinding, workspaceRef, string(domain.Bytes(binding))); err != nil {
		return nil, err
	}
	now := time.Now().UTC()
	expired := now.Add(-time.Minute) // the real Desktop may explicitly request writer takeover.
	buildID := "w1303-fixture-core"
	modelRef := "w1303-fixture-model-no-provider"
	ids := make([]string, 0, sessionCount)
	for i := 0; i < sessionCount; i++ {
		id := fmt.Sprintf("w1303-%s-%03d", batch, i)
		title := fmt.Sprintf("FIXTURE 会话 %03d", i+1)
		if i == 0 {
			title = "FIXTURE · 消息与工具回执"
		}
		created := now.Add(time.Duration(i) * time.Microsecond)
		if err = domain.MapClientSession(ctx, tx, domain.ClientSession{
			ID: id, ProjectID: projectID, Revision: 1, WriterEpoch: 1,
			WriterClientID: clientID, LeaseExpiresAt: &expired,
			CreatedAt: created, UpdatedAt: created, UpstreamSession: "w1303-upstream-" + id,
			WorkspaceRef: &workspaceRef, ModelConfigRef: &modelRef, Title: &title,
			CoreBuildID: &buildID, Protocol: domain.ProtocolV2,
		}); err != nil {
			return nil, err
		}
		ids = append(ids, id)
	}
	mainID := ids[0]
	sequence, revision := int64(0), int64(1)
	appendEvent := func(kind string, payload domain.Object) error {
		sequence++
		eventID := domain.ID()
		protocol := domain.ProtocolV2
		event := &domain.SessionEvent{EventID: &eventID, SessionID: &mainID,
			Sequence: &sequence, CoreBuildID: &buildID, ProtocolVersion: &protocol,
			Kind: &kind, Payload: domain.Bytes(payload)}
		if err := domain.AppendSessionEvent(ctx, tx, doc, projectID, event, 1, revision); err != nil {
			return err
		}
		revision++
		return nil
	}
	message := func(role, body string) error {
		messageID := domain.ID()
		for _, part := range []domain.Object{
			{"message_id": messageID, "role": role, "phase": "START", "part_index": 0, "content_offset_utf8_bytes": 0, "text": ""},
			{"message_id": messageID, "role": role, "phase": "DELTA", "part_index": 0, "content_offset_utf8_bytes": 0, "text": body},
			{"message_id": messageID, "role": role, "phase": "END", "part_index": 0, "content_offset_utf8_bytes": len([]byte(body)), "text": ""},
		} {
			if err := appendEvent("MESSAGE", part); err != nil {
				return err
			}
		}
		return nil
	}
	if err = message("USER", "FIXTURE：请检查已封存的本地研究结果。此消息未调用模型。"); err != nil {
		return nil, err
	}
	toolCall := domain.ID()
	if err = appendEvent("TOOL_STARTED", domain.Object{"tool_call_id": toolCall, "parent_tool_call_id": nil,
		"tool_name": "fixture.inspect-sealed-artifact", "input_summary": "FIXTURE：仅显示现有封存产物引用；未运行工具", "input_artifact_ref": nil}); err != nil {
		return nil, err
	}
	if err = appendEvent("TOOL_RESULT", domain.Object{"tool_call_id": toolCall, "outcome": "UNKNOWN",
		"summary": "FIXTURE：没有真实工具执行；产物引用来自现有 API 封存记录", "stdout_artifact_ref": ref,
		"stderr_artifact_ref": nil, "result_artifact_refs": []any{ref}}); err != nil {
		return nil, err
	}
	if err = message("ASSISTANT", "FIXTURE 展示文本：本页只验证持久化消息和事件渲染；没有模型回复或权限决定。"); err != nil {
		return nil, err
	}
	snapshot, err := domain.BuildSessionSnapshot(ctx, tx, doc, projectID, mainID)
	if err != nil {
		return nil, err
	}
	if len(snapshot["messages"].([]any)) != 2 || snapshot["event_sequence"] != sequence {
		return nil, errors.New("typed snapshot did not recover fixture messages and watermark")
	}
	page, err := domain.ReadSessionEvents(ctx, tx, projectID, mainID, 0, 20)
	if err != nil || len(page.Events) != int(sequence) {
		return nil, errors.New("typed event page did not recover all fixture events")
	}
	if err = verifyTypedReads(ctx, tx, doc, ownerID, projectID, mainID); err != nil {
		return nil, err
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	return &output{MainSessionID: mainID, SessionIDs: ids, WorkspaceRef: workspaceRef,
		SessionCount: len(ids), EventCount: int(sequence),
		Provenance: []string{
			"W13-only local SQLite fixture; no credential was minted or read",
			"102 sessions persisted with domain.MapClientSession; pagination remains a real v2 service query",
			"messages and tool records persisted with schema-validated domain.AppendSessionEvent",
			"workspace binding is an explicit temporary fixture, not an OS directory selection",
			"tool outcome UNKNOWN: no tool or model actually ran",
			"permission.respond is NOT_IMPLEMENTED; no approval or permission grant was seeded",
		}}, nil
}

func verifyTypedReads(ctx context.Context, tx *sql.Tx, doc *domain.SchemaDoc, ownerID, projectID, mainID string) error {
	// Exercise the same typed command dispatch as /v2/command. Read command
	// idempotency rows are rolled back; only the fixture records are committed.
	if _, err := tx.ExecContext(ctx, "SAVEPOINT w1303_verify"); err != nil {
		return err
	}
	defer func() {
		tx.ExecContext(ctx, "ROLLBACK TO w1303_verify")
		tx.ExecContext(ctx, "RELEASE w1303_verify")
	}()
	svc := domain.ClientService{Doc: doc}
	call := func(method string, session *string, payload domain.Object) (map[string]any, error) {
		envelope := domain.Object{"protocol_version": domain.ProtocolV2, "command_id": domain.ID(),
			"client_id": "w1303-fixture-check", "project_id": projectID, "session_id": session,
			"expected_revision": nil, "writer_epoch": nil, "method": method, "payload": payload}
		env, err := domain.DecodeEnvelope(domain.Bytes(envelope))
		if err != nil {
			return nil, err
		}
		response, _, err := svc.Execute(ctx, tx, env, ownerID)
		if err != nil {
			return nil, err
		}
		if response.Status == nil || *response.Status != "COMPLETED" {
			return nil, fmt.Errorf("typed %s did not complete", method)
		}
		return response.Result, nil
	}
	first, err := call("session.list", nil, domain.Object{"cursor": nil, "limit": 100})
	if err != nil {
		return err
	}
	items, ok := first["items"].([]any)
	if !ok || len(items) != 100 || first["next_cursor"] == nil {
		return errors.New("typed session.list first page was not a bounded 100-row page")
	}
	second, err := call("session.list", nil, domain.Object{"cursor": first["next_cursor"], "limit": 100})
	if err != nil {
		return err
	}
	remaining, ok := second["items"].([]any)
	if !ok || len(remaining) < 2 {
		return errors.New("typed session.list continuation did not return remaining sessions")
	}
	snapshot, err := call("session.get", &mainID, domain.Object{})
	if err != nil {
		return err
	}
	messages, ok := snapshot["messages"].([]any)
	if !ok || len(messages) != 2 {
		return errors.New("typed session.get did not recover two fixture messages")
	}
	events, err := call("session.events", &mainID, domain.Object{"after_sequence": 0, "limit": 20})
	if err != nil {
		return err
	}
	page, ok := events["events"].([]any)
	if !ok || len(page) != 8 {
		return errors.New("typed session.events did not recover eight fixture events")
	}
	return nil
}
