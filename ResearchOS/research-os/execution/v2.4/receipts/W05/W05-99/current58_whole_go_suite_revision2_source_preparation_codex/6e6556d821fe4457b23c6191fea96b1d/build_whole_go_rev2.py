"""Static, exclusive source preparation. This script never imports candidates."""
import ast
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

here = Path(__file__).resolve().parent
old = here.parents[1] / "current58_whole_go_suite_revision_source_preparation_codex/6a9f35409cc34e4784ad92b374d73986"

def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError("source anchor not unique: " + before[:70])
    return text.replace(before, after)

gate = (old / "whole58_gate.v3.proposed.py").read_text(encoding="utf-8")
gate = replace_once(gate, '''def validate_go_tree(tree_ref, attestation_ref, go_ref, locked, root):
''', '''def validate_go_tree(tree_ref, attestation_ref, attestation_review_ref,
                     go_ref, locked, root, run_uuid):
''')
gate = replace_once(gate, '''    _, attestation = read_pin(attestation_ref)
    selection_raw = json.dumps(members, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")
    require(attestation.get("schema") == "researchos.current58-frozen-go-hash-attestation.v1"
            and attestation.get("root_path") == str(go_root)
            and attestation.get("selection_members_sha256") == sha(selection_raw)
            and attestation.get("build_hash") == go_entry["sha256"]
            and isinstance(tree.get("frozen_go_tree_hash"), str)
            and tree["frozen_go_tree_hash"].startswith("sha256:")
            and attestation.get("tree_hash") == tree["frozen_go_tree_hash"]
            and attestation.get("implementation_ref") == pin_file(root / "internal/host/runtime_check_windows.go")
            and attestation.get("producer") == "ROOT_ACTUAL_FROZEN_GO_TOOLCHAIN_HASH"
            and attestation.get("independent_review_ref"), "GO_NATIVE_TREE_ATTESTATION_OPEN")
    _, review = read_pin(attestation["independent_review_ref"])
    require(review.get("decision") == "PASS" and review.get("attestation_ref") == attestation_ref
            and review.get("actor_id") != attestation.get("actor_id"), "GO_TREE_ATTESTATION_NOT_REVIEWED")
''', '''    _, attestation = read_pin(attestation_ref)
    selection_raw = json.dumps(members, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")
    require(attestation.get("schema") == "researchos.current58-frozen-go-hash-attestation.v2"
            and attestation.get("run_uuid") == run_uuid
            and attestation.get("root_path") == str(go_root)
            and attestation.get("go_tree_ref") == tree_ref
            and attestation.get("go_executable_ref") == go_ref
            and attestation.get("locked_toolchain_ref") == pin_file(root / "execution/toolchains/locked.json")
            and attestation.get("selection_members_sha256") == sha(selection_raw)
            and attestation.get("build_hash") == go_entry["sha256"]
            and isinstance(tree.get("frozen_go_tree_hash"), str)
            and tree["frozen_go_tree_hash"].startswith("sha256:")
            and attestation.get("tree_hash") == tree["frozen_go_tree_hash"]
            and attestation.get("implementation_ref") == pin_file(root / "internal/host/runtime_check_windows.go")
            and attestation.get("producer") == "ROOT_ACTUAL_FROZEN_GO_TOOLCHAIN_HASH"
            and attestation.get("actor_id") == "codex:/root"
            and "independent_review_ref" not in attestation,
            "GO_NATIVE_TREE_ATTESTATION_OPEN")
    native_ref = attestation.get("native_result_ref")
    _, native = read_pin(native_ref)
    require(native.get("schema") == "researchos.current58-frozen-go-native-result.v1"
            and native.get("run_uuid") == run_uuid
            and native.get("actual_exit") == 0
            and native.get("go_executable_ref") == go_ref
            and native.get("tree_hash") == attestation["tree_hash"]
            and native.get("build_hash") == attestation["build_hash"]
            and native.get("implementation_ref") == attestation["implementation_ref"],
            "GO_NATIVE_HASH_RESULT_NOT_BOUND")
    _, review = read_pin(attestation_review_ref)
    require(review.get("schema") == "researchos.current58-frozen-go-independent-review.v1"
            and review.get("decision") == "PASS"
            and review.get("run_uuid") == run_uuid
            and review.get("attestation_ref") == attestation_ref
            and review.get("native_result_ref") == native_ref
            and review.get("go_tree_ref") == tree_ref
            and review.get("actor_id") not in (None, "", attestation["actor_id"]),
            "GO_TREE_ATTESTATION_NOT_REVIEWED")
''')
gate = replace_once(gate, '''    go_root, go_path, tree = validate_go_tree(go_tree_ref, scope.get("go_tree_attestation_ref"),
                                              scope.get("pinned_go_ref"), locked, root)
''', '''    go_root, go_path, tree = validate_go_tree(
        go_tree_ref, scope.get("go_tree_attestation_ref"),
        scope.get("go_tree_attestation_review_ref"), scope.get("pinned_go_ref"),
        locked, root, uuid)
''')
gate = replace_once(gate, '''            and registration.get("source_manifest_ref") == scope["source_manifest_ref"],
''', '''            and registration.get("source_manifest_ref") == scope["source_manifest_ref"]
            and registration.get("go_tree_attestation_review_ref") ==
                scope["go_tree_attestation_review_ref"],
''')
gate = replace_once(gate, '''            and review.get("source_manifest_ref") == scope["source_manifest_ref"],
''', '''            and review.get("source_manifest_ref") == scope["source_manifest_ref"]
            and review.get("go_tree_attestation_review_ref") ==
                scope["go_tree_attestation_review_ref"],
''')
gate = replace_once(gate, '''            and grant.get("source_manifest_ref") == scope["source_manifest_ref"]
''', '''            and grant.get("source_manifest_ref") == scope["source_manifest_ref"]
            and grant.get("go_tree_attestation_ref") == scope["go_tree_attestation_ref"]
            and grant.get("go_tree_attestation_review_ref") ==
                scope["go_tree_attestation_review_ref"]
''')
gate = replace_once(gate, '''            "source_manifest_ref": scope["source_manifest_ref"],
''', '''            "source_manifest_ref": scope["source_manifest_ref"],
            "go_tree_attestation_ref": scope["go_tree_attestation_ref"],
            "go_tree_attestation_review_ref": scope["go_tree_attestation_review_ref"],
''')
gate = replace_once(gate, '''    for name in ("outer_job_ref", "meter_ref", "path_authority_ref", "registration_ref", "grant_ref", "source_manifest_ref"):
''', '''    for name in ("outer_job_ref", "meter_ref", "path_authority_ref", "registration_ref",
                 "grant_ref", "source_manifest_ref", "go_tree_attestation_ref",
                 "go_tree_attestation_review_ref"):
''')
ast.parse(gate)
gate_bytes = gate.encode("utf-8")
gate_sha = hashlib.sha256(gate_bytes).hexdigest()

