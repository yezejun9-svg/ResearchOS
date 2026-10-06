//go:build windows

package domain

import (
	"context"
	"database/sql"
	"errors"
	"testing"
	"time"
)

// Native filesystem behavior is tested in internal/host. This port lets the
// domain tests witness whether unauthorized requests ever reach native I/O.
type clientWorkspacePort struct {
	calls        int
	root, access string
	raw          []byte
	err          error
}

func (p *clientWorkspacePort) hit(root, access string) error {
	p.calls++
	p.root, p.access = root, access
	return p.err
}
func (p *clientWorkspacePort) WorkspaceTree(_ context.Context, root, access string, b Object) (Object, error) {
	err := p.hit(root, access)
	return Object{"workspace_ref": b["workspace_ref"], "root_revision": 1, "entries": Empty(), "next_cursor": nil}, err
}
func (p *clientWorkspacePort) WorkspaceRead(_ context.Context, root, access string, b Object) (Object, error) {
	err := p.hit(root, access)
	return Object{"workspace_ref": b["workspace_ref"], "relative_path": b["relative_path"], "content_hash": Digest(p.raw), "byte_size": len(p.raw), "encoding": "UTF-8", "text": string(p.raw), "modified_at": Now(), "editable": access == "READ_WRITE"}, err
}
func (p *clientWorkspacePort) WorkspaceDiff(_ context.Context, root, access string, b Object) (Object, []byte, error) {
	err := p.hit(root, access)
	return Object{"workspace_ref": b["workspace_ref"], "base": b["base"], "base_revision": "fixture-git-revision", "files": Empty(), "total_files": 501, "truncated": true, "full_diff_artifact_ref": nil}, p.raw, err
}
func (p *clientWorkspacePort) WorkspaceContent(_ context.Context, root, access, _ string, max int64) ([]byte, error) {
	if max != 64<<20 {
		return nil, errors.New("incorrect import size bound")
	}
	return p.raw, p.hit(root, access)
}

type clientWorkspaceAuthority struct{ err error }

func (a clientWorkspaceAuthority) ConsumeSelection(context.Context, string, string, string) (WorkspaceSelection, error) {
	return WorkspaceSelection{}, errors.New("not a selection request")
}
func (a clientWorkspaceAuthority) ConfirmPath(context.Context, string, string) error { return a.err }

func clientWorkspaceFixture(t *testing.T) (*fixture, *ClientService, *clientWorkspacePort, *WorkspaceBinding, string) {
	t.Helper()
	return clientWorkspaceFixtureFor(t, contextFixture(t))
}
func clientWorkspaceFixtureFor(t *testing.T, f *fixture) (*fixture, *ClientService, *clientWorkspacePort, *WorkspaceBinding, string) {
	t.Helper()
	b := &WorkspaceBinding{AuthorizedRef: "workspace-test", DisplayName: "fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 2, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: "workspace-client", HostPrincipalRef: "fixture", CreatedAt: Now()}
	port := &clientWorkspacePort{raw: []byte("精确字节\r\n")}
	svc := &ClientService{Domain: f.s, Doc: clientHistoryDoc(t), WorkspaceAuthority: clientWorkspaceAuthority{}, WorkspaceFiles: port, Host: ClientHostInfo{CoreBuildID: "workspace-fixture"}}
	sid := ID()
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if err := f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record()); err != nil {
			return err
		}
		now := time.Now().UTC()
		expires := now.Add(time.Hour)
		return MapClientSession(context.Background(), tx, ClientSession{ID: sid, ProjectID: f.project, Revision: 1, WriterEpoch: 1, WriterClientID: b.ClientID, WorkspaceRef: &b.AuthorizedRef, UpstreamSession: ID(), CreatedAt: now, UpdatedAt: now, LeaseExpiresAt: &expires, Protocol: ProtocolV2})
	})
	return f, svc, port, b, sid
}

func (p *clientWorkspacePort) WorkspaceWrite(ctx context.Context, in ClientWorkspaceWriteInput) (ClientWorkspaceWriteResult, error) {
	p.calls++
	return ClientWorkspaceWriteResult{}, errors.New("test must refuse before the physical writer")
}

