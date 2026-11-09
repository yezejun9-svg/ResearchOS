"""Count every literal replacement against its immutable source, without writes."""
import ast
import pathlib
import sys

sys.dont_write_bytecode = True
root = pathlib.Path("D:/作品集/ResearchOS/research-os")
here = root / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v5_source_codex/39387323960a441ca81f04b9bcdecd17"
old = root / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v4_source_codex/87c5a05ce5054e3c9ffa2f62ba898c57"
inputs = {"v5": (old / "mu_sdk_trial.v4.proposed.py").read_text(encoding="utf-8"),
          "cli": (root / "apps/cli/cli_stream.go").read_text(encoding="utf-8")}
tree = ast.parse((here / "build_source.py").read_text(encoding="utf-8"))
result = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "replace_once":
        if len(node.args) != 4 or not isinstance(node.args[0], ast.Name):
            continue
        source_name = node.args[0].id
        if source_name not in inputs:
            continue
        needle = ast.literal_eval(node.args[1])
        label = ast.literal_eval(node.args[3])
        result.append((label, source_name, inputs[source_name].count(needle)))
for label, source_name, count in result:
    print(f"{label}|{source_name}|{count}")
print("ALL_ONE=" + str(bool(result) and all(x[2] == 1 for x in result)))
