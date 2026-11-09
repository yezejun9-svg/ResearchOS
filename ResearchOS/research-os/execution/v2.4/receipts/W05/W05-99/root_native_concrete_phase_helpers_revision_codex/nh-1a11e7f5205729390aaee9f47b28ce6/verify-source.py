import ast,json,hashlib,types,copy
from datetime import datetime,timezone,timedelta
from pathlib import Path
N=Path(__file__).resolve().parent
D=json.loads((N/"author-inputs.json").read_bytes())
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256="sha256:"+hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (N/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(N/n)
paths=[Path(D["controller"]),Path(D["harness"]),Path(D["A"])/"root_public_api_broker4.actual.py",
 Path(D["C"])/"controller.public.config.json",Path(D["C"])/"native-harness.public.config.json",
 Path(D["C"])/"controller-runtime/controller.closed.json",Path(D["C"])/"controller-runtime/test.invocation.json",Path(D["C"])/"controller-runtime/test.stdout.raw",
 Path(D["C"])/"controller-runtime/sign-release.receipt.json",Path(D["C"])/"controller-runtime/sign-grant.receipt.json",
 Path(D["C"])/"harness-facts/01-release.payload.json",Path(D["C"])/"harness-facts/02-grant.payload.json",
 Path(D["C"])/"harness-facts/fixture.public.json",Path(D["C"])/"harness-facts/06-fixture-retained.ready.json",
 Path(D["S"])/"approve_exact_initial_release_payload.actual.py",Path(D["S"])/"approve_exact_migration_grant_payload.actual.py",Path(D["S"])/"approve_exact_signed_release_publish.actual.py",
 Path(D["B"])/"integration_codex/native-temp-failed-root-release-1791509915469/approve_failed_fixture_specific_release.actual.py"]
refs=[pin(p) for p in paths]
expected={str((Path(D["A"])/"root_public_api_broker4.actual.py").resolve()):("6eeae42516cdb6cad02f09555747c103e4e736c0ca4752dfe210a66c975fb04b",14698),
str((Path(D["C"])/"controller-runtime/controller.closed.json").resolve()):("062393463cc93a22669effe1200f26e15d8f4b0575200a3ac49826770ff3307b",1232140)}
for ref in refs:
 if ref["path"] in expected:assert (ref["sha256"][7:],ref["bytes"])==expected[ref["path"]]
save("sourceguard.initial.json",dict(refs=refs,method="read-only exact before-after Source pins"))
# Preserve only the four prior helper Source texts, not private/provision metadata.
for p in paths[-4:]:
 out=N/"base";out.mkdir(exist_ok=True)
 (out/p.name).write_bytes(p.read_bytes())
hraw=(N/"root_concrete_approval_helper.py").read_bytes()
tree=ast.parse(hraw);archive=ast.parse((N/"public_evidence_archive.py").read_bytes())
m=types.ModuleType("pure_source_test");m.__file__=str(N/"root_concrete_approval_helper.py")
exec(compile(hraw,m.__file__,"exec"),m.__dict__)
results=[]
def ok(name,call):
 call();results.append(dict(name=name,outcome="PASS",kind="pure_Source_contract_control"))
def rejects(name,call):
 try:call()
 except (ValueError,KeyError,TypeError):results.append(dict(name=name,outcome="PASS_EXPECTED_REJECTION",kind="pure_Source_negative_control"))
 else:raise AssertionError(name)
ok("strict_type_positive",lambda:m.require(m.exact({"x":1},{"x":1}),""))
rejects("bool_as_native_exit",lambda:m.native_closed_zero({"actual_exit":False}))
rejects("float_as_native_exit",lambda:m.native_closed_zero({"actual_exit":0.0}))
rejects("duplicate_JSON",lambda:m.decode('{"x":1,"x":2}'))
rejects("nonfinite_JSON",lambda:m.decode('{"x":NaN}'))
rejects("bool_integer_alias",lambda:m.require(m.exact({"x":1},{"x":True}),""))
rec=m.decode((Path(D["C"])/"controller-runtime/sign-release.receipt.json").read_bytes())
ok("actual_archived_signer_closed_zero_fields",lambda:m.native_closed_zero(rec["result"]))
ok("actual_archived_signer_guard_closed",lambda:m.guard_closed(rec["source_guard_cleanup"]))
for flag in m.JOB_FLAGS:
 bad=copy.deepcopy(rec["result"]);bad["job_cleanup"][flag]=False
 rejects("missing_job_flag_"+flag,lambda bad=bad:m.native_closed_zero(bad))
bad=copy.deepcopy(rec["result"]);bad["job_cleanup"]["active_processes_last_observed"]=1
rejects("live_child_remains",lambda:m.native_closed_zero(bad))
bad=copy.deepcopy(rec["source_guard_cleanup"]);bad["retained_handles_count"]=1
rejects("retained_guard_handle",lambda:m.guard_closed(bad))
payload=(Path(D["C"])/"harness-facts/01-release.payload.json").read_bytes()
signed=Path(rec["signed_ref"]["path"]).read_bytes();refs.append(pin(rec["signed_ref"]["path"]))
ok("archived_signed_payload_exact",lambda:m.signed_payload_exact(signed,payload))
rejects("signed_payload_semantically_equal_byte_different",lambda:m.signed_payload_exact(signed,payload+b" "))
rejects("signed_wrapper_duplicate_member",lambda:m.signed_payload_exact(b'{"payload":{},"signature":"x","signature":"y"}',b"{}"))
grant=m.decode((Path(D["C"])/"harness-facts/02-grant.payload.json").read_bytes())
issued=datetime.fromisoformat(grant["issued_utc"].replace("Z","+00:00"));expiry=datetime.fromisoformat(grant["expires_utc"].replace("Z","+00:00"))
ok("archived_interval_synthetic_midpoint_only",lambda:m.validity(grant,"grant",issued+timedelta(seconds=1)))
rejects("grant_expiry_exact_boundary",lambda:m.validity(grant,"grant",expiry))
rejects("grant_future_issued",lambda:m.validity(grant,"grant",issued-timedelta(seconds=1)))
bad=dict(grant,expires_utc=(expiry+timedelta(seconds=1)).isoformat())
rejects("grant_TTL_extension",lambda:m.validity(bad,"grant",issued+timedelta(seconds=1)))
cfg=m.decode((Path(D["C"])/"controller.public.config.json").read_bytes());hc=m.decode((Path(D["C"])/"native-harness.public.config.json").read_bytes())
rejects("T10_terminal_lifecycle_refused",lambda:m.current_phase(cfg,hc,"grant"))
rows={"auth_credentials":{"columns":["token_hash"],"row_digests":["sha256:"+"0"*64]}}
ok("public_typed_digests_allowed",lambda:m.public_rows(rows))
rejects("raw_SQL_rows_forbidden",lambda:m.public_rows({"x":{"columns":["a"],"rows":[["secret"]]}}))
rejects("non_digest_in_rows_forbidden",lambda:m.public_rows({"x":{"columns":["a"],"row_digests":["secret"]}}))
# Static no subprocess/SQL/private-resource open/sign/publish/auto-phase execution paths.
for t in (tree,archive):
 imported={alias.name for n in ast.walk(t) if isinstance(n,(ast.Import,ast.ImportFrom)) for alias in n.names}
 assert not imported.intersection({"subprocess","sqlite3","ctypes","socket","requests"})
 forbidden={"sign_reviewed","publish_signed","release_fixture","serve","poll","snapshot","run_owned","Popen"}
 assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in forbidden for n in ast.walk(t))
 assert not any(isinstance(n,ast.While) for n in ast.walk(t))
