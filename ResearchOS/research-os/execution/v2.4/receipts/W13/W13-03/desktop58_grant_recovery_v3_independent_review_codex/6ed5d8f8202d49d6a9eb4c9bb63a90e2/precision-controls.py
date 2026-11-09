"""Pure predicate counterexamples only. No observer, gate or recovery execution."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path("D:/作品集/ResearchOS/research-os")
source = ROOT / "execution/v2.4/receipts/W05/W05-99/scope7_grant_recovery_postgate_observer_source_preparation_codex/7716ce1dbb0849eb9dc0fd52457047e8/scope7_grant_recover.v3.proposed.py"
raw = source.read_bytes()
assert len(raw) == 35703 and hashlib.sha256(raw).hexdigest() == "861385985841f257a14665a70a6dffa9e5d9fd754cf6ddc83434071ada87310b"
tree = ast.parse(raw)
observe = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "observe")
predicate = next(n for n in observe.body if isinstance(n, ast.Expr) and ast.unparse(n).endswith("' owned CIM PID/creation/parent chain mismatch')"))
def need(ok, message):
    if not ok:
        raise RuntimeError(message)
code = compile(ast.Module(body=[predicate], type_ignores=[]), "<exact-creation-predicate>", "exec")
born = 134359248965439659
base = {"need": need, "phase": "synthetic-precision", "python_pid": 101, "wrapper_pid": 100,
        "python_birth": born - 10000000, "result": {"owned_child_pid": 102, "creation_time_100ns": born},
        "SOURCE": source,
        "own": {"ProcessId": 102, "CreationTime100ns": born, "ParentProcessId": 101, "CommandLine": "Get-CimInstance Win32_Process"},
        "parent": {"ProcessId": 101, "CreationTime100ns": born - 10000000, "ParentProcessId": 100, "CommandLine": source.name},
        "wrapper": {"ProcessId": 100, "CreationTime100ns": born - 20000000, "CommandLine": source.name}}
exec(code, base)
rounded = copy.deepcopy({k:v for k,v in base.items() if k != "__builtins__"})
for key in ("own", "parent", "wrapper"):
    rounded[key]["CreationTime100ns"] -= rounded[key]["CreationTime100ns"] % 10
try:
    exec(code, rounded)
except RuntimeError as exc:
    rejection = str(exc)
else:
    raise AssertionError("The exact-equality precision counterexample was not reproduced")
out = {"schema": "researchos.scope7-v3-creation-precision-counterexample.v1",
       "source_sha256": hashlib.sha256(raw).hexdigest(), "source_bytes": len(raw),
       "checks": [{"name":"synthetic identical 100ns values accepted","result":"PASS"},
                  {"name":"same identities with CIM microsecond representation rejected","result":"CONFIRMED_BLOCKER","error":rejection}],
       "historical_actual_FILETIME_used": born, "representable_CIM_FILETIME": born - born % 10,
       "documentation": ["https://learn.microsoft.com/en-us/windows/win32/wmisdk/cim-datetime",
                         "https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes"],
       "observer_calls":0,"gate_calls":0,"recovery_main_calls":0,"native_product_calls":0,
       "synthetic_predicate_only":True}
p = Path(__file__).parent / "precision-counterexample.json"
with p.open("xb") as f:
    f.write((json.dumps(out,ensure_ascii=False,indent=2)+"\n").encode())
print(json.dumps({"path":p.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size,"checks":2}))

