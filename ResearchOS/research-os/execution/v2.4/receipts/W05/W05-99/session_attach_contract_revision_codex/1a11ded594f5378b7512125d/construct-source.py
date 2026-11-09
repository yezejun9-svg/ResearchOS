"""Source-only attach repair; no Go, native, database or model execution."""
import difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
T=Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1")
B=P.parent.parent
INV=B/"integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2/actual-tagged-compiler-input-inventory.json"
SPEC=Path("D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/22_CLIENT_INTERFACE_DETAILS.md")
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def new(n,b):
 p=P/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(b)
def js(n,v):new(n,(json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
base=T/"internal/domain/client_protocol.go"
raw=base.read_bytes();assert ref(base)["sha256"]=="8eab2b524cbf436a11c48ac40b738c7f682d6c4e59cf58df9f3655fd2ed85bcf"
inventory=json.loads(INV.read_bytes())
matches=[v for v in inventory["build_inputs"] if Path(v["path"]).resolve()==base.resolve()]
assert len(matches)==1 and matches[0]["sha256"].removeprefix("sha256:")==ref(base)["sha256"] and matches[0]["bytes"]==len(raw)
old=raw.decode();code=old;changes=[]
def change(a,b):
 global code
 assert code.count(a)==1,repr(a[:100]);position=code.index(a);code=code.replace(a,b);changes.append({"before":a,"after":b,"position":position})
change('''	// ack reports the session revision *after* every write this command performed, so a
	// client that journals one event and a client that transfers ownership both learn the
	// exact revision to refresh against.
	ack := func(revision int64, result map[string]any) *Response {
		return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method,
			Status: strptr("ACKNOWLEDGED"), SessionID: env.SessionID, Revision: revPtr(revision), Result: result}
	}
''',"")
change('''		// Reacquisition by the current client renews the writer lease through the
		// same CAS and epoch rotation as a handoff. Any queued old claim expires.
''','''		nowT := time.Now().UTC()
		if s.Host.LeaseTTL <= 0 {
			return nil, fmt.Errorf("HOST_LEASE_POLICY_MISSING")
		}
		// A still-valid owner renews only its lease. Expired or missing leases
		// must pass the settled reacquisition path and receive a fresh epoch.
		if sess.writerClientID == deref(env.ClientID) {
			var lease string
			if err := tx.QueryRowContext(ctx, `SELECT COALESCE(lease_expires_at,'') FROM client_sessions WHERE id=? AND project_id=?`,
				sess.sessionID, sess.project).Scan(&lease); err != nil {
				return nil, err
			}
			until, parseErr := time.Parse(time.RFC3339Nano, lease)
			if parseErr == nil && nowT.Before(until) {
				renewed, err := tx.ExecContext(ctx, `UPDATE client_sessions SET lease_expires_at=?
					WHERE id=? AND project_id=? AND revision=? AND writer_epoch=? AND writer_client_id=?
					AND lease_expires_at=? AND sealed_at IS NULL AND archived_at IS NULL`,
					nowT.Add(s.Host.LeaseTTL).Format(time.RFC3339Nano), sess.sessionID, sess.project,
					sess.revision, sess.epoch, deref(env.ClientID), lease)
				if err != nil {
					return nil, err
				}
				n, err := renewed.RowsAffected()
				if err != nil {
					return nil, err
				}
				if n != 1 {
					return reject(sess.revision, sess.epoch, "VERSION_CONFLICT", "writer lease changed before renewal"), nil
				}
				snapshot, err := BuildSessionSnapshot(ctx, tx, s.Doc, sess.project, sess.sessionID)
				if err != nil {
					return nil, err
				}
				return complete(sess.revision, map[string]any{"snapshot": snapshot, "write_owner_acquired": true}), nil
			}
		}
''')
change('''		nowT := time.Now().UTC()
		if s.Host.LeaseTTL <= 0 {
			// A handoff must publish a real writer lease; the TTL comes from host config,
			// and the service refuses to invent one.
			return nil, fmt.Errorf("HOST_LEASE_POLICY_MISSING")
		}
''',"")
change('''		return ack(sess.revision+1, map[string]any{"accepted_at": now, "operation_id": "op-" + deref(env.CommandID),
			"after_sequence": sess.watermark + 1, "related_resource_ref": nil}), nil
''','''		// Ownership and CLIENT_HANDOFF are already written in this transaction.
		// Persist their real terminal result through Execute's existing command
		// identity/idempotency path; replay must not transfer or renew again.
		snapshot, err := BuildSessionSnapshot(ctx, tx, s.Doc, sess.project, sess.sessionID)
		if err != nil {
			return nil, err
		}
		return complete(sess.revision+1, map[string]any{"snapshot": snapshot, "write_owner_acquired": true}), nil
''')
inverse=code
for c in reversed(changes):
 p=c["position"];assert inverse[p:p+len(c["after"])]==c["after"]
 inverse=inverse[:p]+c["before"]+inverse[p+len(c["after"]):]
assert inverse.encode()==raw
# Reconstruct directly from unchanged spans and exact replacements.
rebuilt=old
for c in changes:rebuilt=rebuilt.replace(c["before"],c["after"],1)
assert rebuilt==code
# Only handleWrite's attach branch and its now-unused ACK helper changed.
prefix=old[:old.index("func (s *ClientService) handleWrite(")]
suffix=old[old.index('\tcase "session.control":',old.index("func (s *ClientService) handleWrite(")):]
assert code.startswith(prefix) and code.endswith(suffix)
assert 'ack(' not in code
new("candidate-root/internal/domain/client_protocol.go",code.encode())
js("production-replacements.json",changes)
new("client-protocol-attach.patch","".join(difflib.unified_diff(old.splitlines(True),code.splitlines(True),fromfile="T6/internal/domain/client_protocol.go",tofile="candidate-root/internal/domain/client_protocol.go")).encode())
names=["client_protocol.go","v24_sessions.go","client_protocol_journal.go","client_protocol_sessions.go",
 "client_protocol_configuration.go","client_command_identity.go","client_session_fence.go","session_service.go",
 "client_protocol_configuration_test.go","client_protocol_control_windows_test.go","runtime_configuration_binding_windows_test.go",
 "runtime_typed_client_fixture_windows_test.go","contracts/client.protocol.schema.json"]
pins=[ref(T/"internal/domain"/n) for n in names]+[ref(INV),ref(SPEC)]
js("public-input-pins.json",{"schema":"researchos.attach-repair-public-inputs.v1","inputs":pins,
 "actual_T6_production_pin_verified":True})
js("static-evidence.json",{"schema":"researchos.attach-repair-static.v1",
 "production_baseline_ref":ref(base),"production_candidate_ref":ref(P/"candidate-root/internal/domain/client_protocol.go"),
 "exact_forward_replacements":True,"unchanged_prefix_includes_entire_Execute_and_dispatch_gates":True,
 "unchanged_suffix_includes_entire_session_control_and_journal":True,
 "new_production_imports":False,"schema_or_database_migration":False,
 "new_valid_owner_branch_does_not_call_HandoffEpoch_or_journal":True,
 "existing_settlement_rejection_and_transfer_journal_preserved":True,
 "legacy_ACK_replay_unchanged":True,"Go_gofmt_native_SQL_model_run":False,
 "scope":"valid-owner renewal and already-settled synchronous transfer only",
 "open_branches":["active asynchronous pause/settlement takeover","historical cached attach ACK reconciliation"]})
print(json.dumps({"source_root":str(P),"production":ref(P/"candidate-root/internal/domain/client_protocol.go"),"inputs":len(pins)},ensure_ascii=True))

