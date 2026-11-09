import ast
import pathlib
import sys
sys.dont_write_bytecode = True
root = pathlib.Path("D:/作品集/ResearchOS/research-os")
here = root / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb"
old = root / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v5_source_codex/39387323960a441ca81f04b9bcdecd17/mu_sdk_trial.v5.final.proposed.py"
tree = ast.parse((here / "build_v6.py").read_text(encoding="utf-8"))
needle = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "needle" for t in node.targets))
source = old.read_text(encoding="utf-8")
checks = {"multi_row_anchor": source.count(needle),
          "function_anchor": source.count("def verified_cli_context_transition("),
          "return_anchor": source.count('return {"original_jsonl_command": name, "admission_method": methods[-1],')}
print(checks)
print("ALL_ONE=" + str(all(value == 1 for value in checks.values())))
