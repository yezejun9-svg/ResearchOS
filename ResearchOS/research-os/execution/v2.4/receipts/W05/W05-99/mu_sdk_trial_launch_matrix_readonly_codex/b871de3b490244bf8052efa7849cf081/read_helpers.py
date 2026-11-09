import ast,hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
P=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_trial_launch_matrix_readonly_codex/b871de3b490244bf8052efa7849cf081/source-d527eaf03d83208751c046d024747cb42bdc2f806474f8dda7f8ae70c2716a98.raw")
raw=P.read_bytes();tree=ast.parse(raw);lines=raw.decode().splitlines()
names={"current_consumed_states","budget_chain","readonly_db","json_file"}
for n in tree.body:
 if isinstance(n,ast.FunctionDef) and n.name in names:
  print("\nFUNCTION "+n.name)
  for i in range(n.lineno,n.end_lineno+1):print(str(i)+":"+lines[i-1])

