"""SYNTHETIC_NONAUTHORITATIVE source checks; never a product acceptance run."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile

REPO = Path(__file__).resolve().parents[7]
PACKET = Path(__file__).resolve().parent
before = (PACKET / "formal_case_index.before.py").read_bytes()
after = (PACKET / "formal_case_index.after.py").read_bytes()
profile_source = (PACKET / "formal_profile_w09.after.py").read_bytes()
assert before[:51719] == after[:51719]
assert hashlib.sha256(after[:51719]).hexdigest() == "92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1"
ast.parse(after)
ast.parse(profile_source)
index = {"__name__": "synthetic_index"}
exec(compile(after, "formal_case_index.after.py", "exec"), index)
profile = {"__name__": "synthetic_profile"}
exec(compile(profile_source, "formal_profile_w09.after.py", "exec"), profile)
api = index["_profile_api"]()
reader = index["Reader"](REPO)
router_path = reader.path("ops/ci/w09_formal_router.py")
router = profile["_router_contract"](api, reader, {router_path: index["sha256"](router_path)})
assert {tuple((route[0], route[2], route[3])) for route in router["NATIVE"]} == set(profile["ROUTES"])
plan = json.loads((REPO.parent / "ResearchOS_Implementation_Package_v2.4/contracts/execution.plan.json").read_text(encoding="utf-8"))
step = next(row for row in plan["steps"] if row["id"] == "W09-99")
assert {(row["key"], row.get("check_id", ""), row.get("case_id", ""))
        for row in step["verification_commands"]} == set(profile["ROUTES"])
controls = ["W07_COMPAT_PREFIX_EXACT", "AFTER_AST_PARSE", "TRUSTED_ROUTER_LITERAL_MATCHES_FROZEN_SIX"]
with tempfile.TemporaryDirectory(prefix="researchos-w09-synthetic-") as temp:
    root = Path(temp)
    raw_path = root / "execution/v2.4/receipts/W09/W09-99/raw.json"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text('{"actual":{"ok":true}}', encoding="utf-8")
    ref = {"path": raw_path.relative_to(root).as_posix(),
           "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
           "locator": {"json_pointer": "/actual"}}
    synth_reader = index["Reader"](root)
    assert profile["_raw"](api, synth_reader, ref) == {"ok": True}
    controls.append("W09_RAW_LOCATOR_POSITIVE_SYNTHETIC")
    for label, bad in (
        ("MISSING_POINTER_REJECTED", dict(ref, locator={"json_pointer": "/missing"})),
        ("HASH_DRIFT_REJECTED", dict(ref, sha256="0" * 64)),
        ("CROSS_OWNER_PATH_REJECTED", dict(ref, path="execution/v2.4/receipts/W04/W04-99/raw.json")),
    ):
        try:
            profile["_raw"](api, synth_reader, bad)
        except index["InvalidEvidence"]:
            controls.append(label)
        else:
            raise AssertionError(label)
    synth_reader.finish()

print(json.dumps({"schema": "researchos.w09-formal-profile-source-controls.v1",
                  "scope": "SYNTHETIC_NONAUTHORITATIVE", "status": "PASS_SOURCE_ONLY",
                  "checks": controls, "formal_acceptance": False,
                  "native_executions": 0, "dispatcher_executions": 0}, indent=2))
