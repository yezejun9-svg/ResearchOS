"""Read only nonsecret current execution-policy pointers; never print credential data."""
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[7]
cp = json.loads((root / "execution/v2.4/checkpoint.json").read_bytes())
wip = cp.get("work_in_progress", {})
out = {"checkpoint_top_keys": sorted(cp.keys()),
       "wip_policy_key_names": sorted(k for k in wip if any(x in k.lower() for x in
                                                        ("budget", "policy", "grant", "scope", "provider"))),
       "live_budget_resource_ref": wip.get("live_budget_resource_ref"),
       "active_policy_refs": {k: wip[k] for k in wip if k in
                              ("budget_policy_ref", "active_budget_policy_ref",
                               "live_budget_policy_ref", "provider_budget_policy_ref")}}
print(json.dumps(out, ensure_ascii=False, sort_keys=True))
