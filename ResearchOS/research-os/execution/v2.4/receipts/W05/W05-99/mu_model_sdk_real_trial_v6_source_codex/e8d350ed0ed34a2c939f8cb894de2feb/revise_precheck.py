import pathlib
import sys
sys.dont_write_bytecode = True
here = pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb")
original = (here / "precheck_v6.py").read_text(encoding="utf-8")
assert original.count("mu_sdk_trial.v6.proposed.py") == 1
assert original.count("precheck.v6.json") == 1
updated = original.replace("mu_sdk_trial.v6.proposed.py", "mu_sdk_trial.v6.final.proposed.py")
updated = updated.replace("precheck.v6.json", "precheck.v6.final.json")
with (here / "precheck_v6_final.py").open("xb") as stream:
    stream.write(updated.encode("utf-8"))
print("FINAL_PRECHECK_READY")
