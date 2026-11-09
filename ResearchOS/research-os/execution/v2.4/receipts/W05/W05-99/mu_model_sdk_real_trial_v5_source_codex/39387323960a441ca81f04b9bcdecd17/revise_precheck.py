"""Prepare an exclusive pure-IO control script against the final source."""
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v5_source_codex/39387323960a441ca81f04b9bcdecd17")
old = (HERE / "precheck_context.py").read_text(encoding="utf-8")
old = old.replace('mu_sdk_trial.v5.proposed.py', 'mu_sdk_trial.v5.final.proposed.py')
old = old.replace('precheck.v5.json', 'precheck.v5.final.json')
before = '''# Exact-byte no-write branch remains the original v4 behavior.
old_raw = json.dumps(old, separators=(",", ":")).encode()
prior = {"path": "C:/isolated/config.json", "exists": True,
         "sha256": hashlib.sha256(old_raw).hexdigest(), "bytes": len(old_raw)}
discovery = ({"path": "C:/isolated/discovery.json", "exists": True,
              "sha256": "pinned", "bytes": 1}, b"x")
current = [(prior, old_raw)]
scope["current_consumed_states"] = lambda doc: (discovery, current[0])
doc = {"initial_discovery_state": discovery[0], "_expected_config_state": prior,
       "_pre_child_config_json": old, "_pre_child_config_raw": old_raw}
transition, before, post = after(doc, "cli-run", [])
assert transition["context_evidence"] == {"unchanged_original_bytes": True}
assert before == post == old_raw
checks.append("unchanged_context_exact_bytes_positive")
'''
after = '''# A no-write is accepted only with the original final writer-context receipt.
unchanged_row, _ = fixture("cli-run")
unchanged_row["operations"][0]["method"] = "session.get"
for operation in unchanged_row["operations"]:
    operation["result"]["snapshot"]["revision"] = 4
old_unchanged = dict(old, **unchanged_row["saved_context"])
old_raw = json.dumps(old_unchanged, separators=(",", ":")).encode()
prior = {"path": "C:/isolated/config.json", "exists": True,
         "sha256": hashlib.sha256(old_raw).hexdigest(), "bytes": len(old_raw)}
discovery = ({"path": "C:/isolated/discovery.json", "exists": True,
              "sha256": "pinned", "bytes": 1}, b"x")
current = [(prior, old_raw)]
scope["current_consumed_states"] = lambda doc: (discovery, current[0])
doc = {"initial_discovery_state": discovery[0], "_expected_config_state": prior,
       "_pre_child_config_json": old_unchanged, "_pre_child_config_raw": old_raw}
transition, before, post = after(doc, "cli-run", [unchanged_row])
assert transition["context_evidence"]["unchanged_original_bytes"] is True
assert before == post == old_raw
checks.append("unchanged_context_exact_bytes_with_receipt_positive")
try:
    after(doc, "cli-run", [])
except ValueError:
    checks.append("unchanged_context_missing_receipt_rejected")
else:
    raise AssertionError("unchanged context without a receipt accepted")
'''
assert old.count(before) == 1
new = old.replace(before, after)
with (HERE / "precheck_context.final.py").open("xb") as stream:
    stream.write(new.encode("utf-8"))
print("FINAL_PRECHECK_SOURCE_WRITTEN")
