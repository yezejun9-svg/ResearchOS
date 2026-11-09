from pathlib import Path
import hashlib,json,subprocess,datetime
O=Path(__file__).resolve().parent;ROOT=O.parents[6]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paths=['internal/domain/client_protocol.go','internal/domain/client_protocol_workspaces.go','internal/domain/client_protocol_workspaces_test.go','internal/api/v2_configuration_windows_test.go']
spec=ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
assert sha(ROOT/'internal/api/contracts/client.protocol.schema.json')==sha(spec/'contracts/client.protocol.schema.json')=='8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b'
refs=['internal/domain/client_protocol.go','internal/domain/project_workspace.go','internal/domain/client_protocol_sessions.go','internal/domain/client_workspace.go','internal/domain/client_protocol_configuration.go','internal/api/v2.go','internal/api/v2_configuration_windows_test.go','internal/api/contracts/client.protocol.schema.json']
evidence=[dict(path=x,sha256=sha(ROOT/x)) for x in refs]
for name in ['18_EXISTING_REPOSITORY_MIGRATION.md','22_CLIENT_INTERFACE_DETAILS.md','contracts/client.protocol.schema.json']:
 evidence.append(dict(path=str((spec/name).relative_to(ROOT)),sha256=sha(spec/name)))
failure=ROOT/'execution/v2.4/receipts/W05/W05-99/normal_desktop_first_use_causal_retry04_codex/20261012-current-chat/session-creation-blocked.observed.json'
evidence.append(dict(path=str(failure.relative_to(ROOT)),sha256=sha(failure)))
report=dict(schema='researchos.workspace-projection-scope-assessment/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='SCOPE_CONFIRMED_FOR_REPAIR_NOT_CANDIDATE_ACCEPTANCE',
 observed_main_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),base_rule='Root must register the actual chosen clean Source base after its ongoing integration; assessment itself does not register or integrate a branch.',
 allowed_paths=paths,additional_paths_required=False,scope='One shared transactional current-principal workspace metadata projection for host.status and workspace.list, plus domain and actual Windows HTTP regression coverage.',
 confirmed_source_facts=[
 'client_protocol.go host.status returns static Host.WorkspaceBind while production composition does not populate the registered durable workspace rows.',
 'workspace.list is an existing V2 method but handleRead has no case, so it falls to NOT_IMPLEMENTED.',
 'WorkspaceBinding.Reply already returns exactly7 frozen fields. Existing ListWorkspaceBindings uses Service.DB outside caller transaction and is not the implementation to call from Execute.',
 'session.create supports offline configuration; no model qualification requirement should be added to solve this projection defect.',
 'Frozen embedded and snapshot client schemas have identical SHA2568943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b.'
 ],
 production_boundaries=[
 'client_protocol.go: wire host.status and workspace.list to one new private helper. Do not retain a fallback to static Host.WorkspaceBind, even if tests inject an apparently valid list.',
 'client_protocol_workspaces.go: read the authenticated current principal/grants with clientAuthenticatedPrincipal using the caller tx, and query only domain_objects project-empty KindWorkspaceBinding rows in that same transaction. No second DB transaction, authority cache, filesystem scan, registration, root repinning or configuration mutation.',
 'Select only exact binding.PrincipalID == authenticated principal. Bound project rows also require current project-level read grant (Allowed(project,empty task,empty run,false)); a role named OWNER and project grant alone never reveal another principals binding. Task/run-only grants do not become project-wide read authority.',
 'Own unbound project_id=null bindings remain visible as existing authorized metadata, without requiring a nonexistent project grant or manufacturing CanCreateProject rights. READ_ONLY stays READ_ONLY; local metadata listing must not acquire write authority or require a model runtime.',
 'Reject a current remote/device principal for the local workspace projection before disclosing paths, even if device/project grants are present. Preserve existing host.status configuration-owner/host identity checks; workspace.list may read eligible local-principal metadata without reusing a configuration-write Owner gate.',
 'Return own eligible REVOKED rows with their current revision/status so historical references remain distinguishable from an empty directory. Listing is not permission to use them: existing read/write/session binding gates must continue rejecting revoked access.',
 'Use validated WorkspaceBinding.Reply objects only: authorized_workspace_ref, display_name, display_path, access, project_id, revision, status. Never return real_path, principal_id, host_principal_ref, client_id, selection_ref, command_id, created_at, credential material or raw DB body.',
 'Validate binding identity/revision and frozen7-field shape; malformed authorized state must fail closed rather than be silently skipped, repaired or reported as empty. Do not query/deserialize other principals rows merely to expose their corruption or metadata.',
 'Stable deterministic ordering. Both endpoints must obey max1000; detect a1001st eligible record and return a published typed RESOURCE_BLOCKED without partial misleading results rather than widening schema, silently truncating or adding pagination.',
 'For equivalent allowed envelope scope, host.status.workspaces equals workspace.list.items. Host-level commands use null session/revision/writer fields; reject inapplicable session/CAS claims. If an existing legal project context is supplied, require its current grant and apply identical project filtering; do not let an unauthorized project claim expose even own unrelated paths. Do not rewrite the frozen envelope schema or blanket-widen route rules.',
 'Keep authentication-before-data behavior and original command identity/replay policy. Fresh reads use new command_id and observe current binding revision/grants/revocation. Exact original read replay remains its original receipt through existing auth checks; never backfill or mutate historical responses to manufacture freshness.',
 'Preserve original write/selection/native SID/ACL/project bootstrap/qualification contracts and zero external/model/tool work.'
 ],
 completion_criteria=[
 'Domain fixture in caller transaction: register produces own unbound ACTIVE rev1; bootstrap updates same row to project-bound ACTIVE rev2; fresh host.status/list return exact same7-field row with rev2 while static Host.WorkspaceBind is empty or hostile.',
 'Before transaction commit, projection observes same-tx mutation without a second connection; rollback leaves no projection-induced mutation. Error/DB failure returns typed rejection or error, never fabricated empty success.',
 'Two principals, two projects: foreign bindings excluded even with OWNER role/shared project grant; removing own current project grant removes that project row on fresh reads; task/run-restricted grants do not authorize entire project; own unbound row remains visible.',
 'Local READ_ONLY metadata remains readable and unmodified; current revoked principal and credential fail at their existing boundary; remote/device request is denied; REVOKED own binding stays visible as REVOKED and new session/file/write use stays refused.',
 'Empty eligible result returns [] not null. Exactly7 fields, schema ValidateResultAgainstMethod for both methods. Inject extra sensitive DB fields and verify no public leakage.',
 '1000 eligible rows schema-valid and stable;1001 typed RESOURCE_BLOCKED with no partial output; foreign rows do not consume the visible limit. Malformed own row fails without dropping it or leaking raw content.',
 'Envelope negatives: foreign project, nonexistent/foreign session, inappropriate expected_revision/writer_epoch, nonempty payload, wrong protocol/native method/secret fields keep published rejection. Direct ClientService and HTTP cases must both enforce current scope rather than relying solely on API prechecks.',
 'Extend actual Windows Host/SID+authenticated loopback test v2_configuration_windows_test.go: existing deterministic native chooser/register/bootstrap/offline host.configure, then derive workspace_ref from fresh host.status/workspace.list (not fixture direct ref) and create a session. Verify exact project/ref/rev2 and zero Task/Run/resource effects/model calls; unqualified send remains rejected.',
 'Preserve original read idempotent replay separately from fresh-command projection. No reset of real Root dataRoot or old receipt/failure count.',
 'Freeze exact new4-file Source candidate, retain raw targeted test failures and final successes, obtain independent review. Root alone integrates/rebuilds and retries actual visible UI with existing data; source/fixture acceptance does not equal actual-first-use or formal acceptance.'
 ],
 test_scope_note='New domain _test.go can use self-contained portable transaction fixtures or an explicit windows build tag if reusing current Windows helpers; no extra source file is necessary. Existing API configuration Windows test already supplies actual Host/SID and deterministic chooser setup.',
 evidence=evidence,not_performed=['Source changes','Canon/ownership registration','Root GUI/process/dataRoot actions','new tests/build','model/tool/provider calls'],
 source_canon_mutations=0,actual_model_calls=0,actual_tool_calls=0,formal_acceptance_delta=0,parent_acceptance_delta=0)
write('scope-assessment.json',report)
(O/'scope-assessment.sha256').write_text(sha(O/'scope-assessment.json')+'\n',encoding='utf-8')
write('manifest.json',dict(decision=report['decision'],files=[dict(path=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']))
print(json.dumps(dict(scope_sha256=sha(O/'scope-assessment.json'),manifest_sha256=sha(O/'manifest.json'))))

