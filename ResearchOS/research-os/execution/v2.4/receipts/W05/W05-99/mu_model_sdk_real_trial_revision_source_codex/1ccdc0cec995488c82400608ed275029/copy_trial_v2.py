from pathlib import Path
import sys
sys.dont_write_bytecode = True
old = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_executable_source_codex/1b8bc13521764e508f540dc2399ac33d/mu_sdk_trial.proposed.py")
new = Path(__file__).resolve().parent / "mu_sdk_trial.v2.proposed.py"
with new.open("xb") as out:
    out.write(old.read_bytes())
print("COPIED_EXACT_OLD_SOURCE_FOR_NEW_REVISION")
