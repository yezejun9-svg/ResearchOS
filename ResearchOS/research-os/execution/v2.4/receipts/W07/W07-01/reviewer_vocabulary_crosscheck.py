"""Reviewer vocabulary cross-check.

Every W0701-* identifier quoted in the receipt and its evidence files must exist in the check program's own
declared roster (computed the way the program computes it). An id that is quoted but not emitted, or emitted but
not declared, is a false statement about the suite. Also re-checks the three ids the card quotes for the
reused adapter tests against the adapter suite's real test names.
"""
import glob
import importlib.util
import io
import json
import os
import re
import subprocess

REPO = r"D:/作品集/ResearchOS/research-os"
SPEC = importlib.util.spec_from_file_location("w0701_check", os.path.join(REPO, "tests", "sources", "check", "main.py"))
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

declared = set(mod.declared_ids())
receipt_dir = os.path.join(REPO, "execution", "v2.4", "receipts", "W07", "W07-01")

quoted = {}
for p in sorted(glob.glob(os.path.join(receipt_dir, "*.json"))):
    text = io.open(p, encoding="utf-8", errors="replace").read()
    for m in re.findall(r"W0701-[A-Z0-9-]+", text):
        quoted.setdefault(m, []).append(os.path.basename(p))

emitted_clean = set()
for p in [os.path.join(receipt_dir, "laundering_probe.json")]:
    d = json.loads(io.open(p, encoding="utf-8").read())
    for run in d.values():
        emitted_clean |= set(run.get("assertion_ids") or [])
        emitted_clean |= {f["id"] for f in run.get("failures") or []}
        # the program counts a not_verified disclosure as an emission of that id
        emitted_clean |= {n.split(":")[0] for n in (run.get("not_verified") or [])}

names = set()
for f in glob.glob(os.path.join(REPO, "internal", "domain", "*_test.go")) + \
         glob.glob(os.path.join(REPO, "adapters", "sources", "*_test.go")) + \
         glob.glob(os.path.join(REPO, "tests", "sources", "**", "*_test.go"), recursive=True):
    names |= set(re.findall(r"^func (TestW07\w*)", io.open(f, encoding="utf-8").read(), re.M))

action_tests = set()
for v in mod.ACTION_TESTS.values():
    action_tests |= set(v)

out = {
    "declared_roster_size": len(declared),
    "declared_ids": sorted(declared),
    "ids_quoted_in_receipt_dir_not_declared": {k: v for k, v in quoted.items() if k not in declared},
    "declared_ids_never_emitted_in_the_clean_run": sorted(declared - emitted_clean),
    "emitted_ids_not_in_declared_roster": sorted(emitted_clean - declared),
    "adapter_tests_named_by_the_card_that_do_not_exist_in_the_tree": sorted(action_tests - names),
    "count_TestW07_tests_found_in_tree": len(names),
    "routing_forward_passes_source_mode": "RESEARCHOS_SOURCE_MODE" in io.open(
        os.path.join(REPO, "tests", "sources", "check", "main.py"), encoding="utf-8").read(),
}
print(json.dumps(out, ensure_ascii=False, indent=1))
