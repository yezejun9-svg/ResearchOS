"""One-shot source-only transform; never imports or executes candidate gate."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
source = (HERE / "whole58_gate.proposed.py").read_text(encoding="utf-8")
target = HERE / "whole58_gate.v2.proposed.py"

def replace_once(old, new):
    global source
    if source.count(old) != 1:
        raise SystemExit("source transform anchor not unique")
    source = source.replace(old, new)

replace_once('''def read_pin(claim, expected=None):
    require(isinstance(claim, dict) and set(claim) == {"path", "sha256", "bytes"}, "PIN_SHAPE")
    path = absolute(claim["path"])
    if expected is not None:
        require(path == expected, "PIN_PATH_NOT_EXPECTED")
    require(pin_file(path) == claim, "PIN_DRIFT")
    return path, strict_json(path.read_bytes())
''', '''def check_pin(claim, expected=None):
    require(isinstance(claim, dict) and set(claim) == {"path", "sha256", "bytes"}, "PIN_SHAPE")
    path = absolute(claim["path"])
    if expected is not None:
        require(path == expected, "PIN_PATH_NOT_EXPECTED")
    require(pin_file(path) == claim, "PIN_DRIFT")
    return path


def read_pin(claim, expected=None):
    path = check_pin(claim, expected)
    return path, strict_json(path.read_bytes())
''')
replace_once('''    for row in file_members:
        read_pin(row)
''', '''    for row in file_members:
        check_pin(row)
''')
replace_once('''    require(isinstance(env, dict) and set(env) <= ENV_KEYS and all(isinstance(v, str) for v in env.values())
            and env.get("GOTOOLCHAIN") == env.get("GOPROXY") == env.get("GOSUMDB") == "local"
            if False else isinstance(env, dict), "ENVIRONMENT_SHAPE")
''', '''    require(isinstance(env, dict) and set(env) <= ENV_KEYS
            and all(isinstance(v, str) for v in env.values()), "ENVIRONMENT_SHAPE")
''')
replace_once('''            and attestation.get("tree_hash") == tree.get("frozen_go_tree_hash")
''', '''            and isinstance(tree.get("frozen_go_tree_hash"), str)
            and tree["frozen_go_tree_hash"].startswith("sha256:")
            and attestation.get("tree_hash") == tree["frozen_go_tree_hash"]
''')
replace_once('''    require(output.is_dir() and not list(output.iterdir()), "OUTPUT_ROOT_NOT_FRESH")
''', '''    require(output.is_dir() and not list(output.iterdir()), "OUTPUT_ROOT_NOT_FRESH")
    for cache_key in ("GOCACHE", "GOMODCACHE", "GOTMPDIR", "TEMP", "TMP"):
        cache_path = absolute(env[cache_key])
        require(cache_path.is_dir() and cache_path != output
                and output not in cache_path.parents and cache_path not in output.parents,
                "CACHE_OR_TEMP_ROOT_OVERLAPS_OUTPUT")
''')
replace_once('''    require(scope.get("planned_invocations") == calls
            and budgets["max_primary_go_calls"] >= len(calls), "FINITE_PLAN_NOT_EXACT")
''', '''    require(scope.get("planned_invocations") == calls
            and budgets["max_primary_go_calls"] >= len(calls), "FINITE_PLAN_NOT_EXACT")
    require(scope.get("public_catalog_ref") == finite["public_source_catalog_ref"],
            "PUBLIC_SOURCE_CATALOG_NOT_FIXED")
    check_pin(scope["public_catalog_ref"])
''')
replace_once('''            "grant_ref": auth["grant_ref"], "tree": tree}
''', '''            "grant_ref": auth["grant_ref"], "tree": tree,
            "outer_job_ref": auth["outer_job_ref"], "meter_ref": auth["meter_ref"],
            "path_authority_ref": auth["path_authority_ref"]}
''')
replace_once('''    _heartbeat(root, authority["meter"])
    require(_in_current_windows_job(), "RUNNER_LEFT_OUTER_JOB")
''', '''    for name in ("outer_job_ref", "meter_ref", "path_authority_ref", "registration_ref", "grant_ref"):
        check_pin(authority[name])
    _heartbeat(root, authority["meter"])
    require(_in_current_windows_job(), "RUNNER_LEFT_OUTER_JOB")
''')
with target.open("xb") as handle:
    handle.write(source.encode("utf-8"))
print(target)
