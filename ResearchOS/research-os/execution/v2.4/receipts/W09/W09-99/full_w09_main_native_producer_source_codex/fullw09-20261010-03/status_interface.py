"""After sealing, call the unchanged production package_refs entry point only."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
N = Path(__file__).resolve().parent
runtime = N / "full_w09_runtime.source.py"
expected_runtime = "1709bc96848fb52fe4ddde8591fe063576515aaabdc63d35630b1023a82ccc08"
actual_runtime = hashlib.sha256(runtime.read_bytes()).hexdigest()
assert actual_runtime == expected_runtime
spec = importlib.util.spec_from_file_location("full_w09_v3_status_interface", runtime)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
handoff, manifest, members = module.package_refs()
hdf = module.decode(module.read_ref(handoff))
assert hdf["status"] == "SOURCE_READY_PENDING_INDEPENDENT_REVIEW"
assert hdf["execution_grant"] is False
assert hdf["actual_executed"] is False
assert len(members) >= 8
print(json.dumps({"status": "PASS_UNCHANGED_PACKAGE_REFS", "runtime_sha256": actual_runtime,
                  "HDF": handoff, "MF": manifest, "read_refs": len(members),
                  "execution_grant": False}, ensure_ascii=False))