assert "private_resource_ref" in hraw.decode() and "Deliberately never follow private_resource_ref" in hraw.decode()
inv=json.loads((Path(D["C"])/"controller-runtime/test.invocation.json").read_bytes())
r=inv["result"];assert r["actual_exit"]==1 and r["owned_child_pid"]==42244 and r["creation_time_100ns"]==134359866411023123 and r["timed_out"] is False and r["job_cleanup"]["termination_requested"] is False
harness=Path(D["harness"]).read_text(encoding="utf-8")
assert "context.WithTimeout(context.Background(), 20*time.Minute)" in harness
assert 'nativeHarnessWait(t, ctx, filepath.Join(cfg.OutputDirectory, "06-release-fixture.approval.json"), "release-fixture")' in harness
fixture=json.loads((Path(D["C"])/"harness-facts/06-fixture-retained.ready.json").read_bytes())
save("T10-lifecycle-cause.json",dict(original_invocation=pin(Path(D["C"])/"controller-runtime/test.invocation.json"),original_stdout=pin(Path(D["C"])/"controller-runtime/test.stdout.raw"),harness_source=pin(D["harness"]),native_PID=r["owned_child_pid"],native_FILETIME_decimal=str(r["creation_time_100ns"]),native_exit=1,elapsed_seconds=r["elapsed_seconds"],timed_out=False,termination_requested=False,cause="20-minute main context expired; cleanup reused expired context and immediately failed after retained.ready; TempDir cleanup followed",retained_database_exists=Path(fixture["database"]).exists(),whole_SQL_inspection_performed=False,fixture_release_approval_generated=False,new_native_execution=False))
save("source-controls.json",dict(controls=results,count=len(results),Python_AST=True,no_approval_generated=True,no_native_SQL_model_Git_Go=True,synthetic_time_control_is_not_actual_phase_acceptance=True))
save("sourceguard.final.json",dict(refs=refs,all_unchanged=all(pin(r["path"])==r for r in refs),method="read-only exact Source pins"))
assert all(pin(r["path"])==r for r in refs)
print(json.dumps(dict(status="SOURCE_CONTROLS_PASS",control_count=len(results),source_inputs=len(refs),new_native_SQL_model_Git_Go=False)))

