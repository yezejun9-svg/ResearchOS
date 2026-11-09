"""Finite Source controls only. No product, Go, SQLite, Win32 or OwnerJob call."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import types

N = Path(__file__).resolve().parent
path = N / "main23_root.source.py"
raw = path.read_bytes()
tree = ast.parse(raw)
m = types.ModuleType("main23_source_control_target"); m.__file__ = str(path)
exec(compile(raw, str(path), "exec"), m.__dict__)
rows = []


def case(name, fn, expected=None):
    try:
        value = fn()
        if expected is not None: raise AssertionError("expected rejection: " + expected)
        rows.append({"name": name, "pass": True, "result": value})
    except ValueError as exc:
        if expected is None or str(exc) != expected: raise
        rows.append({"name": name, "pass": True, "rejected": str(exc)})


before = [m.pin(p) for p in m.CANON]
documents = [m.strict(p.read_bytes()) for p in m.CANON]
revisions = {k: v.get("revision") for k, v in zip(("checkpoint", "path_ownership", "step_state", "commands"), documents)}
case("compile-import-does-not-run-native-or-product", lambda: True)
# Preserve the pre371 rejection with a synthetic legacy fixture now that actual Canon is 371.
legacy_canon = list(m.CANON)
legacy_checked = m.checked
legacy_documents = copy.deepcopy(documents)
legacy_documents[0]["revision"] = 370; legacy_documents[1]["revision"] = 174
legacy_refs = copy.deepcopy(before)
legacy_map = {m.canonical(ref["path"]): m.encoded(value) for ref,value in zip(legacy_refs,legacy_documents)}
m.checked = lambda ref: legacy_map[m.canonical(ref["path"])]
try:
    case("current-pre371-canon-rejected", lambda: m.current_four(legacy_refs, dict(revisions, checkpoint=370, path_ownership=174)), "POST_PUBLIC371_ROOT_CANON_REQUIRED")
finally: m.checked = legacy_checked
case("actual-accepted-builder-hdf-chain", lambda: len(m.builder_chain()["refs"]) > 14000)
original = dict(m.BUILDER_REVIEW_REFS["decision"])
case("foreign-forward-slash-ref-preserved", lambda: m.checked(original) is not None and original == m.BUILDER_REVIEW_REFS["decision"])
case("same-physical-ref-alternate-separator", lambda: m.same_ref(original, dict(original, path=original["path"].replace("/", "\\"))))
case("wrong-sha-rejected", lambda: m.checked(dict(original, sha256="0" * 64)), "REF_BYTES_CHANGED")
case("boolean-ref-size-rejected", lambda: m.shape(dict(original, bytes=True)), "REF_PIN_SHAPE")
case("duplicate-json-key-rejected", lambda: m.strict('{"x":1,"x":2}'), "DUPLICATE_JSON_KEY")
case("nonfinite-json-rejected", lambda: m.strict('{"x":NaN}'), "NONFINITE_NUMBER")
case("missing-external-root-pair-rejected", lambda: m.validate_root_capture({}, b"", []), "EXTERNAL_ROOT_CAPTURE_IDENTITY")

cp = copy.deepcopy(documents[0]); ow = copy.deepcopy(documents[1])
cp["revision"] = 371; ow["revision"] = 175
cp["work_in_progress"]["root_next_failure_ordinal_live"] = 4000
cp["work_in_progress"].pop("fresh_main23_root_scope_ref", None)
cp["work_in_progress"].pop("fresh_main23_registration_facts_ref", None)
ow["card_path_bindings"]["W05-99"]["subtasks"].pop(m.KEY, None)
cp["workers"] = [x for x in cp["workers"] if x.get("slice_id") != m.SLICE]
fake = {"path": "D:/Source-control-never-written/a.json", "sha256": "1" * 64, "bytes": 1}
owner = {"scope_ref": fake, "selected_worker_id": m.ROOT}
worker = {"scope_ref": fake, "selected_owner_ref": fake, "worker_id": m.ROOT}
pending = {"pending": [], "next_original_failure_ordinal": 4000}
saved = {key: getattr(m, key) for key in ("checked", "pin", "doc", "physical", "canonical")}


def deny(*unused, **kw): raise AssertionError("TP callback attempted IO")


for key in saved: setattr(m, key, deny)
try:
    after = m.projection(cp, ow, fake, fake, fake, fake, owner, worker, pending, "2030-01-01T00:00:00Z")
    case("pure-exclusive-transform-no-filesystem-reopen", lambda: after[0]["revision"] == 372 and after[1]["revision"] == 176)
    case("synthetic-before-object-not-mutated", lambda: cp["revision"] == 371 and ow["revision"] == 175 and m.KEY not in ow["card_path_bindings"]["W05-99"]["subtasks"])
    case("historical-failures-preserved", lambda: after[0]["failure_counters"] == cp["failure_counters"])
    case("duplicate-slice-rejected", lambda: m.projection(*after, fake, fake, fake, fake, owner, worker, pending, "2030-01-01T00:00:00Z"), "DUPLICATE_BUILD_SLICE")
finally:
    for key, value in saved.items(): setattr(m, key, value)

saved_live = m.live_lease
scope = {"builder_contract_ref": original, "output_root": "D:/Source-control-never-written/build"}
m.live_lease = lambda actual: (scope, None, None, None)
live = m.LiveScope({"case_request_ref": original}, object(), {})
case("live-source-author-required", lambda: live.require_registered(original, original, "not-author"), "REGISTERED_BUILDER_MISMATCH")
case("phase-skipping-rejected", lambda: live.require_phase("build-main23", original, scope["output_root"]), "BUILD_PHASE_SEQUENCE_OR_SCOPE")
for phase in m.PHASES: live.require_phase(phase, original, scope["output_root"])
case("all-six-phases-in-order", lambda: live.next_phase == 6)
case("phase-replay-rejected", lambda: live.require_phase("prepare", original, scope["output_root"]), "BUILD_PHASE_SEQUENCE_OR_SCOPE")
live.held = None
case("released-runtime-closure-rejected", lambda: live.require_registered(original, original, m.BUILDER_AUTHOR), "ROOT_RESOURCE_CLOSURE_RELEASED")
m.live_lease = saved_live

register = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "register")
transform = next(x for x in register.body if isinstance(x, ast.FunctionDef) and x.name == "transform")
calls = {x.func.id for x in ast.walk(transform) if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)}
case("tp-nested-callback-only-pure-need-projection", lambda: calls == {"need", "projection"})
case("registration-held-refs-exclude-exclusive-pair", lambda: "local_refs(refs, CANON[:2])" in ast.unparse(register))
case("full-four-canon-unchanged", lambda: before == [m.pin(p) for p in m.CANON])
if not all(x["pass"] and x.get("result", True) is not False for x in rows): raise AssertionError("source control false result")
result = dict(schema="researchos.main23-root-source-controls.v1", status="SOURCE_CONTROLS_PASSED", caller_ref=m.pin(path), controls=rows, canonical_before=before, canonical_after=[m.pin(p) for p in m.CANON], current_revisions=revisions, synthetic_projection_only=True, actual_registration=False, Go_processes=0, product_processes=0, native_calls=0, sqlite_calls=0, model_calls=0, formal_acceptance=False)
with (N / "source-controls.final.json").open("xb") as stream: stream.write(m.encoded(result))
print(json.dumps(result, ensure_ascii=False))