func TestClientWorkspaceExpiredLeaseDoesNotReadImport(t *testing.T) {
	f, svc, port, b, sid := clientWorkspaceFixture(t)
	if _, err := f.db.Exec("UPDATE client_sessions SET lease_expires_at=? WHERE id=?", time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), sid); err != nil {
		t.Fatal(err)
	}
	env := workspaceTestEnvelope(f, sid, "artifact.import", Object{"workspace_ref": b.AuthorizedRef, "relative_path": "source.txt", "expected_content_hash": nil, "purpose": "ATTACHMENT"})
	res, _ := executeWorkspaceTest(t, f, svc, env)
	if deref(res.ErrorCode) != "LEASE_EXPIRED" || port.calls != 0 {
		t.Fatalf("expired import touched file: %s calls=%d", Bytes(res), port.calls)
	}
}

func TestClientWorkspaceWriterBlocksRunningAliasOfSameRoot(t *testing.T) {
	o := orchestrationSetup(t)
	task := o.task("editable-task", Empty(), Empty())
	busy := o.task("already-running", Empty(), Empty())
	run := o.claim(busy)
	f, svc, port, b, sid := clientWorkspaceFixtureFor(t, o.f)
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		b.Access = "READ_WRITE"
		b.Revision++
		if err := f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record()); err != nil {
			return err
		}
		alias := *b
		alias.AuthorizedRef = "different-reference-same-actual-root"
		alias.Revision = 1
		if err := f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, alias.AuthorizedRef, alias.record()); err != nil {
			return err
		}
		now := time.Now().UTC()
		runID := Str(run.run, "id")
		taskID := Str(run.task, "id")
		return MapClientSession(context.Background(), tx, ClientSession{ID: ID(), ProjectID: f.project, Revision: 1, WriterEpoch: 1, WriterClientID: "other-client", WorkspaceRef: &alias.AuthorizedRef, TaskID: &taskID, RunID: &runID, UpstreamSession: ID(), CreatedAt: now, UpdatedAt: now, Protocol: ProtocolV2})
	})
	env := workspaceTestEnvelope(f, sid, "workspace.write", Object{"workspace_ref": b.AuthorizedRef, "relative_path": "source.txt", "task_id": task["id"], "expected_content_hash": Digest(port.raw), "text": "changed", "create_if_missing": false})
	res, _ := executeWorkspaceTest(t, f, svc, env)
	if deref(res.ErrorCode) != "SESSION_BUSY" || port.calls != 0 {
		t.Fatalf("running alias allowed publication: %s calls=%d", Bytes(res), port.calls)
	}
}
func workspaceTestEnvelope(f *fixture, sid, method string, payload Object) *Envelope {
	return &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("workspace-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Method: &method, Payload: Bytes(payload)}
}
func executeWorkspaceTest(t *testing.T, f *fixture, svc *ClientService, env *Envelope) (*Response, bool) {
	t.Helper()
	var res *Response
	var replay bool
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		var err error
		res, replay, err = svc.Execute(context.Background(), tx, env, f.owner)
		return err
	})
	return res, replay
}
func TestClientWorkspaceAuthorityAndSessionScope(t *testing.T) {
	for _, tc := range []string{"active", "wrong-principal", "wrong-project", "revoked", "session-mismatch", "host-refusal"} {
		t.Run(tc, func(t *testing.T) {
			f, svc, port, b, sid := clientWorkspaceFixture(t)
			if tc != "active" && tc != "host-refusal" {
				sourceTx(t, f.db, func(tx *sql.Tx) error {
					switch tc {
					case "wrong-principal":
						b.PrincipalID = "other"
					case "wrong-project":
						other := "other"
						b.ProjectID = &other
					case "revoked":
						b.Status = WorkspaceRevoked
					case "session-mismatch":
						_, err := tx.Exec("UPDATE client_sessions SET workspace_ref='other' WHERE id=?", sid)
						return err
					}
					b.Revision++
					return f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record())
				})
			}
			if tc == "host-refusal" {
				svc.WorkspaceAuthority = clientWorkspaceAuthority{err: errors.New("PATH_OUT_OF_SCOPE")}
			}
			env := workspaceTestEnvelope(f, sid, "workspace.tree", Object{"workspace_ref": b.AuthorizedRef, "relative_path": ".", "cursor": nil, "limit": 100})
			res, _ := executeWorkspaceTest(t, f, svc, env)
			if tc == "active" {
				if deref(res.Status) != "COMPLETED" || port.calls != 1 || port.root != b.RealPath || port.access != "READ_ONLY" {
					t.Fatalf("bound host call missing: %s %+v", Bytes(res), port)
				}
				n, _ := Num(res.Result, "root_revision")
				if n != 2 || derefI64(res.Revision, 0) != 1 {
					t.Fatalf("binding revision confused with session revision: %s", Bytes(res))
				}
			} else if deref(res.Status) != "REJECTED" || port.calls != 0 {
				t.Fatalf("unauthorized native I/O: %s calls=%d", Bytes(res), port.calls)
			}
		})
	}
}
func TestClientWorkspaceImportExactBytesReplayAndEpoch(t *testing.T) {
	f, svc, port, b, sid := clientWorkspaceFixture(t)
	body := Object{"workspace_ref": b.AuthorizedRef, "relative_path": "source.txt", "expected_content_hash": Digest([]byte("stale")), "purpose": "ATTACHMENT"}
	env := workspaceTestEnvelope(f, sid, "artifact.import", body)
	res, _ := executeWorkspaceTest(t, f, svc, env)
	if deref(res.ErrorCode) != "CONTENT_CONFLICT" {
		t.Fatalf("stale file imported: %s", Bytes(res))
	}
	var count int
	f.db.QueryRow("SELECT count(*) FROM uploaded_content WHERE content_hash=?", Digest(port.raw)).Scan(&count)
	if count != 0 {
		t.Fatal("failed import left uploaded content")
	}
	body["expected_content_hash"] = Digest(port.raw)
	env = workspaceTestEnvelope(f, sid, "artifact.import", body)
	env.WriterEpoch = revPtr(0)
	before := port.calls
	res, _ = executeWorkspaceTest(t, f, svc, env)
	if deref(res.ErrorCode) != "STALE_WRITER_EPOCH" || port.calls != before {
		t.Fatalf("old writer reached file: %s", Bytes(res))
	}
	env = workspaceTestEnvelope(f, sid, "artifact.import", body)
	res, replay := executeWorkspaceTest(t, f, svc, env)
	if deref(res.Status) != "COMPLETED" || replay || derefI64(res.Revision, 0) != 2 {
		t.Fatalf("import: %s", Bytes(res))
	}
	ref := res.Result["artifact_ref"].(map[string]any)
	var stored []byte
	if err := f.db.QueryRow(`SELECT u.bytes FROM uploaded_content u JOIN domain_objects a ON u.storage_key=json_extract(a.body,'$.storage_key') WHERE a.kind='Artifact' AND a.id=?`, ref["id"]).Scan(&stored); err != nil || string(stored) != string(port.raw) {
		t.Fatalf("sealed bytes changed: %q %v", stored, err)
	}
	before = port.calls
	again, replay := executeWorkspaceTest(t, f, svc, env)
	if !replay || string(Bytes(again)) != string(Bytes(res)) || port.calls != before {
		t.Fatalf("command replay reread or resealed: %s", Bytes(again))
	}
	if err := f.db.QueryRow("SELECT count(*) FROM outbox WHERE json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='ARTIFACT'", sid).Scan(&count); err != nil || count != 1 {
		t.Fatalf("artifact journal count=%d err=%v", count, err)
	}
}
func TestClientWorkspaceTruncatedDiffSealsFullBytes(t *testing.T) {
	f, svc, port, b, sid := clientWorkspaceFixture(t)
	port.raw = []byte("diff --git a/a b/a\n--- a/a\n+++ b/a\n@@ -1 +1 @@\n-old\n+new\n")
	env := workspaceTestEnvelope(f, sid, "workspace.diff", Object{"workspace_ref": b.AuthorizedRef, "base": "HEAD", "relative_path": nil, "max_bytes": 64})
	res, _ := executeWorkspaceTest(t, f, svc, env)
	if deref(res.Status) != "COMPLETED" {
		t.Fatalf("diff: %s", Bytes(res))
	}
	ref := res.Result["full_diff_artifact_ref"].(map[string]any)
	if Str(ref, "content_hash") != Digest(port.raw) {
		t.Fatalf("full diff was not sealed: %s", Bytes(res))
	}
	var raw []byte
	if err := f.db.QueryRow(`SELECT u.bytes FROM uploaded_content u JOIN domain_objects a ON u.storage_key=json_extract(a.body,'$.storage_key') WHERE a.kind='Artifact' AND a.id=?`, ref["id"]).Scan(&raw); err != nil || string(raw) != string(port.raw) {
		t.Fatalf("full patch lost: %q %v", raw, err)
	}
}