runner = (old / "whole58_finite_runner.v4.proposed.py").read_text(encoding="utf-8")
runner = replace_once(runner, 'before whole58_gate.v2 validates',
                      'before the byte-pinned whole58_gate revision validates')
runner = replace_once(runner, 'import importlib.util\n', 'import stat\nimport types\n')
runner = replace_once(runner, 'GATE = Path(__file__).with_name("whole58_gate.v3.proposed.py")\n',
    'GATE = Path(__file__).with_name("whole58_gate.rev2.proposed.py")\n'
    + f'GATE_SHA256 = "{gate_sha}"\nGATE_BYTES = {len(gate_bytes)}\n')
runner = replace_once(runner, '''def load_gate():
    spec = importlib.util.spec_from_file_location("whole58_gate_future", GATE)
    if spec is None or spec.loader is None:
        raise ValueError("PINNED_GATE_LOAD_OPEN")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    return gate
''', '''def load_gate():
    """Validate raw gate bytes before compile/exec; no SourceFileLoader or pyc."""
    sys.dont_write_bytecode = True
    info = GATE.lstat()
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if (not stat.S_ISREG(info.st_mode) or GATE.is_symlink()
            or getattr(GATE, "is_junction", lambda: False)()
            or getattr(info, "st_file_attributes", 0) & reparse
            or GATE.resolve(strict=True) != GATE):
        raise ValueError("GATE_SOURCE_ALIAS_OR_REPARSE")
    raw = GATE.read_bytes()
    if len(raw) != GATE_BYTES or sha(raw) != GATE_SHA256:
        raise ValueError("GATE_SOURCE_BYTES_NOT_REVIEWED")
    gate = types.ModuleType("whole58_gate_verified_bytes")
    gate.__file__ = str(GATE)
    code = compile(raw, str(GATE), "exec", dont_inherit=True, optimize=0)
    exec(code, gate.__dict__)
    return gate
''')
runner = replace_once(runner, '''    workers = []
    drain_done = {"stdout": False, "stderr": False}
    def fail(code, detail=None):
        item = {"code": code, "detail": detail}
        if receipt["first_cause"] is None:
            receipt["first_cause"] = item
        else:
            receipt["secondary_causes"].append(item)
''', '''    workers = []
    drain_done = {"stdout": False, "stderr": False}
    cause_lock = threading.Lock()
    def fail(code, detail=None):
        item = {"code": code, "detail": detail}
        with cause_lock:
            if receipt["first_cause"] is None:
                receipt["first_cause"] = item
            else:
                receipt["secondary_causes"].append(item)
    def note_overflow(label, observed):
        item = {"code": "OUTPUT_OVERFLOW", "detail": {"stream": label,
                "observed_bytes_lower_bound": observed, "cap_bytes": budgets[label + "_bytes"]}}
        with cause_lock:
            receipt[label + "_overflow"] = True
            receipt[label + "_observed_bytes_lower_bound"] = observed
            if receipt["first_cause"] is None:
                receipt["first_cause"] = item
            else:
                receipt["secondary_causes"].append(item)
''')
runner = replace_once(runner, '''                    if kept < len(chunk):
                        receipt[label + "_overflow"] = True
                        if proc is not None:
                            proc.kill()
                        break
''', '''                    if kept < len(chunk):
                        note_overflow(label, count + len(chunk))
                        if proc is not None:
                            try: proc.kill()
                            except BaseException as exc: fail("KILL_AFTER_OVERFLOW_FAILURE", repr(exc))
                        break
''')
runner = replace_once(runner, '''    if receipt["stdout"] is None:
        raise ValueError("UNPINNED_GO_JSON_RAW")
''', '''    if (receipt.get("first_cause") or receipt.get("stdout_overflow")
            or receipt.get("stderr_overflow") or receipt.get("drain_incomplete")
            or receipt.get("timed_out") or receipt.get("stdout") is None
            or receipt.get("stderr") is None or receipt.get("actual_exit") != 0):
        raise ValueError("INCOMPLETE_OR_OVERFLOWED_GO_JSON_RAW")
''')
runner = replace_once(runner, '''    if receipt["first_cause"] or receipt["actual_exit"] != 0 or not receipt["stdout"]:
''', '''    if (receipt.get("first_cause") or receipt.get("actual_exit") != 0
            or receipt.get("stdout_overflow") or receipt.get("stderr_overflow")
            or receipt.get("drain_incomplete") or receipt.get("timed_out")
            or receipt.get("stdout") is None or receipt.get("stderr") is None):
''')
runner = replace_once(runner, '''    if receipt["first_cause"] or receipt["actual_exit"] != 0 or not receipt["stdout"]:
''', '''    if (receipt.get("first_cause") or receipt.get("actual_exit") != 0
            or receipt.get("stdout_overflow") or receipt.get("stderr_overflow")
            or receipt.get("drain_incomplete") or receipt.get("timed_out")
            or receipt.get("stdout") is None or receipt.get("stderr") is None):
''')
ast.parse(runner)

