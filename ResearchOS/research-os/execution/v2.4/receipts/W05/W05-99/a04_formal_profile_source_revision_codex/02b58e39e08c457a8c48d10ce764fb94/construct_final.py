"""Additive final source preparation; preserves all intermediate candidate bytes."""
import ast,difflib,hashlib,json
from pathlib import Path
ROOT=Path("D:/作品集/ResearchOS/research-os")
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_revision_codex/02b58e39e08c457a8c48d10ce764fb94")
def pin(p):
 raw=p.read_bytes();return {"path":str(p).replace("\\","/"),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def put(name,raw):
 with (BASE/name).open("xb") as f:f.write(raw)
 return pin(BASE/name)
def edit(text,a,b):
 if text.count(a)!=1:raise ValueError("Final source anchor:"+a[:70])
 return text.replace(a,b)
p=(BASE/"formal_profile_w05.v2.proposed.py").read_text(encoding="utf-8")
p=edit(p,"run.get('children_stopped') is not True or run.get('queue_empty') is not True:","run.get('children_stopped') is not True or run.get('queue_empty') is not True or state.get('children_stopped') is not True or state.get('queue_empty') is not True:")
p=edit(p,"for row in rows:\n        if row['lane'] != ASSERTION_LANES[row['id']]:","for row in rows:\n        if row.get('status') != 'PASS' or not row.get('actual') or type(row.get('raw_evidence_refs')) is not list or not row['raw_evidence_refs']:\n            raise ValueError('OPEN_ASSERTION_RESULT')\n        proof = doc(row['raw_evidence_refs'][0])\n        if type(proof) is not dict or proof.get('schema') != 'researchos.w05.a04-raw-observation.v1' or proof.get('assertion_id') != row['id'] or proof.get('run_id') != bundle['run_id'] or proof.get('lane') != row['lane'] or type(proof.get('facts')) is not dict or not proof['facts'] or type(proof.get('fact_source_refs')) is not dict or set(proof['facts']) != set(proof['fact_source_refs']):\n            raise ValueError('OPEN_EMPTY_OR_UNBOUND_FACT_PROJECTION')\n        for key, reference in proof['fact_source_refs'].items():\n            if reference.get('path') not in originals or reference.get('path') == row['raw_evidence_refs'][0]['path'] or doc(reference) != proof['facts'][key]:\n                raise ValueError('OPEN_UNBOUND_FACT_SOURCE')\n        if row['lane'] != ASSERTION_LANES[row['id']]:")
p=edit(p,"originals = context['product_original_paths']","accounting = bundle.get('accounting')\n    if type(accounting) is not dict or set(accounting) != {'mode', 'status', 'amount_usd', 'source_refs'} or accounting['mode'] not in ('UNLIMITED_AMOUNT', 'CAPPED') or type(accounting['source_refs']) is not list or not ((accounting['status'] == 'UNKNOWN' and accounting['amount_usd'] is None) or (accounting['status'] == 'RECORDED' and type(accounting['amount_usd']) in (int, float) and accounting['amount_usd'] >= 0 and accounting['source_refs'])):\n        raise ValueError('OPEN_UNKNOWN_AMOUNT_IS_NULL')\n    if grant.get('accounting_mode') != accounting['mode'] or issuance.get('schema') != 'researchos.w05.original-root-grant-issuance.v2' or issuance.get('actor_id') != 'codex:/root' or issuance.get('run_id') != bundle['run_id'] or type(issuance.get('original_input')) is not dict or type(issuance.get('original_result')) is not dict or type(issuance['original_result'].get('exit_code')) is not int or issuance['original_result']['exit_code'] != 0:\n        raise ValueError('OPEN_ROOT_GRANT_ACTUAL_ISSUANCE')\n    observed = [_json_original(line) for line in _nonempty(issuance['original_result'].get('output'), 'Root grant original output').splitlines() if line.startswith('{')]\n    if len(observed) != 1 or observed[0].get('grant_ref') != bundle['root_grant_ref']:\n        raise ValueError('OPEN_ROOT_GRANT_ORIGINAL_OUTPUT')\n    originals = context['product_original_paths']")
p_ref=put("formal_profile_w05.final.proposed.py",p.encode())
h=(BASE/"runtime_w05_live.v2.proposed.py").read_text(encoding="utf-8")
oldpin=pin(BASE/"formal_profile_w05.v2.proposed.py")["sha256"]
if h.count(oldpin)!=2:raise ValueError("Expected profile hash pair")
h=h.replace(oldpin,p_ref["sha256"])
h=edit(h,"token.isdigit() and int(token) < len(value)","(token == '0' or token.isascii() and token.isdigit() and not token.startswith('0')) and int(token) < len(value)")
h_ref=put("runtime_w05_live.final.proposed.py",h.encode())
e_ref=put("export_a04_live.final.proposed.py",(BASE/"export_a04_live.v2.proposed.py").read_bytes())
construct=json.loads((BASE/"construction.actual.json").read_bytes());targets=dict(construct["source_pins"])
targets.update({"execution/v2.4/formal_profile_w05.py":p_ref,"ops/ci/runtime_w05_live.py":h_ref,"ops/ci/export_a04_live.py":e_ref})
old=ROOT/"execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_preparation_codex/a61c549b78aa4f2ea3ccf4857e44838e"
before=json.loads((old/"handoff.json").read_bytes())["source_pins"]
entries=[];stats=[]
for target,ref in targets.items():
 a=(ROOT/before[target]["path"]).read_bytes();b=Path(ref["path"]).read_bytes();bt=ast.parse(b);at=ast.parse(a)
 if hashlib.sha256(a).hexdigest()!=before[target]["sha256"] or len(a)!=before[target]["bytes"]:raise ValueError("Old source drift")
 x,y=a.decode(),b.decode();nd=list(difflib.ndiff(x.splitlines(keepends=True),y.splitlines(keepends=True)))
 if "".join(difflib.restore(nd,1)).encode()!=a or "".join(difflib.restore(nd,2)).encode()!=b:raise ValueError("Inverse byte mismatch")
 ad={n.name:ast.dump(n,include_attributes=False) for n in at.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 bd={n.name:ast.dump(n,include_attributes=False) for n in bt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 stats.append({"target":target,"exact_copy":a==b,"other_definition_asts_unchanged":sum(ad[k]==bd[k] for k in ad if k in bd),"changed_definitions":[k for k in ad if k in bd and ad[k]!=bd[k]],"new_definitions":[k for k in bd if k not in ad]})
 entries.append({"target":target,"before_ref":before[target],"after_ref":ref,"raw_bidirectional_restore_exact":True,"inverse_unified_diff":"".join(difflib.unified_diff(y.splitlines(keepends=True),x.splitlines(keepends=True),fromfile=ref["path"],tofile=before[target]["path"]))})
iv=put("source.inverse.final.json",(json.dumps({"schema":"researchos.a04-source-revision-inverse.v1","entries":entries},ensure_ascii=False,indent=2)+"\n").encode())
out=put("construction.final.actual.json",(json.dumps({"source_pins":targets,"inverse_ref":iv,"ast_matrix":stats,"candidate_entrypoints_executed":False,"sql_native_model_calls":0,"actual_root_authority":None,"status":"SOURCE_PROPOSAL_WITH_OPEN"},ensure_ascii=False,indent=2)+"\n").encode())
print(json.dumps({"construction_ref":out,"source_pins":targets,"inverse_ref":iv,"ast_matrix":stats},ensure_ascii=False))

