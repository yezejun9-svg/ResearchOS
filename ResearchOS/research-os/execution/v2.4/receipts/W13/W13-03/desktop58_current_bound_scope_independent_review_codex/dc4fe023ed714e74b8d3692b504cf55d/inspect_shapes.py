import json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r336-dc4fe023ed714e74b8d3692b504cf55d'
b=json.loads((N/'binding.pre-review.json').read_bytes());s=json.loads((N/'scope_registration.json').read_bytes());q=json.loads((N/'root-construction.parameters.desktop58.json').read_bytes())
ow=json.loads((R/'execution/v2.4/path_ownership.json').read_bytes());st=ow['card_path_bindings']['W13-03']['subtasks']
obs=json.loads((N/'tool-observations.fifth-construction.closed.original.json').read_bytes())
print(json.dumps({'prior_lease':st.get('desktop58_finite_validation'),'sourcelease':st.get('desktop_exact15_source_integration'),'obs_keys':list(obs),'qkeys':list(q),'bindingkeys':list(b),'rootinputkeys':list(json.loads((N/'root-inputs.desktop58.pre-review.json').read_bytes()))},ensure_ascii=False))

