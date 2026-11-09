from pathlib import Path
import json
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-'+O.name)
b=json.loads((N/'binding.pre-review.json').read_bytes());s=json.loads((N/'scope_registration.json').read_bytes());ow=json.loads((R/'execution/v2.4/path_ownership.json').read_bytes());lease=ow['card_path_bindings']['W13-03']['subtasks']['desktop58_finite_validation'];q=json.loads((N/'root-construction.parameters.desktop58.json').read_bytes())
out={'scope_sha_from_parent':'0caa54d359072e7200b7cbbc9fb72742ffb325adc82ad3b4622310ac7549e9c1','lease':lease,'qkeys':list(q),'before':b['before'],'after':b['after'],'authority_semantics':b['authority_semantics'],'selectedmetadata':b['metadata_code_refs'],'allocation':q['allocation']}
with (O/'actual-shapes.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(out,ensure_ascii=False))

