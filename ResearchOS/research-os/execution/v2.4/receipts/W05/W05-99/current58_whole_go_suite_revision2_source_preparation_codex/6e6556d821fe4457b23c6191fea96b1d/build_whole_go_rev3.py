"""Static candidate revision for exact worktree/cwd and reviewed gate bootstrap."""
import ast
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent

def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("rev3 source anchor mismatch: " + old[:60])
    return text.replace(old, new)

gate = (here / "whole58_gate.rev2.proposed.py").read_text(encoding="utf-8")
gate = once(gate, '''    require(scope.get("schema") == execution["scope_schema"]
''', '''    require(root == root.resolve(strict=True)
            and Path.cwd().resolve(strict=True) == root
            and scope.get("worktree") == str(root)
            and absolute(scope["worktree"]) == root,
            "ACTUAL_ROOT_WORKTREE_CWD_NOT_BOUND")
    require(scope.get("schema") == execution["scope_schema"]
''')
gate = once(gate, '''            and registration.get("owner") == scope.get("owner")
''', '''            and registration.get("owner") == scope.get("owner")
            and registration.get("worktree") == str(root)
            and registration.get("cwd") == str(root)
''')
gate = once(gate, '''            and grant.get("environment") == env
''', '''            and grant.get("environment") == env
            and grant.get("worktree") == str(root)
            and grant.get("cwd") == str(root)
''')
gate = once(gate, '''            and lease.get("worktree") == scope.get("worktree")
''', '''            and lease.get("worktree") == scope.get("worktree") == str(root)
''')
gate = once(gate, '''            and paths.get("output_root") == str(output), "ACTIVE_METERS_OR_PATH_AUTHORITY_OPEN")
''', '''            and paths.get("output_root") == str(output)
            and paths.get("worktree") == str(root)
            and paths.get("cwd") == str(root), "ACTIVE_METERS_OR_PATH_AUTHORITY_OPEN")
''')
gate = once(gate, '''    require(_in_current_windows_job(), "RUNNER_LEFT_OUTER_JOB")
''', '''    require(Path.cwd().resolve(strict=True) == root
            and authority["scope"].get("worktree") == str(root)
            and _in_current_windows_job(), "RUNNER_LEFT_OUTER_JOB_OR_CWD")
''')
ast.parse(gate)
gate_raw = gate.encode("utf-8")
gate_sha = hashlib.sha256(gate_raw).hexdigest()

runner = (here / "whole58_finite_runner.rev2.proposed.py").read_text(encoding="utf-8")
runner = once(runner, 'note_overflow(label, count + len(chunk))',
              'note_overflow(label, count - kept + len(chunk))')
runner = once(runner, 'GATE = Path(__file__).with_name("whole58_gate.rev2.proposed.py")',
              'GATE = Path(__file__).with_name("whole58_gate.rev3.proposed.py")')
old_sha_line = next(line for line in runner.splitlines() if line.startswith("GATE_SHA256 = "))
old_bytes_line = next(line for line in runner.splitlines() if line.startswith("GATE_BYTES = "))
runner = once(runner, old_sha_line, f'GATE_SHA256 = "{gate_sha}"')
runner = once(runner, old_bytes_line, f'GATE_BYTES = {len(gate_raw)}')
runner = once(runner, '''import sys
import threading
''', '''import sys
sys.dont_write_bytecode = True
import threading
''')
runner = once(runner, '''    info = GATE.lstat()
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if (not stat.S_ISREG(info.st_mode) or GATE.is_symlink()
            or getattr(GATE, "is_junction", lambda: False)()
            or getattr(info, "st_file_attributes", 0) & reparse
            or GATE.resolve(strict=True) != GATE):
        raise ValueError("GATE_SOURCE_ALIAS_OR_REPARSE")
''', '''    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if ROOT not in GATE.parents or GATE.resolve(strict=True) != GATE:
        raise ValueError("GATE_SOURCE_FOREIGN_OR_ALIAS")
    for item in (GATE, *list(GATE.parents)[:7]):
        info = item.lstat()
        if (item.is_symlink() or getattr(item, "is_junction", lambda: False)()
                or getattr(info, "st_file_attributes", 0) & reparse):
            raise ValueError("GATE_BOOTSTRAP_PARENT_REPARSE")
    info = GATE.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("GATE_SOURCE_NOT_REGULAR")
''')
ast.parse(runner)
contract = json.loads((here / "whole58-execution.contract.rev2.proposed.json").read_bytes())
contract["required_actual_root_gate"].append(
    "canonical scope.worktree, registration/grant/pathauthority cwd and lease.worktree must equal actual ROOT and process cwd before launch and every recheck")
interface = json.loads((here / "authority-interface.rev2.proposed.json").read_bytes())
for key in ("root_registration_binding", "root_grant_binding"):
    interface[key].extend(["worktree=canonical ROOT", "cwd=actual ROOT"])
interface["checkpoint_binding"]["worktree_cwd_current_authority"] = None
interface["actual_cap_preflight"]["gate_bootstrap_parent_reparse_guard"] = True
interface["actual_cap_preflight"]["gate_raw_sha256_before_compile"] = gate_sha
interface["execution_argv_template"][5] = "<whole58_finite_runner.rev4.proposed.py>"
interface["registered_source_manifest"]["must_contain_exact_pins_for"][:2] = [
    "whole58_finite_runner.rev4.proposed.py", "whole58_gate.rev3.proposed.py"]
interface["overflow_observed_bytes_lower_bound"] = (
    "The drainer counts all bytes returned by the cap-crossing read; it never invents unread pipe bytes.")
interface["worktree_cwd_exact_binding"] = ["scope.worktree", "registration.worktree/cwd",
    "grant.worktree/cwd", "lease.worktree", "path_authority.worktree/cwd",
    "runner ROOT", "actual Path.cwd()", "all equal canonical absolute ROOT"]
outputs = [
    ("whole58_gate.rev3.proposed.py", gate_raw),
    ("whole58_finite_runner.rev4.proposed.py", runner.encode("utf-8")),
    ("whole58-execution.contract.rev3.proposed.json",
     (json.dumps(contract, ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
    ("authority-interface.rev4.proposed.json",
     (json.dumps(interface, ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
]
for name, raw in outputs:
    if name.endswith(".py"): ast.parse(raw, filename=name)
    else: json.loads(raw)
for name, raw in outputs:
    with (here / name).open("xb") as stream: stream.write(raw)
print("REV3_SOURCE_READY", gate_sha, len(gate_raw), len(outputs))
