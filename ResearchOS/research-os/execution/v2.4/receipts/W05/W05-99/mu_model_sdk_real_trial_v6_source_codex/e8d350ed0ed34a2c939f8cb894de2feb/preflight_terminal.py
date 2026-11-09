import ast
import pathlib
import sys
sys.dont_write_bytecode = True
here = pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb")
tree = ast.parse((here / "revise_terminal.py").read_text(encoding="utf-8"))
needles = [ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "before" for t in node.targets)]
source = (here / "mu_sdk_trial.v6.final.proposed.py").read_text(encoding="utf-8")
print("ANCHORS=" + str([source.count(needle) for needle in needles]))