contract = json.loads((old / "whole58-execution.contract.proposed.json").read_bytes())
contract["go_attestation_review_schema"] = "researchos.current58-frozen-go-independent-review.v1"
contract["go_native_result_schema"] = "researchos.current58-frozen-go-native-result.v1"
contract["required_actual_root_gate"].append(
    "seal native Go tree hash result, then Root attestation, then independent review; scope pins both, with no immutable back-reference")
contract["qualification"]["source_acceptance"] = False
interface = json.loads((old / "authority-interface.proposed.json").read_bytes())
interface["scope_required_fields"].append("go_tree_attestation_review_ref")
interface["root_registration_binding"].append("go_tree_attestation_review_ref")
interface["independent_review_binding"].append("go_tree_attestation_review_ref")
interface["root_grant_binding"].extend(["go_tree_attestation_ref", "go_tree_attestation_review_ref"])
interface["go_tree_attestation_sequence"] = [
    "Root seals an actual native FrozenGoToolchainHash result bound to this run UUID, Go executable, tree hash/build hash and implementation bytes",
    "Root seals attestation with native_result_ref, go_tree_ref, Go executable/locked/implementation pins and no independent_review_ref",
    "Distinct non-author reviewer seals review containing attestation_ref, native_result_ref, tree_ref and run_uuid",
    "Root scope pins both attestation_ref and attestation_review_ref; registration/review/grant bind the latter"]
interface["future_root_literals_assigned"] = False

pending = [
    ("whole58_gate.rev2.proposed.py", gate_bytes),
    ("whole58_finite_runner.rev2.proposed.py", runner.encode("utf-8")),
    ("whole58-execution.contract.rev2.proposed.json",
     (json.dumps(contract, ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
    ("authority-interface.rev2.proposed.json",
     (json.dumps(interface, ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
]
for name, raw in pending:
    if name.endswith(".py"): ast.parse(raw, filename=name)
    else: json.loads(raw)
for name, raw in pending:
    with (here / name).open("xb") as stream: stream.write(raw)
print("REV2_SOURCE_READY", gate_sha, len(gate_bytes), len(pending))
