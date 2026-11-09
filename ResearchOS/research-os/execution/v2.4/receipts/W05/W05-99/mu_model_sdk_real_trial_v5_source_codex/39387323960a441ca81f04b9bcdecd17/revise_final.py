"""Exclusive final revision: require writer receipt even on an exact-byte no-write."""
import ast
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v5_source_codex/39387323960a441ca81f04b9bcdecd17")
prior = (HERE / "mu_sdk_trial.v5.proposed.py").read_text(encoding="utf-8")
before = '''        if config[0] != prior:
            context_evidence = verified_cli_context_transition(label, old, parsed, config[1])
        else:
            context_evidence = {"unchanged_original_bytes": True}
'''
after = '''        context_evidence = verified_cli_context_transition(label, old, parsed, config[1])
        if config[0] == prior:
            context_evidence["unchanged_original_bytes"] = True
'''
assert prior.count(before) == 1
final = prior.replace(before, after)
ast.parse(final)
target = HERE / "mu_sdk_trial.v5.final.proposed.py"
with target.open("xb") as stream:
    stream.write(final.encode("utf-8"))
raw = target.read_bytes()
assert raw == final.encode("utf-8")
print(json.dumps({"final_runner_sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                  "no_write_receipt_required": True}, ensure_ascii=False))
