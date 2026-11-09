import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
import re
import traceback
Q=Path(__file__).resolve().parent
def main():
    details=json.loads((Q/"trial-detail-safe-metadata.json").read_text(encoding="utf-8"))
    focused=[]
    for doc in details["documents"]:
        if Path(doc["source_ref"]["path"]).name in {"input.model-trial.actual.json","runtime-profile.actual-sealed.json"}:
            focused.append({"source_ref":doc["source_ref"],"metadata":[row for row in doc["safe_metadata"]
                if re.search(r"capture|ledger|request|provider|output|root|run_uuid|clock|deadline|duration|started|model|credential",row["pointer"],re.I)
                and not re.search(r"tools|argv|permissions|tool_policy|effect_routes/1",row["pointer"])],
                "public_refs":[item for item in doc["discovered_public_refs"] if re.search(r"runner|trial_v9|host|clock|capture|source",item["pointer"],re.I)]})
    discovery=json.loads((Q/"discovery.json").read_text(encoding="utf-8"))
    v9=[row for row in discovery["registered_relevant_public_refs"] if "mu_model_sdk_real_trial_v9_source_codex" in row["resolved_public_path"]]
    print(json.dumps({"focused":focused,"registered_v9_source_refs":v9},ensure_ascii=False))
code=0
try: main()
except Exception: traceback.print_exc(); code=1
finally: print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)
